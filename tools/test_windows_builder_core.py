from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import zipfile

import windows_builder_core as core


class WindowsBuilderCoreTests(unittest.TestCase):
    def test_validates_exact_metadata_hash_and_arm32_abis(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            apk = Path(temporary) / "original.apk"
            with zipfile.ZipFile(apk, "w") as archive:
                archive.writestr("lib/armeabi/libangrybirds.so", b"arm32")
                archive.writestr("lib/armeabi-v7a/libangrybirds.so", b"arm32")
                archive.writestr("assets/data/scripts/gamelogic.lua", b"game")
            digest = core.sha256_file(apk)
            badging = "package: name='com.rovio.angrybirds' versionCode='142' versionName='1.4.2'\n"
            with patch.object(core, "SUPPORTED_APK_SHA256", digest):
                result = core.validate_original_apk(apk, badging)
            self.assertEqual(result["sha256"], digest)
            self.assertEqual(result["version_name"], "1.4.2")

    def test_rejects_wrong_metadata_even_when_hash_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            apk = Path(temporary) / "original.apk"
            with zipfile.ZipFile(apk, "w") as archive:
                archive.writestr("lib/armeabi/lib.so", b"a")
                archive.writestr("lib/armeabi-v7a/lib.so", b"b")
            digest = core.sha256_file(apk)
            with patch.object(core, "SUPPORTED_APK_SHA256", digest):
                with self.assertRaisesRegex(core.BuilderError, "metadata does not match"):
                    core.validate_original_apk(
                        apk,
                        "package: name='com.rovio.angrybirds' versionCode='143' versionName='1.4.3'\n",
                    )

    def test_extracts_only_assets_data_and_keeps_spaces(self) -> None:
        with tempfile.TemporaryDirectory(prefix="builder space ") as temporary:
            apk = Path(temporary) / "original.apk"
            root = Path(temporary) / "safe output"
            with zipfile.ZipFile(apk, "w") as archive:
                archive.writestr("assets/data/scripts/gamelogic.lua", b"game")
                archive.writestr("assets/icon.png", b"not copied")
            self.assertEqual(core.extract_original_assets(apk, root), 1)
            self.assertEqual((root / "assets/data/scripts/gamelogic.lua").read_bytes(), b"game")
            self.assertFalse((root / "assets/icon.png").exists())

    def test_rejects_traversal_asset_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            apk = Path(temporary) / "malicious.apk"
            root = Path(temporary) / "extracted"
            with zipfile.ZipFile(apk, "w") as archive:
                archive.writestr("assets/data/../../escape.txt", b"escape")
            with self.assertRaisesRegex(core.BuilderError, "Unsafe asset path"):
                core.extract_original_assets(apk, root)
            self.assertFalse((Path(temporary) / "escape.txt").exists())

    def test_extracts_original_launcher_icon_to_local_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            apk = Path(temporary) / "original.apk"
            destination = Path(temporary) / "workspace" / "launcher-icon.png"
            with zipfile.ZipFile(apk, "w") as archive:
                archive.writestr("res/drawable-mdpi/icon.png", b"icon")
            self.assertEqual(core.extract_launcher_icon(apk, destination), destination)
            self.assertEqual(destination.read_bytes(), b"icon")

    def test_output_name_never_overwrites_existing_apk(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "original.apk"
            source.touch()
            existing = Path(temporary) / "angry-birds-classic-1.4.2-arm64.apk"
            existing.write_bytes(b"keep")
            self.assertEqual(core.output_path_for(source, Path(temporary)).name, "angry-birds-classic-1.4.2-arm64-2.apk")
            self.assertEqual(existing.read_bytes(), b"keep")

    def test_runtime_library_must_be_aarch64_elf(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            library = Path(temporary) / "libangryarm64.so"
            header = bytearray(20)
            header[:6] = b"\x7fELF\x02\x01"
            header[18:20] = (183).to_bytes(2, "little")
            library.write_bytes(header + bytes(1024 * 1024))
            core.validate_runtime_library(library)
            header[18:20] = (62).to_bytes(2, "little")
            library.write_bytes(header + bytes(1024 * 1024))
            with self.assertRaisesRegex(core.BuilderError, "not compiled for ARM64"):
                core.validate_runtime_library(library)

    def test_output_preflight_refuses_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            existing = Path(temporary) / "keep.apk"
            existing.write_bytes(b"keep")
            with self.assertRaisesRegex(core.BuilderError, "will not be overwritten"):
                core.probe_output_writable(existing)
            self.assertEqual(existing.read_bytes(), b"keep")


if __name__ == "__main__":
    unittest.main()
