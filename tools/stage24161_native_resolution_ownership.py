#!/usr/bin/env python3
"""Stage 24.16.1 native Android resolution ownership audit.

Runs only LLVM read-only tools against the untouched ARMv7 libangrybirds.so.
It deliberately emits evidence, not a replacement viewport formula.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable


@dataclass
class Symbol:
    addr: int
    size: int
    typ: str
    name: str


def run(args: list[str]) -> tuple[int, list[str]]:
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, errors="replace")
    return p.returncode, p.stdout.splitlines()


def parse_nm(lines: Iterable[str]) -> list[Symbol]:
    out: list[Symbol] = []
    rx = re.compile(r"^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+(\S)\s+(.+?)\s*$")
    for line in lines:
        m = rx.match(line)
        if not m:
            continue
        out.append(Symbol(int(m.group(1), 16), int(m.group(2), 16), m.group(3), m.group(4)))
    return out


def function_blocks(disasm: list[str]) -> list[tuple[int, int, str]]:
    rx = re.compile(r"^\s*([0-9A-Fa-f]+)\s+<(.+)>:\s*$")
    headers: list[tuple[int, str]] = []
    for i, line in enumerate(disasm):
        m = rx.match(line)
        if m:
            headers.append((i, m.group(2)))
    blocks: list[tuple[int, int, str]] = []
    for j, (start, name) in enumerate(headers):
        stop = headers[j + 1][0] if j + 1 < len(headers) else len(disasm)
        blocks.append((start, stop, name))
    return blocks


def target_key(name: str) -> str | None:
    checks = [
        ("egl_setviewport", "gr::EGL_Context::setViewport("),
        ("egl_viewport", "gr::EGL_Context::viewport() const"),
        ("screen_transform", "math::float4x4::setScreenTransform("),
        ("android_setresolution", "framework::AndroidOSInterface::setResolution("),
        ("app_resolutionchanged", "framework::App::resolutionChanged()"),
        ("transform_point_to_screen", "gr::Context::transformPointToScreen("),
        ("gamelua_setrenderstate", "GameLua::setRenderState("),
        ("gamelua_settopleft", "GameLua::setTopLeft("),
        ("gamelua_setworldscale", "GameLua::setWorldScale("),
    ]
    for key, needle in checks:
        if needle in name:
            return key
    # Constructors/destructors are useful ownership boundaries too.
    if "gr::EGL_Context::EGL_Context(" in name:
        return "egl_context_ctor"
    if "framework::AndroidOSInterface::AndroidOSInterface(" in name:
        return "android_os_ctor"
    return None


def print_symbol_body(objdump: str, lib: str, sym: Symbol, key: str) -> None:
    start = sym.addr & ~1
    size = sym.size or 0x800
    stop = start + size
    print()
    print(f"--- EXACT_NATIVE_BODY key={key} symbol={sym.name} type={sym.typ} "
          f"start=0x{start:x} size=0x{size:x} stop=0x{stop:x} ---")
    rc, lines = run([objdump, "-d", "--demangle", f"--start-address=0x{start:x}",
                     f"--stop-address=0x{stop:x}", lib])
    print(f"objdumpExit={rc} lines={len(lines)}")
    for line in lines:
        print(line)


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: stage24161_native_resolution_ownership.py <llvm-nm> <llvm-objdump> <libangrybirds.so>", file=sys.stderr)
        return 2
    nm, objdump, lib = sys.argv[1:]
    print("ANGRY_STAGE24_16_1_NATIVE_RESOLUTION_OWNERSHIP 1")
    print("policy=DIAGNOSTIC_ONLY; untouched ARMv7 binary; no inferred viewport/aspect constants")
    print(f"lib={lib}")
    print(f"llvmNm={nm}")
    print(f"llvmObjdump={objdump}")
    for p in (nm, objdump, lib):
        if not os.path.exists(p):
            print(f"ERROR missing={p}")
            return 3

    rc, nm_lines = run([nm, "-S", "-C", lib])
    if rc != 0 or not nm_lines:
        rc, nm_lines = run([nm, "-D", "-S", "-C", lib])
    symbols = parse_nm(nm_lines)
    print(f"nmExit={rc} parsedSymbols={len(symbols)}")

    related_rx = re.compile(
        r"(?i)(EGL_Context|AndroidOSInterface|resolutionChanged|setScreenTransform|"
        r"transformPointToScreen|viewport|setViewport|setResolution|screen|display|resolution)"
    )
    related = [s for s in symbols if related_rx.search(s.name)]
    print()
    print(f"--- RESOLUTION_OWNERSHIP_SYMBOLS count={len(related)} capped=500 ---")
    for s in related[:500]:
        print(f"{s.addr:08x} {s.size:08x} {s.typ} {s.name}")

    exact: list[tuple[Symbol, str]] = []
    seen: set[tuple[int, str]] = set()
    for s in symbols:
        key = target_key(s.name)
        if key and s.typ in "TtWw" and (s.addr, s.name) not in seen:
            seen.add((s.addr, s.name))
            exact.append((s, key))
    print()
    print(f"exactNativeBodies={len(exact)}")
    for s, key in exact:
        print_symbol_body(objdump, lib, s, key)

    print()
    print("--- DIRECT_CALLER_OWNERSHIP ---")
    print("note=direct BL/BLX calls only; indirect virtual calls are intentionally not guessed")
    drc, disasm = run([objdump, "-d", "--demangle", lib])
    print(f"fullObjdumpExit={drc} lines={len(disasm)}")
    if drc != 0:
        return 4

    blocks = function_blocks(disasm)
    target_needles: dict[str, tuple[str, ...]] = {
        "egl_setviewport": ("gr::EGL_Context::setViewport(",),
        "screen_transform": ("math::float4x4::setScreenTransform(",),
        "android_setresolution": ("framework::AndroidOSInterface::setResolution(",),
        "app_resolutionchanged": ("framework::App::resolutionChanged()",),
        "transform_point_to_screen": ("gr::Context::transformPointToScreen(",),
        "glViewport": ("<glViewport", " glViewport"),
    }
    emitted: set[tuple[str, str, int]] = set()
    for start, stop, caller_name in blocks:
        body = disasm[start:stop]
        for rel_i, line in enumerate(body):
            if not re.search(r"\bblx?\b", line):
                continue
            for key, needles in target_needles.items():
                if any(n in line for n in needles):
                    absolute_i = start + rel_i
                    sig = (key, caller_name, absolute_i)
                    if sig in emitted:
                        continue
                    emitted.add(sig)
                    lo = max(start, absolute_i - 18)
                    hi = min(stop, absolute_i + 25)
                    print()
                    print(f"CALLER target={key} caller={caller_name} callLineIndex={absolute_i} "
                          f"functionLines={stop-start} context={lo}:{hi}")
                    for x in disasm[lo:hi]:
                        print(x)
    print()
    print(f"directCallerHits={len(emitted)}")

    # Also surface direct calls from GameLua constructor to Lua/global registration
    # helpers.  The literal strings screenWidth/screenHeight live near this area,
    # and these calls help establish whether the dimensions are read from Context
    # or injected by the Android framework.
    print()
    print("--- GAMELUA_CONSTRUCTOR_CALLS (registration/Context-focused) ---")
    ctor_blocks = [(a,b,n) for a,b,n in blocks if "GameLua::GameLua(" in n]
    focus_rx = re.compile(r"(?i)(Lua(State|Object|Table)|global|Context::|viewport|width\(|height\(|resolution|screen)")
    focus_hits = 0
    for start, stop, name in ctor_blocks:
        print(f"constructor={name} lines={stop-start}")
        for line in disasm[start:stop]:
            if re.search(r"\bblx?\b", line) and focus_rx.search(line):
                print(line)
                focus_hits += 1
    print(f"constructorFocusedCallHits={focus_hits}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
