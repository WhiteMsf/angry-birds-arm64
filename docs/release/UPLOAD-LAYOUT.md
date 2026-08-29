# Future upload layout

After `build-angry-birds-1.0.0-release.ps1` succeeds:

## `dist/1.0.0/release/`

Candidate user-facing artifacts. This folder contains no private signing key and no plaintext signing password.

The source archive excludes generated APK/build directories, local saves, keystores/cert-private material and the user's original proprietary asset tree.

The locally-built binary APK does contain original game assets sourced from the user's local extraction. Whether that binary/assets may be publicly redistributed is a rights/licensing question separate from technical release readiness.

## `dist/1.0.0/audit/`

Forensic companion, not the minimal public download set. Keep it for reproducibility and future regressions: audited APK, diagnostics, hash-equivalence proof, ELF/page-size proof, packaging reports and the historical profile backup.

## Private signing storage

Never upload:

`%USERPROFILE%\.angry-arm64\signing\angry-birds-release.p12`
