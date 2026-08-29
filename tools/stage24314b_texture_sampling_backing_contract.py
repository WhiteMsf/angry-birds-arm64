#!/usr/bin/env python3
"""Stage 24.31.4b — original ARMv7 texture sampling/backing contract audit.

Read-only. Stage24.31.4a proved that EGL_Image::draw normalizes integer source
rectangles edge-to-edge (src/textureDimension) and RenderBatcher does not add a
half texel. This pass recovers the texture state and physical backing semantics
that make those UVs valid in the original renderer.
"""
from __future__ import annotations
import pathlib, re, subprocess, sys
from dataclasses import dataclass

HEADER='ANGRY_STAGE24_31_4B_ORIGINAL_TEXTURE_SAMPLING_BACKING_CONTRACT 1'

@dataclass
class Sym:
    addr:int; size:int; typ:str; name:str

def run(args):
    try:
        p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors='replace',check=False)
        return p.returncode,p.stdout.splitlines()
    except Exception as e:
        return -1,[f'exception={e}']

def parse_nm(lines):
    rx=re.compile(r'^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+(\S)\s+(.+?)\s*$')
    out=[]
    for ln in lines:
        m=rx.match(ln)
        if m: out.append(Sym(int(m.group(1),16),int(m.group(2),16),m.group(3),m.group(4)))
    return out

def ca(s): return s.addr & ~1

def containing(syms,addr):
    cand=[s for s in syms if ca(s)<=addr<ca(s)+max(s.size,1)]
    return max(cand,key=lambda s:ca(s)) if cand else None

def disasm(objdump,lib,s,max_size=0x1200):
    st=ca(s); sz=min(max(s.size or 0x100,0x40),max_size)
    rc,lines=run([objdump,'-d','--demangle',f'--start-address=0x{st:x}',f'--stop-address=0x{st+sz:x}',lib])
    return rc,st,sz,lines

def group(label,ss,limit=160):
    print(f'\n[{label}] count={len(ss)}')
    for s in ss[:limit]: print(f'addr=0x{ca(s):08x} size=0x{s.size:x} type={s.typ} name={s.name!r}')

