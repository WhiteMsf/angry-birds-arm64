from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON_EMBED_URL = "https://www.python.org/ftp/python/3.14.8/python-3.14.8-embed-amd64.zip"
PYTHON_EMBED_SHA256 = "a93abe456ab01bd96d7a085b3cdb6566b3063f4241360d114142fbdb07f0a310"
PYINSTALLER_VERSION = "6.22.3"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_ok(command: list[str]) -> None:
    print("$ " + subprocess.list2cmdline(command))
    subprocess.run(command, check=True)


def copy_support(destination: Path) -> None:
    support = destination / "support"
    support.mkdir(parents=True)
    shutil.copy2(ROOT / "build.py", support / "build.py")
    shutil.copytree(ROOT / "tools", support / "tools", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    android_source = support / "stage24-android"
    android_source.mkdir()
    shutil.copy2(ROOT / "stage24-android" / "AndroidManifest.xml", android_source / "AndroidManifest.xml")
    for name in ("LICENSE.md", "THIRD_PARTY_NOTICES.md", "CREDITS.md"):
        source = ROOT / name
        if source.is_file():
            shutil.copy2(source, destination / name)
    for source_name, destination_name in (
        ("README.md", "README.txt"),
        ("RELEASE-NOTES.md", "RELEASE-NOTES.txt"),
    ):
        source = ROOT / "docs" / "windows-builder" / source_name
        if source.is_file():
            shutil.copy2(source, destination / destination_name)


def build_package(native_library: Path, output: Path) -> Path:
    native_library = native_library.resolve()
    if not native_library.is_file():
        raise FileNotFoundError(f"ARM64 runtime not found: {native_library}")
    if output.exists():
        raise FileExistsError(f"Refusing to replace an existing package directory: {output}")
    try:
        import PyInstaller
    except ImportError as error:
        raise RuntimeError(f"Install the pinned packager first: pyinstaller=={PYINSTALLER_VERSION}") from error
    if PyInstaller.__version__ != PYINSTALLER_VERSION:
        raise RuntimeError(f"Expected PyInstaller {PYINSTALLER_VERSION}, found {PyInstaller.__version__}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="windows-builder-package-", dir=output.parent) as temporary:
        temporary_root = Path(temporary)
        staged = temporary_root / "AngryBirds-ARM64-Builder-Preview"
        staged.mkdir()

        pyinstaller_dist = temporary_root / "pyinstaller-dist"
        require_ok(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                "--noconfirm",
                "--clean",
                "--onefile",
                "--windowed",
                "--name",
                "AngryBirdsArm64Builder",
                "--distpath",
                str(pyinstaller_dist),
                "--workpath",
                str(temporary_root / "pyinstaller-work"),
                "--specpath",
                str(temporary_root / "pyinstaller-spec"),
                str(ROOT / "tools" / "windows_builder.py"),
            ]
        )
        shutil.copy2(pyinstaller_dist / "AngryBirdsArm64Builder.exe", staged / "AngryBirdsArm64Builder.exe")

        python_zip = temporary_root / "python-3.14.8-embed-amd64.zip"
        print(f"Downloading official Python embeddable runtime: {PYTHON_EMBED_URL}")
        with urllib.request.urlopen(PYTHON_EMBED_URL, timeout=90) as response, python_zip.open("wb") as target:
            shutil.copyfileobj(response, target)
        actual_python_hash = sha256(python_zip)
        if actual_python_hash != PYTHON_EMBED_SHA256:
            raise RuntimeError(
                "Python embeddable runtime checksum mismatch: "
                f"expected {PYTHON_EMBED_SHA256}, received {actual_python_hash}"
            )
        python_root = staged / "python"
        python_root.mkdir()
        with zipfile.ZipFile(python_zip) as archive:
            archive.extractall(python_root)
        pth = python_root / "python314._pth"
        lines = pth.read_text(encoding="ascii").splitlines()
        if "..\\support" not in lines:
            lines.append("..\\support")
        pth.write_text("\n".join(lines) + "\n", encoding="ascii")
        copy_support(staged)
        require_ok([str(python_root / "python.exe"), "-c", "import argparse, zipfile, build; print('portable Python PASS')"])

        (staged / "runtime").mkdir()
        shutil.copy2(native_library, staged / "runtime" / "libangryarm64.so")

        with zipfile.ZipFile(python_zip) as archive:
            if any(name.startswith(("assets/data/", "original/")) for name in archive.namelist()):
                raise RuntimeError("Python runtime unexpectedly contains game assets")
        for path in staged.rglob("*"):
            if path.is_file() and ("assets" in path.parts or path.suffix.casefold() in {".apk", ".pvr", ".dat", ".mp3", ".wav"}):
                raise RuntimeError(f"Refusing to package a file that could contain game assets: {path}")

        manifest = {
            "name": "Angry Birds ARM64 Builder Preview",
            "source_commit": subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                check=False,
            ).stdout.strip() or "unknown",
            "pyinstaller_version": PYINSTALLER_VERSION,
            "builder_exe_sha256": sha256(staged / "AngryBirdsArm64Builder.exe"),
            "runtime_sha256": sha256(staged / "runtime" / "libangryarm64.so"),
            "python_version": "3.14.8",
            "python_embeddable_sha256": actual_python_hash,
        }
        (staged / "builder-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        archive_path = temporary_root / "AngryBirds-ARM64-Builder-Preview.zip"
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=8) as archive:
            for path in staged.rglob("*"):
                if path.is_file():
                    archive.write(path, path.relative_to(staged.parent))
        archive_hash = sha256(archive_path)
        output.mkdir(parents=True)
        final_archive = output / archive_path.name
        shutil.copy2(archive_path, final_archive)
        (output / f"{archive_path.name}.sha256").write_text(f"{archive_hash}  {archive_path.name}\n", encoding="ascii")
        return final_archive


def main() -> int:
    parser = argparse.ArgumentParser(description="Package the Windows GUI builder without original game assets.")
    parser.add_argument("--native-library", required=True, help="CI or local arm64-v8a libangryarm64.so.")
    parser.add_argument("--output", required=True, help="New output directory; an existing directory is never replaced.")
    args = parser.parse_args()
    result = build_package(Path(args.native_library), Path(args.output).expanduser().resolve())
    print(f"Builder package ready: {result}")
    print(f"SHA-256: {sha256(result)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
