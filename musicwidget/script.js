const audio = document.getElementById('audio');
const playPauseBtn = document.getElementById('play-pause');

let isPlaying = false;

playPauseBtn.addEventListener('click', () => {
  if (!isPlaying) {
    audio.play();
    playPauseBtn.textContent = '⏸️';
  } else {
    audio.pause();
    playPauseBtn.textContent = '▶️';
  }
  isPlaying = !isPlaying;
});

// Optional: Update track title dynamically (if using playlist or streaming API)

