#include <cmath>
#include <cstdio>
#include <string>

extern "C" {
#include "vendor/lua-5.1.5/src/lua.h"
#include "vendor/lua-5.1.5/src/lauxlib.h"
#include "vendor/lua-5.1.5/src/lualib.h"
}

static void open_lib(lua_State* L, lua_CFunction fn, const char* name) {
    lua_pushcfunction(L, fn);
    lua_pushstring(L, name);
    lua_call(L, 1, 0);
}

static int count_globals(lua_State* L) {
    int count = 0;
    lua_pushnil(L);
    while (lua_next(L, LUA_GLOBALSINDEX) != 0) {
        ++count;
        lua_pop(L, 1);
    }
    return count;
}

static const char* global_type(lua_State* L, const char* name) {
    lua_getglobal(L, name);
    const char* t = lua_typename(L, lua_type(L, -1));
    lua_pop(L, 1);
    return t;
}

static bool exec_one(lua_State* L, const std::string& path, const char* name) {
    const int before_globals = count_globals(L);

    int rc = luaL_loadfile(L, path.c_str());
    if (rc != 0) {
        const char* err = lua_tostring(L, -1);
        std::printf("[angry-stage3] %-16s LOAD FAIL rc=%d err=%s\n",
                    name, rc, err ? err : "<no message>");
        lua_pop(L, 1);
        return false;
    }

    rc = lua_pcall(L, 0, 0, 0);
    if (rc != 0) {
        const char* err = lua_tostring(L, -1);
        std::printf("[angry-stage3] %-16s EXEC FAIL rc=%d err=%s\n",
                    name, rc, err ? err : "<no message>");
        lua_pop(L, 1);
        return false;
    }

    const int after_globals = count_globals(L);
    std::printf("[angry-stage3] %-16s EXEC OK globals %+d (total=%d)\n",
                name, after_globals - before_globals, after_globals);
    return true;
}

static bool expect_bool(lua_State* L, const char* name, bool expected) {
    lua_getglobal(L, name);
    const bool type_ok = lua_isboolean(L, -1) != 0;
    const bool value = type_ok ? (lua_toboolean(L, -1) != 0) : false;
    lua_pop(L, 1);

    std::printf("[angry-stage3] verify %-16s type=%s value=%s\n",
                name, type_ok ? "boolean" : "WRONG",
                value ? "true" : "false");
    return type_ok && value == expected;
}

static bool expect_number(lua_State* L, const char* name, double expected, double eps) {
    lua_getglobal(L, name);
    const bool type_ok = lua_isnumber(L, -1) != 0;
    const double value = type_ok ? static_cast<double>(lua_tonumber(L, -1)) : 0.0;
    lua_pop(L, 1);

    std::printf("[angry-stage3] verify %-16s type=%s value=%.6f\n",
                name, type_ok ? "number" : "WRONG", value);
    return type_ok && std::fabs(value - expected) <= eps;
}

static bool expect_type(lua_State* L, const char* name, int expected_type) {
    lua_getglobal(L, name);
    const int actual = lua_type(L, -1);
    const char* actual_name = lua_typename(L, actual);
    const char* expected_name = lua_typename(L, expected_type);
    lua_pop(L, 1);

    std::printf("[angry-stage3] verify %-16s type=%s expected=%s\n",
                name, actual_name, expected_name);
    return actual == expected_type;
}

int main(int argc, char** argv) {
    std::setvbuf(stdout, nullptr, _IONBF, 0);
    std::setvbuf(stderr, nullptr, _IONBF, 0);
    if (argc != 2) {
        std::fprintf(stderr, "usage: %s <angry-scripts-dir>\n", argv[0]);
        return 2;
    }

    std::printf("[angry-stage3] FIRST REAL EXECUTION OF ANGRY BIRDS LUA ON ARM64\n");
    std::printf("[angry-stage3] Lua runtime: %s\n", LUA_VERSION);
    std::printf("[angry-stage3] native sizeof(size_t)=%zu sizeof(lua_Number)=%zu\n",
                sizeof(size_t), sizeof(lua_Number));

    if (sizeof(lua_Number) != 4) {
        std::fprintf(stderr, "[angry-stage3] FAIL lua_Number is not float32\n");
        return 3;
    }

    std::printf("[angry-stage3] creating Lua state...\n");
    lua_State* L = luaL_newstate();
    if (!L) {
        std::fprintf(stderr, "[angry-stage3] FAIL luaL_newstate\n");
        return 4;
    }

    std::printf("[angry-stage3] Lua state OK\n");

    // Deliberately open only the harmless libraries needed by top-level setup.
    // Base provides setmetatable(), which the Page/Item constructors use.
    std::printf("[angry-stage3] opening base...\n");
    open_lib(L, luaopen_base, "");
    std::printf("[angry-stage3] opening table...\n");
    open_lib(L, luaopen_table, LUA_TABLIBNAME);
    std::printf("[angry-stage3] opening string...\n");
    open_lib(L, luaopen_string, LUA_STRLIBNAME);
    std::printf("[angry-stage3] opening math...\n");
    open_lib(L, luaopen_math, LUA_MATHLIBNAME);
    std::printf("[angry-stage3] libraries OK\n");

    // Historical baseline used by the 480-wide asset/profile logic.
    lua_pushnumber(L, 480.0f);
    lua_setglobal(L, "screenWidth");
    lua_pushnumber(L, 320.0f);
    lua_setglobal(L, "screenHeight");

    // These values are not needed for bytecode loading. They are minimal
    // runtime context for the top-level object/class construction.
    lua_pushstring(L, "android-arm64-bootstrap");
    lua_setglobal(L, "deviceModel");

    const char* files[] = {
        "animations.lua",
        "blocks.lua",
        "loadlist.lua",
        "particles.lua",
        "starLimits.lua",
        "gamelogic.lua"
    };

    bool ok = true;
    for (const char* f : files) {
        ok = exec_one(L, std::string(argv[1]) + "/" + f, f) && ok;
        if (!ok) {
            lua_close(L);
            return 5;
        }
    }

    std::printf("[angry-stage3] top-level Angry Birds code returned normally\n");
    std::printf("[angry-stage3] key globals after execution:\n");
    const char* inspect[] = {
        "releaseBuild", "tapRadius", "initialize", "update",
        "Page", "Item", "SpriteItem", "TextItem",
        "blockTable", "starTable"
    };
    for (const char* n : inspect) {
        std::printf("[angry-stage3]   %-16s %s\n", n, global_type(L, n));
    }

    bool verified = true;
    verified = expect_bool(L, "releaseBuild", true) && verified;
    verified = expect_number(L, "tapRadius", 15.0, 0.001) && verified;
    verified = expect_type(L, "initialize", LUA_TFUNCTION) && verified;
    verified = expect_type(L, "update", LUA_TFUNCTION) && verified;
    verified = expect_type(L, "Page", LUA_TTABLE) && verified;
    verified = expect_type(L, "Item", LUA_TTABLE) && verified;
    verified = expect_type(L, "SpriteItem", LUA_TTABLE) && verified;
    verified = expect_type(L, "TextItem", LUA_TTABLE) && verified;

    const int globals = count_globals(L);
    std::printf("[angry-stage3] globals total=%d\n", globals);

    lua_close(L);

    if (!verified) {
        std::fprintf(stderr, "[angry-stage3] FAIL semantic verification\n");
        return 6;
    }

    std::printf("[angry-stage3] ORIGINAL GAME LOGIC EXECUTED ON ARM64\n");
    std::printf("[angry-stage3] PASS\n");
    return 0;
}
