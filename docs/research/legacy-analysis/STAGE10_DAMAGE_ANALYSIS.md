# Stage 10 — recovered non-destructive ARMv7 block damage

Stage 9 produced a real Level1 collision corpus from `b2ContactListener`:

- 26 `BeginContact` events
- 19 unique pairs
- max recovered collision metric ~3.1881
- all contacts in the two-second headless run were non-controllable /
  `blockCollision`-class contacts

## Native ARMv7 damage rule recovered

For the ordinary block/block branch, the original `GameLua::BeginContact`
calculates:

```text
F = 0.1 * |mA*vA - mB*vB|
```

Then independently for each Lua object table:

```text
if strength is numeric:
    defence = numeric defence, otherwise 0

    if F >= defence:
        damage = F - defence
        newStrength = oldStrength - damage
        object.strength = newStrength
        damageFlag = true

        if newStrength > 0:
            actualDamage += damage
        else:
            actualDamage += oldStrength
            queue object for native destruction
```

After both objects are processed, the native code calls the **original Lua**:

```text
blockCollision(nameA, nameB, F, damageFlag)
```

The ARMv7 function later also updates a score-like numeric field using
`floor(totalActualDamage) * 10`. The exact target field/table is not yet proven,
so Stage 10 intentionally does not invent that update.

## Stage 10 boundary

The first 120-frame Level1 settling corpus is non-destructive: no recovered
contact should reduce an object's strength to zero.

Therefore Stage 10 safely reconstructs only the proven non-destructive part:

1. real Box2D `BeginContact`
2. exact recovered metric
3. exact strength/defence threshold
4. strength mutation
5. original `blockCollision(...)`
6. original `getDamageSprite()` / damage-sprite state transitions

If any object would hit `strength <= 0`, Stage 10 stops and reports the
destruction-queue boundary instead of pretending that removal is implemented.

## Level1 cross-checks

The original block/material tables resolve to:

- `SmallPiglette`: strength 4, inherited pig defence 1
- `WoodBlock6`: strength 70, inherited wood defence 2.5

The Stage 9 frame-80 contact:

```text
WoodBlock2_1 <-> SmallPiglette_7
F ~= 2.4385
```

predicts:

```text
pig damage   = 2.4385 - 1.0 ~= 1.4385
pig strength = 4.0 - 1.4385 ~= 2.5615
```

That leaves the pig alive at roughly 64% strength. The original
`blockCollision/getDamageSprite` path should consequently advance it from
`PIGLETTE_SMALL_01` to `PIGLETTE_SMALL_02`.

This gives Stage 10 a semantic check stronger than merely "the callback did
not crash."
