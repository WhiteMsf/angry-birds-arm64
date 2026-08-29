#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    print('usage: stage24330_createcircle_lua_metadata_contract.py <stage24_live_surface.cpp>')
    raise SystemExit(2)

src_path = Path(sys.argv[1])
s = src_path.read_text(encoding='utf-8', errors='replace')
errors=[]

def need(label, pattern, flags=re.S):
    if not re.search(pattern, s, flags):
        errors.append(label)

# The native bridge must materialize every createCircle argument that untouched
# updateGame re-reads from flyingBird when constructing specialty children.
for field in ('density','friction','restitution','z_order'):
    need(f'missing Lua-visible numeric field {field}', rf'set_number_field\(L,\s*"{re.escape(field)}"')
need('missing Lua-visible boolean field controllable', r'set_boolean_field\(L,\s*"controllable"')

need('create_lua_object_circle signature does not receive full physical/render metadata',
     r'create_lua_object_circle\s*\([^)]*float\s+density\s*,\s*float\s+friction\s*,\s*float\s+restitution\s*,[^)]*bool\s+controllable\s*,\s*float\s+zOrder')
need('l_createCircle does not forward native call arguments into Lua object materialization',
     r'create_lua_object_circle\s*\(L,\s*name,\s*sprite,\s*x,\s*y,\s*radius,\s*density,\s*friction,\s*restitution,\s*renderFlag87,\s*renderLayer\s*\)')

# This stage repairs the general createCircle object contract. It must not
# implement the Blue by name or synthesize CLUSTER_BOMB children natively.
if 'SmallBlueBird' in s:
    errors.append('bird-specific SmallBlueBird native special-case present')
for bad in (
    r'if\s*\([^\n]*CLUSTER_BOMB',
    r'switch\s*\([^\n]*birdSpecialty',
):
    if re.search(bad, s):
        errors.append('native specialty dispatch/split special-case present')

print('ANGRY_STAGE24_33_0_CREATECIRCLE_LUA_METADATA_CONTRACT 1')
print('source=' + str(src_path))
print('requiredLuaFields=density,friction,restitution,controllable,z_order')
print('authority=generic createCircle argument materialization; untouched Lua updateGame remains specialty owner')
print('blueSpecificNativeSplit=FORBIDDEN')
if errors:
    for e in errors:
        print('FAIL ' + e)
    raise SystemExit(2)
print('fieldMaterialization=PASS')
print('argumentForwarding=PASS')
print('antiBlueHardcode=PASS')
print('verdict=PASS')
