from __future__ import annotations

import hashlib
import re
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


SUPPORTED_APK_SHA256 = "2524167c113d967c5efd40640387482201a14c06124f70f2d1700fff1839d5ed"
SUPPORTED_PACKAGE = "com.rovio.angrybirds"
SUPPORTED_VERSION_CODE = "142"
SUPPORTED_VERSION_NAME = "1.4.2"
EXPECTED_ORIGINAL_ABIS = {"armeabi", "armeabi-v7a"}


class BuilderError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_original_hash(path: Path) -> str:
    if not path.is_file():
        raise BuilderError(f"APK not found: {path}")
    actual_hash = sha256_file(path)
    if actual_hash != SUPPORTED_APK_SHA256:
        raise BuilderError(
            "Unsupported original APK. This preview accepts only the "
            f"validated Angry Birds 1.4.2 (142) file with SHA-256 {SUPPORTED_APK_SHA256}. "
            f"Selected file SHA-256: {actual_hash}."
        )
    return actual_hash


def validate_original_apk(path: Path, badging: str) -> dict[str, str]:
    actual_hash = validate_original_hash(path)

    package_match = re.search(r"^package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'", badging, re.M)
    if not package_match:
        raise BuilderError("Could not read the APK package and version metadata.")
    package, version_code, version_name = package_match.groups()
    if (package, version_code, version_name) != (
        SUPPORTED_PACKAGE,
        SUPPORTED_VERSION_CODE,
        SUPPORTED_VERSION_NAME,
    ):
        raise BuilderError(
            "APK metadata does not match the validated original: "
            f"{package} {version_name} ({version_code})."
        )

    with zipfile.ZipFile(path) as archive:
        abis = {
            PurePosixPath(name).parts[1]
            for name in archive.namelist()
            if name.startswith("lib/") and len(PurePosixPath(name).parts) >= 3
        }
    if abis != EXPECTED_ORIGINAL_ABIS:
        raise BuilderError(
            "The selected original must contain only its validated ARM32 "
            f"libraries ({', '.join(sorted(EXPECTED_ORIGINAL_ABIS))}); found: "
            f"{', '.join(sorted(abis)) or 'none'}."
        )
    return {"sha256": actual_hash, "package": package, "version_code": version_code, "version_name": version_name}


def validate_runtime_library(path: Path) -> None:
    if not path.is_file() or path.stat().st_size < 1024 * 1024:
        raise BuilderError(f"ARM64 runtime library is missing or unexpectedly small: {path}")
    with path.open("rb") as source:
        header = source.read(20)
    if len(header) < 20 or header[:4] != b"\x7fELF" or header[4] != 2 or header[5] != 1:
        raise BuilderError("Bundled native runtime is not a 64-bit little-endian ELF library.")
    if int.from_bytes(header[18:20], "little") != 183:
        raise BuilderError("Bundled native runtime is not compiled for ARM64 (AArch64).")


def extract_original_assets(apk_path: Path, original_root: Path) -> int:
    """Extract only original assets/data, rejecting archive paths outside the destination."""
    target_root = (original_root / "assets" / "data").resolve()
    target_root.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(apk_path) as archive:
        for item in archive.infolist():
            if item.is_dir() or not item.filename.startswith("assets/data/"):
                continue
            relative = PurePosixPath(item.filename).relative_to("assets/data")
            if relative.is_absolute() or any(part in ("", ".", "..") for part in relative.parts):
                raise BuilderError(f"Unsafe asset path in APK: {item.filename}")
            destination = (target_root.joinpath(*relative.parts)).resolve()
            if destination != target_root and target_root not in destination.parents:
                raise BuilderError(f"Unsafe asset path in APK: {item.filename}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(item) as source, destination.open("wb") as output:
                shutil.copyfileobj(source, output)
            count += 1
    if count == 0:
        raise BuilderError("The selected APK contains no assets/data files.")
    return count


def extract_launcher_icon(apk_path: Path, destination: Path) -> Path:
    with zipfile.ZipFile(apk_path) as archive:
        names = set(archive.namelist())
        candidates = [
            "res/drawable-mdpi/icon.png",
            "res/drawable-hdpi/icon.png",
            "res/drawable-ldpi/icon.png",
        ]
        selected = next((name for name in candidates if name in names), None)
        if not selected:
            raise BuilderError("The validated original APK has no supported launcher icon.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(selected) as source, destination.open("wb") as output:
            shutil.copyfileobj(source, output)
    return destination


def output_path_for(_apk_path: Path, output_directory: Path | None = None) -> Path:
    if output_directory is None:
        downloads = Path.home() / "Downloads"
        output_directory = downloads if downloads.is_dir() else Path.home()
    output_directory = output_directory.expanduser().resolve()
    base = output_directory / "angry-birds-classic-1.4.2-arm64.apk"
    if not base.exists():
        return base
    for index in range(2, 1000):
        candidate = base.with_name(f"{base.stem}-{index}{base.suffix}")
        if not candidate.exists():
            return candidate
    raise BuilderError("Could not choose a new output file name without replacing an existing APK.")


def probe_output_writable(path: Path) -> None:
    path = path.expanduser().resolve()
    if path.exists():
        raise BuilderError(f"Output file already exists and will not be overwritten: {path}")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix=".angry-arm64-write-check-", dir=path.parent, delete=True):
            pass
    except OSError as error:
        raise BuilderError(f"Cannot write to the selected output folder: {path.parent}\n{error}") from error
