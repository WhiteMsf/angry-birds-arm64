#!/usr/bin/env python3
"""Stage 24.44.3: close GameLua::setGameOn on the original Android target.

Cross-proof:
  * ARMv7 GameLua::setGameOn(bool) loads App+4 (OSInterface*), negates the bool,
    and virtual-calls slot +0x18.
  * AndroidOSInterface's constructor installs vtable+8 as the object vptr.
  * Resolve vtable+8+0x18 from the original ELF bytes and require it to equal
    framework::AndroidOSInterface::allowSleep(bool).
  * Require the shipping Android allowSleep(bool) body to be the exact one-
    instruction `bx lr` no-op.
  * Require the ARM64 bridge to preserve that no-op while logging !gameOn.
"""
from __future__ import annotations
import re, subprocess, sys
from pathlib import Path


def run(args):
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, errors='replace')
    return p.returncode, p.stdout


def parse_nm(text):
    rows=[]
    # llvm-nm -S -C: address size type demangled-name
    rx=re.compile(r'^\s*([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+(\S)\s+(.+?)\s*$',re.M)
    for m in rx.finditer(text):
        rows.append((int(m.group(1),16)&~1,int(m.group(2),16),m.group(3),m.group(4)))
    return rows


def exact(rows, name):
    xs=[r for r in rows if r[3]==name]
    if not xs:
        return None
    # aliases are fine; prefer a nonzero body and the lowest address.
    xs.sort(key=lambda r:(r[0],-r[1]))
    return xs[0]


def disasm(objdump, lib, addr, size):
    rc,out=run([objdump,'-d','--demangle',f'--start-address=0x{addr:x}',
                f'--stop-address=0x{addr+size:x}',lib])
    return rc,out


def dump_all_bytes(objdump, lib):
    # The original library is small (~1.8 MiB). Dumping all allocated/data
    # sections avoids depending on llvm-objdump -h column formatting across
    # NDK revisions. Addressed hex lines from every dumped section share the
    # same VMA namespace, so the vtable can be read directly by address.
    rc,out=run([objdump,'-s',lib])
    mem={}
    if rc: return mem,out
    # Lines are address then up to four 8-hex groups, then ASCII.
    for ln in out.splitlines():
        m=re.match(r'^\s*([0-9a-fA-F]+)\s+(.+)$',ln)
        if not m: continue
        addr=int(m.group(1),16)
        rest=m.group(2).split()
        off=0
        for tok in rest:
            if not re.fullmatch(r'[0-9a-fA-F]{8}',tok):
                break
            b=bytes.fromhex(tok)
            for x in b:
                mem[addr+off]=x; off+=1
    return mem,out


def word_le(mem, addr):
    try:
        b=bytes(mem[addr+i] for i in range(4))
    except KeyError:
        return None
    return int.from_bytes(b,'little')


