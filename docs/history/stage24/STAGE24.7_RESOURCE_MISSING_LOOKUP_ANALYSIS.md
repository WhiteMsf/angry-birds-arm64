# Stage 24.7 — original ARMv7 missing resource lookup semantics

Static evidence from the original ARMv7 `libangrybirds.so`:

- `LuaResources::getSpriteBounds` converts Lua args 1 and 2 to strings, invokes
  `Resources::getSpriteWidth` and `Resources::getSpriteHeight`, converts their
  integer results to floats, pushes both, and returns 2.
- `Resources::getSpriteHeight`: if the named sheet/sprite lookup resolves to
  null, returns `r0 = 0`.
- `Resources::getSpriteWidth`: same null branch, returns `r0 = 0`.
- `Resources::getSpritePivotX/Y`: same null behavior, returns `r0 = 0`.

This makes missing resources a non-exceptional numeric-zero result at this API
boundary. It specifically explains why `SETTINGS_BG` can exist only as a Lua
literal in the extracted asset tree without having a SPRT metadata owner.
