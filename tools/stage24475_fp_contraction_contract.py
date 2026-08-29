#!/usr/bin/env python3
import pathlib,sys
if len(sys.argv)!=6:
    print('usage: stage24475_fp_contraction_contract.py <cmake> <build.ps1> <cpp> <test.ps1> <binary-audit.py>')
    raise SystemExit(2)
cm=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8-sig',errors='replace')
build=pathlib.Path(sys.argv[2]).read_text(encoding='utf-8-sig',errors='replace')
cpp=pathlib.Path(sys.argv[3]).read_text(encoding='utf-8-sig',errors='replace')
test=pathlib.Path(sys.argv[4]).read_text(encoding='utf-8-sig',errors='replace')
audit=pathlib.Path(sys.argv[5]).read_text(encoding='utf-8-sig',errors='replace')
print('ANGRY_STAGE24_47_5_FP_CONTRACTION_CONTRACT 1')
print('policy=generic numerical-fidelity compiler policy + observe-only order witness')
checks=[]
def gate(n,v): checks.append((n,bool(v))); print(f'{n}={"PASS" if v else "FAIL"}')
gate('box2d_ffp_contract_off','target_compile_options(box2d212 PRIVATE' in cm and '-ffp-contract=off' in cm)
gate('live_bridge_ffp_contract_off','target_compile_options(stage24_live_surface PRIVATE -ffp-contract=off)' in cm)
gate('binary_audit_wired','stage24475_fp_contraction_binary_audit.py' in build and 'stage24.47.5-fp-contraction-binary-audit.txt' in build)
gate('binary_audit_checks_fused_ops',all(x in audit for x in ('fmadd','fmsub','fnmadd','fnmsub')))
gate('runtime_level_reset','[stage24.47.5-fp] LEVEL_RESET' in cpp and 'budgetReset=OBSERVER_ONLY' in cpp)
gate('runtime_world_joint_order','[stage24.47.5-order] WORLD_JOINT_LIST' in cpp and 'WORLD_LIST_ORDER_NOT_ASSUMED_EQUAL_TO_ISLAND_DFS_SOLVER_ORDER' in cpp)
gate('runtime_order_items','[stage24.47.5-order] ITEM' in cpp)
gate('test_ge3','LevelGE_3' in test)
gate('test_8_3','LevelP3_306' in test and '8-3' in test)
gate('stage474_retained','stage24474_rubber_warmstart_integration_contract.py' in build)
# Observer block must not mutate physics.
start=cpp.find('void observeFpAndJointOrder24475')
end=cpp.find('void sampleDistanceJointSpringsBefore24472',start)
block=cpp[start:end] if start>=0 and end>start else ''
mutators=('SetLinearVelocity(','SetAngularVelocity(','ApplyImpulse(','ApplyForce(','SetRestitution(','SetFriction(','CreateJoint(','DestroyJoint(','SetTransform(','SetWarmStarting(')
gate('observer_no_physics_mutators',bool(block) and not any(x in block for x in mutators))
gate('no_level_specific_physics_branch','LevelGE_3' not in block and 'LevelP3_306' not in block)
ok=all(v for _,v in checks)
print('verdict='+('PASS' if ok else 'FAIL'))
raise SystemExit(0 if ok else 1)
