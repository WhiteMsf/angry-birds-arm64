from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'stage24_live_surface.cpp')
s=p.read_text(errors='replace')
checks={
 'registry_guard': 'createSpriteSheet: sprite registry unavailable' in s,
 'pre_gpu_reuse_marker': 'stage24.30.2-pre-gpu-reuse' in s,
 'gpu_gate_after_reuse': s.find('stage24.30.2-pre-gpu-reuse') < s.find('createSpriteSheet: dynamic GPU bridge unavailable'),
 'dynamic_gpu_fail_closed': 'createSpriteSheet: dynamic GPU bridge unavailable' in s,
}
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()): raise SystemExit(1)
print('verdict=PASS_PRE_GPU_RESIDENT_REUSE_ONLY')
