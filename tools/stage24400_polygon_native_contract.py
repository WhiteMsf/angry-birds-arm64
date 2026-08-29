#!/usr/bin/env python3
"""Stage 24.40.0: ARMv7 createPolygon/vertex-accumulator reconstruction contract."""
from __future__ import annotations
import os, re, subprocess, sys
from pathlib import Path

def run(args):
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors='replace')
    return p.returncode,p.stdout

def main():
    if len(sys.argv)!=5:
        print('usage: stage24400_polygon_native_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <stage24_live_surface.cpp>',file=sys.stderr)
        return 2
    nm,objdump,lib,cpp_path=sys.argv[1:]
    for p in (nm,objdump,lib,cpp_path):
        if not os.path.exists(p):
            print('ERROR missing='+p); return 3
    rc,nmt=run([nm,'-S','-C',lib])
    if rc:
        rc,nmt=run([nm,'-D','-S','-C',lib])
    required_symbols=[
        'GameLua::clearVertices()',
        'GameLua::addVertex(float, float)',
        'GameLua::createPolygon(GameLua::RenderObjectData*, lang::String, float, float, float, float, float, float, float)',
        'GameLua::createPolygonLua(lang::String, lang::String, float, float, float, float, float, float, float, bool, bool, float)',
    ]
    missing=[x for x in required_symbols if x not in nmt]
    m=re.search(r'^\s*([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+\S\s+GameLua::createPolygon\(GameLua::RenderObjectData\*.*$',nmt,re.M)
    body=''
    if m:
        start=int(m.group(1),16)&~1; size=int(m.group(2),16)
        _,body=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{start+size:x}',lib])
    native={
        'symbols':not missing,
        'polygon_set':'b2PolygonShape::Set(b2Vec2 const*, int)' in body,
        'create_body':'b2World::CreateBody' in body,
        'create_fixture':'b2Body::CreateFixture' in body,
        'radius_0_1':('3dcccccd' in body.lower() or 'cd cc cc 3d' in body.lower()),
    }
    cpp=Path(cpp_path).read_text(errors='replace')
    current={
        'vertex_buffer':'gStage24400PolygonVertices' in cpp,
        'clear_binding':'setfn(L, "clearVertices", l_stage24400_clearVertices);' in cpp,
        'add_binding':'setfn(L, "addVertex", l_stage24400_addVertex);' in cpp,
        'polygon_binding':'setfn(L, "createPolygon", l_stage24400_createPolygon);' in cpp,
        'polygon_set':'shape.Set(vertices, vertexCount);' in cpp,
        'radius':'shape.m_radius = 0.1f;' in cpp,
        'fixture_material':all(x in cpp for x in ('fd.friction = friction;','fd.restitution = restitution;','fd.density = density;')),
        'lua_materialization':'create_lua_object_polygon(' in cpp,
        'runtime_observer':'[stage24.40.0-polygon] CREATE' in cpp,
    }
    a=cpp.find('static int l_stage24400_createPolygon')
    b=cpp.find('static int l_createBox',a)
    fn=cpp[a:b]
    anti={'no_levelp2_special_case':'LevelP2_' not in fn and 'LevelP2_103' not in fn}
    print('ANGRY_STAGE24_40_0_POLYGON_NATIVE_CONTRACT 1')
    print('authority=ARMv7 GameLua clearVertices/addVertex/createPolygon + untouched Lua createObject producer')
    if missing: print('missingSymbols='+','.join(missing))
    for group,d in (('native',native),('arm64',current),('anti',anti)):
        for k,v in d.items(): print(f"{group}.{k}={'PASS' if v else 'FAIL'}")
    ok=not missing and all(native.values()) and all(current.values()) and all(anti.values())
    if not ok:
        print('--- ARMV7 createPolygon body ---')
        print(body)
        return 4
    print('result=PASS')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
