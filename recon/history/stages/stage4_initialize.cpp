#include <cmath>
#include <cstdio>
#include <cstring>
#include <string>

extern "C" {
#include "vendor/lua-5.1.5/src/lua.h"
#include "vendor/lua-5.1.5/src/lauxlib.h"
#include "vendor/lua-5.1.5/src/lualib.h"
}

static int g_stub_calls = 0;
static int g_initialize_menu_calls = 0;
static int g_set_scale_calls = 0;
static int g_set_enabled_calls = 0;
static int g_request_ad_calls = 0;
static float g_last_scale = -1.0f;
static int g_last_enabled = -1;

static const char* kBindings[] = {
    "requestExit",
    "print",
    "setBGColor",
    "createBox",
    "createCircle",
    "createPolygon",
    "createJoint",
    "destroyJoint",
    "clearVertices",
    "addVertex",
    "applyImpulse",
    "applyForce",
    "setPosition",
    "setRotation",
    "setVelocity",
    "setAngularVelocity",
    "setPhysicsSimulationScale",
    "setPhysicsEnabled",
    "isPhysicsEnabled",
    "setTopLeft",
    "removeObject",
    "setEditing",
    "setWorldScale",
    "drawRect",
    "drawTexturedRect",
    "setRenderState",
    "loadLevel",
    "saveLevel",
    "saveLuaFile",
    "createDirectory",
    "checkDirectory",
    "drawGameNative",
    "drawBackgroundNative",
    "drawParticlesNative",
    "setSprite",
    "setMaterial",
    "setTexture",
    "setTheme",
    "setSleeping",
    "drawLine2D",
    "drawForegroundNative",
    "setObjectParameter",
    "clipText",
    "startNewTrajectory",
    "addToTrajectory",
    "addPuffToTrajectory",
    "setLevelLimits",
    "goToTaskSwitcherLua",
    "setGameOn",
    "checkForLuaFile",
    "activateCrystalUI",
    "activateCrystalUIAtProfile",
    "deactivateCrystalUI",
    "postHighscore",
    "unlockAchievement",
    "showCrystalSplash",
    "isCrystalSplashShowing",
    "isCrystalUIShowing",
    "userEnabledCrystal",
    "avoidCrystalBackgroundActivity",
    "initGameCenter",
    "getLeaderboardScoresForPlayers",
    "getLeaderboardScoresForRange",
    "showLeaderboards",
    "showAchievements",
    "drawSome",
    "showAdvertisement",
    "hideAdvertisement",
    "showVideoAdvertisement",
    "requestVideoAd",
    "requestAndShowVideo",
    "requestAd",
    "logFlurryEvent",
    "logFlurryEventWithParam",
    "logFlurryEventWithParams",
    "getAngle",
    "getWorldPoint",
    "printGlobals",
    "playVideo",
    "setMaxTranslation"
};

static void open_lib(lua_State* L, lua_CFunction fn, const char* name) {
    lua_pushcfunction(L, fn);
    lua_pushstring(L, name);
    lua_call(L, 1, 0);
}

static int stub_binding(lua_State* L) {
    const char* name = lua_tostring(L, lua_upvalueindex(1));
    ++g_stub_calls;
    std::printf("[GameLua stub] %s(", name ? name : "<unknown>");
    const int n = lua_gettop(L);
    for (int i = 1; i <= n; ++i) {
        if (i > 1) std::printf(", ");
        switch (lua_type(L, i)) {
            case LUA_TNUMBER:  std::printf("%.6g", (double)lua_tonumber(L, i)); break;
            case LUA_TBOOLEAN: std::printf("%s", lua_toboolean(L, i) ? "true" : "false"); break;
            case LUA_TSTRING:  std::printf("\"%s\"", lua_tostring(L, i)); break;
            case LUA_TNIL:     std::printf("nil"); break;
            default:           std::printf("<%s>", lua_typename(L, lua_type(L, i))); break;
        }
    }
    std::printf(")\n");
    return 0;
}

