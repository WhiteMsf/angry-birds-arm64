# Stage 23.6A — ARMv7 RenderObjectData transform interpolation

Stage 23.6A replaces the temporary raw `b2Body -> Lua/render` transform sync with the transform-history path recovered from the original ARMv7 `GameLua::update(float)`.

It intentionally does **not** claim original camera or render-order fidelity yet. Those remain separate Stage 23.6B/23.6C audit targets so transform timing can be validated in isolation.

## Recovered ARMv7 behavior reproduced

Static disassembly of the original `libangrybirds.so` shows that each `RenderObjectData` owns two history samples, each containing `(x, y, angle)`. The game keeps a global 0/1 history index.

After a recorded Box2D fixed step:

1. the history index toggles;
2. awake bodies write the new position/angle into the selected slot;
3. after stepping, the game computes `alpha = accumulator / (1/30)`;
4. published `x/y/angle` are interpolated as `(1-alpha)*previous + alpha*current`;
5. angle interpolation chooses the shortest path across the +/-pi wrap.

The recovered published fields are at native `RenderObjectData` offsets 116, 120 and 124.

The original code gates history capture on Box2D `e_awakeFlag (0x0002)`. It also skips intermediate history writes while catch-up still exceeds two fixed steps, retaining the final two solver states. Stage 23.6A mirrors both details.

## Position/rotation setters

The original `GameLua::setPosition` and `GameLua::setRotation` do more than `b2Body::SetTransform`: they immediately update **both history slots and the published transform**. Stage 23.6A mirrors this so sling dragging, teleports and explicit script transforms do not acquire an artificial interpolation lag.

## Runtime gate

The existing full Level1 regression remains active. In addition, Stage 23.6A requires:

- at least one recovered history capture;
- at least one interpolation publish;
- the 60 Hz driver / 30 Hz solver snapshots to expose more than one interpolation phase;
- at least one post-launch snapshot to show a measurable raw-body -> published-render transform delta;
- all GPU snapshots to remain complete with no missing Level1 sprites.

GPU snapshots are captured at frames 70, 71, 220, 221 and 420. Adjacent pairs are intentional: the visual difference should be subtle, because this stage is measuring sub-frame smoothing rather than changing gameplay geometry.

## Still intentionally non-final

- Camera: Stage 23.2 debug view.
- Draw order: deterministic object-name map order.
- Quad topology: `GL_TRIANGLE_STRIP` remains a harness choice.
- The exact numeric source of the angle-wrap pi constant has not yet been resolved as an independent symbol; pi is inferred from the recovered control flow plus the Box2D angular domain.
- Exact Rovio Box2D fork provenance and gravity construction remain on the evidence backlog.
