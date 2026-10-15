# Windows Builder Preview

This preview creates a locally signed ARM64 APK from one supported input:
the original Angry Birds Classic Android 1.4.2 (version code 142) APK.

## Before you start

- Use a 64-bit Windows PC.
- Obtain the original APK yourself. The builder checks its package, version,
  ARM32 libraries, and SHA-256 before extracting anything.
- This preview accepts only SHA-256
  `2524167c113d967c5efd40640387482201a14c06124f70f2d1700fff1839d5ed`.
- Install a Java 17 or newer JDK.
- Install Android SDK Platform 35 and Android SDK Build Tools 35.0.0 with the
  official Android Studio SDK Manager, then accept Google's Android SDK terms.
- Keep an internet connection available only if you need to install those
  developer tools. The build itself does not upload the APK or game data.

The builder includes the project's prebuilt ARM64 runtime, so Python and the
Android NDK are not required. The Windows package contains a portable Python
runtime used internally by the existing staging and packaging scripts.

## Build your APK

1. Download and extract
   [`AngryBirds-ARM64-Builder-Preview.zip`](https://github.com/WhiteMsf/angry-birds-arm64/releases/download/builder-preview-v0.1.1/AngryBirds-ARM64-Builder-Preview.zip)
   from the [0.1.1 preview release](https://github.com/WhiteMsf/angry-birds-arm64/releases/tag/builder-preview-v0.1.1).
2. Verify the ZIP with the adjacent `.sha256` file.
3. Run `AngryBirdsArm64Builder.exe`. The executable is unsigned, so Windows may
   show a publisher warning; check the release checksum before opening it.
4. Select your original 1.4.2 APK, choose a new output path, and select
   **Build ARM64 APK**.
5. Copy the resulting APK to an ARM64 Android device, open it in the device's
   file manager, and confirm installation. Android may ask you to allow app
   installs from that file manager.

The resulting app uses package `dev.angryarm64.stage24` and contains only
`arm64-v8a` native code. Its signature is unique to your Windows user. If
Android refuses to update another copy because the signing certificates differ,
uninstall that older build first; uninstalling can remove its app data.

The builder keeps temporary extracted resources under your local application
data folder and removes the per-run workspace when the build ends. It never
changes the original APK. The default output folder is Downloads. Existing
output files are never replaced.

## Signing key

The first successful build creates a per-user signing key under
`%LOCALAPPDATA%\AngryBirdsARM64\signing`. The private key stays on this PC.
The password is protected with Windows DPAPI for the current Windows user, so
future builds by that account keep the same APK signing identity. Back up the
`.jks` file securely. The protected password file can only be decrypted by the
same Windows account on the same Windows installation; reinstalling Windows or
moving to another account will require a new key and uninstalling the previous
builder APK before installing the newly signed one.

This is a preview, not a supported production release. The generated app is a
debuggable experimental port. It is not affiliated with Rovio. Do not share
the original APK, extracted game data, or the private signing key.

The packaged conversion pipeline and main window passed review on Windows.
The 0.1.1 release fixes a clipped build button and hides the progress bar until
a build starts. The file-picker dialog was not visually exercised here.

## Troubleshooting

- **Original APK rejected:** this preview accepts only the locally validated
  1.4.2 (142) file. Check the SHA-256 shown in the error.
- **SDK or Java missing:** install JDK 17+, Android SDK Platform 35, and Build
  Tools 35.0.0 using the official tools linked from
  <https://developer.android.com/tools>.
- **Output path denied:** choose a folder where your Windows account can create
  files, such as Documents or Downloads.
- **Build failed:** copy the error text from the builder window when reporting
  the problem. Logs contain paths but not the game resources themselves.

For known issues and contributor instructions, see the repository README and
`docs/windows-builder/DEVELOPERS.md`.