def main():
    if len(sys.argv)!=7:
        print('usage: stage24443_setgameon_android_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <stage430-report> <stage161-report> <cpp>',file=sys.stderr)
        return 2
    nm,objdump,lib,stage430p,stage161p,cppp=sys.argv[1:]
    for p in (nm,objdump,lib,stage430p,stage161p,cppp):
        if not Path(p).exists():
            print('ERROR missing='+p); return 3

    stage430=Path(stage430p).read_text(encoding='utf-8-sig',errors='replace')
    stage161=Path(stage161p).read_text(encoding='utf-8-sig',errors='replace')
    cpp=Path(cppp).read_text(encoding='utf-8',errors='replace')

    rc,nmt=run([nm,'-S','-C',lib])
    if rc:
        rc,nmt=run([nm,'-D','-S','-C',lib])
    if rc:
        print('ERROR llvm-nm failed')
        print(nmt); return 4
    rows=parse_nm(nmt)

    names={
      'setgame':'GameLua::setGameOn(bool)',
      'allow':'framework::AndroidOSInterface::allowSleep(bool)',
      'vtable':'vtable for framework::AndroidOSInterface',
    }
    syms={k:exact(rows,v) for k,v in names.items()}

    checks=[]
    def ck(name, cond):
        checks.append((name,bool(cond)))
        print(f'{name}={"PASS" if cond else "FAIL"}')

    print('ANGRY_STAGE24_44_3_SETGAMEON_ANDROID_CONTRACT 1')
    print('policy=exact original Android behavior; setGameOn -> OSInterface::allowSleep(!gameOn); Android allowSleep is a no-op')
    for k,v in syms.items():
        print(f'symbol[{names[k]}]={"MISSING" if v is None else f"0x{v[0]:x}+0x{v[1]:x}"}')

    setbody=''; allowbody=''
    if syms['setgame']:
        _,setbody=disasm(objdump,lib,syms['setgame'][0],syms['setgame'][1])
    if syms['allow']:
        _,allowbody=disasm(objdump,lib,syms['allow'][0],syms['allow'][1])

    ck('prior_setgameon_body_captured',
       '===== ARMV7 GameLua::setGameOn(bool) =====' in stage430 and
       'e2211001' in stage430 and 'e593f018' in stage430)
    ck('setgameon_app_osinterface_shape', 'e5903020' in setbody and 'e5933004' in setbody)
    ck('setgameon_negates_bool', 'e2211001' in setbody)
    ck('setgameon_virtual_slot_18', 'e593f018' in setbody)

    ck('android_os_ctor_vptr_plus8_prior_proof',
       'vtable for framework::AndroidOSInterface' in stage161 and
       'add\tr12, r12, #8' in stage161)
    ck('android_allow_sleep_symbol', syms['allow'] is not None and syms['allow'][1]==4)

    # Resolve the exact original Android vtable entry used by setGameOn.
    vt_target=None; sec_dump=''
    if syms['vtable']:
        vtaddr,vtsz,_,_=syms['vtable']
        mem,sec_dump=dump_all_bytes(objdump,lib)
        if mem:
            # ctor stores vtable+8 as vptr; call uses vptr+0x18.
            vt_target=word_le(mem,vtaddr+8+0x18)
    print('vtableRead=' + ('PASS' if vt_target is not None else 'UNRESOLVED'))
    print('vtableSlotObjectPlus0x18='+('UNRESOLVED' if vt_target is None else f'0x{vt_target:x}'))
    allowaddr=syms['allow'][0] if syms['allow'] else None
    ck('vtable_slot_18_is_allowSleep',
       vt_target is not None and allowaddr is not None and (vt_target & ~1)==allowaddr)

    # Exact Android implementation must be one bx lr instruction. The symbol is
    # four bytes, so this also rejects any hidden side effect.
    ins=[ln for ln in allowbody.splitlines() if re.match(r'^\s*[0-9a-fA-F]+:\s+[0-9a-fA-F]+\s+',ln)]
    ck('android_allowSleep_exact_noop',
       syms['allow'] is not None and syms['allow'][1]==4 and len(ins)==1 and
       'e12fff1e' in ins[0].lower() and re.search(r'\bbx\s+lr\b', ins[0]))

    a=cpp.find('static int l_stage24430_setGameOnAudit')
    b=cpp.find('// Stage 24.44.0: passive live witness',a)
    region=cpp[a:b] if a>=0 and b>a else ''
    ck('arm64_preserves_negated_argument', 'const bool allowSleep = !gStage24430LastGameOn;' in region)
    ck('arm64_preserves_android_noop',
       'action=ORIGINAL_ANDROID_NOOP' in region and
       not any(x in region for x in ('ANativeActivity_setWindowFlags','AWINDOW_FLAG_KEEP_SCREEN_ON','SetActive(','gStage24Paused.store')))
    ck('runtime_witness_retained', '[stage24.44.3-gameon]' in region)

    print('\n===== ARMV7 GameLua::setGameOn(bool) =====')
    print(setbody.rstrip())
    print('\n===== ARMV7 AndroidOSInterface::allowSleep(bool) =====')
    print(allowbody.rstrip())
    print('\nverdict='+('PASS' if all(v for _,v in checks) else 'FAIL'))
    return 0 if all(v for _,v in checks) else 6

if __name__=='__main__':
    raise SystemExit(main())
