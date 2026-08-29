# Stage 6 static analysis — original Angry Birds 1.4.2 Level1

The uploaded `assets\data` bundle contains 566 files / 28,249,319 bytes:

- 216 Lua chunks
- 168 WAV files
- 83 DAT files
- 62 PVR textures
- 18 MP3 files
- 11 PNG files
- 8 ZIP files

There are 210 level Lua chunks across 12 level folders.

## Level1.lua

`levels/pack1/Level1.lua` is 2,911 bytes and is a stripped Lua 5.1 float32
bytecode chunk with 261 instructions and no nested prototypes. It is a pure data
chunk: it builds and exports:

- `world`
- `counts`
- `castleCameraData`
- `physicsToWorld`
- `joints`
- `theme`
- `birdCameraData`

The `world` table contains 21 entries: 20 game objects plus the saved ground.

Definition counts:

- WoodBlock6: 5
- WoodBlock2: 4
- RedBird: 3
- WoodBlock4: 3
- Estrade02: 2
- LightBlock4: 2
- SmallPiglette: 1
- Ground: 1

So the physical body mix expected from this level is:

- 17 boxes including the generated ground
- 4 circles
- 21 bodies total
- 18 dynamic bodies
- 3 static bodies (2 Estrade platforms + ground)

## Original sprite bounds

The original 864x480 KA3D `SPRT` chunks decode cleanly:

- `INGAME_BLOCKS_1.dat`: 202 sprites
- `INGAME_BIRDS_1.dat`: 158 sprites
- combined: 360 sprites

Relevant raw pixel bounds:

- `BLOCK_WOOD_1_2`: 41 x 20
- `BLOCK_WOOD_1_4`: 83 x 20
- `BLOCK_WOOD_1_6`: 168 x 20
- `BLOCK_LIGHT_1_4`: 83 x 20
- `ESTRADE_02`: 179 x 56
- `BIRD_RED`: 46 x 45
- `PIGLETTE_SMALL_01`: 48 x 46

The original Lua `createObject()` uses `res.getSpriteBounds()` and multiplies
those dimensions by `physicsScale`. For movable boxes it also applies the
0.92 collision-size factor visible in the original bytecode.

## Strong reconstruction cross-check

Using the exact Level1 positions, original sprite widths, `physicsScale = 0.05`,
and the original load-level edge calculation gives:

- derived left edge:  -13.1000000238
- derived right edge:  54.9076988220
- derived ground X:    20.9038493991
- Level1 file ground X:20.9039001465
- absolute delta:      0.0000507474

That ~5e-5 difference is only float32/rounding scale. It is strong evidence that
the recovered sprite-bounds + createObject + level-edge path matches the original
engine semantics.

## Stage 6 boundary

Stage 6 deliberately does **not** call the entire original `loadLevelInternal()`
yet because that function also initializes menu, settings, camera, achievements,
audio, and save-state systems.

Instead it executes:

1. the original six core Lua chunks;
2. the original `initialize()`;
3. the original `Level1.lua`;
4. the original `gamelogic.createObject()` for every non-ground Level1 object;
5. the recovered native GameLua physics functions;
6. real Box2D 2.1.2 body creation;
7. the exact ground/edge materialization core reconstructed from
   `loadLevelInternal()`;
8. 120 real Box2D simulation steps.

This isolates the real level/physics path from unrelated UI systems while still
using the original Level1 data and original createObject logic.
