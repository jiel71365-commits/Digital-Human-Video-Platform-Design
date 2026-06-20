import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import setup_wav2lip
from scripts.setup_wav2lip import apply_compatibility_patches


def test_apply_compatibility_patches_updates_wav2lip_source(tmp_path: Path) -> None:
    wav2lip_root = tmp_path / "models" / "Wav2Lip"
    audio_path = wav2lip_root / "audio.py"
    inference_path = wav2lip_root / "inference.py"
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    audio_path.write_text(
        "def _build_mel_basis():\n"
        "    return librosa.filters.mel(hp.sample_rate, hp.n_fft, n_mels=hp.num_mels,\n"
        "                               fmin=hp.fmin, fmax=hp.fmax)\n",
        encoding="utf-8",
    )
    inference_path.write_text(
        "command = 'ffmpeg -y -i {} -i {} -strict -2 -q:v 1 {}'.format(\n"
        "    args.audio, 'temp/result.avi', args.outfile\n"
        ")\n"
        "subprocess.call(command, shell=platform.system() != 'Windows')\n",
        encoding="utf-8",
    )

    changed = apply_compatibility_patches(wav2lip_root)

    assert changed == [audio_path, inference_path]
    assert "librosa.filters.mel(" in audio_path.read_text(encoding="utf-8")
    assert "sr=hp.sample_rate" in audio_path.read_text(encoding="utf-8")
    assert "n_fft=hp.n_fft" in audio_path.read_text(encoding="utf-8")
    assert "subprocess.call(command, shell=True)" in inference_path.read_text(encoding="utf-8")


def test_apply_compatibility_patches_is_idempotent(tmp_path: Path) -> None:
    wav2lip_root = tmp_path / "models" / "Wav2Lip"
    audio_path = wav2lip_root / "audio.py"
    inference_path = wav2lip_root / "inference.py"
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    audio_path.write_text(
        "def _build_mel_basis():\n"
        "    return librosa.filters.mel(\n"
        "        sr=hp.sample_rate,\n"
        "        n_fft=hp.n_fft,\n"
        "        n_mels=hp.num_mels,\n"
        "        fmin=hp.fmin,\n"
        "        fmax=hp.fmax,\n"
        "    )\n",
        encoding="utf-8",
    )
    inference_path.write_text(
        "command = 'ffmpeg -y -i {} -i {} -strict -2 -q:v 1 {}'.format(\n"
        "    args.audio, 'temp/result.avi', args.outfile\n"
        ")\n"
        "subprocess.call(command, shell=True)\n",
        encoding="utf-8",
    )

    changed = apply_compatibility_patches(wav2lip_root)

    assert changed == []


def test_setup_installs_dependencies_before_downloading_assets(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        sys,
        "argv",
        ["setup_wav2lip.py", "--models-dir", str(tmp_path / "models")],
    )
    monkeypatch.setattr(
        setup_wav2lip,
        "ensure_wav2lip_repo",
        lambda wav2lip_root, repo_url: calls.append("repo"),
    )
    monkeypatch.setattr(
        setup_wav2lip,
        "install_runtime_dependencies",
        lambda: calls.append("deps"),
    )
    monkeypatch.setattr(
        setup_wav2lip,
        "ensure_huggingface_download",
        lambda **kwargs: calls.append("download"),
    )
    monkeypatch.setattr(
        setup_wav2lip,
        "apply_compatibility_patches",
        lambda wav2lip_root: [],
    )

    exit_code = setup_wav2lip.main()

    assert exit_code == 0
    assert calls == ["repo", "deps", "download", "download", "download"]
