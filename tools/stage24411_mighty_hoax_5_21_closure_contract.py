#!/usr/bin/env python3
"""Stage 24.41.1: Mighty Hoax Pack5 page-2 closure through 5-21."""
from pathlib import Path
import sys
if len(sys.argv) != 3:
    print('usage: stage24411_mighty_hoax_5_21_closure_contract.py <build.ps1> <stage24_live_surface.cpp>')
    raise SystemExit(2)
build=Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace')
cpp=Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')
remaining=[
('5-11','LevelP2_86'),('5-12','LevelP2_74'),('5-13','LevelP2_115'),('5-14','LevelP2_98'),('5-15','LevelP2_71'),
('5-16','LevelP2_72'),('5-17','LevelP2_87'),('5-18','LevelP2_93'),('5-19','LevelP2_67'),('5-20','LevelP2_97'),('5-21','LevelP2_90')]
full=['LevelP2_78','LevelP2_100','LevelP2_92','LevelP2_94','LevelP2_89','LevelP2_73','LevelP2_76','LevelP2_122','LevelP2_99','LevelP2_84']+[x for _,x in remaining]
checks={}
for human,phys in remaining:
    checks[f'transport_{human}']=(f"levels\\pack5\\{phys}.lua" in build and
                                  f"Copy-Item $level{phys.replace('Level','')}p5" in build and
                                  f'{{"stage24/data/levels/pack5/{phys}.lua", "data/levels/pack5/{phys}.lua"}}' in cpp)
checks.update({
 'full_map_observer':'stage24411_dump_pack5_map' in cpp and '[stage24.41.1-mighty] MAP_SUMMARY' in cpp,
 'map_range':'levelIndex >= 22 && levelIndex <= 42' in cpp,
 'page_range':'pageLevelIndex >= 1 && pageLevelIndex <= 21' in cpp,
 'folder':'data/levels/pack5/' in cpp,
 'context':'themeIndex != 5 || worldNumber != 5 || pageIndex != 2' in cpp,
 'exact_sequence':(','.join(full)) in cpp,
 'next_chain':'stage24.41.1-mighty-5-21-closure-chain' in cpp,
 'final_probe':'"LevelP2_90"' in cpp,
 'no_forced_theme5_complete':'theme5Completed = true' not in cpp and 'theme5Completed=true' not in cpp,
 'no_forced_5_22':'LevelP2_90", "LevelP2_' not in cpp.split('stage24411Mighty521ClosureChain',1)[-1][:1200],
 'no_level_specific_branch':'if (LevelP2_90' not in cpp and 'if (LevelP2_86' not in cpp,
})
failed=[k for k,v in checks.items() if not v]
print('ANGRY_STAGE24_41_1_MIGHTY_HOAX_5_21_CLOSURE_CONTRACT 1')
print('map=' + ','.join(f'{h}:{p}' for h,p in remaining))
print('full_sequence=' + ','.join(full))
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
print('verdict=' + ('PASS' if not failed else 'FAIL'))
if failed:
    print('failed=' + ','.join(failed))
    raise SystemExit(3)
