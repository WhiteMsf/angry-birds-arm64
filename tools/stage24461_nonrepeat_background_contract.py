#!/usr/bin/env python3
import sys, pathlib

if len(sys.argv) != 3:
    print('usage: stage24461_nonrepeat_background_contract.py <armv7-theme-contract> <stage24_live_surface.cpp>')
    raise SystemExit(2)
arm = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8-sig', errors='replace')
cpp = pathlib.Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')

# Exact ARMv7 GameLua::drawBackground() proof recovered in Stage24.15.1.
# Addresses are intentionally checked because this stage exists to close a
# previously fail-closed branch, not to infer behavior from Theme9 visuals.
checks = {
    'armv7_drawbackground_present': 'GameLua::drawBackground()' in arm,
    'armv7_repeat_flag_branch': all(x in arm for x in [
        '4fe38: e7d33007', '4fe3c: e3530000', '4fe40: 0affffa6',
    ]),
    'armv7_nonrepeat_entry': '4fce0:' in arm and '4fd5c:' in arm,
    'armv7_offset_truncate': all(x in arm for x in [
        '4fce0: e59d0020', '4fce8: eb03cb44', '4fcec: eb03ca1c',
        '4fcf4: e59d0020', '4fcf8: eb03c9b2',
    ]),
    'armv7_nonrepeat_camera_parallax': all(x in arm for x in [
        '4fd18: e1a00003', '4fd1c: e59d101c', '4fd24: eb03ca39',
        '4fd2c: e59d0020', '4fd30: eb03c9a5',
    ]),
    'armv7_single_draw_call': '4fd5c: eb010f2e' in arm,
    'cpp_gameplay_nonrepeat_algorithm': all(x in cpp for x in [
        'algorithm=ARMV7_DRAWBACKGROUND_NONREPEAT',
        'layer.offset - (topLeftX * layer.parallax) / layer.layerScale',
        'layer.offset - static_cast<float>(offsetInt)',
        '[stage24.46.1-scene] NONREPEAT_DRAW',
    ]),
    'cpp_menu_nonrepeat_algorithm': cpp.count('layer.offset - (topLeftX * layer.parallax) / layer.layerScale') >= 2,
    'old_gameplay_failclosed_removed': 'non-repeating background not reconstructed' not in cpp,
    'old_menu_failclosed_removed': 'non-repeating background still unsupported' not in cpp,
    'repeat_branch_retained': 'ARMV7_DRAWBACKGROUND_REPEAT' in cpp,
    'theme9_still_generic': 'stage24153_parse_theme_scene' in cpp and 'theme9_scene_not_hardcoded' not in cpp,
}

print('ANGRY_STAGE24_46_1_NONREPEAT_BACKGROUND_CONTRACT 1')
print('source=ARMV7_GameLua_drawBackground_0x4fc58_0x4ffbc')
print('nonrepeat=offset-truncation + camera-parallax/layerScale + one drawSprite')
for k,v in checks.items():
    print(f'{k}={"PASS" if v else "FAIL"}')
print('verdict=' + ('PASS' if all(checks.values()) else 'FAIL'))
raise SystemExit(0 if all(checks.values()) else 1)
