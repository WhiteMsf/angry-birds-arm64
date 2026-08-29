# Stage 15 — recovered exactly-one-bird damage path

Stage 14 proved a real RedBird_4 <-> WoodBlock2_6 BeginContact on the
native-order 30 Hz Box2D driver.

Static ARMv7 analysis now resolves the exactly-one-special-object branch of
`GameLua::BeginContact` far enough to execute its non-destructive path.

## Recovered native strings/table walk

The BeginContact literal pool + PC-relative references resolve to:

```text
material
damageFactors
damageMultiplier
velocityMultiplier
useLegacyCollisionPath
scoreTable
blocks
score
blockCollision
strength
defence
```

For the exactly-one-bird path the native code performs:

```text
material = target.material
profile  = bird.damageFactors

damageMultiplier =
  blockTable.damageFactors[profile].damageMultiplier[material]
  default 1.0 when the numeric entry is absent

velocityMultiplier =
  blockTable.damageFactors[profile].velocityMultiplier[material]
  default 1.0 when the numeric entry is absent
```

`useLegacyCollisionPath` is tested with `LuaTable::isBoolean()`: the native
branch cares whether that field exists with Boolean type, not its Boolean
truth value.

## Exact recovered force

For the special/bird body:

```text
collisionForce =
    (bird.mass * length(bird.linearVelocity) / 10.0)
    * damageMultiplier
```

This is different from the ordinary block/block momentum-difference metric.

## Exact non-destructive target damage

When target strength is numeric:

```text
defence = target.defence if numeric else 0

if collisionForce >= defence:
    requestedDamage = collisionForce - defence
    newStrength = oldStrength - requestedDamage
    target.strength = newStrength

    if newStrength > 0:
        actualDamage = requestedDamage
    else:
        actualDamage = oldStrength
        queue target into deadBlocks
```

Stage 15 deliberately chooses the existing WoodBlock2_6 corpus and requires
the target to survive, so the bird-specific post-destruction velocity branch
is not mixed into this milestone.

## Lua callback boundary

The ARMv7 helper at `0x4F3A4` is called with:

```text
specialName
normalName
collisionForce
floor(actualDamage)
```

Combined with the original four-argument Lua function and the fact this helper
is used only by the special/bird BeginContact paths, Stage 15 reconstructs the
boundary as:

```text
birdCollision(birdName, targetName, collisionForce, floor(actualDamage))
```

Stage 15 invokes the original Lua `birdCollision()` and logs sprite and score
before/after. Score behavior is observed, not pre-assumed by the verifier.

The destructive bird branch and its velocity retention logic remain for a
later stage.
