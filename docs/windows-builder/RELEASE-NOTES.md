# ARM64 Builder Preview 0.1.1

This preview packages a Windows GUI and a prebuilt ARM64 runtime for generating
a local APK from the original Angry Birds Classic Android 1.4.2 (142) APK.

## Included

- Windows GUI executable and portable Python runtime.
- ARM64 runtime built from this repository.
- Existing asset staging, APK packaging, signing, and audit scripts.
- A ZIP checksum and a manifest with hashes for the executable, runtime, and
  Python embeddable archive.

## Changes since 0.1.0

- Enlarged the initial window so the Build button remains visible.
- Show the progress bar only while a build is running.
- Visually reviewed the packaged main window on Windows; the file-picker
  dialog still needs manual interaction testing.

## Requirements and limits

- 64-bit Windows.
- Java 17+ JDK.
- Android SDK Platform 35 and Build Tools 35.0.0, with Google SDK terms
  accepted by the user.
- The single validated original APK hash documented by the builder. No other
  game version is supported by this preview.
- The executable is not code-signed; Windows may display a publisher warning.
- The packaged conversion pipeline and main window passed review on Windows.
- APK creation is local. The builder does not transmit the original APK or
  extracted resources.
- The APK is an experimental, debuggable reconstruction, not affiliated with
  Rovio. The tool package does not include a complete Angry Birds APK or game
  assets.

The signing key is stored on the user's PC and protected for the current
Windows account. Keep a secure backup if future APK updates must retain the
same signing identity.
