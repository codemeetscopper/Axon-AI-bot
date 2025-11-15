const doc = document;
const body = doc.body;
const themeToggle = doc.querySelector('.theme-toggle');
const themeIcon = doc.querySelector('.theme-toggle__icon');
const yearSpan = doc.querySelector('[data-year]');
const audioPlayer = doc.querySelector('.audio-player audio');
const heroButtons = doc.querySelectorAll('.hero__cta button');
const sampleButtons = doc.querySelectorAll('[data-action="sample"]');
const demoControls = doc.querySelectorAll('.demo__controls .chip');
const demoOutput = doc.querySelector('[data-bind="output"]');
const demoPersona = doc.querySelector('[data-bind="persona"]');
const animateTargets = doc.querySelectorAll('[data-animate]');

const personaSamples = {
  strategist:
    "Axon: Here's the strategic outlook. Primary risk is market compression in Q4; recommend doubling user interviews now while we still have signal clarity. Shall I prep the decision brief?",
  researcher:
    "Axon: I've distilled the long-form research into three citations with confidence scores. The anomaly in dataset beta warrants further review before launch.",
  companion:
    "Axon: I'm here with you. Let's breathe, reframe the challenge, and rally the squad around the next move."
};

const demoResponses = {
  strategist:
    "Mission brief loaded. Prioritizing decisive actions, key metrics, and the trade-offs your leads should weigh in the next review.",
  researcher:
    "Research mode engaged. I'll surface evidence, highlight signal-to-noise ratios, and tag every claim with a source.",
  companion:
    "Collaboration mode active. I'll keep conversation energy high, mirror your tone, and flag when someone needs support."
};

const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');

function applyTheme(theme) {
  body.classList.toggle('theme-light', theme === 'light');
  themeIcon.textContent = theme === 'light' ? '🌙' : '☀️';
  window.localStorage.setItem('axon-theme', theme);
}

function initializeTheme() {
  const stored = window.localStorage.getItem('axon-theme');
  if (stored) {
    applyTheme(stored);
  } else {
    applyTheme(prefersDark.matches ? 'dark' : 'light');
  }
}

function toggleTheme() {
  const current = body.classList.contains('theme-light') ? 'light' : 'dark';
  applyTheme(current === 'light' ? 'dark' : 'light');
}

function updateYear() {
  if (yearSpan) {
    yearSpan.textContent = new Date().getFullYear();
  }
}

function setupHeroButtons() {
  heroButtons.forEach((button) => {
    const action = button.dataset.action;

    if (action === 'play') {
      button.addEventListener('click', () => {
        if (!audioPlayer) return;
        audioPlayer.currentTime = 0;
        audioPlayer
          .play()
          .then(() => {
            button.textContent = 'Mission Brief Playing';
            button.disabled = true;
            button.classList.add('is-playing');
            audioPlayer.addEventListener(
              'ended',
              () => {
                button.textContent = 'Play Mission Brief';
                button.disabled = false;
                button.classList.remove('is-playing');
              },
              { once: true }
            );
          })
          .catch(() => {
            button.textContent = 'Unable to play audio';
          });
      });
    }

    if (action === 'persona') {
      button.addEventListener('click', () => {
        const heroAvatar = doc.querySelector('.avatar__core');
        heroAvatar?.classList.add('is-hello');
        button.textContent = 'Axon says hello 👋';
        setTimeout(() => {
          heroAvatar?.classList.remove('is-hello');
          button.textContent = 'Meet Axon';
        }, 3200);
      });
    }
  });
}

function setupSamples() {
  sampleButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const card = button.closest('.voice-card');
      if (!card) return;
      const role = card.dataset.role;
      const sample = card.querySelector('.voice-card__sample');
      const text = personaSamples[role];
      if (!sample || !text) return;

      const isHidden = sample.hasAttribute('hidden');
      sample.textContent = text;
      if (isHidden) {
        sample.removeAttribute('hidden');
        button.textContent = 'Hide sample';
      } else {
        sample.setAttribute('hidden', '');
        button.textContent = 'Sample response';
      }
    });
  });
}

function setupDemo() {
  demoControls.forEach((chip) => {
    chip.addEventListener('click', () => {
      const mode = chip.dataset.mode;
      if (!mode) return;
      demoControls.forEach((el) => el.classList.remove('active'));
      chip.classList.add('active');
      if (demoPersona) {
        demoPersona.textContent = capitalize(mode);
      }
      if (demoOutput) {
        demoOutput.textContent = demoResponses[mode] ?? '';
      }
    });
  });

  const defaultControl = doc.querySelector('.chip[data-mode="strategist"]');
  defaultControl?.classList.add('active');
  if (demoOutput) {
    demoOutput.textContent = demoResponses.strategist;
  }
}

function capitalize(value = '') {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function setupObservers() {
  if (!('IntersectionObserver' in window)) {
    animateTargets.forEach((target) => target.classList.add('is-visible'));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.25 }
  );

  animateTargets.forEach((target) => observer.observe(target));
}

prefersDark.addEventListener('change', (event) => {
  const stored = window.localStorage.getItem('axon-theme');
  if (!stored) {
    applyTheme(event.matches ? 'dark' : 'light');
  }
});

initializeTheme();
updateYear();
setupHeroButtons();
setupSamples();
setupDemo();
setupObservers();

themeToggle?.addEventListener('click', toggleTheme);
