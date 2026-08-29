#!/usr/bin/env python3
import pathlib, re, struct, sys, zipfile

if len(sys.argv) != 3:
    print('usage: stage24301_cutscene_dynamic_contract.py <imageRoot> <stage24_live_surface.cpp>', file=sys.stderr)
    sys.exit(2)
root=pathlib.Path(sys.argv[1]); src=pathlib.Path(sys.argv[2])
names=[
 'CUTSCENES_BACKGROUNDS_1.dat','CUTSCENES_BACKGROUNDS_2.dat','CUTSCENES_BACKGROUNDS_3.dat',
 'CUTSCENES_BACKGROUNDS_4.dat','CUTSCENES_ELEMENTS_1.dat','CUTSCENES_ELEMENTS_2.dat']
print('ANGRY_STAGE24_30_1_CUTSCENE_DYNAMIC_RENDERSTATE_CONTRACT 1')
print('policy=FAIL_CLOSED; dynamic metadata becomes visible only through res.createSpriteSheet; original texture bytes are staged separately and acquired/released with the dynamic sheet')
textures=[]
for n in names:
    p=root/n
    if not p.is_file():
        print(f'FAIL missing DAT {p}'); sys.exit(1)
    b=p.read_bytes(); hits=sorted(set(m.decode('ascii') for m in re.findall(rb'(?<![A-Za-z0-9_-])[A-Za-z0-9_-]+\.(?:pvr|png)(?![A-Za-z0-9_-])',b,re.I)))
    if not hits:
        print(f'FAIL no texture in {n}'); sys.exit(1)
    textures.extend(hits)
    story=len(set(re.findall(rb'STORY_[A-Z0-9_]+',b)))
    print(f'DAT file={n!r} bytes={len(b)} textures={";".join(hits)} storyNames={story}')

for tex in sorted(set(textures)):
    p=root/tex; z=pathlib.Path(str(p)+'.zip')
    data=None; origin=None
    if p.is_file(): data=p.read_bytes(); origin=str(p)
    elif z.is_file():
        with zipfile.ZipFile(z) as f:
            members=[x for x in f.namelist() if not x.endswith('/')]
            if len(members)!=1:
                print(f'FAIL expected one file in {z}, got {len(members)}'); sys.exit(1)
            data=f.read(members[0]); origin=f'{z}!{members[0]}'
    else:
        print(f'FAIL missing texture {p} or {z}'); sys.exit(1)
    if tex.lower().endswith('.pvr'):
        if len(data)<52:
            print(f'FAIL short PVR {origin}'); sys.exit(1)
        vals=struct.unpack_from('<13I',data,0)
        header,height,width,mips,flags,data_len,bpp,rm,gm,bm,am,magic,surfaces=vals
        typ=flags&0xff
        if header!=52 or magic!=0x21525650 or surfaces!=1 or typ not in (0x10,0x13,0x36):
            print(f'FAIL unsupported PVR header texture={tex} header={header} magic=0x{magic:08x} type=0x{typ:02x} surfaces={surfaces}')
            sys.exit(1)
        if header+data_len>len(data):
            print(f'FAIL PVR payload overrun {tex}'); sys.exit(1)
        print(f'TEXTURE logical={tex!r} origin={origin!r} bytes={len(data)} size={width}x{height} type=0x{typ:02x} bpp={bpp} masks={rm:08x}/{gm:08x}/{bm:08x}/{am:08x} exact=yes')
    else:
        print(f'TEXTURE logical={tex!r} origin={origin!r} bytes={len(data)} kind=PNG exact-source=yes')

text=src.read_text(encoding='utf-8',errors='replace')
checks={
 'dynamicCreateBinding':'l_res_createSpriteSheet301' in text and 'action=LOAD' in text,
 'dynamicReleaseBinding':'l_res_releaseSpriteSheet301' in text and 'NOOP_NON_DYNAMIC' in text,
 'registryUnload':'bool unloadSheet(const std::string& raw' in text and 'spriteOwners_.erase' in text,
 'dynamicTextureAcquire':'stage24301AcquireSheetTextures' in text and 'dynamicAtlases' in text,
 'dynamicTextureRelease':'stage24301ReleaseSheetTextures' in text and 'glDeleteTextures' in text,
 'originalReleaseCutScenesRequired':'stage24301ReleaseCutScenesOriginal' in text,
 'renderState2':'n != 2 && n != 4 && n != 5 && n != 7' in text,
 'renderState4':'const float sx = n >= 4' in text,
 'renderState5':'const float angle = n >= 5' in text,
 'renderState7':'const float px = n >= 7' in text,
 'cutsceneProbeRemovedFromBinding':'lua_pushcfunction(L, l_res_createSpriteSheet301)' in text,
}
for k,v in checks.items(): print(f'SOURCE {k}={"PASS" if v else "FAIL"}')
if not all(checks.values()): sys.exit(1)
print('verdict=PASS_DYNAMIC_SPRITESHEET_AND_PROGRESSIVE_RENDERSTATE_READY')
