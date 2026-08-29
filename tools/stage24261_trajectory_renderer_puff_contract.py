#!/usr/bin/env python3
"""Stage 24.26.1: original native trajectory renderer + puff contract audit.

Read-only.  This pass deliberately does not implement trajectory rendering on
ARM64.  It searches the untouched ARMv7 binary for consumers of the recovered
trajectory/puff storage layout, correlates them with GameLua::drawGame(), and
maps all retained trail resources / puff-specialty evidence from the user's
original 1.4.2 data tree.
"""
from __future__ import annotations

import os
import re
import struct
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

HEADER = "ANGRY_STAGE24_26_1_TRAJECTORY_RENDERER_PUFF_CONTRACT 1"
TRAIL_RX = re.compile(r"(?i)(TRAIL_(?:WHITE|BLACK|FLOWER)_[123]|TUTORIAL_TRAIL_[123])")
SPECIAL_RX = re.compile(r"(?i)(BIRD_[A-Z0-9_]*SPECIAL|birdSpecialty|addPuffToTrajectory)")
RENDER_RX = re.compile(
    r"(?i)(GameLua::drawGame|draw|render|Sprite|Image::render|MaskedImage|"
    r"Particles::draw|Resources|texture|trail|trajectory)"
)

# Layout recovered in Stage 24.26.0.  Include Array internals as well as the
# GameLua bank selector because the consumer may address either the Array base
# or its data/size/capacity members directly.
FIELD_PATTERNS = (
    # Require ARM immediate syntax (#...) so absolute branch/comment addresses
    # such as "# 0x200 <symbol>" do not masquerade as GameLua member access.
    ("trajectoryArrayBase", (r"#436\b", r"#0x1b4\b")),
    ("trajectoryArraySize", (r"#440\b", r"#0x1b8\b")),
    ("trajectoryArrayCapacity", (r"#444\b", r"#0x1bc\b")),
    ("puffArrayBase", (r"#508\b", r"#0x1fc\b")),
    ("puffArraySize", (r"#512\b", r"#0x200\b")),
    ("puffArrayCapacity", (r"#516\b", r"#0x204\b")),
    ("currentTrajectoryBank", (r"#580\b", r"#0x244\b")),
)
FIELD_RX = [(name, [re.compile(p, re.I) for p in pats]) for name, pats in FIELD_PATTERNS]


@dataclass
class Sym:
    addr: int
    size: int
    typ: str
    name: str


@dataclass
class Block:
    start_line: int
    end_line: int
    addr: int
    name: str
    lines: list[str]


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


def parse_nm(lines: Iterable[str]) -> list[Sym]:
    out: list[Sym] = []
    rx = re.compile(r"^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+(\S)\s+(.+?)\s*$")
    for ln in lines:
        m = rx.match(ln)
        if m:
            out.append(Sym(int(m.group(1), 16), int(m.group(2), 16), m.group(3), m.group(4)))
    return out


def function_blocks(lines: list[str]) -> list[Block]:
    # llvm-objdump symbol headers normally use this exact form.
    hdr = re.compile(r"^\s*([0-9A-Fa-f]+)\s+<(.+)>:\s*$")
    hs: list[tuple[int, int, str]] = []
    for i, ln in enumerate(lines):
        m = hdr.match(ln)
        if m:
            hs.append((i, int(m.group(1), 16), m.group(2)))
    out: list[Block] = []
    for j, (i, addr, name) in enumerate(hs):
        end = hs[j + 1][0] if j + 1 < len(hs) else len(lines)
        out.append(Block(i, end, addr, name, lines[i:end]))
    return out


def printable_strings(data: bytes, min_len: int = 4):
    rx = re.compile(rb"[\x20-\x7e]{%d,}" % min_len)
    for m in rx.finditer(data):
        yield m.start(), m.group().decode("ascii", "replace")


