#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent

# Version that produced the currently proven build.
DEFAULT_NDK_VERSION = "30.0.15729638"

ANDROID_ABI = "arm64-v8a"
ANDROID_PLATFORM = "android-23"
ANDROID_STL = "c++_static"
CMAKE_BUILD_TYPE = "Release"
TARGET = "stage24_live_surface"

LEVEL_MANIFEST = ROOT / "tools" / "build_assets_levels.json"

SCRIPT_NAMES = (
    "animations.lua",
    "blocks.lua",
    "gamelogic.lua",
    "loadlist.lua",
    "particles.lua",
    "starLimits.lua",
)

FONT_DAT_NAMES = (
    "FONT_BASIC.dat",
    "FONT_MENU.dat",
    "FONT_SCORE.dat",
    "FONT_BIG_NUMBERS.dat",
    "FONT_LS_SMALL.dat",
)

FONT_RENDER_DAT_NAMES = (
    "FONT_BASIC.dat",
    "FONT_BIG_NUMBERS.dat",
    "FONT_SCORE.dat",
    "FONT_MENU.dat",
    "FONT_LS_SMALL.dat",
)

MENU_META_BASE = (
    "BACKGROUNDS_GE_1.dat",
    "BACKGROUNDS_LS_1.dat",
    "BACKGROUNDS_MAIN_1.dat",
    "POPUPS_SHEET_1.dat",
    "BUTTONS_SHEET_1.dat",
    "GOLDEN_EGGS_SHEET_1.dat",
    "LEVELSELECTION_SHEET_1.dat",
    "MENU_ELEMENTS_1.dat",
    "MENU_BACKGROUNDS_1.dat",
    "TUTORIALS_SHEET_1.dat",
    "SPLASHES_SHEET_1.dat",
    "SPLASHES_SHEET_2.dat",
)

MENU_META_OPTIONAL = (
    "ACHIEVEMENTS_SHEET_1.dat",
    "GOLDEN_EGGS_SHEET_2.dat",
    "GOLDEN_EGGS_SHEET_4.dat",
    "LEVELSELECTION_SHEET_2.dat",
    "MENU_ELEMENTS_2.dat",
    "MENU_ELEMENTS_3.dat",
    "SPLASHES_SHEET_3.dat",
)

CUTSCENE_META_NAMES = (
    "CUTSCENES_BACKGROUNDS_1.dat",
    "CUTSCENES_BACKGROUNDS_2.dat",
    "CUTSCENES_BACKGROUNDS_3.dat",
    "CUTSCENES_BACKGROUNDS_4.dat",
    "CUTSCENES_ELEMENTS_1.dat",
    "CUTSCENES_ELEMENTS_2.dat",
)

SCENE_META_NAMES = (
    "INGAME_SKIES_1.dat",
    "INGAME_SKIES_2.dat",
    "INGAME_PARALLAX_1.dat",
    "INGAME_PARALLAX_2.dat",
    "INGAME_PARALLAX_3.dat",
    "INGAME_PARALLAX_4.dat",
    "INGAME_PARALLAX_5.dat",
    "INGAME_PARALLAX_6.dat",
    "INGAME_PARALLAX_7.dat",
    "INGAME_PARALLAX_8.dat",
    "INGAME_PARALLAX_CRANES.dat",
    "INGAME_GROUNDS_1.dat",
)

SCENE_TEXTURE_NAMES = (
    "INGAME_SKIES_1.pvr",
    "INGAME_SKIES_2.pvr",
    "INGAME_PARALLAX_1.pvr",
    "INGAME_PARALLAX_2.pvr",
    "INGAME_PARALLAX_3.pvr",
    "INGAME_PARALLAX_4.pvr",
    "INGAME_PARALLAX_5.pvr",
    "INGAME_PARALLAX_6.pvr",
    "INGAME_PARALLAX_7.pvr",
    "INGAME_PARALLAX_8.pvr",
    "INGAME_PARALLAX_CRANES.pvr",
    "INGAME_GROUNDS_1.pvr",
)

TEXTURE_REFERENCE_RE = re.compile(
    rb"[A-Za-z0-9_.-]+\.(?:png|pvr)",
    re.IGNORECASE,
)


class BuildError(RuntimeError):
    pass


def fail(message: str) -> "NoReturn":
    raise BuildError(message)


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    printable = " ".join(str(x) for x in cmd)
    print(f"[build] $ {printable}")

    result = subprocess.run(
        [str(x) for x in cmd],
        cwd=str(cwd) if cwd else None,
    )

    if result.returncode != 0:
        fail(f"command failed with exit code {result.returncode}: {printable}")


