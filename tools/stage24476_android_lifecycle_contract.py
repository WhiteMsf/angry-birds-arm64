#!/usr/bin/env python3
import pathlib,sys
if len(sys.argv)!=6:
    print('usage: stage24476_android_lifecycle_contract.py <cpp> <build.ps1> <pull.ps1> <test.ps1> <native-audit.py>')
    raise SystemExit(2)
cpp=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8-sig',errors='replace')
build=pathlib.Path(sys.argv[2]).read_text(encoding='utf-8-sig',errors='replace')
pull=pathlib.Path(sys.argv[3]).read_text(encoding='utf-8-sig',errors='replace')
test=pathlib.Path(sys.argv[4]).read_text(encoding='utf-8-sig',errors='replace')
audit=pathlib.Path(sys.argv[5]).read_text(encoding='utf-8-sig',errors='replace')
print('ANGRY_STAGE24_47_6_ANDROID_LIFECYCLE_CONTRACT 1')
print('ownership=Android Surface recreation only; Lua/Box2D/EGLContext persist until APP_CMD_DESTROY')
checks=[]
def gate(n,v): checks.append((n,bool(v))); print(f'{n}={"PASS" if v else "FAIL"}')
# Lifecycle branch extraction.
start=cpp.find('static void stage24_handle_cmd')
end=cpp.find('static int32_t stage24_handle_input',start)
block=cpp[start:end] if start>=0 and end>start else ''
term=block[block.find('case APP_CMD_TERM_WINDOW'):block.find('case APP_CMD_GAINED_FOCUS')] if 'case APP_CMD_TERM_WINDOW' in block else ''
destroy=block[block.find('case APP_CMD_DESTROY'):block.find('default:',block.find('case APP_CMD_DESTROY'))] if 'case APP_CMD_DESTROY' in block else ''
gate('term_window_present','case APP_CMD_TERM_WINDOW' in block)
gate('term_window_does_not_stop_engine','stage24_stop_engine()' not in term and 'action=PRESERVE_ENGINE' in term)
gate('destroy_stops_engine','stage24_stop_engine()' in destroy and 'action=STOP_ENGINE' in destroy)
gate('egl_surface_rebind_method','stage24476RebindCurrentWindow' in cpp and 'eglCreateWindowSurface' in cpp and 'contextPreserved=yes' in cpp)
gate('existing_context_reused','eglMakeCurrent(display, next, next, context)' in cpp)
gate('rebind_on_engine_thread','REBIND_REQUEST' in cpp and 'gpuScene.stage24476RebindCurrentWindow' in cpp)
gate('quiescent_handshake','gStage24476EngineQuiescent' in cpp and 'QUIESCENT_ACK' in cpp)
gate('window_generation','gStage24476WindowGeneration' in cpp and 'gStage24476BoundGeneration' in cpp)
gate('resume_no_splash_contract','splashReplay=no' in cpp and 'coldBoot=no' in cpp)
gate('audio_owner_restore','gStage24476AudioRestoreEnabled' in cpp and 'RESTORE_PRE_BACKGROUND_OWNER_STATE' in cpp)
gate('native_jni_audit_wired','stage24476_native_jni_lifecycle_audit.py' in build and 'stage24.47.6-native-jni-lifecycle-audit.txt' in build)
gate('native_audit_targets',all(x in audit for x in ('nativePause','nativeResume','nativeDeinit','nativeInit')))
gate('pull_runtime_report','stage24.47.6-android-lifecycle-runtime.txt' in pull and 'SURFACE_REBOUND' in pull)
gate('test_recents','multitarefa' in test.lower() and 'splash' in test.lower())
# No synthetic gameplay reset or menu forcing in the lifecycle branch.
forbidden=('setGameMode(','loadLevel(','mainMenu','currentMenuPage','lua_setglobal','lua_setfield','SetTransform(','SetLinearVelocity(')
gate('lifecycle_no_gameplay_mutation',bool(block) and not any(x in block for x in forbidden))
ok=all(v for _,v in checks)
print('verdict='+('PASS' if ok else 'FAIL'))
raise SystemExit(0 if ok else 1)