def elf32_fileoff_to_vaddr(data: bytes, file_off: int) -> int | None:
    # Original libangrybirds.so is ELF32 little-endian ARM.  Keep this helper
    # self-contained so the audit has no pyelftools dependency on Windows.
    if len(data) < 52 or data[:4] != b"\x7fELF" or data[4] != 1 or data[5] != 1:
        return None
    try:
        e_phoff = struct.unpack_from("<I", data, 28)[0]
        e_phentsize = struct.unpack_from("<H", data, 42)[0]
        e_phnum = struct.unpack_from("<H", data, 44)[0]
    except struct.error:
        return None
    if e_phentsize < 32:
        return None
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        if off + 32 > len(data):
            break
        p_type, p_offset, p_vaddr, _p_paddr, p_filesz, _p_memsz, _flags, _align = struct.unpack_from(
            "<IIIIIIII", data, off
        )
        if p_type == 1 and p_offset <= file_off < p_offset + p_filesz:
            return p_vaddr + (file_off - p_offset)
    return None


def field_hits(block: Block) -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}
    for i, ln in enumerate(block.lines):
        for name, regs in FIELD_RX:
            if any(rx.search(ln) for rx in regs):
                out.setdefault(name, []).append(i)
    return out


def emit_hit_context(block: Block, hits: dict[str, list[int]], radius: int = 12) -> None:
    interesting = sorted({i for vals in hits.values() for i in vals})
    if not interesting:
        return
    ranges: list[tuple[int, int]] = []
    for i in interesting:
        lo, hi = max(0, i - radius), min(len(block.lines), i + radius + 1)
        if ranges and lo <= ranges[-1][1]:
            ranges[-1] = (ranges[-1][0], max(ranges[-1][1], hi))
        else:
            ranges.append((lo, hi))
    for ri, (lo, hi) in enumerate(ranges):
        print(f"  CONTEXT[{ri}] localLines={lo}..{hi-1}")
        for ln in block.lines[lo:hi]:
            print(ln)


def pointer_word_offsets(data: bytes, value: int) -> list[int]:
    if value < 0 or value > 0xFFFFFFFF:
        return []
    needle = struct.pack("<I", value)
    out: list[int] = []
    pos = 0
    while True:
        i = data.find(needle, pos)
        if i < 0:
            break
        out.append(i)
        pos = i + 1
        if len(out) >= 128:
            break
    return out


