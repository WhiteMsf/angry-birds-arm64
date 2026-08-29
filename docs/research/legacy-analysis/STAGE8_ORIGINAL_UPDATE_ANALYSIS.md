# Stage 8 — original per-frame Lua loop

Static analysis of the original stripped `gamelogic.lua` identifies:

- `update` = root prototype 11
- parameters = 2
- instructions = 596
- `updateGame` = root prototype 136
- parameters = 2
- instructions = 3,955

The outer `update` uses parameter 1 (`R0`) to advance game time and calls:

`currentGameMode(R0, time)`

It uses parameter 2 (`R1`) for the FPS timer. Stage 8 therefore invokes:

`update(1/60, 1/60)`

for 120 frames.

## Native frame responsibility reconstructed in Stage 8

The original native GameLua layer owns the Box2D world while the Lua game
logic reads per-object fields such as:

- x / y
- xVel / yVel
- angle
- angularVelocity
- mass
- sleeping

Stage 8 mirrors those values from each real Box2D body back into the
corresponding `objects.world[name]` table each frame.

It also derives the native-side `hasMovingObjects` flag from real dynamic-body
velocity, which is consumed by the original `checkLevelComplete()` and
`checkLevelFailed()` functions.

The loop is:

1. physics -> Lua state sync
2. original `update(dt, frameTime)`
3. original `update` calls original `updateGame(dt, time)`
4. real Box2D `Step(1/60)`
5. physics -> Lua state sync

## Still deliberately headless

Rendering, audio output, ads, platform achievements and camera rendering are
no-ops. No collision/damage callbacks are synthesized yet; those are Stage 9.

Gameplay functions left original include the outer `update`, `updateGame`,
`animateBirdToSlingShot`, `updateCharacterAnimations`, `updateFloatingScores`,
`updateScore`, level-completion checks, bird queue logic and input state logic.