static void register_stub(lua_State* L, const char* name) {
    lua_pushstring(L, name);
    lua_pushcclosure(L, stub_binding, 1);
    lua_setglobal(L, name);
}

static int stub_set_scale(lua_State* L) {
    ++g_set_scale_calls;
    g_last_scale = (float)luaL_checknumber(L, 1);
    std::printf("[GameLua] setPhysicsSimulationScale(%.6f)\n", (double)g_last_scale);
    return 0;
}

static int stub_set_enabled(lua_State* L) {
    ++g_set_enabled_calls;
    g_last_enabled = lua_toboolean(L, 1) ? 1 : 0;
    std::printf("[GameLua] setPhysicsEnabled(%s)\n", g_last_enabled ? "true" : "false");
    return 0;
}

static int stub_request_ad(lua_State*) {
    ++g_request_ad_calls;
    std::printf("[GameLua] requestAd() [no-op]\n");
    return 0;
}

static int stub_initialize_menu(lua_State*) {
    ++g_initialize_menu_calls;
    std::printf("[bootstrap] initializeMenu() suppressed: menu/save support scripts are not loaded yet\n");
    return 0;
}

static int deterministic_os_time(lua_State* L) {
    lua_pushnumber(L, 1281398400.0f); // deterministic 2010-era seed; exact date is irrelevant
    return 1;
}

static void seed_xy_table(lua_State* L, const char* name, float x, float y) {
    lua_newtable(L);
    lua_pushnumber(L, x);
    lua_setfield(L, -2, "x");
    lua_pushnumber(L, y);
    lua_setfield(L, -2, "y");
    lua_setglobal(L, name);
}

static bool exec_file(lua_State* L, const std::string& path, const char* name) {
    int rc = luaL_loadfile(L, path.c_str());
    if (rc != 0) {
        std::printf("[stage4] %s LOAD FAIL: %s\n", name, lua_tostring(L, -1));
        lua_pop(L, 1);
        return false;
    }
    rc = lua_pcall(L, 0, 0, 0);
    if (rc != 0) {
        std::printf("[stage4] %s EXEC FAIL: %s\n", name, lua_tostring(L, -1));
        lua_pop(L, 1);
        return false;
    }
    std::printf("[stage4] %-16s EXEC OK\n", name);
    return true;
}

static bool get_number(lua_State* L, const char* name, double expected, double eps) {
    lua_getglobal(L, name);
    bool ok = lua_isnumber(L, -1) != 0;
    double v = ok ? (double)lua_tonumber(L, -1) : 0.0;
    lua_pop(L, 1);
    std::printf("[stage4] verify %-18s type=%s value=%.6f expected=%.6f\n",
                name, ok ? "number" : "WRONG", v, expected);
    return ok && std::fabs(v - expected) <= eps;
}

static bool get_bool(lua_State* L, const char* name, bool expected) {
    lua_getglobal(L, name);
    bool type_ok = lua_isboolean(L, -1) != 0;
    bool v = type_ok && lua_toboolean(L, -1);
    lua_pop(L, 1);
    std::printf("[stage4] verify %-18s type=%s value=%s expected=%s\n",
                name, type_ok ? "boolean" : "WRONG",
                v ? "true" : "false", expected ? "true" : "false");
    return type_ok && v == expected;
}

