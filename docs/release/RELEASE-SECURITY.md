# Release signing security

The 1.0 release key is not part of this repository or source archive.

Private path used by the local release script:

`%USERPROFILE%\.angry-arm64\signing\angry-birds-release.p12`

Rules:

1. Back up the `.p12` offline in at least two secure places.
2. Do not commit it to Git or place it in a public/cloud-shared release folder.
3. Do not publish the password.
4. `SIGNING-CERTIFICATE.pem` and the certificate fingerprints are public and are intentionally placed in `dist/1.0.0/release/`.
5. Reuse the same release key for signature-compatible direct APK updates.
6. If a future store uses its own app-signing service, treat store upload/app-signing key setup as a separate publication step; do not rotate the local direct-distribution key casually.
