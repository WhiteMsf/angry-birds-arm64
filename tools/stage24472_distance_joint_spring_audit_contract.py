#!/usr/bin/env python3
import pathlib, sys

if len(sys.argv) != 5:
    print('usage: stage24472_distance_joint_spring_audit_contract.py <build.ps1> <cpp> <test.ps1> <native-audit.py>')
    sys.exit(2)

build = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8-sig', errors='replace')
cpp = pathlib.Path(sys.argv[2]).read_text(encoding='utf-8-sig', errors='replace')
test = pathlib.Path(sys.argv[3]).read_text(encoding='utf-8-sig', errors='replace')
native = pathlib.Path(sys.argv[4]).read_text(encoding='utf-8-sig', errors='replace')

print('ANGRY_STAGE24_47_2_DISTANCE_JOINT_SPRING_AUDIT_CONTRACT 1')
print('policy=DIAGNOSTIC_ONLY; no joint/contact/body/Lua mutation')
print('reproA=LevelGE_3 rubber/super-ball distance-joint network from latest live run')
print('reproB=LevelP3_306 / Danger Above 8-3 legacy rubber mismatch')
print('goal=measure rest/current length, strain, anchor velocities and reaction force while acquiring original ARMv7 b2DistanceJoint solver bodies')

checks=[]
def gate(name, ok):
    checks.append((name, bool(ok)))
    print(f'{name}={"PASS" if ok else "FAIL"}')

gate('runtime_before_after_present', '[stage24.47.2-spring] BEFORE' in cpp and '[stage24.47.2-spring] AFTER' in cpp)
gate('rubber_joint_trigger', 'isRubberJoint24472' in cpp and '"material") == "rubber"' in cpp)
gate('pre_step_snapshot', 'sampleDistanceJointSpringsBefore24472(dt, frame);' in cpp and cpp.find('sampleDistanceJointSpringsBefore24472(dt, frame);') < cpp.find('world.Step(dt, 10, 10);'))
gate('post_step_snapshot', 'sampleDistanceJointSpringsAfter24472(dt, frame);' in cpp and cpp.find('sampleDistanceJointSpringsAfter24472(dt, frame);') > cpp.find('world.Step(dt, 10, 10);'))
gate('strain_observed', 'restLength' in cpp and 'currentLength' in cpp and 'deltaStrain' in cpp)
gate('reaction_force_observed', 'GetReactionForce(1.0f / dt)' in cpp and 'reactionForceMag' in cpp)
gate('frequency_damping_observed', 'GetFrequency()' in cpp and 'GetDampingRatio()' in cpp)
gate('native_solver_audit_wired', 'stage24472_distance_joint_solver_native_audit.py' in build and 'stage24.47.2-distance-joint-solver-native-audit.txt' in build)
gate('native_targets_all_three_solver_methods', all(x in native for x in ('InitVelocityConstraints', 'SolveVelocityConstraints', 'SolvePositionConstraints')))
gate('cross_repro_levelge3', 'LevelGE_3' in test)
gate('cross_repro_8_3', 'LevelP3_306' in test and '8-3' in test)
gate('distance_joint_reconstruction_retained', 'stage24431_distance_joint_contract.py' in build)
gate('rubber_contact_audit_retained', 'stage24471_rubber_physics_audit_contract.py' in build)
gate('fixed_step_retained', 'world.Step(dt, 10, 10);' in cpp)

start=cpp.find('bool isRubberJoint24472')
end=cpp.find('void BeginContact(', start)
block=cpp[start:end] if start >= 0 and end > start else ''
mutators=(
    'SetLength(', 'SetFrequency(', 'SetDampingRatio(', 'SetLinearVelocity(',
    'SetAngularVelocity(', 'SetTransform(', 'ApplyForce(', 'ApplyImpulse(',
    'CreateJoint(', 'DestroyJoint(', 'SetRestitution(', 'SetFriction('
)
gate('spring_observer_no_physics_mutators', bool(block) and not any(m in block for m in mutators))
gate('no_level_specific_physics_branch', 'LevelGE_3' not in block and 'LevelP3_306' not in block and 'ExtraTrampoline' not in block)

ok=all(v for _,v in checks)
print('verdict=' + ('PASS' if ok else 'FAIL'))
sys.exit(0 if ok else 1)
