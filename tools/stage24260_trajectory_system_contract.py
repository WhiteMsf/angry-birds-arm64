#!/usr/bin/env python3
"""Stage 24.26.0: original trajectory-system contract audit.

Diagnostic only.  This tool does not patch either binary.  It inventories the
untouched ARMv7 GameLua trajectory entry points and correlates them with the
original Lua/script and image-metadata corpus supplied locally by the user.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

HEADER = "ANGRY_STAGE24_26_0_TRAJECTORY_NATIVE_CONTRACT 1"
EXACT_METHODS = (
    "startNewTrajectory",
    "addToTrajectory",
    "addPuffToTrajectory",
)
SEARCH_TERMS = (
    "trajectory",
    "addtotrajectory",
    "addpufftotrajectory",
    "startnewtrajectory",
    "birdtrajectory",
    "recordtrajectory",
    "allowtrajectoryclearing",
    "puff",
    "trail",
)


@dataclass
class Sym:
    addr: int
    size: int
    typ: str
    name: str


def run(args: list[str]) -> tuple[int, list[str]]:
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


def parse_nm(lines: list[str]) -> list[Sym]:
    rx = re.compile(r"^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+(\S)\s+(.+?)\s*$")
    out: list[Sym] = []
    for line in lines:
        m = rx.match(line)
        if m:
            out.append(Sym(int(m.group(1), 16), int(m.group(2), 16), m.group(3), m.group(4)))
    return out


def scan_exact_tree(root: str, needles: tuple[str, ...]) -> dict[str, list[tuple[str, int]]]:
    hits = {n: [] for n in needles}
    if not root or not os.path.isdir(root):
        return hits
    lowered = [(n, n.encode("utf-8").lower()) for n in needles]
    for base, _, files in os.walk(root):
        for fn in files:
            p = os.path.join(base, fn)
            try:
                data = Path(p).read_bytes()
            except OSError:
                continue
            low = data.lower()
            for name, needle in lowered:
                pos = 0
                while True:
                    i = low.find(needle, pos)
                    if i < 0:
                        break
                    hits[name].append((p, i))
                    pos = i + max(1, len(needle))
    return hits


def ascii_runs(data: bytes, min_len: int = 4):
    start = None
    for i, b in enumerate(data + b"\x00"):
        if 32 <= b < 127:
            if start is None:
                start = i
        else:
            if start is not None and i - start >= min_len:
                yield start, data[start:i].decode("ascii", "replace")
            start = None


def scan_metadata_terms(root: str) -> list[tuple[str, int, str]]:
    out: list[tuple[str, int, str]] = []
    if not root or not os.path.isdir(root):
        return out
    allowed = {".dat", ".lua", ".txt", ".xml", ".json", ".ini", ".cfg"}
    for base, _, files in os.walk(root):
        for fn in files:
            p = os.path.join(base, fn)
            ext = Path(fn).suffix.lower()
            low_name = fn.lower()
            if any(t in low_name for t in SEARCH_TERMS):
                out.append((p, -1, f"FILENAME:{fn}"))
            if ext not in allowed:
                continue
            try:
                data = Path(p).read_bytes()
            except OSError:
                continue
            for off, text in ascii_runs(data, 4):
                low = text.lower()
                if any(t in low for t in SEARCH_TERMS):
                    out.append((p, off, text))
                    if len(out) >= 500:
                        return out
    return out


def print_recon_bindings(project_root: Path) -> None:
    tsv = project_root / "recon" / "LuaBindings_80.tsv"
    print("\n--- PROJECT_RECON_BINDING_REGISTRATIONS ---")
    print(f"reconFile={tsv}")
    if not tsv.is_file():
        print("reconFile=NOT_FOUND")
        return
    lines = tsv.read_text(encoding="utf-8", errors="replace").splitlines()
    found = 0
    for line in lines:
        if any(name in line for name in EXACT_METHODS):
            print(line)
            found += 1
    print(f"trajectoryBindingRows={found}")


def main() -> int:
    if len(sys.argv) != 6:
        print(
            "usage: stage24260_trajectory_system_contract.py "
            "<llvm-nm> <llvm-objdump> <libangrybirds.so> <scripts-dir> <image-root>",
            file=sys.stderr,
        )
        return 2

    nm, objdump, lib, scripts, image_root = sys.argv[1:]
    project_root = Path(__file__).resolve().parent.parent

    print(HEADER)
    print("policy=DIAGNOSTIC_ONLY; ARM64 startNewTrajectory/addToTrajectory/addPuffToTrajectory remain behaviorally headless")
    print("questions=native ownership; argument interpretation; storage/lifetime; draw/clear path; original Lua producers; candidate sprite metadata")
    print(f"lib={lib}")
    print(f"scripts={scripts}")
    print(f"imageRoot={image_root}")

    for p in (nm, objdump, lib):
        if not os.path.exists(p):
            print(f"ERROR missing={p}")
            return 3

    print_recon_bindings(project_root)

    rc, nm_lines = run([nm, "-S", "-C", lib])
    if rc != 0 or not nm_lines:
        rc, nm_lines = run([nm, "-D", "-S", "-C", lib])
    syms = parse_nm(nm_lines)

    exact: list[Sym] = []
    related: list[Sym] = []
    seen: set[tuple[int, str]] = set()
    for s in sorted(syms, key=lambda x: (x.addr, x.name)):
        if s.typ not in "TtWw":
            continue
        low = s.name.lower()
        is_exact = "gamelua::" in low and any(name.lower() in low for name in EXACT_METHODS)
        is_related = "trajectory" in low
        if not (is_exact or is_related):
            continue
        key = (s.addr, s.name)
        if key in seen:
            continue
        seen.add(key)
        (exact if is_exact else related).append(s)

    print("\n--- TARGET_SYMBOLS ---")
    print(f"nmExit={rc} parsedSymbols={len(syms)} exactGameLuaTargets={len(exact)} relatedTrajectoryTargets={len(related)}")
    for s in exact:
        print(f"EXACT {s.addr:08x} {s.size:08x} {s.typ} {s.name}")
    for s in related[:80]:
        print(f"RELATED {s.addr:08x} {s.size:08x} {s.typ} {s.name}")
    if len(related) > 80:
        print(f"RELATED_TRUNCATED remaining={len(related)-80}")

    print("\n--- ORIGINAL_SCRIPT_PROVENANCE ---")
    needles = (
        "startNewTrajectory",
        "addToTrajectory",
        "addPuffToTrajectory",
        "birdTrajectory",
        "recordTrajectory",
        "allowTrajectoryClearing",
    )
    script_hits = scan_exact_tree(scripts, needles)
    for needle in needles:
        hits = script_hits[needle]
        print(f"needle='{needle}' hits={len(hits)}")
        for p, off in hits[:80]:
            try:
                rel = os.path.relpath(p, scripts)
            except Exception:
                rel = p
            print(f"  {rel} offset=0x{off:x}")
        if len(hits) > 80:
            print(f"  ... +{len(hits)-80} more")

    print("\n--- ORIGINAL_IMAGE_METADATA_CANDIDATES ---")
    metadata_hits = scan_metadata_terms(image_root)
    print(f"candidateHits={len(metadata_hits)}")
    for p, off, text in metadata_hits[:500]:
        try:
            rel = os.path.relpath(p, image_root)
        except Exception:
            rel = p
        if off < 0:
            print(f"  {rel} {text}")
        else:
            safe = text.replace("\r", "\\r").replace("\n", "\\n")
            print(f"  {rel} offset=0x{off:x} text={safe}")

    # The untouched library itself may retain class/member/sprite terminology
    # that is not present in exported symbol names.
    print("\n--- ORIGINAL_LIB_TRAJECTORY_STRINGS ---")
    data = Path(lib).read_bytes()
    lib_hits: list[tuple[int, str]] = []
    for off, text in ascii_runs(data, 5):
        low = text.lower()
        if any(t in low for t in SEARCH_TERMS):
            lib_hits.append((off, text))
    print(f"stringHits={len(lib_hits)}")
    for off, text in lib_hits[:300]:
        print(f"  offset=0x{off:x} text={text}")
    if len(lib_hits) > 300:
        print(f"  STRING_TRUNCATED remaining={len(lib_hits)-300}")

    # Prefer the three direct GameLua methods, then any related owners.  The
    # bodies are bounded so diagnostics remain uploadable.
    disasm = exact + related
    uniq: list[Sym] = []
    seen.clear()
    for s in disasm:
        key = (s.addr, s.name)
        if key not in seen:
            seen.add(key)
            uniq.append(s)
    uniq = uniq[:28]
    print(f"\n--- ARMV7_DISASSEMBLY targets={len(uniq)} ---")
    for s in uniq:
        start = s.addr & ~1
        size = s.size or 0x180
        size = min(max(size, 4), 0x1200)
        stop = start + size
        print(f"\n--- ARMV7_BODY name={s.name} start=0x{start:x} size=0x{size:x} stop=0x{stop:x} ---")
        drc, body = run([
            objdump,
            "-d",
            "--demangle",
            f"--start-address=0x{start:x}",
            f"--stop-address=0x{stop:x}",
            lib,
        ])
        print(f"objdumpExit={drc} lines={len(body)}")
        for line in body:
            print(line)

    print("\ninterpretationRule=do not draw, clear, space, age, cap, or select trajectory sprites until ARMv7 method bodies plus untouched Lua runtime arguments establish the contract")
    # Missing exported symbols are evidence, not a reason to kill the build;
    # registration recon + script/runtime audits still remain useful.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
