#!/usr/bin/env python3
import pathlib, re, sys

if len(sys.argv) != 4:
    print("usage: stage24471_rubber_physics_audit_contract.py <build.ps1> <stage24_live_surface.cpp> <test.ps1>")
    sys.exit(2)

build = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8-sig", errors="replace")
cpp = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8-sig", errors="replace")
test = pathlib.Path(sys.argv[3]).read_text(encoding="utf-8-sig", errors="replace")

print("ANGRY_STAGE24_47_1_RUBBER_PHYSICS_AUDIT_CONTRACT 1")
print("policy=DIAGNOSTIC_ONLY; no rubber restitution/damping/impulse/geometry/gameplay mutation")
print("reproA=Golden Egg 2 / LevelGE_2 / ExtraRubberBall / material=rubber")
print("reproB=Danger Above 8-3 / LevelP3_306 / same rubber family")
print("goal=correlate pre-solver contact state, mixed material coefficients, solver impulse, post-step velocity and max-translation clamp before changing Box2D")

checks = []

def gate(name, ok):
    checks.append((name, bool(ok)))
    print(f"{name}={'PASS' if ok else 'FAIL'}")

gate("rubber_observer_present", "[stage24.47.1-rubber] BEGIN" in cpp and
     "[stage24.47.1-rubber] SOLVER" in cpp and
     "[stage24.47.1-rubber] AFTER" in cpp)
gate("material_owned_trigger", 'materialA == "rubber" || materialB == "rubber"' in cpp)
gate("pre_solver_begincontact_hook", "observeRubberBegin24471(contact);" in cpp)
gate("solver_impulse_observer", "observeRubberPostSolve24471(contact, impulse, count);" in cpp)
gate("post_step_observer", "flushRubberAfterStep24471(frame);" in cpp)
gate("mixed_restitution_observed", "mixedRestitution" in cpp and
     "restitutionA > restitutionB ? restitutionA : restitutionB" in cpp)
gate("mixed_friction_observed", "std::sqrt(frictionA * frictionB)" in cpp)
gate("max_translation_observed", "translationCandidateA" in cpp and
     "b2_maxTranslation" in cpp)
gate("cross_repro_test_levelge2", "LevelGE_2" in test and "Golden Egg 2" in test)
gate("cross_repro_test_8_3", "LevelP3_306" in test and "8-3" in test)
gate("prior_body_fixture_armv7_audit_retained", "stage24225_body_fixture_contract.py" in build)
gate("prior_contact_bias_armv7_audit_retained", "stage24224_box2d_contact_bias_contract.py" in build)
gate("prior_material_mix_armv7_audit_retained", "stage24226_contact_material_mix_contract.py" in build)
gate("prior_slop_armv7_audit_retained", "stage24227_linear_slop_position_contract.py" in build)
gate("rovio_maxtranslation_reconstruction_retained", "b2_maxTranslationSquared" in cpp and
     "action=ORIGINAL_ARMV7_CONTRACT" in cpp)

# Observer methods must not mutate Box2D contact/body state. Restrict the
# scan to the newly-added Stage24.47.1 method block.
start = cpp.find("bool isRubberContact24471")
end = cpp.find("void BeginContact(", start)
observer_block = cpp[start:end] if start >= 0 and end > start else ""
mutators = [
    "SetLinearVelocity(", "SetAngularVelocity(", "SetTransform(",
    "SetType(", "SetEnabled(", "SetFriction(", "SetRestitution(",
    "ApplyForce(", "ApplyImpulse(", "DestroyBody(", "CreateFixture("
]
gate("rubber_observer_no_physics_mutators",
     bool(observer_block) and not any(m in observer_block for m in mutators))
gate("no_level_specific_physics_branch",
     "LevelGE_2" not in observer_block and "LevelP3_306" not in observer_block and
     "ExtraRubberBall" not in observer_block)

# The existing physical creation path must remain direct, with the recovered
# Rovio angular damping / polygon skin semantics untouched.
gate("circle_fixture_direct_values_retained",
     "fd.friction = friction;" in cpp and
     "fd.restitution = restitution;" in cpp and
     "fd.density = density;" in cpp)
gate("angular_damping_1_retained", "bd.angularDamping = 1.0f;" in cpp)
gate("fixed_step_10_10_retained", "world.Step(dt, 10, 10);" in cpp)

ok = all(v for _, v in checks)
print("verdict=" + ("PASS" if ok else "FAIL"))
sys.exit(0 if ok else 1)
