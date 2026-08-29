#!/usr/bin/env python3
"""Stage 24.28.0: giant original menu/UI/navigation surface contract audit.

Diagnostic only. Inventories the untouched ARMv7 native menu/platform boundary,
the user's original Lua/level corpus, menu image metadata, and localization keys.
It intentionally does not infer or implement behavior from filenames alone.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict

HEADER = "ANGRY_STAGE24_28_0_MENU_UI_NATIVE_CORPUS_CONTRACT 1"

TERMS = (
    "menu", "page", "popup", "episode", "levelselection", "level selection",
    "levelcomplete", "level complete", "levelfailed", "level failed", "pause",
    "settings", "options", "credits", "about", "golden", "egg", "tutorial",
    "cutscene", "cut scene", "cinematic", "movie", "video", "story", "comic",
    "playvideo", "releasecutscenes", "intro", "startup", "splash", "loading",
    "achievement", "leaderboard", "crystal", "gamecenter", "advertisement",
    "save", "highscore", "stars", "unlock", "nextlevel", "replay", "retry",
    "gotomenu", "gotolevelselection", "handlegamemodechange", "drawmenu",
    "preparemenupage", "updatemenu", "createmenupages", "initializemenu",
)

EXACT_NATIVE = (
    "playVideo", "releaseCutScenes", "showCrystalSplash", "isCrystalSplashShowing",
    "activateCrystalUI", "deactivateCrystalUI", "showLeaderboards", "showAchievements",
    "showAdvertisement", "hideAdvertisement", "showVideoAdvertisement", "requestVideoAd",
    "requestAndShowVideo", "requestAd", "saveLuaFile", "checkForLuaFile", "postHighscore",
    "unlockAchievement", "requestExit", "setGameOn", "goToTaskSwitcherLua",
)

SCRIPT_NEEDLES = (
    "initializeMenu", "createMenuPages", "prepareMenuPage", "updateMenu", "drawMenu",
    "drawMenuPage", "handleGameModeChange", "gotoLevelSelection", "levelSelectionPagesBasic",
    "levelComplete", "levelFailed", "pause", "settings", "credits", "golden",
    "playVideo", "releaseCutScenes", "cutScene", "cutscene", "cinematic", "movie",
    "intro", "story", "comic", "Level1", "saveLuaFile", "unlockAchievement",
    "showAchievements", "showLeaderboards", "Crystal", "GameCenter",
)

@dataclass
class Sym:
    addr: int
    size: int
    typ: str
    name: str


def run(args: list[str]) -> tuple[int, list[str]]:
    try:
        p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, errors="replace", check=False)
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


def rel(path: str, root: str) -> str:
    try:
        return os.path.relpath(path, root)
    except Exception:
        return path


def scan_needles(root: str, needles: tuple[str, ...]) -> dict[str, list[tuple[str, int]]]:
    out = {n: [] for n in needles}
    if not os.path.isdir(root):
        return out
    enc = [(n, n.lower().encode("utf-8")) for n in needles]
    for base, _, files in os.walk(root):
        for fn in files:
            p = os.path.join(base, fn)
            try:
                data = Path(p).read_bytes().lower()
            except OSError:
                continue
            for name, needle in enc:
                pos = 0
                while True:
                    i = data.find(needle, pos)
                    if i < 0:
                        break
                    out[name].append((p, i))
                    pos = i + max(1, len(needle))
    return out


def scan_ascii_terms(root: str, extensions: set[str] | None, cap: int = 3000):
    hits = []
    if not os.path.isdir(root):
        return hits
    for base, _, files in os.walk(root):
        for fn in sorted(files):
            p = os.path.join(base, fn)
            if extensions is not None and Path(fn).suffix.lower() not in extensions:
                continue
            try:
                data = Path(p).read_bytes()
            except OSError:
                continue
            for off, text in ascii_runs(data, 4):
                low = text.lower()
                if any(t in low for t in TERMS):
                    hits.append((p, off, text))
                    if len(hits) >= cap:
                        return hits
    return hits


def disasm_symbol(objdump: str, lib: str, s: Sym, max_lines: int = 220) -> list[str]:
    if s.size <= 0:
        return []
    start = s.addr & ~1
    stop = start + s.size
    rc, lines = run([objdump, "-d", "--demangle", f"--start-address=0x{start:x}",
                     f"--stop-address=0x{stop:x}", lib])
    if rc != 0:
        return [f"objdumpExit={rc}"] + lines[:20]
    return lines[:max_lines]


def main() -> int:
    if len(sys.argv) != 8:
        print("usage: stage24280_menu_ui_surface_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <data-root> <scripts-dir> <image-root> <localization-root>", file=sys.stderr)
        return 2
    nm, objdump, lib, data_root, scripts, image_root, localization_root = sys.argv[1:]
    levels_root = os.path.join(data_root, "levels")
    project_root = Path(__file__).resolve().parent.parent

    print(HEADER)
    print("policy=DIAGNOSTIC_ONLY; no menu/navigation/cutscene/persistence/platform behavior is implemented or changed")
    print("scope=ARMv7 native platform boundary + original scripts/levels + menu image metadata + localization + project binding frontier")
    print("explicitFutureGate=Level1 first-entry film/cutscene is inventoried here but NOT implemented in Stage24.28.0")
    print(f"lib={lib}")
    print(f"dataRoot={data_root}")
    print(f"scripts={scripts}")
    print(f"levelsRoot={levels_root}")
    print(f"imageRoot={image_root}")
    print(f"localizationRoot={localization_root}")

    for p in (nm, objdump, lib):
        if not os.path.exists(p):
            print(f"ERROR missing={p}")
            return 3

    rc, nm_lines = run([nm, "-S", "-C", lib])
    if rc != 0 or not nm_lines:
        rc, nm_lines = run([nm, "-D", "-S", "-C", lib])
    syms = parse_nm(nm_lines)
    menu_syms = []
    exact_syms = []
    for s in syms:
        if s.typ not in "TtWw":
            continue
        low = s.name.lower()
        if any(n.lower() in low for n in EXACT_NATIVE):
            exact_syms.append(s)
        if ("gamelua::" in low or "menu" in low or "crystal" in low or "video" in low or "advert" in low) and any(t.replace(" ", "") in low.replace(" ", "") for t in TERMS):
            menu_syms.append(s)
    uniq = {}
    for s in exact_syms + menu_syms:
        uniq[(s.addr, s.name)] = s
    targets = sorted(uniq.values(), key=lambda x: (x.addr, x.name))

    print("\n--- ARMV7_NATIVE_SURFACE ---")
    print(f"nmExit={rc} parsedSymbols={len(syms)} selectedSymbols={len(targets)}")
    for s in targets:
        exact = any(n.lower() in s.name.lower() for n in EXACT_NATIVE)
        print(f"{'EXACT' if exact else 'RELATED'} {s.addr:08x} {s.size:08x} {s.typ} {s.name}")

    print("\n--- ARMV7_SELECTED_DISASSEMBLY ---")
    dis_targets = [s for s in targets if any(n.lower() in s.name.lower() for n in EXACT_NATIVE)]
    # Also keep a bounded set of menu/draw/platform owners.
    for s in targets:
        low = s.name.lower()
        if any(k in low for k in ("menu", "video", "cutscene", "achievement", "leaderboard", "save")):
            if s not in dis_targets:
                dis_targets.append(s)
    for s in dis_targets[:60]:
        print(f"\n>>> {s.name} addr=0x{s.addr:x} size=0x{s.size:x}")
        for line in disasm_symbol(objdump, lib, s):
            print(line)
    if len(dis_targets) > 60:
        print(f"DISASSEMBLY_TRUNCATED remaining={len(dis_targets)-60}")

    print("\n--- PROJECT_RECON_BINDINGS_FRONTIER ---")
    tsv = project_root / "recon" / "LuaBindings_80.tsv"
    print(f"reconFile={tsv}")
    if tsv.is_file():
        rows = tsv.read_text(encoding="utf-8", errors="replace").splitlines()
        picked = [r for r in rows if any(t.replace(" ", "") in r.lower().replace(" ", "") for t in TERMS)]
        print(f"matchingRows={len(picked)}")
        for r in picked:
            print(r)
    else:
        print("reconFile=NOT_FOUND")

    print("\n--- ORIGINAL_SCRIPT_EXACT_NEEDLES ---")
    script_hits = scan_needles(scripts, SCRIPT_NEEDLES)
    for needle in SCRIPT_NEEDLES:
        hits = script_hits[needle]
        print(f"needle='{needle}' hits={len(hits)}")
        for p, off in hits[:120]:
            print(f"  {rel(p, scripts)} offset=0x{off:x}")
        if len(hits) > 120:
            print(f"  ... +{len(hits)-120} more")

    print("\n--- LEVEL_CORPUS_CUTSCENE_AND_NAVIGATION_PROVENANCE ---")
    level_needles = ("playVideo", "releaseCutScenes", "cutScene", "cutscene", "intro", "movie", "story", "comic", "Level1", "tutorial", "gotoLevelSelection", "levelComplete")
    level_hits = scan_needles(levels_root, level_needles)
    for needle in level_needles:
        hits = level_hits[needle]
        print(f"needle='{needle}' hits={len(hits)}")
        for p, off in hits[:160]:
            print(f"  {rel(p, levels_root)} offset=0x{off:x}")
        if len(hits) > 160:
            print(f"  ... +{len(hits)-160} more")

    print("\n--- ORIGINAL_SCRIPT_RELEVANT_ASCII_RUNS ---")
    shits = scan_ascii_terms(scripts, {".lua", ".dat", ".txt", ".xml", ".ini", ".cfg"}, 2400)
    print(f"asciiHits={len(shits)}")
    for p, off, text in shits:
        safe = text.replace("\r", "\\r").replace("\n", "\\n")
        print(f"  {rel(p, scripts)} offset=0x{off:x} text={safe}")

    print("\n--- MENU_IMAGE_METADATA_INVENTORY ---")
    meta_files = []
    if os.path.isdir(image_root):
        for fn in sorted(os.listdir(image_root)):
            if Path(fn).suffix.lower() != ".dat":
                continue
            low = fn.lower()
            if any(k in low for k in ("menu", "level", "background", "popup", "button", "tutorial", "golden", "egg")):
                meta_files.append(os.path.join(image_root, fn))
    print(f"candidateDatFiles={len(meta_files)}")
    for p in meta_files:
        try:
            data = Path(p).read_bytes()
        except OSError as exc:
            print(f"FILE {os.path.basename(p)} ERROR {exc}")
            continue
        strings = [(off, text) for off, text in ascii_runs(data, 4)]
        print(f"\nFILE {os.path.basename(p)} bytes={len(data)} asciiRuns={len(strings)}")
        for off, text in strings[:1200]:
            print(f"  0x{off:x} {text}")
        if len(strings) > 1200:
            print(f"  STRINGS_TRUNCATED remaining={len(strings)-1200}")

    print("\n--- LOCALIZATION_MENU_KEY_INVENTORY ---")
    lhits = scan_ascii_terms(localization_root, None, 2200)
    print(f"asciiHits={len(lhits)}")
    for p, off, text in lhits:
        safe = text.replace("\r", "\\r").replace("\n", "\\n")
        print(f"  {rel(p, localization_root)} offset=0x{off:x} text={safe}")

    print("\n--- ORIGINAL_LIB_RELEVANT_STRINGS ---")
    data = Path(lib).read_bytes()
    libhits = []
    for off, text in ascii_runs(data, 5):
        low = text.lower()
        if any(t in low for t in TERMS):
            libhits.append((off, text))
    print(f"stringHits={len(libhits)}")
    for off, text in libhits[:1500]:
        print(f"  offset=0x{off:x} text={text}")
    if len(libhits) > 1500:
        print(f"  STRING_TRUNCATED remaining={len(libhits)-1500}")

    print("\n--- AUDIT_GATES ---")
    print("gate1=inventory all original menu/page tables at runtime after untouched initializeMenu")
    print("gate2=map callback/navigation strings and current page/game-mode transitions without changing dispatch")
    print("gate3=locate Level1 first-entry film/cutscene ownership; implementation explicitly deferred")
    print("gate4=classify platform/service surfaces separately from local vanilla UI")
    print("result=PASS_STATIC_INVENTORY_GENERATED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
