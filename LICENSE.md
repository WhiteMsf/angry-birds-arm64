# License and scope

The top-level [`LICENSE`](LICENSE) contains the MIT License, with the copyright
notice `Copyright (c) 2026 WhiteMsf`. It applies only to original project work
that WhiteMsf is entitled to license. It does not place every file in this
repository under one license.

## Included project work

Subject to the exclusions below, the MIT grant covers project-authored runtime
and Android integration source, build and packaging scripts, CI configuration,
developer tools, tests, and non-historical project documentation. This includes
independently written implementations informed by behavioral observation and
reverse engineering. The license does not assert that the work was developed
in a "clean room" or that no third-party rights are involved.

The MIT grant does not cover third-party code merely because project patches,
build scripts, or compatibility tooling operate on it. Where code or a portion
of a file is copied or adapted from a third-party source, the applicable
third-party terms continue to govern that material.

## Excluded material

The following are outside the MIT grant:

- `vendor/**`, including Lua 5.1.5 and the altered Box2D 2.1.2 source. Their
  upstream licenses and notices remain authoritative.
- `recon/**`, `docs/history/**`, and `docs/research/**`. These preserve
  historical experiments, research, reverse-engineering records, and material
  whose provenance or licensing has not been individually established. Their
  presence is not a grant of rights in any third-party-derived excerpts or
  other source material.
- `docs/media/*.gif`, which are illustrative gameplay captures and may show
  original game artwork and other protected content.
- Any original Angry Birds source code, Lua bytecode, APK material, game data,
  artwork, animation, audio, text, or other content supplied locally by a
  user or otherwise belonging to Rovio Entertainment or another rights holder.
- Names, logos, trademarks, and other branding of Rovio, Angry Birds, OpenAI,
  or other parties.
- Any other third-party material or file carrying its own copyright, license,
  or attribution notice.

No rights to the excluded materials are granted by the top-level `LICENSE`.
See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and
[`CREDITS.md`](CREDITS.md) for additional provenance and attribution
information.
