"""Local speech-to-text recorder using faster-whisper and sounddevice."""

from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from scipy.io.wavfile import write as write_wav


class VoiceRecorder:
	"""Records microphone audio and transcribes it fully offline."""

	# Shared default duration that can be updated by settings at runtime.
	default_duration = 5

	def __init__(self) -> None:
		# Load a compact Whisper model configured for CPU inference.
		self.model = WhisperModel("small", device="cpu", compute_type="int8")
		self.sample_rate = 16000
		self.duration = self.default_duration

	def record_and_transcribe(self) -> str:
		# Capture microphone input, write a temp WAV, and transcribe its segments.
		try:
			print("Listening...")

			# Record mono audio for the configured duration at the configured sample rate.
			audio = sd.rec(
				int(self.duration * self.sample_rate),
				samplerate=self.sample_rate,
				channels=1,
				dtype="float32",
			)
			sd.wait()

			# Convert to 16-bit PCM because WAV writers and ASR models commonly expect it.
			audio_pcm = np.int16(np.clip(audio, -1.0, 1.0) * 32767)

			# Persist the recording temporarily so faster-whisper can read from disk.
			with NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
				temp_path = Path(temp_file.name)

			write_wav(str(temp_path), self.sample_rate, audio_pcm)

			# Transcribe and merge all text chunks into one plain string.
			segments, _info = self.model.transcribe(str(temp_path))
			text = " ".join(segment.text.strip() for segment in segments if segment.text).strip()

			# Clean up the temp file after transcription is complete.
			temp_path.unlink(missing_ok=True)
			return text
		except Exception:
			return ""