int main(int argc, char** argv) {
    std::setvbuf(stdout, nullptr, _IONBF, 0);
    std::setvbuf(stderr, nullptr, _IONBF, 0);

    if (argc != 2) {
        std::fprintf(stderr, "usage: %s <angry-scripts-dir>\n", argv[0]);
        return 2;
    }

    std::printf("[angry-stage4] ORIGINAL initialize() CORE PROBE / ARM64\n");
    std::printf("[angry-stage4] Lua=%s sizeof(size_t)=%zu sizeof(lua_Number)=%zu\n",
                LUA_VERSION, sizeof(size_t), sizeof(lua_Number));

    lua_State* L = luaL_newstate();
    if (!L) return 3;

    open_lib(L, luaopen_base, "");
    open_lib(L, luaopen_table, LUA_TABLIBNAME);
    open_lib(L, luaopen_string, LUA_STRLIBNAME);
    open_lib(L, luaopen_math, LUA_MATHLIBNAME);

    // Minimal deterministic replacement for os.time(), the only os call made by initialize().
    lua_newtable(L);
    lua_pushcfunction(L, deterministic_os_time);
    lua_setfield(L, -2, "time");
    lua_setglobal(L, "os");

    lua_pushnumber(L, 480.0f); lua_setglobal(L, "screenWidth");
    lua_pushnumber(L, 320.0f); lua_setglobal(L, "screenHeight");
    lua_pushstring(L, "android-arm64-bootstrap"); lua_setglobal(L, "deviceModel");
    seed_xy_table(L, "cursor", 0.0f, 0.0f);

    const char* files[] = {
        "animations.lua", "blocks.lua", "loadlist.lua",
        "particles.lua", "starLimits.lua", "gamelogic.lua"
    };
    for (const char* f : files) {
        if (!exec_file(L, std::string(argv[1]) + "/" + f, f)) {
            lua_close(L);
            return 4;
        }
    }

    // Recovered from the original GameLua constructor: expose the entire 80-name native API
    // as traced no-op closures, then give the three initialize() calls semantic probes.
    for (const char* name : kBindings) register_stub(L, name);

    lua_pushcfunction(L, stub_set_scale);
    lua_setglobal(L, "setPhysicsSimulationScale");
    lua_pushcfunction(L, stub_set_enabled);
    lua_setglobal(L, "setPhysicsEnabled");
    lua_pushcfunction(L, stub_request_ad);
    lua_setglobal(L, "requestAd");

    // initializeMenu requires the wider save/menu script graph that was not in the six-file
    // root scripts ZIP. Suppress only this branch; the rest of initialize() is original.
    lua_pushcfunction(L, stub_initialize_menu);
    lua_setglobal(L, "initializeMenu");

    lua_getglobal(L, "initialize");
    if (!lua_isfunction(L, -1)) {
        std::fprintf(stderr, "[stage4] initialize is not a function\n");
        lua_close(L);
        return 5;
    }

    std::printf("[stage4] CALL initialize()\n");
    int rc = lua_pcall(L, 0, 0, 0);
    if (rc != 0) {
        std::printf("[stage4] initialize() FAIL: %s\n", lua_tostring(L, -1));
        lua_pop(L, 1);
        lua_close(L);
        return 6;
    }
    std::printf("[stage4] initialize() RETURNED NORMALLY\n");

    bool ok = true;
    ok = get_number(L, "physicsToWorld", 20.0, 0.001) && ok;
    ok = get_number(L, "physicsScale", 0.05, 0.0001) && ok;
    ok = get_bool(L, "physicsEnabled", false) && ok;
    ok = get_bool(L, "adRequested", true) && ok;

    std::printf("[stage4] native call counts: scale=%d enabled=%d requestAd=%d menuBypass=%d generic=%d\n",
                g_set_scale_calls, g_set_enabled_calls, g_request_ad_calls,
                g_initialize_menu_calls, g_stub_calls);
    std::printf("[stage4] native args: scale=%.6f enabled=%d\n",
                (double)g_last_scale, g_last_enabled);

    ok = (g_set_scale_calls == 1 && std::fabs(g_last_scale - 20.0f) < 0.001f) && ok;
    ok = (g_set_enabled_calls == 1 && g_last_enabled == 0) && ok;
    ok = (g_request_ad_calls == 1) && ok;
    ok = (g_initialize_menu_calls == 1) && ok;

    lua_close(L);

    if (!ok) {
        std::fprintf(stderr, "[angry-stage4] FAIL semantic verification\n");
        return 7;
    }

    std::printf("[angry-stage4] ORIGINAL initialize() CORE EXECUTED ON ARM64\n");
    std::printf("[angry-stage4] 80-NAME GameLua API SURFACE INSTALLED\n");
    std::printf("[angry-stage4] PASS\n");
    return 0;
}
