# In-game ARM64 Reconstruction Credits

This document defines the public credit copy and the intended presentation inside the game. It is deliberately separate from the original Rovio About/Credits screen.

## Placement

Do **not** replace or rewrite the original About/Credits page.

The public ARM64 build should add a clearly separate entry from the original About/Credits screen:

**ARM64 RECONSTRUCTION**

Selecting it opens an additional project-owned credit panel. Returning from that panel restores the untouched original About/Credits page.

## Recommended on-screen copy

### Page 1 — project credit

**ARM64 RECONSTRUCTION**

Independent preservation & compatibility project

Project lead / technical direction
`<PROJECT_MAINTAINER>`

Testing & device validation
`<PROJECT_MAINTAINER>`

AI-assisted engineering, reconstruction,
analysis, debugging & documentation
**ChatGPT by OpenAI**

**NEXT**    **BACK**

### Page 2 — what was reconstructed

**WHAT WE RECONSTRUCTED**

ARM64 Android runtime
Native / Lua compatibility
Rendering & menu integration
Input & Android lifecycle
Physics compatibility
Audio, saves & progression bridges
Build, diagnostics & release tooling

Behavior was reconstructed from the shipped
legacy game and technical evidence.

**NEXT**    **BACK**

### Page 3 — what remains original

**THE ORIGINAL GAME IS ROVIO'S**

We did not create the original game, levels,
characters, artwork, animation, audio, music,
branding, or other proprietary game content.

This is not original or leaked Rovio source code.
Original proprietary assets are not distributed
as part of the public reconstruction source.

Angry Birds and original game content belong to
Rovio Entertainment / their respective rights holders.

Unofficial project. No Rovio or OpenAI endorsement.

**BACK TO ORIGINAL CREDITS**

## Presentation rules

1. The new panel must visually read as **project-added material**, not as part of Rovio's original credit roll.
2. The original About/Credits page must remain available and unchanged beneath/alongside it.
3. The reconstruction credit should never use Rovio logos or imitate an official legal notice in a way that could imply endorsement.
4. The project-maintainer field must be replaced with the chosen public name/handle before a public release.
5. The ChatGPT/OpenAI credit should remain descriptive: it acknowledges AI-assisted engineering and documentation, not co-ownership or endorsement.
6. The full legal/technical attribution lives in `CREDITS.md`; the in-game screen is intentionally concise.

## Implementation boundary

The preferred implementation is a **presentation-only overlay owned by the ARM64 reconstruction layer** and reachable from `page == "about"`.

It should not patch the builder's original `gamelogic.lua` or alter the original proprietary About/Credits content. The overlay should consume its own touches while open, render using the already reconstructed menu/font path, and return cleanly to the original About page.

This creates an explicit technical boundary:

- original About/Credits: original game ownership;
- ARM64 Reconstruction panel: project ownership;
- gameplay/Lua behavior: unaffected by the credit overlay.
