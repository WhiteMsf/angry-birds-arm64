cmake_minimum_required(VERSION 3.16)

project(angry_birds_arm64 LANGUAGES C CXX)

option(
    ANGRY_BUILD_HOST_TESTS
    "Build host-only runtime contract tests"
    OFF
)

if(NOT ANDROID)
    if(NOT ANGRY_BUILD_HOST_TESTS)
        message(FATAL_ERROR
            "The primary target is an Android ARM64 NativeActivity library. "
            "Configure with the Android NDK toolchain, or set "
            "ANGRY_BUILD_HOST_TESTS=ON for host-only runtime tests."
        )
    endif()

    enable_testing()

    add_executable(presentation_geometry_tests
        tests/presentation_geometry_test.cpp
        src/runtime/presentation/presentation_geometry.cpp
    )

    target_include_directories(presentation_geometry_tests
        PRIVATE
            "${CMAKE_CURRENT_SOURCE_DIR}/src/runtime/presentation"
    )

    target_compile_features(presentation_geometry_tests
        PRIVATE
            cxx_std_17
    )

    add_test(
        NAME presentation_geometry
        COMMAND presentation_geometry_tests
    )

    return()
endif()

# ---------------------------------------------------------------------------
# Lua 5.1.5
#
# Angry Birds 1.4.2 uses Lua 5.1-era game scripts. The vendored tree contains
# the compatibility patches required by this reconstruction.
# ---------------------------------------------------------------------------

set(LUA51_SRC "${CMAKE_CURRENT_SOURCE_DIR}/vendor/lua-5.1.5/src")

if(NOT EXISTS "${LUA51_SRC}/lua.h")
    message(FATAL_ERROR
        "Lua 5.1.5 source tree not found at ${LUA51_SRC}"
    )
endif()

set(LUA51_ANGRY_CORE
    ${LUA51_SRC}/lapi.c
    ${LUA51_SRC}/lcode.c
    ${LUA51_SRC}/ldebug.c
    ${LUA51_SRC}/ldo.c
    ${LUA51_SRC}/ldump.c
    ${LUA51_SRC}/lfunc.c
    ${LUA51_SRC}/lgc.c
    ${LUA51_SRC}/llex.c
    ${LUA51_SRC}/lmem.c
    ${LUA51_SRC}/lobject.c
    ${LUA51_SRC}/lopcodes.c
    ${LUA51_SRC}/lparser.c
    ${LUA51_SRC}/lstate.c
    ${LUA51_SRC}/lstring.c
    ${LUA51_SRC}/ltable.c
    ${LUA51_SRC}/ltm.c
    ${LUA51_SRC}/lundump.c
    ${LUA51_SRC}/lvm.c
    ${LUA51_SRC}/lzio.c
    ${LUA51_SRC}/lauxlib.c
    ${LUA51_SRC}/lbaselib.c
    ${LUA51_SRC}/ltablib.c
    ${LUA51_SRC}/lstrlib.c
    ${LUA51_SRC}/lmathlib.c
)

add_library(lua51_angry STATIC ${LUA51_ANGRY_CORE})

target_include_directories(lua51_angry
    PUBLIC
        ${LUA51_SRC}
)

target_compile_options(lua51_angry
    PRIVATE
        -Wno-unused-function
        -Wno-unused-parameter
)

# ---------------------------------------------------------------------------
# Box2D 2.1.2
#
# Pinned period-correct physics implementation used by the reconstruction.
# build.py passes BOX2D212_ROOT explicitly; the local vendor path is also
# accepted for direct CMake use.
# ---------------------------------------------------------------------------

if(NOT DEFINED BOX2D212_ROOT)
    set(
        BOX2D212_ROOT
        "${CMAKE_CURRENT_SOURCE_DIR}/vendor/box2d-v2.1.2"
    )
endif()

set(B2 "${BOX2D212_ROOT}/Box2D/Box2D")

if(NOT EXISTS "${B2}/Dynamics/b2World.cpp")
    message(FATAL_ERROR
        "Box2D 2.1.2 source tree not found at ${BOX2D212_ROOT}"
    )
endif()

add_library(box2d212 STATIC
    ${B2}/Collision/b2BroadPhase.cpp
    ${B2}/Collision/b2CollideCircle.cpp
    ${B2}/Collision/b2CollidePolygon.cpp
    ${B2}/Collision/b2Collision.cpp
    ${B2}/Collision/b2Distance.cpp
    ${B2}/Collision/b2DynamicTree.cpp
    ${B2}/Collision/b2TimeOfImpact.cpp

    ${B2}/Collision/Shapes/b2CircleShape.cpp
    ${B2}/Collision/Shapes/b2PolygonShape.cpp

    ${B2}/Common/b2BlockAllocator.cpp
    ${B2}/Common/b2Math.cpp
    ${B2}/Common/b2Settings.cpp
    ${B2}/Common/b2StackAllocator.cpp

    ${B2}/Dynamics/b2Body.cpp
    ${B2}/Dynamics/b2ContactManager.cpp
    ${B2}/Dynamics/b2Fixture.cpp
    ${B2}/Dynamics/b2Island.cpp
    ${B2}/Dynamics/b2World.cpp
    ${B2}/Dynamics/b2WorldCallbacks.cpp

    ${B2}/Dynamics/Contacts/b2CircleContact.cpp
    ${B2}/Dynamics/Contacts/b2Contact.cpp
    ${B2}/Dynamics/Contacts/b2ContactSolver.cpp
    ${B2}/Dynamics/Contacts/b2PolygonAndCircleContact.cpp
    ${B2}/Dynamics/Contacts/b2PolygonContact.cpp
    ${B2}/Dynamics/Contacts/b2TOISolver.cpp

    ${B2}/Dynamics/Joints/b2DistanceJoint.cpp
    ${B2}/Dynamics/Joints/b2FrictionJoint.cpp
    ${B2}/Dynamics/Joints/b2GearJoint.cpp
    ${B2}/Dynamics/Joints/b2Joint.cpp
    ${B2}/Dynamics/Joints/b2LineJoint.cpp
    ${B2}/Dynamics/Joints/b2MouseJoint.cpp
    ${B2}/Dynamics/Joints/b2PrismaticJoint.cpp
    ${B2}/Dynamics/Joints/b2PulleyJoint.cpp
    ${B2}/Dynamics/Joints/b2RevoluteJoint.cpp
    ${B2}/Dynamics/Joints/b2WeldJoint.cpp
)

