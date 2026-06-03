from __future__ import annotations

import numpy as np
import soundfile as sf

from audio import preprocess_audio, probe_audio


def test_preprocess_audio_writes_mono_wav(tmp_path):
    source = tmp_path / "source.wav"
    output = tmp_path / "output.wav"
    sample_rate = 16_000
    tone = np.sin(np.linspace(0, 1_000, sample_rate, dtype=np.float32))
    stereo = np.column_stack([tone, tone])
    sf.write(source, stereo, sample_rate)

    info = preprocess_audio(source, output, 24_000)

    assert output.exists()
    assert info.sample_rate == 24_000
    assert info.channels == 1
    assert probe_audio(output).duration_seconds > 0
