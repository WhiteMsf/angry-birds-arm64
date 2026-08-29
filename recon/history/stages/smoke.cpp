#include <lang/Globals.h>
#include <lang/GlobalStorage.h>
#include <lua/LuaState.h>
#include <lua/LuaTable.h>
#include <cstdio>
#include <cstring>

int main()
{
    lang::lang_Globals::init();

    int rc = 0;
    try
    {
        lua::LuaState state;
        const char* code = "answer = 40 + 2";
        state.compile(code, (int)std::strlen(code), lang::String("stage0"), 0);

        const float answer = state.globals().getNumber(lang::String("answer"));
        std::printf("[angry-bootstrap] KA3D/Lua smoke answer=%.0f\\n", answer);

        if (answer != 42.0f)
        {
            std::printf("[angry-bootstrap] FAIL: expected 42\\n");
            rc = 2;
        }
        else
        {
            std::printf("[angry-bootstrap] PASS\\n");
        }
    }
    catch (...)
    {
        std::printf("[angry-bootstrap] FAIL: exception while booting KA3D/Lua\\n");
        rc = 3;
    }

    lang::lang_Globals::cleanup();
    lang::GlobalStorage::release();
    return rc;
}
