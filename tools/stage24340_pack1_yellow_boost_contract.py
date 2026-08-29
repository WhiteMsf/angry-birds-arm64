#!/usr/bin/env python3
"""Stage 24.34.0 Pack1 1-16 + original Yellow BOOST static contract."""
from pathlib import Path
import re, sys, hashlib
if len(sys.argv) != 4:
    raise SystemExit("usage: stage24340_pack1_yellow_boost_contract.py <build.ps1> <stage24.cpp> <scripts-dir>")
build=Path(sys.argv[1]).read_text(encoding='utf-8-sig', errors='replace')
cpp=Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')
game=Path(sys.argv[3])/'gamelogic.lua'
if not game.is_file(): raise SystemExit(f'missing untouched gamelogic.lua: {game}')
raw=game.read_bytes()
def strings(data,n=4):
    out=[]; cur=bytearray()
    for b in data:
        if 32<=b<=126: cur.append(b)
        else:
            if len(cur)>=n: out.append(cur.decode('ascii','ignore'))
            cur.clear()
    if len(cur)>=n: out.append(cur.decode('ascii','ignore'))
    return out
joined='\n'.join(strings(raw))
expected=[('1-11','Level9'),('1-12','Level13'),('1-13','Level10'),('1-14','Level39'),('1-15','Level12'),('1-16','Level15')]
errors=[]
print('ANGRY_STAGE24_34_0_PACK1_YELLOW_BOOST_CONTRACT 1')
print('mapping_source=untouched levelOrder.pack1 runtime table captured by Stage24.28.0')
for human,phys in expected:
    ok=(f"levels\\pack1\\{phys}.lua" in build and f"'{phys}.lua') -Force" in build)
    print(f'LEVEL human={human} physical={phys} staged={"PASS" if ok else "FAIL"}')
    if not ok: errors.append(f'missing transport {human}={phys}')
checks={
 'progression_map_1_16':'Level8,Level9,Level13,Level10,Level39,Level12,Level15' in cpp,
 'active_level_observer':'[stage24.32-progression] LEVEL_ACTIVE' in cpp,
 'specialty_observer':'[stage24.32.1-specialty] STATE' in cpp,
 'yellow_template_telemetry':all(x in cpp for x in ('"mass"','"xVel"','"yVel"','"sprite"')),
 'boost_impulse_observer':'[stage24.34.0-boost] APPLY_IMPULSE' in cpp,
 'no_small_yellow_native_case':'SmallYellowBird' not in cpp,
 'no_yellow_sprite_native_case':'BIRD_YELLOW_SPECIAL' not in cpp,
}
# observer is allowed to compare the generic specialty string BOOST, but no native
# code may synthesize force/velocity based on it. Check the observer block itself.
boost_pos=cpp.find('[stage24.34.0-boost] APPLY_IMPULSE')
checks['boost_observer_after_real_applyImpulse']=boost_pos>=0 and 'b->ApplyLinearImpulse(impulse, point)' in cpp[max(0,boost_pos-1800):boost_pos]
for k,v in checks.items():
    print(f'CHECK {k}={"PASS" if v else "FAIL"}')
    if not v: errors.append(k)
for tok in ('birdSpecialtyAvailable','birdSpecialty','BOOST','boostForce','applyImpulse','addParticles','BIRD_YELLOW_SPECIAL','setSprite','specialty'):
    ok=tok in joined
    print(f'ORIGINAL_GAMELOGIC_TOKEN token={tok!r} present={"PASS" if ok else "FAIL"}')
    if not ok: errors.append('gamelogic token '+tok)
print(f'ORIGINAL_GAMELOGIC sha256={hashlib.sha256(raw).hexdigest()} bytes={len(raw)} copied_into_project=NO')
print('yellow_runtime_authority=untouched updateGame BOOST branch')
print('RESULT='+('FAIL' if errors else 'PASS'))
if errors:
    for e in errors: print('ERROR '+e)
    raise SystemExit(1)
