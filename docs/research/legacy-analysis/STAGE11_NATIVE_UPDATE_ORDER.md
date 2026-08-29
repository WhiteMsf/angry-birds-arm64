# Stage 11 — ARMv7 native frame-driver order

Stage 10 remains a valid semantic bridge proof: the recovered ARMv7
non-destructive `strength` / `defence` rule mutated original Lua object state,
the original `blockCollision()` ran, and the original `getDamageSprite()`
advanced SmallPiglette from `PIGLETTE_SMALL_01` to `PIGLETTE_SMALL_02`.

A later static pass over the unstripped ARMv7 `GameLua::update(float)` shows
that the Stage 8–10 compatibility frame driver did not yet match native
scheduling: it stepped Box2D at 60 Hz after Lua `update()`.

## Recovered ARMv7 core order

Relevant addresses:

```text
0x55218  load physics accumulator (+0x1AC)
0x55220  accumulator += frame dt

0x55238  load fixed timestep literal
          literal @ 0x554E4 = 0.033333335 (1/30)

0x55250  velocity iterations = 10
0x55260  position iterations = 10
0x55264  b2World::Step(1/30, 10, 10)

0x55268  accumulator -= 1/30
0x5527C  LuaObject::call(...)      // static match: removeBlocks

... fixed-step / body-history loop ...

0x553AC  b2World::ClearForces()

... transform history/interpolation and native work ...

0x55768  push Lua member           // static match: update
0x55770  push frame dt
0x5577C  push frame dt
0x55790  LuaState::call(2, 0)
```

## Stage 11 driver

At a 60 Hz outer cadence:

```text
if physics was enabled at frame start:
    accumulator += 1/60

    while accumulator >= 1/30:
        Box2D Step(1/30, 10, 10)
        accumulator -= 1/30
        original removeBlocks()

    ClearForces()

direct physics -> Lua object sync
original update(1/60, 1/60)
```

Damage mutation is disabled in this pass so `deadBlocks` cannot contaminate
the timing experiment.

## Strong transition prediction

The original Lua `updateGame()` enables physics during Lua frame 61.

Because native physics runs before that Lua call:

- frame 61: zero physics steps; Lua enables physics at frame end
- frame 62: accumulator = 1/60; zero physics steps
- frame 63: accumulator reaches 1/30; first fixed Box2D step

Across frames 62–120, Stage 11 should execute exactly 29 fixed steps and finish
with one 1/60 accumulator remainder.

## Remaining approximation

The original native function maintains RenderObjectData transform history and
interpolates between physics states before publishing them to Lua/rendering.
Stage 11 still uses direct reconstructed physics->Lua synchronization.
Input packaging, rendering, audio and several platform services remain
headless.

So this stage reconstructs the core physics/Lua scheduling order, not every
instruction of native `GameLua::update(float)`.
