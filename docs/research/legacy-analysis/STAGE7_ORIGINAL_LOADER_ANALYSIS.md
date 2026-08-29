# Stage 7 — exact bytecode boundary

`loadLevelInternal()` in the original stripped `gamelogic.lua` is a 941
instruction Lua 5.1 function.

Static bytecode analysis shows the decisive loader sequence at PCs 259–263:

```text
GETGLOBAL loadLevel
MOVE      <function argument>
CALL
GETGLOBAL filterLoadedLevel
CALL
```

The object materialization loop then starts at PC 351 and calls the original
`createObject()` at PC 361. Ground creation is at PC 479. Joint creation is at
PC 523. The function later builds the bird list, level-goal list, damage sprite
state, slingshot start position, background color and camera state before
clearing `loadedObjects` and returning.

Stage 7 reconstructs the native `loadLevel(String)` boundary instead of
transcribing that Lua code.

## Reconstructed `loadLevel(String)`

The level chunk runs inside a private Lua environment table. Writes such as
`world = {...}`, `theme = ...`, `joints = {...}` therefore become fields of that
table, while an `__index = _G` metatable lets the level read normal game globals.

After the chunk returns, that environment is assigned to global
`loadedObjects`, exactly matching what `loadLevelInternal()` expects.

Everything after that point is the original 941-instruction Lua function.

## Headless stubs

Only unrelated platform/render/menu services are suppressed:

- releaseCutScenes
- prepareMenuPage
- setAnimationState
- setTheme
- setWorldScale
- setBGColor
- initCameras
- achievements
- setSprite / audio

Physics, level loading, filtering, createObject, getNextBird, scoring setup and
the Level1 object graph remain in the original control flow.

`setObjectParameter(selector=2)` now also implements the ARMv7-recovered Box2D
body-type behavior: value 0 -> static, nonzero -> dynamic.
