import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import setup_musetalk


def test_setup_prepares_repo_dependencies_and_weights(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        sys,
        "argv",
        ["setup_musetalk.py", "--models-dir", str(tmp_path / "models")],
    )
    monkeypatch.setattr(
        setup_musetalk,
        "ensure_musetalk_repo",
        lambda musetalk_root, repo_url: calls.append("repo"),
    )
    monkeypatch.setattr(
        setup_musetalk,
        "install_runtime_dependencies",
        lambda musetalk_root: calls.append("deps"),
    )
    monkeypatch.setattr(
        setup_musetalk,
        "ensure_required_weights",
        lambda model_root, hf_endpoint: calls.append("weights"),
    )

    exit_code = setup_musetalk.main()

    assert exit_code == 0
    assert calls == ["repo", "deps", "weights"]


def test_required_weight_downloads_match_musetalk_runtime_checks() -> None:
    targets = {download.target.as_posix() for download in setup_musetalk.REQUIRED_WEIGHT_DOWNLOADS}

    assert "musetalkV15/unet.pth" in targets
    assert "musetalkV15/musetalk.json" in targets
    assert "sd-vae/config.json" in targets
    assert "whisper/config.json" in targets
    assert "whisper/preprocessor_config.json" in targets
    assert "dwpose/dw-ll_ucoco_384.pth" in targets
    assert "face-parse-bisent/79999_iter.pth" in targets
    assert "face-parse-bisent/resnet18-5c106cde.pth" in targets
    assert "syncnet/latentsync_syncnet.pt" in targets


def test_face_parser_weights_use_huggingface_repo() -> None:
    face_parser_downloads = [
        download
        for download in setup_musetalk.REQUIRED_WEIGHT_DOWNLOADS
        if download.target.parts[0] == "face-parse-bisent"
    ]

    assert face_parser_downloads
    assert {download.repo_id for download in face_parser_downloads} == {
        "ManyOtherFunctions/face-parse-bisent"
    }
