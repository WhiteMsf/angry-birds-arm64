# Stage 16 — bird-caused destruction and the legacy velocity branch

Stage 15 closed the non-destructive exactly-one-bird collision path:

```text
RedBird_4 profile = DefaultDamageFactors
wood damageMultiplier = 1
bird mass = 13.618805
bird speed = 8
collisionForce = 10.895044
wood defence = 2.5
actualDamage = 8.395044
strength 40 -> 31.604956
birdCollision(..., floorDamage=8)
```

The original Lua callback spawned `redBuff`, did not change the block sprite
for that hit, and left the block score at zero.

## Stage 16 controlled destructive corpus

Only `WoodBlock2_6.strength` is changed:

```text
40 -> 4
```

Everything else is preserved: material, defence, mass, body geometry,
filters, Box2D timing, bird mass and injected speed.

With the same recovered force:

```text
requestedDamage = 10.895044 - 2.5 = 8.395044
newStrength     = 4 - 8.395044 = -4.395044
```

The ARMv7 <=0 branch writes the negative strength, queues the target into
`deadBlocks`, and saturates `actualDamage` at the old remaining strength:

```text
actualDamage = 4
```

Therefore original Lua receives:

```text
birdCollision("RedBird_4", "WoodBlock2_6", 10.895044, 4)
```

## Exact `useLegacyCollisionPath` branch

RedBird_4 has a Boolean-typed `useLegacyCollisionPath` field. The ARMv7 path
at `0x56FE8..0x57050` computes:

```text
overkill = -newStrength

velocityScale =
  min(
    (((overkill / birdMass) / collisionForce) * 10.0) * 1.75,
    1.0
  )

birdVelocity = oldBirdVelocity * velocityScale
contact.enabled = false
```

For this corpus the expected scale is about 0.518.

The alternate non-legacy branch stores a deferred velocity in
RenderObjectData and is intentionally not implemented until a runtime corpus
that actually uses it exists.

## Removal order

The native update order remains:

```text
world.Step(1/30,10,10)
original removeBlocks()
world.ClearForces()
original Lua update(dt,dt)
```

So after the bird queues `deadBlocks` inside BeginContact, original
`removeBlocks()` must consume it on the same fixed step, call the reconstructed
native `removeObject()`, destroy the Box2D body, clean Lua tables and award the
normal destruction score.

Stage 16 expects a stable 20-body world afterward.
