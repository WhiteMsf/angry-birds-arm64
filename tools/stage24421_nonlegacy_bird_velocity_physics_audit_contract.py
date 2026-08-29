#!/usr/bin/env python3
"""Stage 24.42.1: exact nonlegacy deferred bird velocity + passive glass/wood physics audit."""
from pathlib import Path
import re
import sys

if len(sys.argv) != 4:
    print("usage: stage24421_nonlegacy_bird_velocity_physics_audit_contract.py <build.ps1> <stage24_live_surface.cpp> <stage24.19.2-armv7-block-score-ownership.txt>")
    raise SystemExit(2)

build = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
cpp = Path(sys.argv[2]).read_text(encoding="utf-8", errors="replace")
armv7 = Path(sys.argv[3]).read_text(encoding="utf-8", errors="replace").lower()

checks = {}

# Require the retained original ARMv7 BeginContact evidence, not just source-text
# conformance. These addresses/data writes are the recovered alternate producer.
armv7_tokens = [
    "57898:", "578a0:", "__subsf3",
    "578a8:", "__divsf3",
    "578ac:", "578b0:", "__mulsf3",
    "578d4: e58b002c",
    "578e8: e5cb3084",
    "578ec: e58b0030",
    "578f0:", "57810:",
]
checks["armv7_nonlegacy_evidence"] = all(tok in armv7 for tok in armv7_tokens)

# Exact alternate BeginContact producer recovered at ARMv7 0x57898..0x578F0.
checks["nonlegacy_formula"] = (
    "((collisionForce - strength) / collisionForce)" in cpp
    and "* velocityMultiplier" in cpp
)
checks["upper_clamp_only"] = (
    "if (velocityScale > 1.0f)" in cpp
    and "velocityScale = 1.0f;" in cpp
)
checks["deferred_store"] = (
    "deferredVelocity24421[birdName] = pending;" in cpp
    and "[stage24.42.1-nonlegacy] DEFER_STORE" in cpp
)
checks["contact_disabled"] = (
    "storeDeferredVelocity24421(" in cpp
    and "contact->SetEnabled(false);" in cpp
    and "[stage24.42.1-nonlegacy] PRODUCER" in cpp
)
checks["old_fail_closed_removed"] = (
    "recovered bird destruction entered the still-unreconstructed non-legacy deferred-velocity path"
    not in cpp
)

# Producer is deferred, not collapsed to the immediate legacy SetLinearVelocity path.
m = re.search(
    r"if \(!legacyFieldPresent\) \{(?P<body>.*?)\n\s*\} else \{",
    cpp, re.S
)
nonlegacy_body = m.group("body") if m else ""
checks["nonlegacy_not_immediate"] = (
    bool(nonlegacy_body)
    and "storeDeferredVelocity24421" in nonlegacy_body
    and "SetLinearVelocity" not in nonlegacy_body
)

# Consumer must happen after Step/removeBlocks and before render-history/next Step.
call = "physics.applyDeferredVelocities24421(frame);"
call_pos = cpp.find(call)
remove_pos = cpp.rfind("callOriginalRemoveBlocks(frame)", 0, call_pos) if call_pos >= 0 else -1
capture_pos = cpp.find("physics.captureRenderHistoryAfterFixedStep()", call_pos) if call_pos >= 0 else -1
checks["post_step_deferred_consumer"] = (
    call_pos >= 0 and remove_pos >= 0 and capture_pos > call_pos > remove_pos
    and "[stage24.42.1-nonlegacy] DEFER_APPLY" in cpp
)

# Passive glass/wood audit must cover pre-first-step state, first fixed steps,
# contact transitions, gravity, awake state and material/fixture parameters.
audit_tokens = [
    "[stage24.42.1-glasswood] SNAPSHOT_BEGIN",
    "enable-request-pre-first-step",
    '"post-fixed-step"',
    "[stage24.42.1-glasswood] CONTACT",
    'materialA == "glass" && materialB == "wood"',
    "world.GetGravity()",
    "IsAwake()",
    "GetFriction()",
    "GetRestitution()",
    "GetDensity()",
    "GetManifold()",
    "IsTouching()",
]
checks["glasswood_audit_surface"] = all(tok in cpp for tok in audit_tokens)
checks["first_12_steps"] = (
    "physics.glassWoodFixedSteps24421 < 12" in cpp
    and "physics.glassWoodFixedSteps24421 >= 12" in cpp
)

# Read-only auditor bodies may inspect but must not alter Box2D state.
def function_body(name, next_name):
    a = cpp.find(name)
    b = cpp.find(next_name, a + len(name))
    return cpp[a:b] if a >= 0 and b > a else ""

audit_body = (
    function_body("void logGlassWoodContact24421(", "void snapshotGlassWood24421(")
    + function_body("void snapshotGlassWood24421(", "void notePhysicsEnable24421(")
)
forbidden_audit_mutations = [
    "SetLinearVelocity(", "SetAngularVelocity(", "SetTransform(",
    "SetAwake(", "SetActive(", "SetEnabled(", "SetFriction(",
    "SetRestitution(", "SetGravity(", "ApplyForce(", "ApplyImpulse(",
    "DestroyBody(", "CreateBody(",
]
checks["audit_read_only"] = bool(audit_body) and not any(
    tok in audit_body for tok in forbidden_audit_mutations
)

# No bird/level-specific implementation.
checks["no_boomerang_native_hack"] = (
    'if (birdSpecialty == "BOOMERANG")' not in cpp
    and 'if (birdName == "BoomerangBird_1")' not in cpp
)
checks["no_level_specific_fix"] = not re.search(
    r"if\s*\([^\n)]*LevelP3_224", cpp
)

# Build must gate this contract.
checks["build_gate"] = (
    "stage24421_nonlegacy_bird_velocity_physics_audit_contract.py" in build
    and "stage24.42.1-nonlegacy-bird-velocity-physics-audit-contract.txt" in build
    and "$blockScoreOwnershipAudit" in build
)

failed = [k for k, v in checks.items() if not v]
print("ANGRY_STAGE24_42_1_NONLEGACY_BIRD_VELOCITY_PHYSICS_AUDIT_CONTRACT 1")
print("armv7_nonlegacy=scale=min(((collisionForce-strengthBefore)/collisionForce)*velocityMultiplier,1); deferred velocity; disable contact")
print("glasswood=OBSERVE_ONLY pre-first-step + first 12 fixed steps + Begin/End contact")
for k, v in checks.items():
    print(f"{k}={'PASS' if v else 'FAIL'}")
print("verdict=" + ("PASS" if not failed else "FAIL"))
if failed:
    print("failed=" + ",".join(failed))
    raise SystemExit(3)
