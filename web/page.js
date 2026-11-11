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
