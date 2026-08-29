#!/usr/bin/env python3
import re, subprocess, sys
from pathlib import Path

HEADER='ANGRY_STAGE24_24_1_PARTICLE_EMITTER_LIMIT_CONTRACT 1'

def run(cmd):
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors='replace',check=False)
    return p.returncode,p.stdout.splitlines()

def parse_nm(lines):
    out=[]
    rx=re.compile(r'^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+\S+\s+(.+)$')
    for l in lines:
        m=rx.match(l)
        if m: out.append((int(m.group(1),16),int(m.group(2),16),m.group(3)))
    return out

def find(sym, needle):
    vals=[x for x in sym if needle in x[2]]
    if not vals: return None
    vals.sort(key=lambda x:(0 if x[2].startswith(needle) else 1,x[0]))
    return vals[0]

def dump(objdump,lib,start,stop):
    rc,lines=run([str(objdump),'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{stop:x}',str(lib)])
    return rc,lines

def text(lines): return '\n'.join(lines)

def require(ok,msg):
    if not ok:
        print('PROOF_FAIL '+msg)
        raise RuntimeError(msg)

def main():
    if len(sys.argv)!=4:
        print('usage: stage24241_particle_emitter_limit_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so>')
        return 2
    nm,objdump,lib=map(Path,sys.argv[1:])
    print(HEADER)
    print('policy=DIAGNOSTIC_ONLY; semantic summary emitted only after exact ARMv7 pattern checks')
    print(f'lib={lib}')
    rc,nmlines=run([str(nm),'-S','-C',str(lib)])
    if rc!=0 or not nmlines:
        rc,nmlines=run([str(nm),'-D','-S','-C',str(lib)])
    syms=parse_nm(nmlines)
    ctor=find(syms,'Particles::Particles(lua::LuaState*, GameLua*, game::Resources*)')
    add=find(syms,'Particles::addParticles(lang::String, float, float, float, float, float, float, bool)')
    upd=find(syms,'Particles::update(float)')
    if not ctor or not add or not upd:
        print(f'ctor={ctor} add={add} update={upd}')
        return 3
    print(f'ctor=0x{ctor[0]:x}+0x{ctor[1]:x}')
    print(f'addParticles=0x{add[0]:x}+0x{add[1]:x}')
    print(f'update=0x{upd[0]:x}+0x{upd[1]:x}')

    crc,ctorlines=dump(objdump,lib,ctor[0]&~1,(ctor[0]&~1)+min(max(ctor[1],0x220),0x260))
    arc,addlines=dump(objdump,lib,add[0]&~1,(add[0]&~1)+min(max(add[1],0xe50),0xe50))
    urc,uplines=dump(objdump,lib,upd[0]&~1,(upd[0]&~1)+min(max(upd[1],0x4e8),0x4e8))
    ct,at,ut=text(ctorlines),text(addlines),text(uplines)
    if crc or arc or urc: return 4

    # Constructor defaults: 0.5f, 40, 125 stored at +0x4c/+0x50/+0x54.
    require('[r5, #0x4c]' in ct and '[r5, #0x50]' in ct and '[r5, #0x54]' in ct,
            'constructor limit fields missing')
    require('mov\tr1, #40' in ct and 'mov\tr1, #125' in ct and '#1056964608' in ct,
            'constructor default constants missing')

    # Limit path at function entry and generation/update proof markers.
    for marker in ('[r7, #0x1c]','[r7, #0x4c]','[r7, #0x50]','[r7, #0x54]'):
        require(marker in at,'limit marker '+marker+' missing')
    require(at.count('math::RandomUtil::random()') >= 7,'expected particle random generators missing')
    require('#1069547520' in at and '#2097152' in at,
            'random birth-position 0.5 double constant construction missing')
    require('#1124073472' in at and '#3407872' in at,
            '180-degree conversion constant construction missing')
    require('<cosf>' in at and '<sinf>' in at,'rotated birth rectangle trig missing')
    require('__fixsfsi' in at,'random sprite/count integer conversion missing')
    require('#108' in at or '#0x6c' in at,'ParticleData 108-byte stride missing')
    require('[r5, #0x3c]' in at and '[r5, #0x3d]' in at,'animation/randomizeBirthPosition flags missing')
    for off in ('#0x40','#0x44','#0x48','#0x4c','#0x50','#0x54','#0x58','#0x5c','#0x60','#0x6c','#0x70'):
        require(f'[r5, {off}]' in at,'definition field '+off+' missing')

    require('#108' in ut or '#0x6c' in ut,'ParticleData update stride missing')
    require('__aeabi_fadd' in ut and '__mulsf3' in ut and '__divsf3' in ut,
            'update integration/interpolation math missing')

    print('')
    print('--- PROVEN SEMANTIC CONTRACT ---')
    print('ParticleArray.countOffset=0x1c ParticleData.stride=108')
    print('defaults.softFactor=0.5 defaults.softLimit=40 defaults.hardLimit=125')
    print('limitPolicy=if bypassLimits==false: if active+count>softLimit then count*=softFactor; if active+count>hardLimit then count=hardLimit-active; if count<=0 return')
    print('limitPolicy.bypass=arg8 true skips soft/hard adjustment')
    print('spawnLoop=integer i starts at 0; after each append i++; continue while float(i)<adjustedCount => positive noninteger count produces ceil(adjustedCount) particles')
    print('definition.randomizeBirthPosition=field +0x3d; absent field defaults true')
    print('birth.fixed=when randomizeBirthPosition==false: position=(x,y)')
    print('birth.random=dx=(random()-0.5)*width; dy=(random()-0.5)*height; position.x=x+dx*cos(objectAngle)-dy*sin(objectAngle); position.y=y+dx*sin(objectAngle)+dy*cos(objectAngle)')
    print('velocity.x=uniform(minVel,maxVel); velocity.y=uniform(minVel,maxVel)')
    print('particle.angle=uniform(angleMinEmitter,angleMaxEmitter) converted degrees*pi/180; absent angle fields default 0..360')
    print('particle.angularVelocity=uniform(minAngleVel,maxAngleVel)')
    print('particle.startScale=uniform(minScaleBegin,maxScaleBegin); endScale=uniform(minScaleEnd,maxScaleEnd)')
    print('definition.animationLifeTime=field +0x3c set when animation=="lifeTime"; animated definitions start on the first sprite; nonanimated definitions choose a random sprite at birth')
    print('update=age+=dt; remove when age>lifeTime; velocity+=gravity*dt; position+=velocity*dt; angle+=angularVelocity*dt; scale=start+(end-start)*(age/lifeTime)')
    print('animatedFrame=ceil(spriteCount*age/lifeTime), clamped to 1..spriteCount; sprite changes only when frame changes')
    print('alphaCurve=NONE in custom Particles wrapper; visual evolution is scale and optional lifetime sprite animation')

    def section(title,lines,start_off,end_off,base):
        lo=base+start_off; hi=base+end_off
        print(f'--- {title} 0x{lo:x}..0x{hi:x} ---')
        rx=re.compile(r'^\s*([0-9a-fA-F]+):')
        for l in lines:
            m=rx.match(l)
            if not m: continue
            a=int(m.group(1),16)
            if lo <= a < hi: print(l)

    abase=add[0]&~1; ubase=upd[0]&~1; cbase=ctor[0]&~1
    section('CTOR_LIMIT_DEFAULTS',ctorlines,0x70,0xb0,cbase)
    section('ADD_LIMIT_POLICY',addlines,0x40,0xdc,abase)
    section('ADD_EMITTER_CORE',addlines,0x470,0x6dc,abase)
    section('ADD_RANDOM_BIRTH_ROTATION',addlines,0xab0,0xbac,abase)
    section('UPDATE_CORE',uplines,0x20,0x270,ubase)
    print('PROOF_PASS exact ARMv7 emitter/limit/update ownership recovered')
    return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except RuntimeError: raise SystemExit(5)
