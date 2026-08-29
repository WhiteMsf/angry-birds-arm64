# Angry ARM64 bootstrap v0.5 — Stage 4

Stage 3 proved all six original Angry Birds 1.4.2 chunks execute normally on
the patched Lua 5.1 VM on Android ARM64.

Stage 4 goes one level deeper:

- Installs all **80** Lua-visible native names recovered from the original
  `GameLua` constructor.
- Uses traced no-op closures for the unimplemented native methods.
- Gives real semantic probes to the three native calls made by `initialize()`:
  `setPhysicsSimulationScale`, `setPhysicsEnabled`, and `requestAd`.
- Seeds the historical 480x320 baseline plus a `cursor` table and deterministic
  `os.time()`.
- Calls the original `initialize()` function.
- Deliberately replaces **only** `initializeMenu()` with a no-op because the
  six-file script archive does not include the wider save/settings/menu data
  graph needed by that branch.

Expected native calls from static bytecode analysis:

```text
setPhysicsSimulationScale(20)
setPhysicsEnabled(false)
requestAd()
```

Expected Lua state after `initialize()`:

```text
physicsToWorld = 20
physicsScale   = 0.05
physicsEnabled = false
adRequested    = true
```

This is not a full game boot yet. It is a controlled proof that the original
game initialization core can cross from Lua into the reconstructed native API
surface on ARM64.
