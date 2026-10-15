from __future__ import annotations

import argparse
import base64
import ctypes
from datetime import datetime, timezone
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
import traceback
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from windows_builder_core import (
    BuilderError,
    extract_original_assets,
    extract_launcher_icon,
    output_path_for,
    probe_output_writable,
    validate_original_apk,
    validate_original_hash,
    validate_runtime_library,
)


APP_NAME = "Angry Birds ARM64 Builder Preview"
ANDROID_SDK_URL = "https://developer.android.com/tools"
JAVA_URL = "https://adoptium.net/temurin/releases/?version=17"
BUILDER_BUILD_TOOLS_VERSION = "35.0.0"
BUILDER_PLATFORM_API = 35


def app_root() -> Path:
    return Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]


def support_root(override: str | None = None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    bundled = app_root() / "support"
    if bundled.joinpath("build.py").is_file():
        return bundled
    return app_root()


def runtime_library(override: str | None = None) -> Path:
    if override:
        candidate = Path(override).expanduser().resolve()
        if not candidate.is_file():
            raise BuilderError(f"The selected ARM64 runtime library does not exist: {candidate}")
        return candidate
    candidates = []
    candidates.extend(
        [
            app_root() / "runtime" / "libangryarm64.so",
            app_root() / "build" / "android-arm64" / "libangryarm64.so",
        ]
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise BuilderError(
        "The ARM64 runtime library is missing. Reinstall the builder package "
        "or rebuild the runtime from the project source."
    )


def local_data_root() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        raise BuilderError("Windows did not provide LOCALAPPDATA for private build files.")
    root = Path(base) / "AngryBirdsARM64"
    root.mkdir(parents=True, exist_ok=True)
    return root


def append_app_log(message: str) -> None:
    try:
        log_dir = local_data_root() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        with (log_dir / "builder.log").open("a", encoding="utf-8") as log:
            log.write(f"[{datetime.now(timezone.utc).isoformat()}] {message}\n")
    except OSError:
        pass


def find_sdk(explicit: str | None = None) -> Path:
    support = support_root()
    sys.path.insert(0, str(support))
    import build as build_system

    return build_system.discover_android_sdk(explicit)


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_uint32), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


def _dpapi(data: bytes, *, protect: bool) -> bytes:
    if os.name != "nt":
        raise BuilderError("Per-user signing password protection is available only on Windows.")
    crypt32 = ctypes.WinDLL("Crypt32.dll", use_last_error=True)
    kernel32 = ctypes.WinDLL("Kernel32.dll", use_last_error=True)
    input_buffer = ctypes.create_string_buffer(data)
    input_blob = _DataBlob(len(data), ctypes.cast(input_buffer, ctypes.POINTER(ctypes.c_ubyte)))
    output_blob = _DataBlob()
    if protect:
        function = crypt32.CryptProtectData
        function.argtypes = [
            ctypes.POINTER(_DataBlob),
            ctypes.c_wchar_p,
            ctypes.POINTER(_DataBlob),
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(_DataBlob),
        ]
        function.restype = ctypes.c_int
        ok = function(ctypes.byref(input_blob), "Angry Birds ARM64 local signing password", None, None, None, 1, ctypes.byref(output_blob))
    else:
        function = crypt32.CryptUnprotectData
        function.argtypes = [
            ctypes.POINTER(_DataBlob),
            ctypes.c_void_p,
            ctypes.POINTER(_DataBlob),
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(_DataBlob),
        ]
        function.restype = ctypes.c_int
        ok = function(ctypes.byref(input_blob), None, None, None, None, 1, ctypes.byref(output_blob))
    if not ok:
        raise OSError(ctypes.get_last_error(), "Windows DPAPI operation failed")
    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        kernel32.LocalFree.restype = ctypes.c_void_p
        kernel32.LocalFree(output_blob.pbData)


def protect_password(password: str) -> str:
    try:
        return base64.b64encode(_dpapi(password.encode("utf-8"), protect=True)).decode("ascii")
    except OSError as error:
        raise BuilderError(f"Windows could not protect the local signing password with DPAPI: {error}") from error


def unprotect_password(encrypted_file: Path) -> str:
    try:
        encrypted = base64.b64decode(encrypted_file.read_text(encoding="ascii").strip(), validate=True)
        return _dpapi(encrypted, protect=False).decode("utf-8")
    except (OSError, ValueError, UnicodeError) as error:
        raise BuilderError(
            "Could not decrypt the saved signing key password for this Windows account. "
            "Restore the original Windows user profile or choose a new signing key."
        ) from error


def signing_material(root: Path) -> tuple[Path, str, str]:
    signing_dir = root / "signing"
    signing_dir.mkdir(parents=True, exist_ok=True)
    keystore = signing_dir / "angry-birds-arm64-user.jks"
    encrypted_password = signing_dir / "password.dpapi"
    alias = "angry-birds-arm64-user"
    if keystore.exists() != encrypted_password.exists():
        raise BuilderError(
            "The saved signing key and its protected password are out of sync. "
            f"Back up or remove both files together: {signing_dir}"
        )
    if not keystore.exists():
        import secrets

        password = secrets.token_urlsafe(32)
        encrypted = protect_password(password)
        temp_secret = encrypted_password.with_suffix(".tmp")
        temp_secret.write_text(encrypted + "\n", encoding="utf-8")
        try:
            temp_secret.replace(encrypted_password)
        except OSError:
            temp_secret.unlink(missing_ok=True)
            raise
    else:
        password = unprotect_password(encrypted_password)
    return keystore, password, alias


def command_python() -> Path:
    if getattr(sys, "frozen", False):
        bundled = app_root() / "python" / "python.exe"
        if bundled.is_file():
            return bundled
        raise BuilderError("The portable Python runtime is missing from this builder package.")
    return Path(sys.executable)


def run_command(command: list[str], *, env: dict[str, str], progress, cwd: Path | None = None) -> str:
    printable = " ".join(command)
    progress(f"Running: {printable}")
    result = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.stdout:
        progress(result.stdout.rstrip())
    if result.returncode:
        raise BuilderError(f"Command failed with exit code {result.returncode}: {printable}")
    return result.stdout


def build_once(
    apk_path: Path,
    output_apk: Path | None = None,
    *,
    android_sdk: str | None = None,
    support: str | None = None,
    runtime: str | None = None,
    signing_root: str | None = None,
    progress=lambda _message: None,
) -> tuple[Path, str]:
    apk_path = apk_path.expanduser().resolve()
    support = support_root(support)
    runtime = runtime_library(runtime)
    validate_runtime_library(runtime)
    build_script = support / "build.py"
    if not build_script.is_file():
        raise BuilderError(f"Builder support files are missing: {build_script}")

    try:
        sdk = find_sdk(android_sdk)
    except Exception as error:
        raise BuilderError(
            "Android SDK was not found. Install Android SDK Platform 35 and "
            f"Build Tools {BUILDER_BUILD_TOOLS_VERSION} from the official SDK Manager, then retry.\n{error}"
        ) from error
    sys.path.insert(0, str(support))
    import build as build_system

    try:
        tools = build_system.discover_android_packaging_tools(
            sdk,
            build_tools_version=BUILDER_BUILD_TOOLS_VERSION,
            platform_api=BUILDER_PLATFORM_API,
        )
    except Exception as error:
        raise BuilderError(
            "This preview requires Android SDK Platform 35 and Build Tools "
            f"{BUILDER_BUILD_TOOLS_VERSION}. Install them using Android Studio's SDK Manager.\n{error}"
        ) from error
    java = shutil.which("java")
    java_home = os.environ.get("JAVA_HOME")
    java_executable: Path | None = Path(java).resolve() if java else None
    if java:
        java_home = str(Path(java).resolve().parent.parent)
    elif java_home:
        candidate = Path(java_home) / "bin" / "java.exe"
        if candidate.is_file():
            java_executable = candidate
        else:
            java_home = None
    if not java_home:
        raise BuilderError(
            f"Java 17 or newer was not found. Install a JDK from {JAVA_URL}, then retry."
        )
    version_result = subprocess.run(
        [str(java_executable or (Path(java_home) / "bin" / "java.exe")), "-version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    version_match = re.search(r'version "([0-9]+)', version_result.stdout)
    if version_result.returncode != 0 or not version_match or int(version_match.group(1)) < 17:
        found_version = version_match.group(1) if version_match else "unknown"
        raise BuilderError(
            f"Java 17 or newer is required; found Java {found_version}. Install a JDK from {JAVA_URL}."
        )
    aapt = tools["aapt"]
    apksigner = tools["apksigner"]
    env = os.environ.copy()
    env["ANDROID_SDK_ROOT"] = str(sdk)
    env["ANDROID_HOME"] = str(sdk)
    env["JAVA_HOME"] = java_home
    env["PATH"] = str(Path(java_home) / "bin") + os.pathsep + env.get("PATH", "")

    progress("Checking the selected APK...")
    validate_original_hash(apk_path)
    badging = run_command(build_system.external_command(aapt, "dump", "badging", str(apk_path)), env=env, progress=progress)
    details = validate_original_apk(apk_path, badging)
    run_command(build_system.external_command(apksigner, "verify", "--verbose", str(apk_path)), env=env, progress=progress)
    progress(
        f"Validated Angry Birds {details['version_name']} ({details['version_code']}), "
        f"SHA-256 {details['sha256']}. Original APK contains ARM32 libraries only."
    )

    final_output = output_apk.expanduser().resolve() if output_apk else output_path_for(apk_path)
    probe_output_writable(final_output)
    root = Path(signing_root).expanduser().resolve() if signing_root else local_data_root()
    root.mkdir(parents=True, exist_ok=True)
    keystore, password, alias = signing_material(root)
    work_base = root / "work"
    work_base.mkdir(parents=True, exist_ok=True)

    try:
        with tempfile.TemporaryDirectory(prefix="run-", dir=work_base) as temporary:
            temporary_root = Path(temporary)
            original_root = temporary_root / "original"
            build_root = temporary_root / "build"
            password_file = temporary_root / "signing-password.txt"
            password_file.write_text(password + "\n", encoding="utf-8")
            try:
                extracted_count = extract_original_assets(apk_path, original_root)
                launcher_icon = extract_launcher_icon(apk_path, original_root / "launcher-icon.png")
                progress(f"Extracted {extracted_count} local game resource files.")
                python = command_python()
                run_command(
                    [str(python), str(build_script), "stage", "--original-root", str(original_root), "--build-root", str(build_root)],
                    env=env,
                    progress=progress,
                    cwd=support,
                )
                run_command(
                    [
                        str(python),
                        str(build_script),
                        "package",
                        "--android-sdk",
                        str(sdk),
                        "--build-tools-version",
                        BUILDER_BUILD_TOOLS_VERSION,
                        "--platform-api",
                        str(BUILDER_PLATFORM_API),
                        "--build-root",
                        str(build_root),
                        "--original-root",
                        str(original_root),
                        "--launcher-icon",
                        str(launcher_icon),
                        "--native-library",
                        str(runtime),
                        "--keystore",
                        str(keystore),
                        "--keystore-alias",
                        alias,
                        "--keystore-password-file",
                        str(password_file),
                        "--output-apk",
                        str(final_output),
                    ],
                    env=env,
                    progress=progress,
                    cwd=support,
                )
            finally:
                password_file.unlink(missing_ok=True)

        final_badging = run_command(build_system.external_command(aapt, "dump", "badging", str(final_output)), env=env, progress=progress)
        if "package: name='dev.angryarm64.stage24'" not in final_badging:
            raise BuilderError("The output package name did not match the ARM64 port.")
        run_command(build_system.external_command(apksigner, "verify", "--verbose", "--print-certs", str(final_output)), env=env, progress=progress)
    except Exception:
        final_output.unlink(missing_ok=True)
        raise
    import hashlib

    digest = hashlib.sha256(final_output.read_bytes()).hexdigest()
    progress(f"Build completed. APK: {final_output}\nSHA-256: {digest}")
    return final_output, digest


def run_gui() -> None:
    root = tk.Tk()
    root.title(APP_NAME)
    root.geometry("760x600")
    root.minsize(700, 560)

    apk_value = tk.StringVar()
    output_value = tk.StringVar()
    status_value = tk.StringVar(value="Select the validated original 1.4.2 APK to begin.")
    messages: queue.Queue[tuple[str, str]] = queue.Queue()

    frame = ttk.Frame(root, padding=18)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text=APP_NAME, font=("Segoe UI", 16, "bold")).pack(anchor="w")
    ttk.Label(
        frame,
        text=(
            "Build an ARM64 APK locally. The selected APK and game assets stay on this computer. "
            "Only the validated Angry Birds Classic 1.4.2 (142) APK is supported."
        ),
        wraplength=700,
    ).pack(anchor="w", pady=(8, 16))

    row = ttk.Frame(frame)
    row.pack(fill="x")
    entry = ttk.Entry(row, textvariable=apk_value)
    entry.pack(side="left", fill="x", expand=True)

    def choose_apk() -> None:
        selected = filedialog.askopenfilename(
            title="Select original Angry Birds 1.4.2 APK",
            filetypes=[("Android package", "*.apk"), ("All files", "*.*")],
        )
        if selected:
            apk_value.set(selected)
            output_value.set(str(output_path_for(Path(selected))))

    ttk.Button(row, text="Browse…", command=choose_apk).pack(side="left", padx=(8, 0))

    output_row = ttk.Frame(frame)
    output_row.pack(fill="x", pady=(8, 0))
    ttk.Label(output_row, text="Save APK:").pack(side="left", padx=(0, 8))
    ttk.Entry(output_row, textvariable=output_value).pack(side="left", fill="x", expand=True)

    def choose_output() -> None:
        selected = filedialog.asksaveasfilename(
            title="Choose a new output APK path",
            defaultextension=".apk",
            initialfile="angry-birds-classic-1.4.2-arm64.apk",
            filetypes=[("Android package", "*.apk")],
        )
        if selected:
            output_value.set(selected)

    ttk.Button(output_row, text="Save as…", command=choose_output).pack(side="left", padx=(8, 0))
    progress = ttk.Progressbar(frame, mode="indeterminate")
    ttk.Label(frame, textvariable=status_value).pack(anchor="w")
    log = tk.Text(frame, height=11, wrap="word", state="disabled", font=("Consolas", 9))
    log.pack(fill="both", expand=True, pady=(8, 12))

    button = ttk.Button(frame, text="Build ARM64 APK")
    button.pack(anchor="e")

    def append(message: str) -> None:
        log.configure(state="normal")
        log.insert("end", message + "\n")
        log.see("end")
        log.configure(state="disabled")

    def check_messages() -> None:
        try:
            while True:
                kind, message = messages.get_nowait()
                if kind == "progress":
                    append(message)
                    status_value.set(message.splitlines()[0][:140])
                elif kind == "done":
                    progress.stop()
                    progress.pack_forget()
                    button.configure(state="normal")
                    output, digest = message.split("\n", 1)
                    status_value.set("Build finished and verified.")
                    messagebox.showinfo(APP_NAME, f"{output}\n\n{digest}")
                elif kind == "error":
                    progress.stop()
                    progress.pack_forget()
                    button.configure(state="normal")
                    status_value.set("Build failed. See the details below.")
                    messagebox.showerror(APP_NAME, message)
        except queue.Empty:
            pass
        root.after(150, check_messages)

    def start_build() -> None:
        selected = Path(apk_value.get().strip())
        if not selected.is_file():
            messagebox.showerror(APP_NAME, "Choose an existing APK file first.")
            return
        button.configure(state="disabled")
        progress.pack(fill="x", pady=(14, 8))
        progress.start(12)
        status_value.set("Preparing the local build…")
        append("--- New build ---")

        def worker() -> None:
            try:
                def report_progress(text: str) -> None:
                    append_app_log(text)
                    messages.put(("progress", text))

                output, digest = build_once(selected, Path(output_value.get()) if output_value.get().strip() else None, progress=report_progress)
                append_app_log(f"SUCCESS APK: {output}; SHA-256: {digest}")
                messages.put(("done", f"APK: {output}\nSHA-256: {digest}"))
            except Exception as error:  # Display unexpected runtime and dependency errors to the user.
                details = f"{error}\n\n{traceback.format_exc(limit=4)}"
                append_app_log(f"FAILURE: {details}")
                messages.put(("error", details))

        threading.Thread(target=worker, daemon=True).start()

    button.configure(command=start_build)
    check_messages()
    root.mainloop()


def main() -> int:
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument("--build", action="store_true", help="Run the full build without opening the GUI.")
    parser.add_argument("--apk", help="Original APK path for headless validation/build.")
    parser.add_argument("--output", help="New output APK path (must not already exist).")
    parser.add_argument("--android-sdk", help="Android SDK root.")
    parser.add_argument("--support-root", help="Builder support source directory.")
    parser.add_argument("--runtime-library", help="Prebuilt ARM64 runtime library.")
    parser.add_argument("--signing-root", help="User-local signing key storage directory.")
    args = parser.parse_args()
    if args.build:
        if not args.apk:
            parser.error("--apk is required with --build")
        try:
            def report_progress(message: str) -> None:
                if sys.stdout is not None:
                    print(message)
                else:
                    append_app_log(message)

            output, digest = build_once(
                Path(args.apk),
                Path(args.output) if args.output else None,
                android_sdk=args.android_sdk,
                support=args.support_root,
                runtime=args.runtime_library,
                signing_root=args.signing_root,
                progress=report_progress,
            )
            if sys.stdout is not None:
                print(f"APK: {output}\nSHA-256: {digest}")
            else:
                append_app_log(f"SUCCESS APK: {output}; SHA-256: {digest}")
            return 0
        except Exception as error:
            if sys.stderr is not None:
                print(f"Builder error: {error}\n{traceback.format_exc(limit=6)}", file=sys.stderr)
            else:
                append_app_log(f"FAILURE: {error}\n{traceback.format_exc(limit=6)}")
                try:
                    messagebox.showerror(APP_NAME, f"Build failed: {error}\n\nSee the log at %LOCALAPPDATA%\\AngryBirdsARM64\\logs\\builder.log")
                except tk.TclError:
                    pass
            return 1
    run_gui()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
