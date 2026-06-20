from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WAV2LIP_REPO = "https://github.com/Rudrabha/Wav2Lip.git"
DEFAULT_MODEL_REPO = "camenduru/Wav2Lip"
DEFAULT_FACE_REPO = "rippertnt/wav2lip"
DEFAULT_FACE_FILE = "boy.mp4"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare local Wav2Lip runtime assets under the ignored models/ directory."
    )
    parser.add_argument("--models-dir", type=Path, default=PROJECT_ROOT / "models")
    parser.add_argument("--wav2lip-repo", default=DEFAULT_WAV2LIP_REPO)
    parser.add_argument("--model-repo", default=DEFAULT_MODEL_REPO)
    parser.add_argument("--face-repo", default=DEFAULT_FACE_REPO)
    parser.add_argument("--skip-deps", action="store_true")
    args = parser.parse_args()

    models_dir = args.models_dir
    wav2lip_root = models_dir / "Wav2Lip"
    ensure_wav2lip_repo(wav2lip_root, args.wav2lip_repo)
    if not args.skip_deps:
        install_runtime_dependencies()
    ensure_huggingface_download(
        repo_id=args.model_repo,
        filename="checkpoints/wav2lip_gan.pth",
        target=wav2lip_root / "checkpoints" / "wav2lip_gan.pth",
    )
    ensure_huggingface_download(
        repo_id=args.model_repo,
        filename="face_detection/detection/sfd/s3fd.pth",
        target=wav2lip_root / "face_detection" / "detection" / "sfd" / "s3fd.pth",
    )
    ensure_huggingface_download(
        repo_id=args.face_repo,
        filename=DEFAULT_FACE_FILE,
        target=models_dir / "default-presenter.mp4",
    )
    changed = apply_compatibility_patches(wav2lip_root)
    if changed:
        print("Patched Wav2Lip compatibility files:")
        for path in changed:
            print(f"- {path}")
    else:
        print("Wav2Lip compatibility patches already applied.")
    print("Wav2Lip runtime assets are ready.")
    return 0


def ensure_wav2lip_repo(wav2lip_root: Path, repo_url: str) -> None:
    inference_path = wav2lip_root / "inference.py"
    if inference_path.exists():
        print(f"Wav2Lip repo already present: {wav2lip_root}")
        return
    wav2lip_root.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", repo_url, str(wav2lip_root)], check=True)


def ensure_huggingface_download(*, repo_id: str, filename: str, target: Path) -> None:
    if target.exists() and target.stat().st_size > 0:
        print(f"Asset already present: {target}")
        return
    from huggingface_hub import hf_hub_download

    target.parent.mkdir(parents=True, exist_ok=True)
    cached = Path(hf_hub_download(repo_id=repo_id, filename=filename, repo_type="model"))
    shutil.copyfile(cached, target)
    print(f"Downloaded {repo_id}:{filename} -> {target}")


def apply_compatibility_patches(wav2lip_root: Path) -> list[Path]:
    changed: list[Path] = []
    audio_path = wav2lip_root / "audio.py"
    inference_path = wav2lip_root / "inference.py"
    if _patch_audio_py(audio_path):
        changed.append(audio_path)
    if _patch_inference_py(inference_path):
        changed.append(inference_path)
    return changed


def install_runtime_dependencies() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "huggingface_hub",
            "librosa",
            "scikit-image",
            "tqdm",
        ],
        check=True,
    )


def _patch_audio_py(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    old = (
        "return librosa.filters.mel(hp.sample_rate, hp.n_fft, n_mels=hp.num_mels,\n"
        "                               fmin=hp.fmin, fmax=hp.fmax)"
    )
    new = (
        "return librosa.filters.mel(\n"
        "        sr=hp.sample_rate,\n"
        "        n_fft=hp.n_fft,\n"
        "        n_mels=hp.num_mels,\n"
        "        fmin=hp.fmin,\n"
        "        fmax=hp.fmax,\n"
        "    )"
    )
    if old not in text:
        return False
    path.write_text(text.replace(old, new), encoding="utf-8")
    return True


def _patch_inference_py(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    old = "subprocess.call(command, shell=platform.system() != 'Windows')"
    new = "subprocess.call(command, shell=True)"
    if old not in text:
        return False
    path.write_text(text.replace(old, new), encoding="utf-8")
    return True


if __name__ == "__main__":
    raise SystemExit(main())
