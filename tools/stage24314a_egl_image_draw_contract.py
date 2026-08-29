#!/usr/bin/env python3
"""Stage 24.31.4a — original ARMv7 EGL_Image/subrect backend contract audit.

Read-only against the untouched original ARMv7 library.  The purpose is to
recover the layer that SpriteSheet::drawSprite delegates source rectangles to,
instead of choosing UV/pixel-center behavior in the ARM64 SpriteSheet bridge.

This auditor deliberately prints raw function bodies and call targets.  It does
NOT assert that +0.5/-0.5 is original merely because the experimental ARM64
Stage24.31.4 seam pass improved screenshots.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys
from dataclasses import dataclass

HEADER = "ANGRY_STAGE24_31_4A_ORIGINAL_EGL_IMAGE_DRAW_CONTRACT 1"

@dataclass
class Sym:
    addr: int
    size: int
    typ: str
    name: str


def run(args):
    try:
        p = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            check=False,
        )
        return p.returncode, p.stdout.splitlines()
    except Exception as exc:
        return -1, [f"exception={exc}"]


def parse_nm(lines):
    # llvm-nm -S -C normally yields: addr size type demangled-name
    rx = re.compile(r"^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+(\S)\s+(.+?)\s*$")
    out = []
    for ln in lines:
        m = rx.match(ln)
        if not m:
            continue
        out.append(Sym(int(m.group(1), 16), int(m.group(2), 16), m.group(3), m.group(4)))
    return out


def canonical_addr(s: Sym) -> int:
    # Thumb symbols may carry bit0 in some symbol tables.
    return s.addr & ~1


def containing_symbol(syms, addr):
    best = None
    for s in syms:
        a = canonical_addr(s)
        n = max(s.size, 1)
        if a <= addr < a + n:
            if best is None or a > canonical_addr(best):
                best = s
    return best


def nearest_symbol(syms, addr):
    below = [s for s in syms if canonical_addr(s) <= addr]
    if not below:
        return None
    return max(below, key=lambda s: canonical_addr(s))


def disasm(objdump, lib, s, max_size=0x1000):
    start = canonical_addr(s)
    size = s.size if s.size else 0x100
    size = min(max(size, 0x40), max_size)
    rc, lines = run([
        objdump,
        "-d",
        "--demangle",
        f"--start-address=0x{start:x}",
        f"--stop-address=0x{start + size:x}",
        lib,
    ])
    return rc, start, size, lines


def branch_targets(lines):
    # LLVM objdump ARM examples:
    #   98ebc: ... bl 0xe7b0c <gr::EGL_Image::draw(...)>
    #   e1234: ... ldr pc, [r12, #0x14]  (virtual; no concrete target)
    rx = re.compile(r"\b(?:blx?|b(?:eq|ne|lt|gt|le|ge|hi|ls|cs|cc|mi|pl|vs|vc)?)\s+0x([0-9a-fA-F]+)")
    out = []
    for ln in lines:
        m = rx.search(ln)
        if m:
            out.append((int(m.group(1), 16), ln.strip()))
    return out


def print_symbol_group(label, items):
    print(f"\n[{label}] count={len(items)}")
    for s in items:
        print(f"addr=0x{canonical_addr(s):08x} raw=0x{s.addr:08x} size=0x{s.size:x} type={s.typ} name={s.name!r}")


def main():
    if len(sys.argv) != 5:
        print(
            "usage: stage24314a_egl_image_draw_contract.py <llvm-nm> <llvm-objdump> <armv7-lib> <project-cpp>",
            file=sys.stderr,
        )
        return 2

    nm, objdump, lib, cpp_path = sys.argv[1:]
    cpp = pathlib.Path(cpp_path)
    src = cpp.read_text(encoding="utf-8", errors="replace") if cpp.is_file() else ""

    print(HEADER)
    print("policy=READ_ONLY_ARMV7_BACKEND_RECOVERY; no new UV/pixel-center fix selected by this report")
    print("question=Where does original ARMv7 convert integer Sprite source rectangles into final texture coordinates/vertices?")
    print("experimentalArm64CenterSampling=" + ("ACTIVE_NONCANONICAL_AB_REFERENCE" if "STAGE24314_APPLY_HALF_TEXEL_FIX" in src else "INACTIVE"))

    rc, nm_lines = run([nm, "-S", "-C", lib])
    if rc != 0 or not nm_lines:
        rc, nm_lines = run([nm, "-D", "-S", "-C", lib])
    syms = parse_nm(nm_lines)
    print(f"nmExit={rc} parsedSymbols={len(syms)}")

    image_draw = [s for s in syms if "EGL_Image::draw(" in s.name]
    image_other = [s for s in syms if "EGL_Image::" in s.name and "EGL_Image::draw(" not in s.name]
    batcher = [s for s in syms if "EGL_RenderBatcher::" in s.name]
    sprite_draw = [s for s in syms if "SpriteSheet::drawSprite(" in s.name]
    context = [s for s in syms if ("EGL_Context::" in s.name or "gr::Context::" in s.name) and any(k in s.name.lower() for k in ("project", "matrix", "viewport", "render", "transform"))]

    print_symbol_group("EGL_IMAGE_DRAW_SYMBOLS", image_draw)
    print_symbol_group("EGL_IMAGE_RELATED_SYMBOLS", image_other[:80])
    print_symbol_group("EGL_RENDER_BATCHER_SYMBOLS", batcher[:120])
    print_symbol_group("SPRITESHEET_DRAW_SYMBOLS", sprite_draw)
    print_symbol_group("CONTEXT_MATRIX_VIEWPORT_CANDIDATES", context[:80])

    bodies = []
    # Raw original bodies are the primary evidence. Keep all EGL_Image::draw
    # overloads, all Batcher add/flush/draw-like methods, and SpriteSheet draw.
    targets = []
    targets.extend(image_draw)
    targets.extend([s for s in batcher if any(k in s.name.lower() for k in ("add(", "flush(", "draw(", "render("))])
    targets.extend(sprite_draw)
    targets.extend([s for s in context if 'setProjection(' in s.name or 'getProjection(' in s.name])

    seen = set()
    for s in targets:
        key = (canonical_addr(s), s.name)
        if key in seen:
            continue
        seen.add(key)
        orc, start, size, lines = disasm(objdump, lib, s)
        bodies.append((s, lines))
        print(f"\n[BODY] name={s.name!r} start=0x{start:x} size=0x{size:x} objdumpExit={orc} lines={len(lines)}")
        for ln in lines:
            print(ln)

        # Raw section bytes preserve literal-pool evidence that disassembly may
        # reference through PC-relative loads. Candidate float bit-pattern hits
        # are reported only as search aids, never as semantic proof.
        rrc, raw = run([
            objdump, "-s", f"--start-address=0x{start:x}",
            f"--stop-address=0x{start + size:x}", lib
        ])
        print(f"[RAW_BYTES] objdumpExit={rrc} lines={len(raw)}")
        raw_text = "\n".join(raw).lower()
        for tag, pat in (("float0.5_le", "0000003f"), ("float1.0_le", "0000803f"), ("float2.0_le", "00000040")):
            if pat in raw_text:
                print(f"candidateLiteral={tag} pattern={pat} PRESENT_UNINTERPRETED")
        for ln in raw:
            print(ln)

        print("[DIRECT_BRANCH_CALL_TARGETS]")
        for addr, ln in branch_targets(lines):
            c = containing_symbol(syms, addr)
            n = c or nearest_symbol(syms, addr)
            if n:
                delta = addr - canonical_addr(n)
                print(f"target=0x{addr:08x} symbol={n.name!r} delta=0x{delta:x} via={ln}")
            else:
                print(f"target=0x{addr:08x} symbol=<unknown> via={ln}")

        virtual = [ln.strip() for ln in lines if re.search(r"\bldr\s+pc\b|\bblx\s+r\d+\b|\bmov\s+lr,\s*pc\b", ln)]
        print(f"[INDIRECT_VIRTUAL_CALL_SITES] count={len(virtual)}")
        for ln in virtual:
            print(ln)

    print("\n[ARITHMETIC_SIGNAL_SCAN]")
    all_body_text = "\n".join("\n".join(lines) for _, lines in bodies)
    signals = [
        "__addsf3", "__subsf3", "__mulsf3", "__divsf3",
        "__aeabi_fadd", "__aeabi_fsub", "__aeabi_fmul", "__aeabi_fdiv",
        "floor", "floorf", "ceil", "ceilf", "round", "roundf", "trunc", "truncf",
        "glTexCoordPointer", "glVertexPointer", "glDrawArrays", "glDrawElements",
    ]
    for sig in signals:
        hits = all_body_text.count(sig)
        if hits:
            print(f"signal={sig!r} hits={hits}")

    # Print exact lines that look like source-rect integer loads/conversions and
    # float arithmetic around the Image draw body. This is intentionally broad;
    # the next pass can map register provenance from the raw body without rerun.
    print("\n[EGL_IMAGE_DRAW_INTERESTING_LINES]")
    interesting_rx = re.compile(
        r"(?i)\b(ldrsh|ldrh|sxt|uxt|vcvt|vadd|vsub|vmul|vdiv|add|sub|mul|bl|blx|ldr\s+pc|str|stm)\b"
    )
    for s, lines in bodies:
        if "EGL_Image::draw(" not in s.name:
            continue
        print(f"FUNCTION {s.name!r}")
        for ln in lines:
            if interesting_rx.search(ln):
                print(ln)

    guards = {
        "originalEglImageDrawFound": bool(image_draw),
        "originalSpriteSheetDrawFound": bool(sprite_draw),
        # Batcher may be stripped/inlined in some edition; report rather than
        # fail the whole build if it is absent.
        "renderBatcherSymbolsObserved": bool(batcher),
        "arm64ExperimentalFixStillExplicit": "STAGE24314_APPLY_HALF_TEXEL_FIX" in src,
    }
    print("\n[GUARDS]")
    for k, v in guards.items():
        print(f"{k}={'PASS' if v else 'MISSING'}")

    print("\n[INTERPRETATION_RULES]")
    print("rule1=Do NOT infer original +0.5/-0.5 from ARM64 screenshot improvement alone.")
    print("rule2=SpriteSheet integer srcRect delegation is provenance; final UV semantics belong to EGL_Image/RenderBatcher unless raw ARMv7 body proves otherwise.")
    print("rule3=If EGL_Image delegates raw pixel rectangles again, continue one level down before implementing Stage24.31.4b.")
    print("rule4=Any future ARM64 fix should centralize recovered image-subrect semantics instead of branching on target-sized UI sprites.")

    # Fail closed only on the two indispensable provenance anchors. Do not make
    # this audit brittle on optional/inlined RenderBatcher symbol names.
    ok = bool(image_draw) and bool(sprite_draw)
    print("VERDICT=" + ("PASS_RAW_CONTRACT_CAPTURED" if ok else "FAIL_MISSING_CORE_SYMBOL"))
    return 0 if ok else 4


if __name__ == "__main__":
    raise SystemExit(main())
