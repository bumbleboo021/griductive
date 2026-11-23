const loadingScreen = document.getElementById("loading-screen");
const loadingMessage = document.getElementById("loading-message");
const playButton = document.getElementById("play-button");
const infobox = document.getElementById("infobox");

function updateLoadingMessage() {
  const message = infobox.textContent.trim();
  if (message.includes("Ready to start")) {
    loadingMessage.textContent = "Your game is ready.";
    loadingScreen.classList.add("ready-to-play");
    playButton.hidden = false;
  } else if (message.startsWith("installing")) {
    loadingMessage.textContent = "Preparing the game…";
  }
}

new MutationObserver(updateLoadingMessage).observe(infobox, {
  childList: true,
  characterData: true,
  subtree: true,
});
updateLoadingMessage();

playButton.addEventListener("click", () => {
  playButton.disabled = true;
  playButton.hidden = true;
  loadingScreen.classList.remove("ready-to-play");
  loadingMessage.textContent = "Opening the game…";
  document.getElementById("canvas").click();
});

window.griductiveGameReady = () => {
  document.body.classList.add("game-ready");
  loadingScreen.hidden = true;
  window.window_resize();
  document.getElementById("canvas").focus();
};

// Keep music outside the WebAssembly archive and let the browser stream it.
window.griductiveMusic = {
  audio: null,
  pending: null,
  name: "",
  message: "",
  volume: .22,
  request: 0,

  release(audio) {
    if (!audio) return;
    audio.pause();
    audio.removeAttribute("src");
    audio.load();
  },

  state() {
    return {
      name: this.name,
      message: this.message,
      enabled: Boolean(this.audio && !this.audio.paused),
    };
  },

  select(name) {
    const request = ++this.request;
    this.release(this.pending);
    const candidate = new Audio(new URL("music/" + encodeURIComponent(name), document.baseURI));
    candidate.preload = "none";
    candidate.loop = true;
    candidate.volume = Math.max(0, Math.min(1, this.volume));
    this.pending = candidate;
    this.message = "Loading " + name.replace(/\.ogg$/i, "") + "…";
    candidate.play().then(() => {
      if (request !== this.request) {
        this.release(candidate);
        return;
      }
      this.release(this.audio);
      this.audio = candidate;
      this.pending = null;
      this.name = name;
      this.message = "Playing " + name.replace(/\.ogg$/i, "") + ".";
    }).catch(() => {
      if (request !== this.request) return;
      this.release(candidate);
      this.pending = null;
      this.message = "Music unavailable. Please try the track again.";
    });
    return this.message;
  },

  toggle(defaultName) {
    if (this.pending || (this.audio && !this.audio.paused)) return this.stop();
    return this.select(this.name || defaultName);
  },

  stop() {
    ++this.request;
    this.release(this.pending);
    this.release(this.audio);
    this.pending = this.audio = null;
    this.message = "Music off.";
    return this.message;
  },
};
