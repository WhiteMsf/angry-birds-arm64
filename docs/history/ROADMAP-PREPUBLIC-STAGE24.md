### Stage 24.10 / v0.26.13 — original `loadLuaFile(..., tableName)` starTable namespace
- v0.26.12 proved `loadFonts()` and exact `res.useFont(FONT_BASIC)` reach the post-level result path.
- ARMv7 `GameLua::loadLuaFile` non-empty-name branch creates a fresh LuaTable, executes the chunk with that table as function environment, then installs it under the requested name.
- `starLimits.lua` is now loaded into `starTable` with those semantics instead of being executed directly in `_G`; result rendering remains intentionally headless.


### Stage 24.9 / v0.26.12 — original font bootstrap boundary
- v0.26.11 proved original `initializeMenu()` PASS (36 levelComplete / 24 levelFailed items) and reached post-level `setFont(fontBasic)`.
- Recovered ARMv7 `res.useFont` non-throwing lookup/default semantics.
- Replay untouched `loadFonts()` slice with locally staged 480x320 original font DATs; visual glyph rendering remains deferred.

- Stage 24.12: original prepareMenuPage restored; bitmap-font metrics/clipText bridge added; awaiting live result-mode validation.
