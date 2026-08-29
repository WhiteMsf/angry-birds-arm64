#!/usr/bin/env python3
"""Stage 24.43.1: original type=1 distance-joint reconstruction contract."""
from pathlib import Path
import sys


def sl(text, a, b):
    i=text.find(a)
    if i < 0: return ''
    j=text.find(b, i+len(a))
    return text[i:] if j < 0 else text[i:j]


def main():
    if len(sys.argv) != 4:
        print('usage: stage24431_distance_joint_contract.py <cpp> <build_ps1> <stage24430_report>')
        return 2
    cpp=Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace')
    build=Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')
    arm=Path(sys.argv[3]).read_text(encoding='utf-8', errors='replace')

    impl=sl(cpp, 'void eraseJointRecordsForBodyAfterDestroy24431', 'static int l_stage24431_createJoint')
    lua=sl(cpp, 'static void stage24431StoreJointLuaMetadata', '// High-value physics/lifecycle debt')
    bounds=sl(cpp, 'static int l_stage24430_setLevelLimitsAudit', 'static int l_createBox')

    checks={}
    checks['armv7_discovery_pass']=('verdict=PASS' in arm and 'GameLua::createJointLua' in arm and 'GameLua::destroyJointLua' in arm)
    checks['armv7_create_destroy_owners']=('b2World::CreateJoint' in arm and 'b2World::DestroyJoint' in arm)
    checks['armv7_distance_type_literal']=('5ee6c:' in arm and 'mov\tr12, #3' in arm)
    checks['armv7_coord_branches']=all(x in arm for x in ('5f1bc:', '5f2ec:', '5f484:', '5ef0c:'))
    checks['distance_definition']=all(x in impl for x in (
        'b2DistanceJointDef def;', 'def.bodyA = bodyA;', 'def.bodyB = bodyB;',
        'def.collideConnected = false;', 'def.frequencyHz = 4.0f;',
        'def.dampingRatio = 0.5f;', 'world.CreateJoint(&def)'))
    checks['coord0_exact']=all(x in impl for x in (
        'if (coordType == 0)', 'def.localAnchorA.Set(0.0f, 0.0f);',
        'worldA = bodyA->GetPosition();', 'worldB = bodyB->GetPosition();'))
    checks['coord1_exact']=all(x in impl for x in (
        '} else if (coordType == 1)', 'x1 - pA.x', 'y1 - pA.y',
        'x2 - pB.x', 'y2 - pB.y'))
    checks['coord2_exact']=all(x in impl for x in (
        '} else if (coordType == 2)', 'def.localAnchorA.Set(x1, y1);',
        'def.localAnchorB.Set(x2, y2);', 'bodyA->GetWorldPoint(def.localAnchorA)',
        'bodyB->GetWorldPoint(def.localAnchorB)'))
    checks['unknown_coord_default']=('def.length = 1.0f;' in impl and 'coordType >= 0 && coordType <= 2' in impl)
    checks['destroy_by_name']=('destroyJoint24431' in impl and 'world.DestroyJoint(it->second.joint)' in impl and 'joints24431.erase(it)' in impl)
    checks['body_destroy_record_hygiene']=('eraseJointRecordsForBodyAfterDestroy24431' in cpp and cpp.count('eraseJointRecordsForBodyAfterDestroy24431') >= 5)
    checks['lua_metadata_exact_keys']=all(('"'+k+'"') in lua for k in ('objects','joints','name','end1','end2','type','coordType','x1','y1','x2','y2'))
    checks['coord_rounding']=('std::floor(raw + 0.5f)' in lua)
    checks['type1_gate']=('if (gPhysics && type == 1.0f)' in lua and 'ORIGINAL_ARMV7_NO_CREATEJOINT_BRANCH' in lua)
    checks['bindings']=all(x in cpp for x in (
        'setfn(L, "createJoint", l_stage24431_createJoint);',
        'setfn(L, "destroyJoint", l_stage24431_destroyJoint);'))
    checks['telemetry_retained']=all(x in cpp for x in (
        '[stage24.43.0-joint]', 'BODY_MATCH arg=', '[stage24.43.1-joint]',
        'CREATE_DISTANCE', 'frequencyHz=4.000000', 'dampingRatio=0.500000'))
    limit_probe=sl(cpp, 'static int l_stage24430_setLevelLimitsAudit', 'static int l_stage24430_setMaxTranslationAudit')
    game_probe=sl(cpp, 'static int l_stage24430_setGameOnAudit', '// Stage 24.44.0: passive live witness')
    # Historical Stage24.43.1 required both probes to be observe-only. Later
    # Stage24.44.3 may close setGameOn as the proven original Android no-op;
    # accept that closure while still forbidding physics/lifecycle synthesis.
    checks['level_limits_gameon_nonmutating']=bool(limit_probe and game_probe) and (
        'action=OBSERVE_ONLY' in limit_probe and
        ('action=OBSERVE_ONLY' in game_probe or 'action=ORIGINAL_ANDROID_NOOP' in game_probe)
    ) and not any(x in (limit_probe+game_probe) for x in (
        'SetLinearVelocity(', 'SetAngularVelocity(', 'SetTransform(', 'SetGravity(',
        'ApplyForce(', 'ApplyImpulse(', 'CreateJoint(', 'DestroyJoint(',
        'ANativeActivity_setWindowFlags', 'AWINDOW_FLAG_KEEP_SCREEN_ON'))
    forbidden=('LevelP3_231','LevelP2_86','SmallPiglette','HelmetPiglette','StaticBalloon')
    checks['no_level_or_object_hack']=not any(x in (impl+lua) for x in forbidden)
    checks['build_gate']=('stage24431_distance_joint_contract.py' in build and 'stage24.43.1-distance-joint-contract.txt' in build)

    print('ANGRY_STAGE24_43_1_DISTANCE_JOINT_CONTRACT 1')
    print('ownership=ARMv7 GameLua::createJointLua type=1 -> b2DistanceJointDef; destroyJointLua -> b2World::DestroyJoint by name')
    print('liveEvidence=Danger Above 6-15 issued nine argc=9 type=1 coordType=2 joints between pig bodies and static balloon bodies; discovery build created none')
    print('constants=Box2D joint type 3; frequencyHz=4.0; dampingRatio=0.5; collideConnected=false')
    for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
    failed=[k for k,v in checks.items() if not v]
    print('verdict=' + ('PASS' if not failed else 'FAIL'))
    if failed:
        print('failed=' + ','.join(failed))
        return 5
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