target_include_directories(box2d212
    PUBLIC
        "${BOX2D212_ROOT}/Box2D"
)

set_target_properties(box2d212 PROPERTIES
    CXX_STANDARD 11
    CXX_STANDARD_REQUIRED ON
)

target_compile_options(box2d212
    PRIVATE
        -Wno-unused-parameter
        -Wno-deprecated-declarations
        -Wno-register

        # Preserve the recovered ARMv7 floating-point operation ordering.
        # Do not silently contract a*b+c into FMADD/FMSUB.
        -ffp-contract=off
)

# ---------------------------------------------------------------------------
# Angry Birds ARM64 reconstruction
# ---------------------------------------------------------------------------

if(DEFINED CMAKE_ANDROID_NDK)
    set(
        STAGE24_NATIVE_APP_GLUE
        "${CMAKE_ANDROID_NDK}/sources/android/native_app_glue"
    )
else()
    set(
        STAGE24_NATIVE_APP_GLUE
        "${ANDROID_NDK}/sources/android/native_app_glue"
    )
endif()

if(NOT EXISTS
    "${STAGE24_NATIVE_APP_GLUE}/android_native_app_glue.c"
)
    message(FATAL_ERROR
        "android_native_app_glue.c not found under "
        "${STAGE24_NATIVE_APP_GLUE}"
    )
endif()

add_library(stage24_live_surface SHARED
    stage24_live_surface.cpp
    src/runtime/presentation/presentation_geometry.cpp
    "${STAGE24_NATIVE_APP_GLUE}/android_native_app_glue.c"
)

target_include_directories(stage24_live_surface
    BEFORE PRIVATE
        ${LUA51_SRC}
        "${BOX2D212_ROOT}/Box2D"
        "${STAGE24_NATIVE_APP_GLUE}"
)

set(
    STAGE24_DISPLAY_MODE
    "wvga854"
    CACHE STRING
    "Presentation mode: wvga854 or native"
)

set_property(
    CACHE STAGE24_DISPLAY_MODE
    PROPERTY STRINGS
        wvga854
        native
)

option(
    STAGE24282_GLOBAL_SPRITE_REGISTRY
    "Use recovered global sprite-registry behavior"
    OFF
)

if(STAGE24282_GLOBAL_SPRITE_REGISTRY)
    target_compile_definitions(stage24_live_surface
        PRIVATE
            STAGE24282_GLOBAL_SPRITE_REGISTRY=1
    )
else()
    target_compile_definitions(stage24_live_surface
        PRIVATE
            STAGE24282_GLOBAL_SPRITE_REGISTRY=0
    )
endif()

message(
    STATUS
    "Stage24.28.2 global sprite registry contract: "
    "${STAGE24282_GLOBAL_SPRITE_REGISTRY}"
)

if(STAGE24_DISPLAY_MODE STREQUAL "native")

    target_compile_definitions(stage24_live_surface
        PRIVATE
            STAGE24_LIVE=1
            STAGE24_DEBUG_LOGICAL_W=0
            STAGE24_DEBUG_LOGICAL_H=0
    )

elseif(STAGE24_DISPLAY_MODE STREQUAL "wvga854")

    target_compile_definitions(stage24_live_surface
        PRIVATE
            STAGE24_LIVE=1
            STAGE24_DEBUG_LOGICAL_W=854
            STAGE24_DEBUG_LOGICAL_H=480
    )

else()

    message(FATAL_ERROR
        "Unknown STAGE24_DISPLAY_MODE='${STAGE24_DISPLAY_MODE}' "
        "(expected wvga854 or native)"
    )

endif()

message(
    STATUS
    "Stage24 display mode: ${STAGE24_DISPLAY_MODE}"
)

# Same numerical-fidelity policy used by the Box2D target.
target_compile_options(stage24_live_surface
    PRIVATE
        -ffp-contract=off
)

target_link_libraries(stage24_live_surface
    PRIVATE
        lua51_angry
        box2d212
        android
        EGL
        GLESv1_CM
        OpenSLES
        mediandk
        log
        dl
        m
)

set_target_properties(stage24_live_surface PROPERTIES
    OUTPUT_NAME angryarm64
)