def main() -> int:
    if len(sys.argv) != 6:
        print(
            "usage: stage24261_trajectory_renderer_puff_contract.py "
            "<llvm-nm> <llvm-objdump> <libangrybirds.so> <scripts-dir> <image-root>",
            file=sys.stderr,
        )
        return 2

    nm, objdump, lib, scripts, image_root = sys.argv[1:]
    print(HEADER)
    print("policy=DIAGNOSTIC_ONLY; ARM64 trajectory/puff rendering remains headless")
    print("inherits=Stage24.26.0 recovered 3 slots x 2 banks, trajectory arrays at +0x1b4 family, puff arrays at +0x1fc family, bank selector +0x244")
    print("questions=exact native consumers; draw order; simultaneous-bank policy; sprite/resource selection; puff specialties; fade/scale/alpha/transform ownership")
    print(f"lib={lib}")
    print(f"scripts={scripts}")
    print(f"imageRoot={image_root}")
    for p in (nm, objdump, lib):
        if not os.path.exists(p):
            print(f"ERROR missing={p}")
            return 3

    rc, nm_lines = run([nm, "-S", "-C", lib])
    if rc != 0 or not nm_lines:
        rc, nm_lines = run([nm, "-D", "-S", "-C", lib])
    syms = parse_nm(nm_lines)
    print(f"nmExit={rc} parsedSymbols={len(syms)}")

    related = [s for s in syms if s.typ in "TtWw" and RENDER_RX.search(s.name)]
    print(f"\n--- RENDER_RELATED_SYMBOLS count={len(related)} capped=500 ---")
    for s in related[:500]:
        print(f"{s.addr:08x} {s.size:08x} {s.typ} {s.name}")

    # Full disassembly is intentionally used: prior draw-order work proved that
    # the ELF symbol size can truncate the real GameLua::drawGame tail.
    drc, dis = run([objdump, "-d", "--demangle", lib])
    print(f"\n--- FULL_TEXT_DISASSEMBLY status={drc} lines={len(dis)} ---")
    if drc != 0 or not dis:
        print("ERROR full disassembly unavailable")
        return 4
    blocks = function_blocks(dis)
    print(f"functionBlocks={len(blocks)}")

    draw = next((b for b in blocks if b.name == "GameLua::drawGame()"), None)
    if not draw:
        draw = next((b for b in blocks if "GameLua::drawGame()" in b.name), None)
    print("\n--- DRAWGAME_FULL_BODY ---")
    if draw:
        print(f"start=0x{draw.addr:x} bodyLines={len(draw.lines)} name={draw.name}")
        for ln in draw.lines:
            print(ln)
        calls = [(i, ln) for i, ln in enumerate(draw.lines) if re.search(r"\bblx?\b", ln)]
        print(f"\n--- DRAWGAME_CALL_SEQUENCE calls={len(calls)} ---")
        for k, (i, ln) in enumerate(calls):
            print(f"CALL[{k:03d}] localLine={i:04d} {ln}")
        dh = field_hits(draw)
        print(f"\n--- DRAWGAME_TRAJECTORY_FIELD_HITS kinds={len(dh)} ---")
        for name, vals in dh.items():
            print(f"{name} hits={len(vals)} localLines={','.join(str(x) for x in vals)}")
        emit_hit_context(draw, dh, 18)
    else:
        print("drawGame=NOT_FOUND")

    candidates: list[tuple[int, Block, dict[str, list[int]]]] = []
    for b in blocks:
        hits = field_hits(b)
        if not hits:
            continue
        # A lone common immediate such as 512 is weak evidence.  Require a
        # recovered family base/bank field or at least two distinct layout
        # fields in the same function.
        strong = any(k in hits for k in ("trajectoryArrayBase", "puffArrayBase", "currentTrajectoryBank"))
        if not strong and len(hits) < 2:
            continue
        raw_count = sum(len(v) for v in hits.values())
        score = raw_count * 10
        if RENDER_RX.search(b.name):
            score += 80
        if "GameLua::drawGame" in b.name:
            score += 200
        # Storage writers are expected evidence, but rank consumers above them.
        if "addToTrajectory" in b.name or "addPuffToTrajectory" in b.name or "startNewTrajectory" in b.name:
            score -= 40
        candidates.append((score, b, hits))
    candidates.sort(key=lambda x: (-x[0], x[1].addr))

    print(f"\n--- WHO_TOUCHES_RECOVERED_TRAJECTORY_LAYOUT candidates={len(candidates)} capped=80 ---")
    for idx, (score, b, hits) in enumerate(candidates[:80]):
        summary = ",".join(f"{k}:{len(v)}" for k, v in hits.items())
        print(f"\nCANDIDATE[{idx}] score={score} addr=0x{b.addr:x} name={b.name} bodyLines={len(b.lines)} fields={summary}")
        emit_hit_context(b, hits, 14)

    data = Path(lib).read_bytes()
    trail_strings = [(off, s) for off, s in printable_strings(data, 5) if TRAIL_RX.search(s)]
    print(f"\n--- ARMV7_TRAIL_STRINGS count={len(trail_strings)} ---")
    trail_addresses: list[tuple[str, int, int | None]] = []
    for off, text in trail_strings:
        va = elf32_fileoff_to_vaddr(data, off)
        trail_addresses.append((text, off, va))
        print(f"fileOff=0x{off:x} vaddr={'NA' if va is None else f'0x{va:x}'} text={text}")
        if va is not None:
            refs = pointer_word_offsets(data, va)
            print(f"  exactPointerWords={len(refs)}")
            for roff in refs[:32]:
                rva = elf32_fileoff_to_vaddr(data, roff)
                print(f"    pointerFileOff=0x{roff:x} pointerVaddr={'NA' if rva is None else f'0x{rva:x}'}")

    # Search objdump text for direct mentions of string VAs or exact pointer-slot
    # VAs. This is opportunistic evidence; position-independent GOT indirection
    # can legitimately leave this section empty.
    search_addrs: set[int] = set()
    for _text, _off, va in trail_addresses:
        if va is None:
            continue
        search_addrs.add(va)
        for roff in pointer_word_offsets(data, va):
            rva = elf32_fileoff_to_vaddr(data, roff)
            if rva is not None:
                search_addrs.add(rva)
    print(f"\n--- DISASSEMBLY_TRAIL_ADDRESS_MENTIONS addresses={len(search_addrs)} ---")
    mention_count = 0
    for i, ln in enumerate(dis):
        low = ln.lower()
        matched = [a for a in search_addrs if f"0x{a:x}" in low or re.search(rf"\b{a:x}\b", low)]
        if not matched:
            continue
        mention_count += 1
        print(f"\nMENTION[{mention_count}] addrs={','.join(f'0x{x:x}' for x in sorted(matched))} disLine={i}")
        for x in dis[max(0, i - 10):min(len(dis), i + 12)]:
            print(x)
        if mention_count >= 80:
            break
    print(f"addressMentionContexts={mention_count}")

    # Exact asset metadata around all TRAIL_* entries.  Neighbouring strings in
    # the DAT frequently reveal sheet/resource grouping without guessing pixels.
    root = Path(image_root)
    print("\n--- ORIGINAL_TRAIL_ASSET_METADATA ---")
    meta_files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in (".dat", ".txt", ".xml", ".lua")]
    meta_hit_files = 0
    for p in meta_files:
        try:
            raw = p.read_bytes()
        except OSError:
            continue
        alls = list(printable_strings(raw, 4))
        hit_idx = [i for i, (_off, s) in enumerate(alls) if TRAIL_RX.search(s)]
        if not hit_idx:
            continue
        meta_hit_files += 1
        try:
            rel = p.relative_to(root)
        except Exception:
            rel = p
        print(f"\nMETA file={rel} bytes={len(raw)} hits={len(hit_idx)}")
        shown: set[int] = set()
        for hi in hit_idx:
            for j in range(max(0, hi - 5), min(len(alls), hi + 6)):
                if j in shown:
                    continue
                shown.add(j)
                off, text = alls[j]
                print(f"  STR 0x{off:06x} {text}")
    print(f"metadataFilesWithTrailHits={meta_hit_files}")

    print("\n--- ORIGINAL_SCRIPT_PUFF_SPECIALTY_STRINGS ---")
    script_root = Path(scripts)
    special_hits = 0
    if script_root.is_dir():
        for p in script_root.rglob("*"):
            if not p.is_file():
                continue
            try:
                raw = p.read_bytes()
            except OSError:
                continue
            alls = list(printable_strings(raw, 4))
            idxs = [i for i, (_off, text) in enumerate(alls) if SPECIAL_RX.search(text)]
            if not idxs:
                continue
            special_hits += len(idxs)
            try:
                rel = p.relative_to(script_root)
            except Exception:
                rel = p
            print(f"\nSCRIPT file={rel} matchingStrings={len(idxs)}")
            shown: set[int] = set()
            for hi in idxs:
                for j in range(max(0, hi - 6), min(len(alls), hi + 7)):
                    if j in shown:
                        continue
                    shown.add(j)
                    off, text = alls[j]
                    print(f"  STR 0x{off:08x} {text}")
    print(f"scriptSpecialtyStringHits={special_hits}")

    print("\n--- AUDIT_CONCLUSION_GUARD ---")
    print("implementationDecision=DEFERRED_UNTIL_REPORT_REVIEW")
    print("requiredEvidence=identify actual readers of both recovered buffer families; establish drawGame/callee placement; establish exact trail resource selection; decode puff-specialty callsites")
    print("nonGoal=no ARM64 dot/puff storage or rendering is introduced by this stage")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
