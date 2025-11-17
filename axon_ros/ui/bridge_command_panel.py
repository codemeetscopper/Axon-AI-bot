"""Command controls for the robot bridge inside the simulator UI."""

from __future__ import annotations

import json

from PySide6.QtNetwork import QAbstractSocket
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from robot_control.remote_bridge import RemoteBridgeController


class BridgeCommandPanel(QWidget):
    """Expose the auxiliary Waveshare/WaveRover controls within the simulator."""

    def __init__(self, controller: RemoteBridgeController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._connected = controller.is_connected()
        self._controlled_widgets: list[QWidget] = []
        self._build_ui()
        self._wire_controller()
        self._update_state_label(self._controller.state())
        self._apply_link_state(self._connected)

    # ------------------------------------------------------------------
    # UI construction helpers
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        self.setMinimumWidth(320)

        title = QLabel("Bridge command console")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Send PWM, OLED, telemetry and IO commands through the serial bridge."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.65);")
        layout.addWidget(subtitle)

        status_row = QHBoxLayout()
        status_row.setSpacing(6)
        status_row.addWidget(QLabel("Status:"))
        self._status_label = QLabel("Idle")
        self._status_label.setObjectName("bridgeCommandStatus")
        status_row.addWidget(self._status_label, 1)
        layout.addLayout(status_row)

        command_tabs = QHBoxLayout()
        command_tabs.setSpacing(12)
        command_tabs.addWidget(self._register_control(self._build_pwm_group()))
        command_tabs.addWidget(self._register_control(self._build_oled_group()))
        layout.addLayout(command_tabs)

        info_row = QHBoxLayout()
        info_row.setSpacing(12)
        info_row.addWidget(self._register_control(self._build_info_group()))
        info_row.addWidget(self._register_control(self._build_io_group()))
        layout.addLayout(info_row)

        layout.addWidget(self._register_control(self._build_raw_group()))

        self._log_view = QPlainTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setMaximumBlockCount(400)
        self._log_view.setPlaceholderText("Command log will appear here")
        self._log_view.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0.05);"
            "border-radius: 6px;"
            "font-family: 'JetBrains Mono', 'Fira Code', monospace;"
            "font-size: 12px;"
        )
        layout.addWidget(self._log_view, 1)

    def _register_control(self, widget: QWidget) -> QWidget:
        self._controlled_widgets.append(widget)
        return widget

    def _build_pwm_group(self) -> QGroupBox:
        box = QGroupBox("PWM (T=11)")
        form = QFormLayout()
        box.setLayout(form)

        self._pwm_left = QSpinBox()
        self._pwm_left.setRange(-255, 255)
        self._pwm_left.setAccelerated(True)
        self._pwm_right = QSpinBox()
        self._pwm_right.setRange(-255, 255)
        self._pwm_right.setAccelerated(True)
        form.addRow("Left:", self._pwm_left)
        form.addRow("Right:", self._pwm_right)

        send_button = QPushButton("Send PWM")
        send_button.clicked.connect(self._send_pwm)
        form.addRow(send_button)
        return box

    def _build_oled_group(self) -> QGroupBox:
        box = QGroupBox("OLED (T=3 / T=-3)")
        form = QFormLayout()
        box.setLayout(form)

        self._oled_line = QSpinBox()
        self._oled_line.setRange(0, 3)
        self._oled_line.setValue(0)
        self._oled_text = QLineEdit()
        self._oled_text.setPlaceholderText("Message to display")

        form.addRow("Line:", self._oled_line)
        form.addRow("Text:", self._oled_text)

        button_row = QHBoxLayout()
        send_button = QPushButton("Send text")
        send_button.clicked.connect(self._send_oled_text)
        restore_button = QPushButton("Restore defaults")
        restore_button.clicked.connect(self._restore_oled)
        button_row.addWidget(send_button)
        button_row.addWidget(restore_button)
        form.addRow(button_row)
        return box

    def _build_info_group(self) -> QGroupBox:
        box = QGroupBox("Feedback")
        column = QVBoxLayout()
        column.setSpacing(8)
        box.setLayout(column)

        imu_button = QPushButton("Get IMU (T=126)")
        imu_button.clicked.connect(lambda: self._send_json({"T": 126}, label="IMU request"))
        base_button = QPushButton("Get base (T=130)")
        base_button.clicked.connect(lambda: self._send_json({"T": 130}, label="Base feedback"))
        self._continuous_feedback = QCheckBox("Continuous feedback (T=131)")
        self._continuous_feedback.toggled.connect(self._toggle_continuous_feedback)
        self._serial_echo = QCheckBox("Serial echo (T=143)")
        self._serial_echo.toggled.connect(self._toggle_serial_echo)

        column.addWidget(imu_button)
        column.addWidget(base_button)
        column.addSpacing(4)
        column.addWidget(self._continuous_feedback)
        column.addWidget(self._serial_echo)
        column.addStretch(1)
        return box

    def _build_io_group(self) -> QGroupBox:
        box = QGroupBox("IO4/IO5 (T=132)")
        form = QFormLayout()
        box.setLayout(form)

        self._io4_spin = QSpinBox()
        self._io4_spin.setRange(0, 255)
        self._io5_spin = QSpinBox()
        self._io5_spin.setRange(0, 255)
        form.addRow("IO4 PWM:", self._io4_spin)
        form.addRow("IO5 PWM:", self._io5_spin)

        send_button = QPushButton("Send IO PWM")
        send_button.clicked.connect(self._send_io_pwm)
        form.addRow(send_button)
        return box

    def _build_raw_group(self) -> QGroupBox:
        box = QGroupBox("Raw JSON command")
        row = QHBoxLayout()
        row.setSpacing(6)
        box.setLayout(row)

        self._raw_edit = QLineEdit()
        self._raw_edit.setPlaceholderText('Example: {"T":1,"L":0.5,"R":0.5}')
        send_button = QPushButton("Send")
        send_button.clicked.connect(self._send_raw_json)

        row.addWidget(self._raw_edit, 1)
        row.addWidget(send_button)
        return box

    # ------------------------------------------------------------------
    # Controller wiring & status helpers
    # ------------------------------------------------------------------
    def _wire_controller(self) -> None:
        self._controller.connectionStateChanged.connect(self._handle_state_changed)
        self._controller.remoteActiveChanged.connect(self._handle_link_active)
        self._controller.errorOccurred.connect(
            lambda message: self._append_log(f"[ERROR] {message}")
        )
        self._controller.lineReceived.connect(self._handle_bridge_line)

    def _handle_state_changed(self, state: QAbstractSocket.SocketState) -> None:
        self._update_state_label(state)

    def _handle_link_active(self, active: bool) -> None:
        self._connected = active
        self._apply_link_state(active)

    def _apply_link_state(self, active: bool) -> None:
        for widget in self._controlled_widgets:
            widget.setEnabled(active)
        self._raw_edit.setEnabled(active)
        if not active:
            self._append_log("Bridge inactive - connect via Robot link tab")

    def _update_state_label(self, state: QAbstractSocket.SocketState) -> None:
        label = {
            QAbstractSocket.SocketState.UnconnectedState: "Disconnected",
            QAbstractSocket.SocketState.HostLookupState: "Resolving host",
            QAbstractSocket.SocketState.ConnectingState: "Connecting",
            QAbstractSocket.SocketState.ConnectedState: "Connected",
            QAbstractSocket.SocketState.ClosingState: "Closing",
        }.get(state, "Unknown")
        self._status_label.setText(label)

    def _handle_bridge_line(self, line: str) -> None:
        if line.startswith("telemetry"):
            return
        self._append_log(f"[RX] {line}")

    # ------------------------------------------------------------------
    # Command helpers
    # ------------------------------------------------------------------
    def _append_log(self, text: str) -> None:
        self._log_view.appendPlainText(text)
        bar = self._log_view.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _send_json(self, payload: dict[str, object], *, label: str | None = None) -> bool:
        text = json.dumps(payload)
        try:
            self._controller.send_command(text)
        except RuntimeError as exc:
            self._append_log(f"[ERROR] {exc}")
            return False
        display = label or text
        self._append_log(f"[TX] {display}")
        return True

    def _send_pwm(self) -> None:
        payload = {"T": 11, "L": self._pwm_left.value(), "R": self._pwm_right.value()}
        self._send_json(payload, label=f"PWM L={self._pwm_left.value()} R={self._pwm_right.value()}")

    def _send_oled_text(self) -> None:
        payload = {
            "T": 3,
            "lineNum": int(self._oled_line.value()),
            "Text": self._oled_text.text(),
        }
        self._send_json(payload, label=f"OLED line {payload['lineNum']} text")

    def _restore_oled(self) -> None:
        self._send_json({"T": -3}, label="Restore OLED")

    def _toggle_continuous_feedback(self, checked: bool) -> None:
        if not self._send_json({"T": 131, "cmd": 1 if checked else 0}, label="Continuous feedback"):
            self._continuous_feedback.blockSignals(True)
            self._continuous_feedback.setChecked(not checked)
            self._continuous_feedback.blockSignals(False)

    def _toggle_serial_echo(self, checked: bool) -> None:
        if not self._send_json({"T": 143, "cmd": 1 if checked else 0}, label="Serial echo"):
            self._serial_echo.blockSignals(True)
            self._serial_echo.setChecked(not checked)
            self._serial_echo.blockSignals(False)

    def _send_io_pwm(self) -> None:
        payload = {"T": 132, "IO4": self._io4_spin.value(), "IO5": self._io5_spin.value()}
        self._send_json(payload, label=f"IO pwm IO4={payload['IO4']} IO5={payload['IO5']}")

    def _send_raw_json(self) -> None:
        text = self._raw_edit.text().strip()
        if not text:
            return
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = None
        if payload is not None and isinstance(payload, dict):
            if self._send_json(payload):
                self._raw_edit.clear()
            return
        # fall back to sending the raw string if parsing fails
        try:
            self._controller.send_command(text)
        except RuntimeError as exc:
            self._append_log(f"[ERROR] {exc}")
            return
        self._append_log(f"[TX] {text}")
        self._raw_edit.clear()
