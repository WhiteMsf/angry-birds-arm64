# Windows Builder: developer notes

The GUI in `tools/windows_builder.py` is a thin Windows front end over the
canonical `build.py stage` and `build.py package` pipeline. It accepts only the
validated 1.4.2 APK hash, checks the original metadata and ARM32-only payload,
extracts `assets/data` into a private temporary workspace, stages resources,
packages the supplied AArch64 library, signs with a per-user key, then verifies
the APK metadata, signature, and ABI payload.

The native library is built in CI and distributed as a builder component. This
avoids requiring users to install the NDK or compile C++. Android Build Tools
35.0.0, SDK Platform 35, and Java 17+ remain required for packaging and
signing. The builder currently detects these installed dependencies; it does
not download or silently accept their licenses.

## Local checks

Run the offline builder contract checks:

```powershell
python tools/test_windows_builder_core.py -v
python -m py_compile build.py tools/windows_builder.py tools/windows_builder_core.py
```

Run the real end-to-end path with a validated local APK and an ARM64 runtime:

```powershell
python tools/windows_builder.py --build `
  --apk "C:\path with spaces\original.apk" `
  --output "C:\path with spaces\output.apk" `
  --android-sdk "$env:LOCALAPPDATA\Android\Sdk" `
  --support-root "$PWD" `
  --runtime-library "$PWD\build\android-arm64\libangryarm64.so"
```

The original APK and resulting game assets must remain outside Git. Use a
throwaway signing directory for tests that exercise signing failures.

## Package a Windows preview

On 64-bit Windows, install the pinned PyInstaller build in a temporary virtual
environment, then package the CI-built native library:

```powershell
python -m pip install pyinstaller==6.22.3
python tools/package_windows_builder.py `
  --native-library "build\android-arm64\libangryarm64.so" `
  --output "dist\windows-builder-preview"
```

The packager obtains the official Python 3.14.8 embeddable ZIP from python.org
and verifies its published SHA-256 before including it. The package contains
only the builder executable, Python runtime, project build scripts, notices,
and the ARM64 runtime. It rejects APKs and files with proprietary game resource
extensions. The manifest records hashes for the builder executable, runtime,
and Python archive. The package ZIP has an adjacent `.sha256` checksum file.

Do not publish a complete game APK or original game resources in a GitHub
release. A release should contain only the tool package, its checksum, and
documentation. Do not claim a one-click setup while Java/Android SDK
installation remains manual.
