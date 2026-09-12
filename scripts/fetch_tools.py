"""Install checksum-pinned verification tools inside this checkout."""

import hashlib
import os
import platform
import tarfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = {
    "gitleaks": (
        "gitleaks/gitleaks", "v8.30.1",
        ("gitleaks_8.30.1_linux_x64.tar.gz", "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb"),
        ("gitleaks_8.30.1_windows_x64.zip", "d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e"),
    ),
    "actionlint": (
        "rhysd/actionlint", "v1.7.12",
        ("actionlint_1.7.12_linux_amd64.tar.gz", "8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8"),
        ("actionlint_1.7.12_windows_amd64.zip", "6e7241b51e6817ea6a047693d8e6fed13b31819c9a0dd6c5a726e1592d22f6e9"),
    ),
    "trivy": (
        "aquasecurity/trivy", "v0.74.0",
        ("trivy_0.74.0_Linux-64bit.tar.gz", "2ae6fe3ee734b7fdf11335663e18c75ea12dccc76062f09f164a3b0f8be4371a"),
        ("trivy_0.74.0_windows-64bit.zip", "94c40e0696e4b907a74b7b2e1438d5d72ebaca83115817407f568a002d520842"),
    ),
}


def main() -> None:
    windows = platform.system() == "Windows"
    if platform.machine().lower() not in {"amd64", "x86_64"}:
        raise SystemExit("Pinned tool archives currently target x86_64 Linux/Windows.")
    for name, (repository, tag, linux_asset, windows_asset) in TOOLS.items():
        filename, expected = windows_asset if windows else linux_asset
        destination = ROOT / ".tools" / name
        destination.mkdir(parents=True, exist_ok=True)
        archive = ROOT / ".tools" / filename
        if not archive.exists():
            url = f"https://github.com/{repository}/releases/download/{tag}/{filename}"
            with urllib.request.urlopen(url, timeout=90) as response, archive.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
            raise SystemExit(f"Checksum mismatch for {name}.")
        if windows:
            with zipfile.ZipFile(archive) as package:
                for member in package.infolist():
                    if not (destination / member.filename).resolve().is_relative_to(destination):
                        raise SystemExit("Unsafe archive member.")
                package.extractall(destination)
        else:
            with tarfile.open(archive) as package:
                package.extractall(destination, filter="data")
            os.chmod(destination / name, 0o755)
        print(f"Verified {name} {tag}.")


if __name__ == "__main__":
    main()
