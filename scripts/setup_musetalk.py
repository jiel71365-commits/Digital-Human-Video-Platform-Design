from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MUSETALK_REPO = "https://github.com/TMElyralab/MuseTalk.git"
DEFAULT_HF_ENDPOINT = "https://hf-mirror.com"


@dataclass(frozen=True)
class WeightDownload:
    repo_id: str
    filename: str
    target: Path


REQUIRED_WEIGHT_DOWNLOADS = [
    WeightDownload(
        repo_id="TMElyralab/MuseTalk",
        filename="musetalkV15/unet.pth",
        target=Path("musetalkV15/unet.pth"),
    ),
    WeightDownload(
        repo_id="TMElyralab/MuseTalk",
        filename="musetalkV15/musetalk.json",
        target=Path("musetalkV15/musetalk.json"),
    ),
    WeightDownload(
        repo_id="stabilityai/sd-vae-ft-mse",
        filename="config.json",
        target=Path("sd-vae/config.json"),
    ),
    WeightDownload(
        repo_id="stabilityai/sd-vae-ft-mse",
        filename="diffusion_pytorch_model.bin",
        target=Path("sd-vae/diffusion_pytorch_model.bin"),
    ),
    WeightDownload(
        repo_id="openai/whisper-tiny",
        filename="config.json",
        target=Path("whisper/config.json"),
    ),
    WeightDownload(
        repo_id="openai/whisper-tiny",
        filename="pytorch_model.bin",
        target=Path("whisper/pytorch_model.bin"),
    ),
    WeightDownload(
        repo_id="openai/whisper-tiny",
        filename="preprocessor_config.json",
        target=Path("whisper/preprocessor_config.json"),
    ),
    WeightDownload(
        repo_id="yzd-v/DWPose",
        filename="dw-ll_ucoco_384.pth",
        target=Path("dwpose/dw-ll_ucoco_384.pth"),
    ),
    WeightDownload(
        repo_id="ManyOtherFunctions/face-parse-bisent",
        filename="79999_iter.pth",
        target=Path("face-parse-bisent/79999_iter.pth"),
    ),
    WeightDownload(
        repo_id="ManyOtherFunctions/face-parse-bisent",
        filename="resnet18-5c106cde.pth",
        target=Path("face-parse-bisent/resnet18-5c106cde.pth"),
    ),
    WeightDownload(
        repo_id="ByteDance/LatentSync",
        filename="latentsync_syncnet.pt",
        target=Path("syncnet/latentsync_syncnet.pt"),
    ),
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare local MuseTalk runtime assets under the ignored models/ directory."
    )
    parser.add_argument("--models-dir", type=Path, default=PROJECT_ROOT / "models")
    parser.add_argument("--musetalk-repo", default=DEFAULT_MUSETALK_REPO)
    parser.add_argument("--hf-endpoint", default=DEFAULT_HF_ENDPOINT)
    parser.add_argument("--skip-deps", action="store_true")
    args = parser.parse_args()

    musetalk_root = args.models_dir / "MuseTalk"
    model_root = musetalk_root / "models"
    ensure_musetalk_repo(musetalk_root, args.musetalk_repo)
    if not args.skip_deps:
        install_runtime_dependencies(musetalk_root)
    ensure_required_weights(model_root, args.hf_endpoint)
    print("MuseTalk runtime assets are ready.")
    return 0


def ensure_musetalk_repo(musetalk_root: Path, repo_url: str) -> None:
    inference_path = musetalk_root / "scripts" / "inference.py"
    if inference_path.exists():
        print(f"MuseTalk repo already present: {musetalk_root}")
        return
    musetalk_root.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", repo_url, str(musetalk_root)], check=True)


def install_runtime_dependencies(musetalk_root: Path) -> None:
    requirements_path = musetalk_root / "requirements.txt"
    subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"], check=True)
    if requirements_path.exists():
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
            check=True,
        )


def ensure_required_weights(model_root: Path, hf_endpoint: str) -> None:
    for download in REQUIRED_WEIGHT_DOWNLOADS:
        ensure_huggingface_download(
            repo_id=download.repo_id,
            filename=download.filename,
            target=model_root / download.target,
            hf_endpoint=hf_endpoint,
        )


def ensure_huggingface_download(
    *,
    repo_id: str,
    filename: str,
    target: Path,
    hf_endpoint: str,
) -> None:
    if target.exists() and target.stat().st_size > 0:
        print(f"Asset already present: {target}")
        return
    from huggingface_hub import hf_hub_download

    target.parent.mkdir(parents=True, exist_ok=True)
    cached = Path(
        hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            repo_type="model",
            endpoint=hf_endpoint,
        )
    )
    shutil.copyfile(cached, target)
    print(f"Downloaded {repo_id}:{filename} -> {target}")


if __name__ == "__main__":
    raise SystemExit(main())
