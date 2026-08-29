# Stage 13 — deadBlocks -> removeBlocks -> removeObject -> DestroyBody

Stage 12 proved collision damage on the recovered native-order 30 Hz driver.
The passive Level1 corpus never naturally reaches strength <= 0, so Stage 13
uses one deterministic probe to cross that exact branch.

## What static reconstruction now proves

### ARMv7 BeginContact death branch

The original `GameLua::BeginContact`:

1. computes the collision metric;
2. subtracts `(metric - defence)` from `strength`;
3. writes the new strength;
4. if the new value is `<= 0`, inserts the Lua object table into a cached
   table with `LuaTable::setTable(name, objectTable)`.

The cached table at `GameLua + 0x16c` is loaded by the native level path and
feeds the public Lua `deadBlocks` lifecycle used by original `removeBlocks()`.

For overkill damage, the ARMv7 accounting adds the victim's *old remaining
strength* to actualDamage rather than the full requested damage.

### Original Lua removeBlocks()

Static Lua 5.1 bytecode reconstruction identifies `removeBlocks` as root child
prototype 143, 471 instructions.

Its outer loop is effectively:

```text
for name, object in pairs(deadBlocks):
    ... original score/audio/particles/achievement logic ...
    removeObject(name)
    levelGoals[name] = nil
    objects.world[name] = nil
    deadBlocks[name] = nil
```

It also updates:

```text
scoreTable.blocks.score += destructionScore
```

before native removal.

### ARMv7 GameLua::removeObject(String)

The unstripped native function is 1208 bytes. Its ordinary-object path:

- looks up RenderObjectData in the native object hashtable;
- repairs special-object bookkeeping when applicable;
- calls `b2World::DestroyBody(body)`;
- removes native object storage;
- also contains joint/native-container cleanup paths.

The Stage 13 target is an ordinary Level1 block with no controlled joint
dependency, so the reconstructed compatibility implementation performs the
architectural core: `DestroyBody` + removal from the native body/object map.
Original Lua `removeBlocks()` performs the public Lua-table cleanup around it.

## Controlled target

Stage 11's corrected-timing corpus already observed:

```text
frame 81
WoodBlock6_3 <-> WoodBlock6_5
collision metric ~= 3.5319
```

Wood has defence 2.5, so this contact produces about 1.0319 damage.

Stage 13 changes only:

```text
WoodBlock6_5.strength: 70 -> 0.75
```

before the frame loop. Geometry, mass, velocity, defence, Box2D timing and all
other Level1 data are unchanged.

Therefore the already-observed frame-81 contact should drive:

```text
newStrength ~= 0.75 - (3.5319 - 2.5)
            ~= -0.2819

BeginContact
 -> deadBlocks["WoodBlock6_5"] = object

same fixed-step frame, after Step returns:
 -> original removeBlocks()
 -> original scoring/effects path
 -> removeObject("WoodBlock6_5")
 -> b2World::DestroyBody
 -> objects.world[name] = nil
 -> deadBlocks[name] = nil
```

WoodBlock6_5 is deliberately not the pig goal, so destroying it does not
immediately complete Level1.

## Diagnostic safety

When `deadBlocks` is non-empty, Stage 13 enables the exact stripped-Lua VM PC
tracer only around the original `removeBlocks()` call. If a headless service
dependency is still missing, the next log will identify the original function
and instruction PC instead of requiring guesswork.
