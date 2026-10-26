/* aditazzz.github.io: the video player and the code panel.
 *
 * 1. The video loads as a thumbnail and only becomes a YouTube player when someone clicks it (fast pages, no
 *    tracking until then). It uses the YouTube IFrame Player API so the page knows when the video is really playing.
 * 2. The code panel starts "encrypted" (blurred under a veil). When the video starts playing, it decrypts with a
 *    short scan animation. This is a reveal, not a lock: the code is in the page for search engines and screen
 *    readers, there's a "Decrypt it now" button, and every line is on GitHub anyway.
 * 3. "Copy with credit" copies the code with a header that credits aditazzz and links the video.
 */
(function () {
  "use strict";

  const term = document.querySelector("[data-lock]");
  const ytButton = document.querySelector(".yt[data-id]");

  // ---- the code panel: lock it once JavaScript is running (without JS it stays readable)
  function unlock() {
    if (!term || !term.classList.contains("locked")) return;
    term.classList.remove("locked");
    term.classList.add("unlocking");
    setTimeout(() => term.classList.remove("unlocking"), 1500);
  }
  if (term) {
    term.classList.add("locked");
    term.querySelector("[data-unlock]")?.addEventListener("click", unlock);
  }

  // ---- copy with credit
  document.querySelectorAll("[data-copy]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const panel = btn.closest(".term");
      const text = panel.querySelector("[data-attrib]").value + panel.querySelector("pre").innerText;
      try {
        await navigator.clipboard.writeText(text);
        btn.textContent = "Copied, with credit";
      } catch (e) {
        // clipboard refused: select the code so the reader can copy it by hand
        const range = document.createRange();
        range.selectNodeContents(panel.querySelector("pre"));
        const sel = getSelection(); sel.removeAllRanges(); sel.addRange(range);
        btn.textContent = "Selected, press Copy";
      }
      unlock();
      setTimeout(() => (btn.textContent = "Copy with credit"), 2600);
    });
  });

  // ---- the player: swap the thumbnail for a real YouTube player on click
  if (!ytButton) return;
  let apiReady;
  function loadApi() {
    if (apiReady) return apiReady;
    apiReady = new Promise((resolve) => {
      window.onYouTubeIframeAPIReady = () => resolve(window.YT);
      const s = document.createElement("script");
      s.src = "https://www.youtube.com/iframe_api";
      document.head.appendChild(s);
    });
    return apiReady;
  }

  ytButton.addEventListener("click", async () => {
    const id = ytButton.dataset.id;
    const holder = document.createElement("div");
    ytButton.appendChild(holder);
    const YT = await loadApi();
    new YT.Player(holder, {
      videoId: id,
      host: "https://www.youtube-nocookie.com",
      playerVars: { autoplay: 1, rel: 0, modestbranding: 1, playsinline: 1, origin: location.origin },
      events: {
        // YT.PlayerState.PLAYING === 1: a real play, so decrypt the code
        onStateChange: (e) => { if (e.data === 1) unlock(); },
      },
    });
  }, { once: true });
})();
