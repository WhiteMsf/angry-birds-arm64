# Stage 14 — controlled active-RedBird contact corpus

Stage 13 closes the ordinary block lifecycle:

`collision -> damage -> deadBlocks -> original removeBlocks() -> removeObject()
-> DestroyBody -> score/table cleanup`.

The next major gameplay branch is the special/bird side of
`GameLua::BeginContact`.

## Static ARMv7 facts already recovered

`RenderObjectData + 0x87` is tested for both colliders before the ordinary
block/block branch.

- both flags zero -> the block damage path recovered in Stages 9–13
- one or both flags nonzero -> special/bird path

The two-special-object sub-path at `0x56988` is relatively simple:

```text
choose the faster body
forceLike = body.mass * |body.velocity| / 1.75
call unnamed helper 0x4F3A4(nameA, nameB, forceLike, 0)
```

The helper's call shape strongly matches the original Lua
`birdCollision(nameA, nameB, collisionForce, damageMetric)` boundary, but the
symbol/name has not yet been proven.

The exactly-one-special-object path is more complicated. It reads multiple
data-driven Lua tables/numbers/booleans before calling the same helper. That
is the path a normal bird hitting a block should use, and it should not be
guessed from the block formula.

## Stage 14 goal

Create one deterministic real Box2D contact involving the already-active
`RedBird_4` while keeping all collision damage mutation disabled.

At native fixed-step frame 67:

1. read the *current* `WoodBlock2_6` body position;
2. place RedBird_4 just to its left with a small positive gap;
3. give RedBird_4 +8 world-units/s horizontal velocity;
4. run the normal `b2World::Step(1/30,10,10)`;
5. collect the resulting contact corpus;
6. classify the contact using the original Lua `controllable` state.

This is intentionally not a sling reconstruction and does not call
`birdCollision()` with guessed parameters. It is the bird-branch equivalent
of Stage 9: establish a runtime corpus first, then map the ARMv7 branch exactly.

The existing ordinary block momentum metric is logged only as diagnostic
telemetry for the contact. It is explicitly *not* claimed to be the native
one-bird collision scalar.
