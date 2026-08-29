# Stage 3 rationale

Static decoding of the six original Lua 5.1 chunks shows:

- `animations.lua`: no external globals are read by the root prototype.
- `blocks.lua`: no external globals are read by the root prototype.
- `loadlist.lua`: no external globals are read by the root prototype.
- `particles.lua`: no external globals are read by the root prototype.
- `starLimits.lua`: no external globals are read by the root prototype.
- `gamelogic.lua`: the root prototype externally reads only `screenWidth` (twice).

`gamelogic.lua` also performs six top-level method calls while constructing the
Page/Item class hierarchy. The Page/Item constructors use `_G.setmetatable`, so
Stage 3 opens only Lua's base/table/string/math libraries and seeds:

- `screenWidth = 480`
- `screenHeight = 320`
- `deviceModel = "android-arm64-bootstrap"`

The test then executes all six original chunks with `lua_pcall` and verifies:

- `releaseBuild == true`
- `tapRadius == 15`
- `initialize` is a function
- `update` is a function
- `Page`, `Item`, `SpriteItem`, `TextItem` are tables

This is intentionally before GameLua/Box2D/JNI integration: it proves the original
top-level game code itself can run to completion on the patched ARM64 Lua 5.1 VM.