def capture(cmd: list[str]) -> str:
    result = subprocess.run(
        [str(x) for x in cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        fail(
            f"command failed with exit code {result.returncode}: "
            + " ".join(str(x) for x in cmd)
            + "\n"
            + result.stdout
        )

    return result.stdout


def require_program(name: str) -> Path:
    found = shutil.which(name)
    if found:
        return Path(found).resolve()

    fail(f"required program not found in PATH: {name}")


def discover_ninja() -> Path:
    found = shutil.which("ninja")
    if found:
        return Path(found).resolve()

    if platform.system() == "Windows":
        candidates = [
            Path(r"C:\Program Files\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe"),
            Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe"),
            Path(r"C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe"),
            Path(r"C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe"),
            Path(r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe"),
            Path(r"C:\Program Files\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe"),
            Path(r"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe"),
        ]

        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()

    fail(
        "Ninja not found. Install Ninja or add it to PATH. "
        "On Windows, Visual Studio's bundled Ninja is also detected."
    )


def host_tag() -> str:
    system = platform.system()

    if system == "Windows":
        return "windows-x86_64"

    if system == "Linux":
        return "linux-x86_64"

    fail(
        f"unsupported build host: {system}. "
        "This build currently supports Windows and Linux."
    )


def exe(name: str) -> str:
    if platform.system() == "Windows":
        return name + ".exe"
    return name


def discover_android_sdk(explicit: str | None) -> Path:
    candidates: list[Path] = []

    if explicit:
        candidates.append(Path(explicit).expanduser())

    for env_name in ("ANDROID_SDK_ROOT", "ANDROID_HOME"):
        value = os.environ.get(env_name)
        if value:
            candidates.append(Path(value).expanduser())

    if platform.system() == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            candidates.append(Path(local_app_data) / "Android" / "Sdk")
    else:
        candidates.append(Path.home() / "Android" / "Sdk")

    seen: set[str] = set()

    for candidate in candidates:
        try:
            candidate = candidate.resolve()
        except OSError:
            continue

        key = str(candidate).casefold()

        if key in seen:
            continue

        seen.add(key)

        if (
            candidate.is_dir()
            and (candidate / "platforms").is_dir()
            and (candidate / "build-tools").is_dir()
        ):
            return candidate

    rendered = "\n".join(f"  - {x}" for x in candidates)

    fail(
        "Android SDK not found.\n"
        "Checked:\n"
        f"{rendered}\n"
        "Use --android-sdk or ANDROID_SDK_ROOT."
    )


def discover_ndk(
    sdk: Path,
    explicit: str | None,
    ndk_version: str,
) -> Path:
    if explicit:
        ndk = Path(explicit).expanduser().resolve()

        if not (ndk / "build" / "cmake" / "android.toolchain.cmake").is_file():
            fail(f"invalid Android NDK path: {ndk}")

        return ndk

    pinned = sdk / "ndk" / ndk_version

    if pinned.is_dir():
        return pinned.resolve()

    installed_root = sdk / "ndk"

    installed = []
    if installed_root.is_dir():
        installed = sorted(
            (x.name for x in installed_root.iterdir() if x.is_dir()),
            reverse=True,
        )

    installed_text = ", ".join(installed) if installed else "<none>"

    fail(
        f"pinned Android NDK {ndk_version} not found at:\n"
        f"  {pinned}\n"
        f"Installed NDKs: {installed_text}\n"
        "Use --android-ndk to intentionally build with another NDK."
    )


def ndk_tool(ndk: Path, name: str) -> Path:
    tool = (
        ndk
        / "toolchains"
        / "llvm"
        / "prebuilt"
        / host_tag()
        / "bin"
        / exe(name)
    )

    if not tool.is_file():
        fail(f"NDK tool not found: {tool}")

    return tool



def numeric_version_key(name: str) -> tuple[int, ...]:
    nums = re.findall(r"\d+", name)
    return tuple(int(x) for x in nums) if nums else (0,)


def discover_android_packaging_tools(sdk: Path) -> dict[str, Path]:
    build_tools_root = sdk / "build-tools"

    if not build_tools_root.is_dir():
        fail(f"Android build-tools directory missing: {build_tools_root}")

    directories = sorted(
        [p for p in build_tools_root.iterdir() if p.is_dir()],
        key=lambda p: numeric_version_key(p.name),
        reverse=True,
    )

    if platform.system() == "Windows":
        tool_names = {
            "aapt": "aapt.exe",
            "zipalign": "zipalign.exe",
            "apksigner": "apksigner.bat",
        }
    else:
        tool_names = {
            "aapt": "aapt",
            "zipalign": "zipalign",
            "apksigner": "apksigner",
        }

    chosen = None

    for directory in directories:
        candidates = {
            key: directory / filename
            for key, filename in tool_names.items()
        }

        if all(path.is_file() for path in candidates.values()):
            chosen = candidates
            chosen["build_tools"] = directory
            break

    if chosen is None:
        fail(
            "No Android build-tools installation contains "
            "aapt + zipalign + apksigner."
        )

    platforms_root = sdk / "platforms"

    platforms = sorted(
        [
            p
            for p in platforms_root.iterdir()
            if p.is_dir()
            and re.fullmatch(r"android-\d+", p.name)
            and (p / "android.jar").is_file()
        ],
        key=lambda p: int(p.name.split("-", 1)[1]),
        reverse=True,
    )

    if not platforms:
        fail(f"No usable Android platform found in {platforms_root}")

    chosen["android_jar"] = platforms[0] / "android.jar"

    return chosen


def external_command(executable: Path, *args: str) -> list[str]:
    if (
        platform.system() == "Windows"
        and executable.suffix.casefold() in {".bat", ".cmd"}
    ):
        return [
            "cmd.exe",
            "/d",
            "/c",
            str(executable),
            *map(str, args),
        ]

    return [
        str(executable),
        *map(str, args),
    ]


class AsciiPathBridges:
    def __init__(self) -> None:
        self._mapped: list[str] = []
        self._cache: dict[str, Path] = {}

    def bridge_root(self, root: Path) -> Path:
        root = root.resolve()

        if platform.system() != "Windows":
            return root

        if str(root).isascii():
            return root

        key = str(root).casefold()

        if key in self._cache:
            return self._cache[key]

        listing = subprocess.run(
            ["subst"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).stdout.casefold()

        for letter in reversed("PQRSTUVWXYZ"):
            drive = f"{letter}:"

            if drive.casefold() in listing:
                continue

            if Path(drive + "\\").exists():
                continue

            result = subprocess.run(
                ["subst", drive, str(root)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            if result.returncode != 0:
                continue

            mapped = Path(drive + "\\")
            self._mapped.append(drive)
            self._cache[key] = mapped

            print(f"[package] ASCII bridge: {mapped} -> {root}")
            return mapped

        fail(f"could not allocate ASCII subst drive for: {root}")

    def convert(
        self,
        path: Path,
        original_root: Path,
        bridged_root: Path,
    ) -> Path:
        original_root = original_root.resolve()
        path = path.resolve()

        relative = path.relative_to(original_root)
        return bridged_root / relative

    def close(self) -> None:
        if platform.system() != "Windows":
            return

        for drive in reversed(self._mapped):
            subprocess.run(
                ["subst", drive, "/d"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        self._mapped.clear()
        self._cache.clear()


def prepare_launcher_icon(
    original_root: Path,
    destination: Path,
    explicit: str | None,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    if explicit:
        copy_required(
            Path(explicit).expanduser().resolve(),
            destination,
        )
        return

    helper = ROOT / "tools" / "stage24481_find_original_launcher_icon.py"

    if not helper.is_file():
        fail(
            "launcher-icon helper missing. "
            "Use --launcher-icon explicitly."
        )

    downloads_root = Path.home() / "Downloads"

    run(
        [
            sys.executable,
            str(helper),
            str(original_root),
            str(downloads_root),
            str(destination),
        ]
    )

    if not destination.is_file():
        fail(
            "launcher icon discovery produced no file. "
            "Use --launcher-icon PATH."
        )


def ensure_debug_keystore(path: Path) -> None:
    if path.is_file():
        return

    keytool = require_program("keytool")

    path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[package] Creating persistent debug keystore: {path}")

    run(
        [
            str(keytool),
            "-genkeypair",
            "-noprompt",
            "-keystore",
            str(path),
            "-storepass",
            "android",
            "-keypass",
            "android",
            "-alias",
            "androiddebugkey",
            "-dname",
            "CN=Android Debug,O=Android,C=US",
            "-keyalg",
            "RSA",
            "-keysize",
            "2048",
            "-validity",
            "10000",
            "-storetype",
            "JKS",
        ]
    )


def package_debug_apk(args: argparse.Namespace) -> None:
    env = resolve_environment(args)
    tools = discover_android_packaging_tools(env["sdk"])

    original_root = discover_original_root(args.original_root)

    native_so = ROOT / "build" / "android-arm64" / "libangryarm64.so"
    assets_root = ROOT / "build" / "staging" / "assets"

    if not native_so.is_file():
        fail(f"native library missing: {native_so}")

    if not assets_root.is_dir():
        fail(f"staged assets missing: {assets_root}")

    package_root = ROOT / "build" / "apk"

    if package_root.exists():
        shutil.rmtree(package_root)

    package_root.mkdir(parents=True)

    res_root = package_root / "res"
    drawable_root = res_root / "drawable"

    launcher_icon = drawable_root / "app_icon.png"

    prepare_launcher_icon(
        original_root,
        launcher_icon,
        args.launcher_icon,
    )

    manifest_source = (
        ROOT
        / "stage24-android"
        / "AndroidManifest.xml"
    )

    if not manifest_source.is_file():
        fail(f"audit Android manifest missing: {manifest_source}")

    manifest_root = package_root / "package-manifest"
    manifest_root.mkdir(parents=True)

    manifest = manifest_root / "AndroidManifest.xml"
    shutil.copy2(manifest_source, manifest)

    unsigned = package_root / "stage24-unsigned.apk"
    with_lib = package_root / "stage24-with-lib.apk"
    aligned = package_root / "stage24-aligned.apk"
    signed = package_root / "angry-birds-arm64-audit.apk"

    debug_keystore = (
        Path.home()
        / ".android"
        / "angry-arm64-stage24-debug.keystore"
    )

    ensure_debug_keystore(debug_keystore)

    bridges = AsciiPathBridges()

    try:
        project_bridge = bridges.bridge_root(ROOT)
        sdk_bridge = bridges.bridge_root(env["sdk"])
        key_root = debug_keystore.parent.resolve()
        key_bridge = bridges.bridge_root(key_root)

        def project_path(path: Path) -> Path:
            return bridges.convert(
                path,
                ROOT,
                project_bridge,
            )

        def sdk_path(path: Path) -> Path:
            return bridges.convert(
                path,
                env["sdk"],
                sdk_bridge,
            )

        def key_path(path: Path) -> Path:
            return bridges.convert(
                path,
                key_root,
                key_bridge,
            )

        aapt = sdk_path(tools["aapt"])
        zipalign = sdk_path(tools["zipalign"])
        apksigner = sdk_path(tools["apksigner"])
        android_jar = sdk_path(tools["android_jar"])

        print()
        print(
            "[package] Packaging NativeActivity APK "
            "from staged user-owned assets..."
        )

        run(
            external_command(
                aapt,
                "package",
                "-f",
                "-0",
                "mp3",
                "-M",
                str(project_path(manifest)),
                "-I",
                str(android_jar),
                "-S",
                str(project_path(res_root)),
                "-A",
                str(project_path(assets_root)),
                "-F",
                str(project_path(unsigned)),
            )
        )

        add_lib = ROOT / "tools" / "apk_add_native_lib.py"

        if not add_lib.is_file():
            fail(f"APK native-lib helper missing: {add_lib}")

        run(
            [
                sys.executable,
                str(add_lib),
                str(unsigned),
                str(with_lib),
                str(native_so),
                "lib/arm64-v8a/libangryarm64.so",
            ]
        )

        ensure_dir_tool = (
            ROOT
            / "tools"
            / "apk_ensure_asset_dir.py"
        )

        if not ensure_dir_tool.is_file():
            fail(
                f"APK asset-directory helper missing: "
                f"{ensure_dir_tool}"
            )

        ensure_pairs = (
            (
                assets_root / "stage24" / "menu-textures",
                "assets/stage24/menu-textures",
            ),
            (
                assets_root / "stage24" / "font-textures",
                "assets/stage24/font-textures",
            ),
            (
                assets_root / "stage24" / "scene-textures",
                "assets/stage24/scene-textures",
            ),
            (
                assets_root / "stage24" / "data" / "audio",
                "assets/stage24/data/audio",
            ),
        )

        for local_dir, apk_dir in ensure_pairs:
            run(
                [
                    sys.executable,
                    str(ensure_dir_tool),
                    str(with_lib),
                    str(local_dir),
                    apk_dir,
                ]
            )

        run(
            external_command(
                zipalign,
                "-f",
                "-p",
                "4",
                str(project_path(with_lib)),
                str(project_path(aligned)),
            )
        )

        run(
            external_command(
                apksigner,
                "sign",
                "--ks",
                str(key_path(debug_keystore)),
                "--ks-pass",
                "pass:android",
                "--key-pass",
                "pass:android",
                "--ks-key-alias",
                "androiddebugkey",
                "--out",
                str(project_path(signed)),
                str(project_path(aligned)),
            )
        )

        print()
        print("[verify] APK signature...")

        run(
            external_command(
                apksigner,
                "verify",
                "--verbose",
                "--print-certs",
                str(project_path(signed)),
            )
        )

        print("[verify] Signature PASS")

        payload_audit = (
            ROOT
            / "tools"
            / "stage24480_apk_payload_audit.py"
        )

        if payload_audit.is_file():
            run(
                [
                    sys.executable,
                    str(payload_audit),
                    str(signed),
                ]
            )

            print("[verify] ARM64-only payload PASS")

        badging = capture(
            external_command(
                aapt,
                "dump",
                "badging",
                str(project_path(signed)),
            )
        )

        if "label='Angry Birds'" not in badging:
            fail(
                "APK branding check failed: "
                "expected label='Angry Birds'"
            )

        if "icon='res/drawable/app_icon.png'" not in badging:
            fail(
                "APK branding check failed: "
                "launcher icon mismatch"
            )

        print("[verify] Angry Birds label/icon PASS")

    finally:
        bridges.close()

    if not signed.is_file():
        fail(f"signed APK missing: {signed}")

    print()
    print("[package] PASS")
    print(f"[package] APK ready: {signed}")


def build_apk(args: argparse.Namespace) -> None:
    print("=== NATIVE ===")
    native_build(args)

    print()
    print("=== ASSETS ===")
    stage_assets(args)

    print()
    print("=== APK ===")
    package_debug_apk(args)


def resolve_environment(args: argparse.Namespace) -> dict[str, Path]:
    sdk = discover_android_sdk(args.android_sdk)
    ndk = discover_ndk(sdk, args.android_ndk, args.ndk_version)

    cmake = require_program("cmake")
    ninja = discover_ninja()

    toolchain = ndk / "build" / "cmake" / "android.toolchain.cmake"

    if not toolchain.is_file():
        fail(f"Android CMake toolchain not found: {toolchain}")

    readelf = ndk_tool(ndk, "llvm-readelf")

    return {
        "sdk": sdk,
        "ndk": ndk,
        "cmake": cmake,
        "ninja": ninja,
        "toolchain": toolchain,
        "readelf": readelf,
    }



def discover_original_root(explicit: str | None) -> Path:
    candidates: list[Path] = []

    if explicit:
        candidates.append(Path(explicit).expanduser())

    env_root = os.environ.get("ANGRY_BIRDS_ORIGINAL_ROOT")
    if env_root:
        candidates.append(Path(env_root).expanduser())

    candidates.extend(
        [
            Path.home() / "Downloads" / "angry-re",
            Path.home() / "angry-re",
        ]
    )

    seen: set[str] = set()

    for candidate in candidates:
        try:
            candidate = candidate.resolve()
        except OSError:
            continue

        key = str(candidate).casefold()
        if key in seen:
            continue
        seen.add(key)

        if (candidate / "assets" / "data").is_dir():
            return candidate

    rendered = "\n".join(f"  - {x}" for x in candidates)

    fail(
        "Original Angry Birds extraction not found.\n"
        "Checked:\n"
        f"{rendered}\n"
        "Use --original-root or ANGRY_BIRDS_ORIGINAL_ROOT."
    )


def copy_required(source: Path, destination: Path) -> None:
    if not source.is_file():
        fail(f"required original asset missing: {source}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def write_ascii_lines(path: Path, lines: list[str] | tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(lines) + "\n"
    path.write_bytes(payload.encode("ascii"))


def extract_single_pvr(archive: Path, destination: Path) -> Path:
    if not archive.is_file():
        fail(f"PVR archive not found: {archive}")

    if destination.exists():
        shutil.rmtree(destination)

    destination.mkdir(parents=True, exist_ok=True)
    destination_resolved = destination.resolve()

    with zipfile.ZipFile(archive, "r") as zf:
        for member in zf.infolist():
            target = (destination / member.filename).resolve()

            try:
                target.relative_to(destination_resolved)
            except ValueError:
                fail(f"unsafe ZIP member in {archive}: {member.filename}")

        zf.extractall(destination)

    pvrs = sorted(
        p
        for p in destination.rglob("*")
        if p.is_file() and p.suffix.casefold() == ".pvr"
    )

    if len(pvrs) != 1:
        fail(
            f"expected exactly one PVR in {archive}; "
            f"found {len(pvrs)}"
        )

    return pvrs[0]


def materialize_pvr(
    image_root: Path,
    texture_name: str,
    temp_root: Path,
    tag: str,
) -> Path:
    direct = image_root / texture_name

    if direct.is_file():
        return direct

    archive = Path(str(direct) + ".zip")
    safe = Path(texture_name).stem

    return extract_single_pvr(
        archive,
        temp_root / f"{tag}_{safe}",
    )


def discover_texture_names(meta_files: list[Path]) -> list[str]:
    found: dict[str, str] = {}

    for meta in meta_files:
        if not meta.is_file():
            fail(f"required original metadata missing: {meta}")

        for raw in TEXTURE_REFERENCE_RE.findall(meta.read_bytes()):
            name = raw.decode("ascii")
            found.setdefault(name.casefold(), name)

    names = sorted(found.values(), key=str.casefold)

    if not names:
        fail("no PNG/PVR texture references found in metadata")

    return names


def run_png_conversion(source: Path, destination: Path) -> None:
    tool = ROOT / "tools" / "png_to_rgba8.py"

    if not tool.is_file():
        fail(f"PNG conversion helper missing: {tool}")

    destination.parent.mkdir(parents=True, exist_ok=True)

    run(
        [
            sys.executable,
            str(tool),
            str(source),
            str(destination),
        ]
    )

    if not destination.is_file():
        fail(f"PNG conversion produced no output: {destination}")


def recover_font_image_name(font_dat: Path) -> str:
    tool = ROOT / "tools" / "font_dat_image_name.py"

    if not tool.is_file():
        fail(f"font image-name helper missing: {tool}")

    output = capture(
        [
            sys.executable,
            str(tool),
            str(font_dat),
        ]
    )

    lines = [line.strip() for line in output.splitlines() if line.strip()]

    if not lines:
        fail(f"could not recover bitmap image name from {font_dat}")

    return lines[-1]


def resolve_font_texture(
    data_root: Path,
    font_profile_root: Path,
    logical_name: str,
) -> tuple[Path | None, list[Path]]:
    parts = [
        p
        for p in re.split(r"[\\/]+", logical_name)
        if p
    ]

    basename = parts[-1]
    candidates: list[Path] = []

    if parts and parts[0].casefold() == "data":
        candidates.append(data_root.joinpath(*parts[1:]))

    elif parts and parts[0].casefold() == "fonts":
        candidates.append(data_root.joinpath(*parts))

    candidates.append(font_profile_root / basename)

    for candidate in candidates:
        if candidate.is_file():
            return candidate, candidates

    found = [
        p
        for p in data_root.rglob("*")
        if p.is_file() and p.name.casefold() == basename.casefold()
    ]

    if len(found) == 1:
        return found[0], candidates

    if len(found) > 1:
        profile_matches = [
            p
            for p in found
            if "fonts/864x480" in p.as_posix().casefold()
        ]

        if len(profile_matches) == 1:
            return profile_matches[0], candidates

    return None, candidates


def stage_assets(args: argparse.Namespace) -> None:
    original_root = discover_original_root(args.original_root)

    data_root = original_root / "assets" / "data"
    scripts_root = data_root / "scripts"
    image_root = data_root / "images" / "864x480"
    localization_root = data_root / "localization"
    font_profile_root = data_root / "fonts" / "864x480"
    audio_root = data_root / "audio"

    required_roots = (
        scripts_root,
        image_root,
        localization_root,
        font_profile_root,
        audio_root,
    )

    for required in required_roots:
        if not required.is_dir():
            fail(f"required original asset directory missing: {required}")

    work_root = ROOT / "build" / "staging"

    if work_root.exists():
        shutil.rmtree(work_root)

    assets_root = work_root / "assets"
    stage_root = assets_root / "stage24"
    temp_root = work_root / "tmp"

    assets_scripts = stage_root / "scripts"
    assets_sprite_meta = stage_root / "sprite-meta"
    assets_localization = stage_root / "localization"
    assets_fonts = stage_root / "fonts" / "864x480"
    assets_font_textures = stage_root / "font-textures"
    assets_menu_textures = stage_root / "menu-textures"
    assets_scene_meta = stage_root / "scene-meta"
    assets_scene_textures = stage_root / "scene-textures"
    assets_dynamic_sheets = stage_root / "dynamic-sheets"
    assets_dynamic_textures = stage_root / "dynamic-textures"
    assets_audio = stage_root / "data" / "audio"

    directories = (
        assets_scripts,
        assets_sprite_meta,
        assets_localization,
        assets_fonts,
        assets_font_textures,
        assets_menu_textures,
        assets_scene_meta,
        assets_scene_textures,
        assets_dynamic_sheets,
        assets_dynamic_textures,
        assets_audio,
        temp_root,
    )

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    print(f"[stage] Original root: {original_root}")

    # --------------------------------------------------------
    # Lua scripts
    # --------------------------------------------------------

    for name in SCRIPT_NAMES:
        copy_required(
            scripts_root / name,
            assets_scripts / name,
        )

    print(f"[stage] Lua scripts: {len(SCRIPT_NAMES)}")

    # --------------------------------------------------------
    # Complete level map, mechanically extracted from the
    # homologated legacy builder.
    # --------------------------------------------------------

    if not LEVEL_MANIFEST.is_file():
        fail(f"level staging manifest missing: {LEVEL_MANIFEST}")

    try:
        level_records = json.loads(
            LEVEL_MANIFEST.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid level staging manifest: {exc}")

    if not isinstance(level_records, list) or len(level_records) != 211:
        fail(
            "level staging manifest must contain exactly "
            f"211 records; found {len(level_records) if isinstance(level_records, list) else 'non-list'}"
        )

    seen_destinations: set[str] = set()

    for record in level_records:
        if not isinstance(record, dict):
            fail("invalid level manifest record")

        source_rel = record.get("source")
        destination_rel = record.get("destination")

        if not isinstance(source_rel, str) or not isinstance(destination_rel, str):
            fail("invalid level manifest source/destination")

        destination_key = destination_rel.casefold()

        if destination_key in seen_destinations:
            fail(f"duplicate level staging destination: {destination_rel}")

        seen_destinations.add(destination_key)

        copy_required(
            data_root / Path(source_rel),
            stage_root / Path(destination_rel),
        )

    print(f"[stage] Level files: {len(level_records)} staging records")

    # --------------------------------------------------------
    # Gameplay sprite data + terrain PVRs
    # --------------------------------------------------------

    for name in (
        "INGAME_BLOCKS_1.dat",
        "INGAME_BIRDS_1.dat",
    ):
        copy_required(
            image_root / name,
            stage_root / name,
        )

    for name, tag in (
        ("INGAME_BLOCKS_1.pvr", "blocks"),
        ("INGAME_BIRDS_1.pvr", "birds"),
    ):
        # The historical Android extraction stores these two
        # as one-file .pvr.zip wrappers.
        source = extract_single_pvr(
            Path(str(image_root / name) + ".zip"),
            temp_root / tag,
        )
        copy_required(source, stage_root / name)

    for index in range(1, 9):
        name = f"INGAME_THEME_GROUND_{index}.pvr"

        source = materialize_pvr(
            image_root,
            name,
            temp_root,
            f"theme_ground_{index}",
        )

        copy_required(source, stage_root / name)

    print("[stage] Gameplay DAT/PVR transports: PASS")

    # --------------------------------------------------------
    # Scene families
    # --------------------------------------------------------

    for name in SCENE_META_NAMES:
        copy_required(
            image_root / name,
            assets_scene_meta / name,
        )

    scene_manifest: list[str] = []

    for name in SCENE_TEXTURE_NAMES:
        copy_required(
            image_root / name,
            assets_scene_textures / name,
        )

        scene_manifest.append(
            f"{name}\tPVRV2\t{name}"
        )

    write_ascii_lines(
        assets_scene_textures / "manifest.tsv",
        scene_manifest,
    )

    print(
        "[stage] Scene families: "
        f"meta={len(SCENE_META_NAMES)} "
        f"textures={len(SCENE_TEXTURE_NAMES)}"
    )

    # --------------------------------------------------------
    # Localization + bitmap fonts
    # --------------------------------------------------------

    copy_required(
        localization_root / "TEXTS_BASIC.dat",
        assets_localization / "TEXTS_BASIC.dat",
    )

    for name in FONT_DAT_NAMES:
        copy_required(
            font_profile_root / name,
            assets_fonts / name,
        )

    font_inputs: list[tuple[str, str, Path, str]] = []
    font_seen: set[str] = set()

    for font_dat_name in FONT_RENDER_DAT_NAMES:
        font_dat = font_profile_root / font_dat_name
        logical = recover_font_image_name(font_dat)

        if logical in font_seen:
            continue

        font_seen.add(logical)

        source, candidates = resolve_font_texture(
            data_root,
            font_profile_root,
            logical,
        )

        basename = re.split(r"[\\/]+", logical)[-1]
        extension = Path(basename).suffix.casefold()
        safe_font = Path(font_dat_name).stem

        if extension == ".pvr":
            if source is None:
                for candidate in candidates:
                    archive = Path(str(candidate) + ".zip")

                    if archive.is_file():
                        source = extract_single_pvr(
                            archive,
                            temp_root / f"font_{safe_font}",
                        )
                        break

            if source is None:
                fail(
                    f"original bitmap-font PVR not found "
                    f"for {font_dat_name}: {logical}"
                )

            asset_name = f"{safe_font}-{basename}.bin"

            font_inputs.append(
                (logical, "pvr4444", source, asset_name)
            )

        elif extension == ".png":
            if source is None:
                fail(
                    f"original bitmap-font PNG not found "
                    f"for {font_dat_name}: {logical}"
                )

            asset_name = f"{safe_font}-{basename}.rgba8.bin"
            materialized = temp_root / asset_name

            run_png_conversion(source, materialized)

            font_inputs.append(
                (logical, "rgba8", materialized, asset_name)
            )

        else:
            fail(
                f"unsupported bitmap-font texture extension "
                f"for {font_dat_name}: {logical}"
            )

    font_manifest: list[str] = []

    for logical, kind, source, asset_name in font_inputs:
        copy_required(
            source,
            assets_font_textures / asset_name,
        )

        font_manifest.append(
            f"{logical}\t{kind}\t{asset_name}"
        )

    write_ascii_lines(
        assets_font_textures / "manifest.tsv",
        font_manifest,
    )

    print(
        "[stage] Bitmap fonts: "
        f"dat={len(FONT_DAT_NAMES)} "
        f"textures={len(font_inputs)}"
    )

    # --------------------------------------------------------
    # Menu metadata
    # --------------------------------------------------------

    menu_meta_names = list(MENU_META_BASE)

    supplemental = [
        name
        for name in MENU_META_OPTIONAL
        if (image_root / name).is_file()
    ]

    menu_meta_names.extend(
        name
        for name in supplemental
        if name not in menu_meta_names
    )

    if "GOLDEN_EGGS_SHEET_2.dat" not in supplemental:
        fail(
            "required original GOLDEN_EGGS_SHEET_2.dat "
            "is missing"
        )

    menu_meta_files = [
        image_root / name
        for name in menu_meta_names
    ]

    for source in menu_meta_files:
        copy_required(
            source,
            assets_sprite_meta / source.name,
        )

    copy_required(
        image_root / "TUTORIALS_composprites.dat",
        assets_sprite_meta / "TUTORIALS_composprites.dat",
    )

    write_ascii_lines(
        assets_sprite_meta / "bootstrap-menu-meta.txt",
        menu_meta_names,
    )

    menu_texture_names = discover_texture_names(
        menu_meta_files
    )

    menu_manifest: list[str] = []

    for texture_name in menu_texture_names:
        extension = Path(texture_name).suffix.casefold()

        if extension == ".pvr":
            materialized = materialize_pvr(
                image_root,
                texture_name,
                temp_root,
                "menu",
            )

            asset_name = f"{texture_name}.bin"
            kind = "pvr4444"

        elif extension == ".png":
            source = image_root / texture_name

            if not source.is_file():
                fail(f"original menu PNG missing: {source}")

            asset_name = f"{texture_name}.rgba8.bin"
            materialized = temp_root / asset_name

            run_png_conversion(
                source,
                materialized,
            )

            kind = "rgba8"

        else:
            fail(
                f"unsupported menu texture extension: "
                f"{texture_name}"
            )

        copy_required(
            materialized,
            assets_menu_textures / asset_name,
        )

        menu_manifest.append(
            f"{texture_name}\t{kind}\t{asset_name}"
        )

    write_ascii_lines(
        assets_menu_textures / "manifest.tsv",
        menu_manifest,
    )

    print(
        "[stage] Menu resources: "
        f"meta={len(menu_meta_names)} "
        f"textures={len(menu_manifest)}"
    )

    # --------------------------------------------------------
    # Dynamic cutscene resources
    # --------------------------------------------------------

    cutscene_meta_files = [
        image_root / name
        for name in CUTSCENE_META_NAMES
    ]

    cutscene_texture_names = discover_texture_names(
        cutscene_meta_files
    )

    for source in cutscene_meta_files:
        copy_required(
            source,
            assets_dynamic_sheets / source.name,
        )

    cutscene_manifest: list[str] = []

    for texture_name in cutscene_texture_names:
        extension = Path(texture_name).suffix.casefold()

        if extension == ".pvr":
            materialized = materialize_pvr(
                image_root,
                texture_name,
                temp_root,
                "cutscene",
            )

            asset_name = f"{texture_name}.bin"
            kind = "pvrv2"

        elif extension == ".png":
            source = image_root / texture_name

            if not source.is_file():
                fail(f"original cutscene PNG missing: {source}")

            asset_name = f"{texture_name}.rgba8.bin"
            materialized = temp_root / asset_name

            run_png_conversion(
                source,
                materialized,
            )

            kind = "rgba8"

        else:
            fail(
                f"unsupported cutscene texture extension: "
                f"{texture_name}"
            )

        copy_required(
            materialized,
            assets_dynamic_textures / asset_name,
        )

        cutscene_manifest.append(
            f"{texture_name}\t{kind}\t{asset_name}"
        )

    write_ascii_lines(
        assets_dynamic_textures / "manifest.tsv",
        cutscene_manifest,
    )

    print(
        "[stage] Cutscene resources: "
        f"meta={len(CUTSCENE_META_NAMES)} "
        f"textures={len(cutscene_manifest)}"
    )

    # --------------------------------------------------------
    # Audio subtree
    # --------------------------------------------------------

    shutil.copytree(
        audio_root,
        assets_audio,
        dirs_exist_ok=True,
    )

    audio_files = [
        p
        for p in assets_audio.rglob("*")
        if p.is_file()
    ]

    wav_count = sum(
        p.suffix.casefold() == ".wav"
        for p in audio_files
    )

    mp3_count = sum(
        p.suffix.casefold() == ".mp3"
        for p in audio_files
    )

    print(
        "[stage] Audio: "
        f"wav={wav_count} "
        f"mp3={mp3_count} "
        f"total={len(audio_files)}"
    )

    # --------------------------------------------------------
    # Final staging sanity
    # --------------------------------------------------------

    staged_files = [
        p
        for p in stage_root.rglob("*")
        if p.is_file()
    ]

    if not staged_files:
        fail("asset staging produced no files")

    print()
    print("[stage] PASS")
    print(f"[stage] Root:  {assets_root}")
    print(f"[stage] Files: {len(staged_files)}")

def doctor(args: argparse.Namespace) -> None:
    env = resolve_environment(args)

    box2d = ROOT / "vendor" / "box2d-v2.1.2"
    lua = ROOT / "vendor" / "lua-5.1.5"
    source = ROOT / "stage24_live_surface.cpp"
    cmakelists = ROOT / "CMakeLists.txt"

    required = {
        "stage24_live_surface.cpp": source,
        "CMakeLists.txt": cmakelists,
        "Lua 5.1.5": lua,
        "Box2D 2.1.2": box2d,
    }

    print()
    print("Angry Birds ARM64 build doctor")
    print("--------------------------------")
    print(f"Host:       {platform.system()} / {platform.machine()}")
    print(f"Python:     {sys.executable}")
    print(f"SDK:        {env['sdk']}")
    print(f"NDK:        {env['ndk']}")
    print(f"Host tag:   {host_tag()}")
    print(f"CMake:      {env['cmake']}")
    print(f"Ninja:      {env['ninja']}")
    print(f"readelf:    {env['readelf']}")
    print()

    missing = False

    for label, path in required.items():
        state = "OK" if path.exists() else "MISSING"
        print(f"{label:28} {state:7} {path}")

        if not path.exists():
            missing = True

    if missing:
        fail("source/vendor preflight failed")

    print()
    print("[build] doctor PASS")


def native_build(args: argparse.Namespace) -> None:
    env = resolve_environment(args)

    box2d = ROOT / "vendor" / "box2d-v2.1.2"

    if not box2d.is_dir():
        fail(f"Box2D source missing: {box2d}")

    build_dir = ROOT / "build" / "android-arm64"

    if args.clean and build_dir.exists():
        print(f"[build] removing {build_dir}")
        shutil.rmtree(build_dir)

    build_dir.mkdir(parents=True, exist_ok=True)

    configure = [
        str(env["cmake"]),
        "-S",
        str(ROOT),
        "-B",
        str(build_dir),
        "-G",
        "Ninja",
        f"-DCMAKE_MAKE_PROGRAM={env['ninja']}",
        f"-DCMAKE_TOOLCHAIN_FILE={env['toolchain']}",
        f"-DANDROID_ABI={ANDROID_ABI}",
        f"-DANDROID_PLATFORM={ANDROID_PLATFORM}",
        f"-DANDROID_STL={ANDROID_STL}",
        f"-DCMAKE_BUILD_TYPE={CMAKE_BUILD_TYPE}",
        f"-DSTAGE24_DISPLAY_MODE={args.display_mode}",
        "-DSTAGE24282_GLOBAL_SPRITE_REGISTRY=OFF",
        f"-DBOX2D212_ROOT={box2d}",
    ]

    print()
    print("[build] Configuring Android ARM64 native target...")
    run(configure)

    build_cmd = [
        str(env["cmake"]),
        "--build",
        str(build_dir),
        "--target",
        TARGET,
    ]

    if args.jobs:
        build_cmd += ["--parallel", str(args.jobs)]

    print()
    print("[build] Building libangryarm64.so...")
    run(build_cmd)

    so = build_dir / "libangryarm64.so"

    if not so.is_file():
        fail(f"native output missing: {so}")

    header = capture([str(env["readelf"]), "-h", str(so)])

    if "AArch64" not in header:
        fail(f"native output is not AArch64: {so}")

    print()
    print("[build] AArch64 verification PASS")
    print(f"[build] Native library ready: {so}")
    print()
    print(
        "[build] Incremental build directory retained. "
        "Use --clean only when a full rebuild is actually needed."
    )


def add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--android-sdk",
        help="Android SDK root. Falls back to ANDROID_SDK_ROOT / ANDROID_HOME.",
    )
    parser.add_argument(
        "--android-ndk",
        help="Explicit Android NDK root.",
    )
    parser.add_argument(
        "--ndk-version",
        default=DEFAULT_NDK_VERSION,
        help=f"Pinned SDK/ndk version (default: {DEFAULT_NDK_VERSION}).",
    )


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Cross-platform Angry Birds ARM64 build orchestrator. "
            "Windows and Linux hosts are supported."
        )
    )

    sub = parser.add_subparsers(dest="command", required=True)

    doctor_parser = sub.add_parser(
        "doctor",
        help="Check host build dependencies without compiling.",
    )
    add_common_options(doctor_parser)
    doctor_parser.set_defaults(func=doctor)

    native_parser = sub.add_parser(
        "native",
        help="Build the Android ARM64 native library with CMake/Ninja.",
    )
    add_common_options(native_parser)

    native_parser.add_argument(
        "--display-mode",
        choices=("wvga854", "native"),
        default="wvga854",
    )
    native_parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete the incremental native build directory first.",
    )
    native_parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        help="Parallel build jobs. Ninja default is used when omitted.",
    )

    native_parser.set_defaults(func=native_build)

    stage_parser = sub.add_parser(
        "stage",
        help="Stage original game assets for APK packaging.",
    )

    stage_parser.add_argument(
        "--original-root",
        help=(
            "Root of the user's extracted original game tree. "
            "Falls back to ANGRY_BIRDS_ORIGINAL_ROOT."
        ),
    )

    stage_parser.set_defaults(func=stage_assets)

    apk_parser = sub.add_parser(
        "apk",
        help=(
            "Build, stage and package a locally signed "
            "Android ARM64 audit APK."
        ),
    )

    add_common_options(apk_parser)

    apk_parser.add_argument(
        "--original-root",
        help=(
            "Root of the user's extracted original game tree. "
            "Falls back to ANGRY_BIRDS_ORIGINAL_ROOT."
        ),
    )

    apk_parser.add_argument(
        "--launcher-icon",
        help=(
            "Explicit original launcher icon PNG. "
            "Automatic discovery is used when omitted."
        ),
    )

    apk_parser.add_argument(
        "--display-mode",
        choices=("wvga854", "native"),
        default="wvga854",
    )

    apk_parser.add_argument(
        "--clean",
        action="store_true",
        help="Force a clean native rebuild before packaging.",
    )

    apk_parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        help="Parallel native build jobs.",
    )

    apk_parser.set_defaults(func=build_apk)

    return parser


def main() -> int:
    parser = make_parser()
    args = parser.parse_args()

    try:
        args.func(args)
        return 0
    except BuildError as exc:
        print()
        print(f"[build] ERROR: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n[build] interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())