def main():
    if len(sys.argv)!=5:
        print('usage: ... <llvm-nm> <llvm-objdump> <armv7-lib> <project-cpp>',file=sys.stderr); return 2
    nm,objdump,lib,cpp_path=sys.argv[1:]
    src=pathlib.Path(cpp_path).read_text(encoding='utf-8',errors='replace')
    print(HEADER)
    print('policy=READ_ONLY; Stage24.31.4 half-texel remains experimental/noncanonical')
    print('knownFrom31_4a=EGL_Image integer-subrect UVs are edge-to-edge: src/textureWidth and (src+size)/textureWidth; RenderBatcher copies UVs without half-texel mutation')
    print('question1=What GL min/mag/wrap state does original ARMv7 assign to sprite-sheet textures?')
    print('question2=What object supplies textureWidth/textureHeight to EGL_Image::draw, and are those logical or physical/padded backing dimensions?')

    rc,nml=run([nm,'-S','-C',lib]);
    if rc!=0 or not nml: rc,nml=run([nm,'-D','-S','-C',lib])
    syms=parse_nm(nml); print(f'nmExit={rc} parsedSymbols={len(syms)}')
    tex=[s for s in syms if 'EGL_Texture::' in s.name or re.search(r'(^|::)Texture::',s.name)]
    imgctor=[s for s in syms if 'EGL_Image::EGL_Image(' in s.name]
    create=[s for s in syms if any(k in s.name for k in ('createTexture(','createImage(','createRenderTarget(','loadTexture(','textureFrom'))]
    pot=[s for s in syms if any(k in s.name.lower() for k in ('poweroftwo','power_of_two','nextpower','nearestpower','texturewidth','textureheight'))]
    group('EGL_TEXTURE_RELATED_SYMBOLS',tex)
    group('IMAGE_TEXTURE_CREATION_SYMBOLS',imgctor+create)
    group('POT_OR_BACKING_DIMENSION_CANDIDATES',pot)

    # Whole disassembly is used only as an index for GL API callsites; the report
    # prints small windows and targeted owner bodies, not the whole library.
    drc,all_dis=run([objdump,'-d','--demangle',lib]); print(f'wholeDisasmExit={drc} lines={len(all_dis)}')
    addr_rx=re.compile(r'^\s*([0-9a-fA-F]+):')
    apis=['glTexParameteri','glTexParameterf','glTexImage2D','glTexSubImage2D','glCompressedTexImage2D','glBindTexture','glGenerateMipmap','glGenerateMipmapOES']
    hits=[]
    for i,ln in enumerate(all_dis):
        if not any(a in ln for a in apis): continue
        m=addr_rx.match(ln)
        if not m: continue
        a=int(m.group(1),16); owner=containing(syms,a)
        hits.append((i,a,ln.strip(),owner))
    print(f'\n[GL_TEXTURE_API_CALLS] count={len(hits)}')
    for i,a,ln,owner in hits:
        print(f'CALL addr=0x{a:08x} owner={(owner.name if owner else "<unknown>")!r}')
        for w in all_dis[max(0,i-14):min(len(all_dis),i+3)]: print('  '+w)

    owners=[]; seen=set()
    # Critical object methods + every owner that configures/uploads textures.
    for s in tex+imgctor+create+[h[3] for h in hits if h[3] is not None]:
        if s is None: continue
        key=(ca(s),s.name)
        if key in seen: continue
        if ('EGL_Texture::' in s.name or 'EGL_Image::EGL_Image(' in s.name or 'createTexture(' in s.name or 'createImage(' in s.name or any(s is h[3] for h in hits)):
            seen.add(key); owners.append(s)
    print(f'\n[TARGETED_OWNER_BODIES] count={len(owners)}')
    for s in owners:
        orc,st,sz,lines=disasm(objdump,lib,s)
        print(f'\n[BODY] name={s.name!r} start=0x{st:x} size=0x{sz:x} objdumpExit={orc}')
        for ln in lines: print(ln)

    print('\n[KNOWN_GL_ENUMS_FOR_READING_CALL_WINDOWS]')
    enums={
      'GL_TEXTURE_MAG_FILTER':0x2800,'GL_TEXTURE_MIN_FILTER':0x2801,
      'GL_TEXTURE_WRAP_S':0x2802,'GL_TEXTURE_WRAP_T':0x2803,
      'GL_NEAREST':0x2600,'GL_LINEAR':0x2601,
      'GL_NEAREST_MIPMAP_NEAREST':0x2700,'GL_LINEAR_MIPMAP_NEAREST':0x2701,
      'GL_NEAREST_MIPMAP_LINEAR':0x2702,'GL_LINEAR_MIPMAP_LINEAR':0x2703,
      'GL_REPEAT':0x2901,'GL_CLAMP_TO_EDGE':0x812F,'GL_TEXTURE_2D':0x0DE1,
    }
    for k,v in enums.items(): print(f'{k}=0x{v:04x} ({v})')

    print('\n[CURRENT_ARM64_EXPERIMENTAL_STATE]')
    print('halfTexelExperiment=' + ('ACTIVE' if 'STAGE24314_APPLY_HALF_TEXEL_FIX = true' in src else 'INACTIVE'))
    for needle in ('GL_TEXTURE_MIN_FILTER, GL_LINEAR','GL_TEXTURE_MAG_FILTER, GL_LINEAR','GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE','GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE'):
        print(f"sourceContains[{needle!r}]={'yes' if needle in src else 'no'}")

    guards={
      'textureSymbolsObserved':bool(tex),
      'imageConstructorObserved':bool(imgctor),
      'glTextureApiCallsObserved':bool(hits),
      'texParameterCallObserved':any('glTexParameteri' in h[2] or 'glTexParameterf' in h[2] for h in hits),
      'textureUploadCallObserved':any(('glTexImage2D' in h[2] or 'glCompressedTexImage2D' in h[2]) for h in hits),
    }
    print('\n[GUARDS]')
    for k,v in guards.items(): print(f'{k}={"PASS" if v else "MISSING"}')
    print('\n[INTERPRETATION_RULES]')
    print('rule1=Do not retain the Stage24.31.4 half-texel branch merely because it reduced seams; 31.4a disproved it as the original UV formula.')
    print('rule2=If ARMv7 sampler state is NEAREST, reproduce sampler state centrally; do not offset individual UI UVs.')
    print('rule3=If EGL_Texture width/height differs from logical image dimensions, reproduce backing allocation/denominator centrally in Image/Texture transport.')
    print('rule4=If both match ARM64 already, audit atlas padding/extrusion and destination rasterization next rather than inventing per-widget fixes.')
    ok=bool(imgctor) and bool(hits)
    print('VERDICT=' + ('PASS_SAMPLER_BACKING_EVIDENCE_CAPTURED' if ok else 'FAIL_MISSING_TEXTURE_EVIDENCE'))
    return 0 if ok else 4

if __name__=='__main__': raise SystemExit(main())
