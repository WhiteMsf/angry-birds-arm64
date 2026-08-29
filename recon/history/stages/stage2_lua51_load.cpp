#include <cstdio>
#include <string>
extern "C" {
#include "lua.h"
#include "lauxlib.h"
}

static bool load_one(lua_State* L, const std::string& path, const char* name) {
    const int before = lua_gettop(L);
    const int rc = luaL_loadfile(L, path.c_str());
    if (rc != 0) {
        const char* err = lua_tostring(L, -1);
        std::printf("[angry-stage2] %-16s FAIL rc=%d err=%s\n", name, rc, err ? err : "<no message>");
        lua_settop(L, before); return false;
    }
    const bool fn = lua_isfunction(L, -1) != 0;
    std::printf("[angry-stage2] %-16s LOAD OK stack=%d type=%s\n", name, lua_gettop(L), fn ? "function" : lua_typename(L, lua_type(L,-1)));
    lua_settop(L, before);
    return fn;
}

int main(int argc, char** argv) {
    if (argc != 2) { std::fprintf(stderr, "usage: %s <angry-scripts-dir>\n", argv[0]); return 2; }
    std::printf("[angry-stage2] Lua runtime: %s\n", LUA_VERSION);
    std::printf("[angry-stage2] native sizeof(size_t)=%zu sizeof(lua_Number)=%zu\n", sizeof(size_t), sizeof(lua_Number));
    std::printf("[angry-stage2] real VM load only; chunks are NOT executed\n");
    if (sizeof(lua_Number) != 4) { std::fprintf(stderr, "[angry-stage2] FAIL lua_Number is not float32\n"); return 3; }
    lua_State* L = luaL_newstate();
    if (!L) return 4;
    const char* files[] = {"animations.lua","blocks.lua","gamelogic.lua","loadlist.lua","particles.lua","starLimits.lua"};
    bool ok=true;
    for (const char* f: files) ok = load_one(L, std::string(argv[1])+"/"+f, f) && ok;
    lua_close(L);
    if (!ok) { std::fprintf(stderr, "[angry-stage2] FAIL one or more chunks were rejected by the real Lua VM\n"); return 5; }
    std::printf("[angry-stage2] ALL SIX ORIGINAL CHUNKS ARE REAL LUA FUNCTIONS ON ARM64\n");
    std::printf("[angry-stage2] PASS\n");
    return 0;
}
