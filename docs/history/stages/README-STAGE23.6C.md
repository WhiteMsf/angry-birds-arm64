# Stage 23.6C — Original KA3D draw order / RenderObjectData passes

This stage removes the last name-sorted object-rendering placeholder from the Level1 GLES1 audit renderer.

Recovered from the original ARMv7 `GameLua::drawGame()` and a historical Pixelgene/KA3D source copy used during development (not included in the public repository):

- `Hashtable<String, RenderObjectData*>` iteration order, including the exact 0.75 load factor, prime capacity sequence, `String::hashCode()` h*31+byte hash, bucket traversal and collision-chain insertion semantics.
- Level1 starts with 21 native RenderObjectData entries, so the table should remain at capacity 37.
- `createBoxLua`: both render booleans and the final render-layer float are now retained.
- `createCircleLua`: render flag, final layer, circle marker, and the `int(layer)==999` special flag are retained.
- `setObjectParameter(name,1,value)` now updates the native draw-pass flag (+0x89 equivalent).
- `setSprite()` now updates the reconstructed native RenderObjectData sprite pointer by sprite name instead of remaining a headless no-op.
- `setTexture()` records the MaskedImage path. Level1 must contain zero such objects in this stage; otherwise the stage fails instead of approximating it.
- Original object passes:
  1. inverse-mass-zero (`b2Body.m_invMass==0`) and `int(layer)<=4`, then MaskedImage flush;
  2. dynamic back (`b2Body.m_invMass!=0`, flag87=0, flag89=0, layer<=4);
  3. original slingshot/resource-array interleave boundary;
  4. dynamic/front (`flag87!=0 || flag89!=0`, layer<=4);
  5. `layer>4` pass, including the recovered special-999 branch marker;
  6. Particles draw boundary.

The visual slingshot/resource arrays and particles themselves are not reconstructed by this stage; only their exact positions relative to object passes are recorded. Background, foreground, HUD and audio remain later presentation work.

All previous Level1 gates remain active: recovered polygon skin, full three-bird original input state machine, damage/destruction, RenderObjectData interpolation, original Lua camera, original RGBA4444 atlases and recovered GLES1 state.

Expected final marker:

```
[angry-stage23.6C] OBJECT DRAW-ORDER AUDIT BOUNDARY CLOSED; NEXT = LIVE ANDROID SURFACE + TOUCH
[angry-stage23.6C] PASS
```


## v0.25.4 runtime-gate correction

The ARMv7 renderer can draw the same RenderObjectData in more than one object pass.
In particular, pass2 checks flag87/flag89 + layer and does not re-check b2Body inverse mass,
so queued/front objects may be emitted once in pass0 and again in pass2. v0.25.3 incorrectly
required total draw calls <= Hashtable entries. v0.25.4 gates unique drawn objects against
Hashtable entries and records multiPassRedraws explicitly. This changes the audit only; it does
not collapse or remove the original redraw behavior.
