const audio = document.getElementById('audio');
const playPauseBtn = document.getElementById('play-pause');
const waveform = document.getElementById('waveform');

let isPlaying = false;

playPauseBtn.addEventListener('click', () => {
  if (!isPlaying) {
    audio.play();
    playPauseBtn.textContent = '⏸️';
    waveform.classList.add('active');
  } else {
    audio.pause();
    playPauseBtn.textContent = '▶️';
    waveform.classList.remove('active');
  }
  isPlaying = !isPlaying;
});

