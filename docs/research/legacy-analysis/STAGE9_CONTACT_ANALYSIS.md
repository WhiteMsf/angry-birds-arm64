# Stage 9 — real Box2D contact-listener boundary

Stage 8 proved the complete 120-frame headless loop:

- original `update(dt, frameTime)`
- original `updateGame(dt, time)`
- original one-second level-start gate
- original call to `setPhysicsEnabled(true)`
- real Box2D 2.1.2 stepping
- physics -> Lua object-state synchronization

Stage 9 restores the next native architecture boundary: **GameLua as a
`b2ContactListener`**.

The original ARMv7 binary contains:

- `GameLua::BeginContact(b2Contact*)` — 3316 bytes
- `GameLua::EndContact(b2Contact*)` — 4-byte no-op
- `GameLua::PreSolve(...)` — 4-byte no-op
- inherited/no-op `PostSolve`

## Exact recovered block-branch metric

The ARMv7 `BeginContact` block/block path loads both body masses and linear
velocities, forms the momentum-vector difference, takes its length, and
multiplies by `0.1`:

```text
collisionMetric =
    0.1 * length(massA * velocityA - massB * velocityB)
```

Stage 9 reproduces that scalar for every real `BeginContact`.

It also records Box2D's solver normal impulse in `PostSolve` only as independent
telemetry. This is **not** substituted for the original metric.

## Why collision callbacks are not invoked yet

The native ARMv7 `BeginContact` does more than call Lua:

- it inspects per-object collision class/state;
- computes damage/defence/strength transitions;
- can update object tables before Lua dispatch;
- then reaches the original `birdCollision` / `blockCollision` Lua paths.

Calling those Lua functions prematurely with guessed damage values would make a
false-positive port.

So Stage 9 is deliberately a contact-corpus pass:

1. real Box2D contact occurs;
2. real listener callback fires;
3. object names/masses/velocities are captured;
4. recovered ARMv7 collision metric is calculated;
5. event is classified as the eventual original `birdCollision` or
   `blockCollision` path from the original Lua object's `controllable` flag;
6. gameplay state is not mutated by collision code yet.

The resulting corpus is the input for Stage 10's reconstruction of the actual
damage/strength transition.
