#!/usr/bin/env python3
"""Static contract for the original loading-page draw path."""

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "stage24_live_surface.cpp"
text = SOURCE.read_text(encoding="utf-8")
failures: list[str] = []


def require(name: str, condition: bool) -> None:
    print(f"{name}={'PASS' if condition else 'FAIL'}")
    if not condition:
        failures.append(name)


def section(start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    end = text.find(end_marker, start + len(start_marker)) if start >= 0 else -1
    if start < 0 or end < 0:
        return ""
    return text[start:end]


loading_mode = section(
    "static bool stage24IsLoadingMode(",
    "static ",
)
renderer = section(
    "bool renderSnapshot(",
    "bool windowToLogical(",
)
renderer_compact = re.sub(r"\s+", "", renderer)
menu_ownership = section(
    "const bool stage24284FullFrameMenu =",
    "const bool stage24283MenuOwned =",
)
caller = text[text.find("gpuScene.renderSnapshot(") :]
caller_compact = re.sub(r"\s+", "", caller)

require(
    "recognizes_updateLoading_and_updateLoadingEx",
    '"updateLoading"' in loading_mode and '"updateLoadingEx"' in loading_mode,
)
require(
    "renderer_receives_pre_update_mode",
    "const std::string& stage24PreUpdateMode" in renderer,
)
require(
    "loading_frame_uses_pre_and_post_modes",
    "stage24IsLoadingMode(stage24PreUpdateMode)" in renderer
    and "stage24IsLoadingMode(stage24283Mode)" in renderer,
)
require(
    "loading_frame_bypasses_menu_owned_early_return",
    "!stage24283LoadingFrame" in menu_ownership,
)
require(
    "main_loop_passes_pre_update_mode",
    "gpuScene.renderSnapshot(frame,L,physics,sprites,stage24133PreUpdateMode)"
    in caller_compact,
)
clear_at = renderer.find("glClear(GL_COLOR_BUFFER_BIT)")
draw_at = renderer.find('lua_getglobal(L, "__stage24_original_drawMenu")')
require(
    "original_drawMenu_runs_after_frame_clear",
    clear_at >= 0 and draw_at > clear_at,
)
require(
    "loading_draw_uses_original_closure",
    "stage24283LoadingFrame" in renderer_compact
    and "||stage24283LoadingFrame" in renderer_compact
    and '"__stage24_original_drawMenu"' in renderer_compact,
)
require(
    "loading_flag_is_temporarily_enabled_and_restored",
    'lua_getglobal(L, "loading")' in renderer
    and "lua_pushboolean(L, 1)" in renderer
    and 'lua_setglobal(L, "loading")' in renderer
    and "lua_pushvalue(L, stage24283SavedLoading)" in renderer,
)

if failures:
    print("VERDICT=FAIL missing=" + ",".join(failures))
    sys.exit(1)

print("VERDICT=PASS original_loading_page_render_contract")
