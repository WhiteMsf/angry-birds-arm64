# Stage 12 — recovered damage on the native-order 30 Hz driver

Stage 10 proved the ARMv7 non-destructive strength/defence rule and original
Lua `blockCollision()` / `getDamageSprite()` behavior.

Stage 11 then corrected the compatibility frame driver:

- Box2D fixed timestep = 1/30
- Step iterations = 10 / 10
- physics before Lua update()
- original removeBlocks() after each fixed Step
- ClearForces() after the fixed-step loop
- first fixed Step at render frame 63 after Lua enables physics at frame 61

Stage 12 combines those two proven pieces.

## Native-order collision path

During `b2World::Step(1/30,10,10)`:

```text
BeginContact
  -> F = 0.1 * |mA*vA - mB*vB|
  -> strength/defence mutation
  -> original blockCollision(nameA,nameB,F,damageFlag)
```

After the Step returns:

```text
original removeBlocks()
```

This is the architecture we wanted before attempting real destruction.

## Corrected Level1 prediction

Stage 11 measured the SmallPiglette contact on the corrected 30 Hz corpus:

```text
WoodBlock2_1 <-> SmallPiglette_7
F ~= 2.5354
```

The original pig data has:

```text
strength = 4
defence  = 1
```

So the recovered native rule predicts:

```text
damage        ~= 2.5354 - 1 = 1.5354
final strength ~= 4 - 1.5354 = 2.4646
```

The pig remains alive and the original Lua damage-sprite path should again
advance:

```text
PIGLETTE_SMALL_01 -> PIGLETTE_SMALL_02
```

No destruction is expected in the passive 120-frame settling corpus. If any
object would reach strength <= 0, Stage 12 stops rather than fabricating the
still-unreconstructed native deadBlocks/removeObject queue.
