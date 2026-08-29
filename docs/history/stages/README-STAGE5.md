# Angry ARM64 bootstrap v0.6 — Stage 5

Stage 4 proved the original Angry Birds `initialize()` function crosses into
the recovered 80-name GameLua API surface on ARM64.

Stage 5 replaces the first physics tranche with **real Box2D 2.1.2**.

The build script downloads a public mirror pinned to commit:

`20100c5e81ed18619b0fbd5d78bd60e7b13c7fe9`

That source has the same historical `b2BodyDef::inertiaScale` field seen in the
original Angry Birds ARMv7 binary, which is strong evidence that Box2D 2.1.x is
the correct ABI/API family.

Real bindings in this stage:

- `setPhysicsSimulationScale`
- `setPhysicsEnabled`
- `isPhysicsEnabled`
- `createBox`
- `createCircle`
- `setVelocity`
- `setAngularVelocity`
- `setPosition`
- `setRotation`
- `getAngle`
- `getWorldPoint`
- `applyImpulse`
- `applyForce`
- `removeObject`
- `setSleeping`

The original `initialize()` configures the bridge first. A controlled Lua probe
then exercises those recovered API names against actual Box2D bodies and runs
60 physics steps on the Android ARM64 device.

Expected final lines:

```text
[angry-stage5] ORIGINAL initialize() -> REAL BOX2D 2.1.2 BRIDGE
[angry-stage5] createBox/createCircle/velocity/impulse/transform/step VERIFIED
[angry-stage5] PASS
```

This is deliberately not a level boot yet. The next boundary is the game's
level/resource graph (`loadLevel`, level Lua files, SpriteSheet/Resources).
