#include <cmath>
#include <cstdio>
#include <cstring>
#include <map>
#include <string>
#include <vector>

extern "C" {
#include "vendor/lua-5.1.5/src/lua.h"
#include "vendor/lua-5.1.5/src/lauxlib.h"
#include "vendor/lua-5.1.5/src/lualib.h"
}

#include <Box2D/Box2D.h>

struct PhysicsBridge {
    b2World world;
    std::map<std::string, b2Body*> bodies;
    float simulationScale;
    bool physicsEnabled;

    PhysicsBridge()
        : world(b2Vec2(0.0f, 10.0f), true),
          simulationScale(1.0f),
          physicsEnabled(true) {}

    b2Body* find(const char* name) {
        auto it = bodies.find(name ? name : "");
        return it == bodies.end() ? nullptr : it->second;
    }

    b2Body* createBox(const char* name,
                      float x, float y, float width, float height,
                      float density, float friction, float restitution) {
        if (b2Body* old = find(name)) {
            world.DestroyBody(old);
            bodies.erase(name);
        }

        b2BodyDef bd;
        bd.type = density == 0.0f ? b2_staticBody : b2_dynamicBody;
        bd.position.Set(x, y);
        bd.angle = 0.0f;
        bd.linearVelocity.Set(0.0f, 0.0f);
        bd.angularVelocity = 0.0f;
        bd.linearDamping = 0.0f;
        bd.angularDamping = 1.0f;
        bd.allowSleep = true;
        bd.awake = true;
        bd.fixedRotation = false;
        bd.bullet = false;
        bd.active = true;
        bd.userData = nullptr;
        bd.inertiaScale = 1.0f;

        b2Body* body = world.CreateBody(&bd);

        b2PolygonShape shape;
        shape.SetAsBox(width * 0.5f, height * 0.5f);

        b2FixtureDef fd;
        fd.shape = &shape;
        fd.userData = nullptr;
        fd.friction = friction;
        fd.restitution = restitution;
        fd.density = density;
        fd.isSensor = false;
        fd.filter.categoryBits = 0x0001;
        fd.filter.maskBits = 0xFFFF;
        fd.filter.groupIndex = 0;

        body->CreateFixture(&fd);
        bodies[name] = body;
        return body;
    }

    b2Body* createCircle(const char* name,
                         float x, float y, float radius,
                         float density, float friction, float restitution) {
        if (b2Body* old = find(name)) {
            world.DestroyBody(old);
            bodies.erase(name);
        }

        b2BodyDef bd;
        bd.type = density == 0.0f ? b2_staticBody : b2_dynamicBody;
        bd.position.Set(x, y);
        bd.angularDamping = 1.0f;
        bd.inertiaScale = 1.0f;

        b2Body* body = world.CreateBody(&bd);

        b2CircleShape shape;
        shape.m_radius = radius;

        b2FixtureDef fd;
        fd.shape = &shape;
        fd.friction = friction;
        fd.restitution = restitution;
        fd.density = density;
        fd.isSensor = false;
        fd.filter.categoryBits = 0x0001;
        fd.filter.maskBits = 0xFFFF;
        fd.filter.groupIndex = 0;

        body->CreateFixture(&fd);
        bodies[name] = body;
        return body;
    }

    void step(float dt) {
        if (physicsEnabled) {
            world.Step(dt, 8, 3);
            world.ClearForces();
        }
    }
};

static PhysicsBridge* g = nullptr;
static int g_stub_calls = 0;
static int g_menu_bypass = 0;

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

static int generic_stub(lua_State* L) {
    const char* name = lua_tostring(L, lua_upvalueindex(1));
    ++g_stub_calls;
    std::printf("[GameLua stub] %s argc=%d\n", name ? name : "<unknown>", lua_gettop(L));
    return 0;
}

static void register_stub(lua_State* L, const char* name) {
    lua_pushstring(L, name);
    lua_pushcclosure(L, generic_stub, 1);
    lua_setglobal(L, name);
}

static b2Body* require_body(lua_State* L, int index) {
    const char* name = luaL_checkstring(L, index);
    b2Body* b = g->find(name);
    if (!b) luaL_error(L, "unknown physics object '%s'", name);
    return b;
}

static int l_setPhysicsSimulationScale(lua_State* L) {
    g->simulationScale = (float)luaL_checknumber(L, 1);
    std::printf("[GameLua/Box2D] setPhysicsSimulationScale(%.6f)\n",
                (double)g->simulationScale);
    return 0;
}

static int l_setPhysicsEnabled(lua_State* L) {
    g->physicsEnabled = lua_toboolean(L, 1) != 0;
    std::printf("[GameLua/Box2D] setPhysicsEnabled(%s)\n",
                g->physicsEnabled ? "true" : "false");
    return 0;
}

static int l_isPhysicsEnabled(lua_State* L) {
    lua_pushboolean(L, g->physicsEnabled ? 1 : 0);
    return 1;
}

static int l_createBox(lua_State* L) {
    // Recovered native signature:
    // (String name, String sprite, x, y, width, height,
    //  density, friction, restitution, bool, bool, z_order)
    const char* name = luaL_checkstring(L, 1);
    (void)luaL_checkstring(L, 2);
    float x = (float)luaL_checknumber(L, 3);
    float y = (float)luaL_checknumber(L, 4);
    float w = (float)luaL_checknumber(L, 5);
    float h = (float)luaL_checknumber(L, 6);
    float density = (float)luaL_checknumber(L, 7);
    float friction = (float)luaL_checknumber(L, 8);
    float restitution = (float)luaL_checknumber(L, 9);
    (void)lua_toboolean(L, 10);
    (void)lua_toboolean(L, 11);
    (void)luaL_checknumber(L, 12);

    b2Body* b = g->createBox(name, x, y, w, h, density, friction, restitution);
    std::printf("[GameLua/Box2D] createBox('%s') pos=(%.3f,%.3f) size=(%.3f,%.3f) mass=%.6f\n",
                name, (double)x, (double)y, (double)w, (double)h, (double)b->GetMass());
    return 0;
}

static int l_createCircle(lua_State* L) {
    // Recovered native signature:
    // (String name, String sprite, x, y, radius,
    //  density, friction, restitution, bool, z_order)
    const char* name = luaL_checkstring(L, 1);
    (void)luaL_checkstring(L, 2);
    float x = (float)luaL_checknumber(L, 3);
    float y = (float)luaL_checknumber(L, 4);
    float radius = (float)luaL_checknumber(L, 5);
    float density = (float)luaL_checknumber(L, 6);
    float friction = (float)luaL_checknumber(L, 7);
    float restitution = (float)luaL_checknumber(L, 8);
    (void)lua_toboolean(L, 9);
    (void)luaL_checknumber(L, 10);

    b2Body* b = g->createCircle(name, x, y, radius, density, friction, restitution);
    std::printf("[GameLua/Box2D] createCircle('%s') pos=(%.3f,%.3f) r=%.3f mass=%.6f\n",
                name, (double)x, (double)y, (double)radius, (double)b->GetMass());
    return 0;
}

static int l_setVelocity(lua_State* L) {
    b2Body* b = require_body(L, 1);
    const float x = (float)luaL_checknumber(L, 2);
    const float y = (float)luaL_checknumber(L, 3);
    if (b->GetType() != b2_staticBody) b->SetLinearVelocity(b2Vec2(x, y));
    return 0;
}

static int l_setAngularVelocity(lua_State* L) {
    b2Body* b = require_body(L, 1);
    const float w = (float)luaL_checknumber(L, 2);
    if (b->GetType() != b2_staticBody) b->SetAngularVelocity(w);
    return 0;
}

static int l_setPosition(lua_State* L) {
    b2Body* b = require_body(L, 1);
    const float x = (float)luaL_checknumber(L, 2);
    const float y = (float)luaL_checknumber(L, 3);
    b->SetTransform(b2Vec2(x, y), b->GetAngle());
    return 0;
}

static int l_setRotation(lua_State* L) {
    b2Body* b = require_body(L, 1);
    float a = (float)luaL_checknumber(L, 2);
    const float twoPi = 6.2831853071795864769f;
    a = std::fmod(a, twoPi);
    if (a < 0.0f) a += twoPi;
    b->SetTransform(b->GetPosition(), a);
    return 0;
}

static int l_getAngle(lua_State* L) {
    b2Body* b = require_body(L, 1);
    lua_pushnumber(L, b->GetAngle());
    return 1;
}

static int l_getWorldPoint(lua_State* L) {
    b2Body* b = require_body(L, 1);
    const float x = (float)luaL_checknumber(L, 2);
    const float y = (float)luaL_checknumber(L, 3);
    const b2Vec2 p = b->GetWorldPoint(b2Vec2(x, y));
    lua_pushnumber(L, p.x);
    lua_pushnumber(L, p.y);
    return 2;
}

static int l_applyImpulse(lua_State* L) {
    b2Body* b = require_body(L, 1);
    b2Vec2 impulse((float)luaL_checknumber(L, 2),
                   (float)luaL_checknumber(L, 3));
    b2Vec2 point((float)luaL_checknumber(L, 4),
                 (float)luaL_checknumber(L, 5));
    if (b->GetType() == b2_dynamicBody) b->ApplyLinearImpulse(impulse, point);
    return 0;
}

static int l_applyForce(lua_State* L) {
    b2Body* b = require_body(L, 1);
    b2Vec2 force((float)luaL_checknumber(L, 2),
                 (float)luaL_checknumber(L, 3));
    b2Vec2 point((float)luaL_checknumber(L, 4),
                 (float)luaL_checknumber(L, 5));
    if (b->GetType() == b2_dynamicBody) b->ApplyForce(force, point);
    return 0;
}

static int l_removeObject(lua_State* L) {
    const char* name = luaL_checkstring(L, 1);
    auto it = g->bodies.find(name);
    if (it != g->bodies.end()) {
        g->world.DestroyBody(it->second);
        g->bodies.erase(it);
    }
    return 0;
}

static int l_setSleeping(lua_State* L) {
    b2Body* b = require_body(L, 1);
    const bool sleeping = lua_toboolean(L, 2) != 0;
    b->SetAwake(!sleeping);
    return 0;
}

static int l_requestAd(lua_State*) {
    std::printf("[GameLua] requestAd() [no-op]\n");
    return 0;
}

static int l_initializeMenu(lua_State*) {
    ++g_menu_bypass;
    std::printf("[bootstrap] initializeMenu() suppressed (same Stage 4 boundary)\n");
    return 0;
}

static int l_os_time(lua_State* L) {
    lua_pushnumber(L, 1281398400.0f);
    return 1;
}

static void setfn(lua_State* L, const char* name, lua_CFunction fn) {
    lua_pushcfunction(L, fn);
    lua_setglobal(L, name);
}

static void seed_xy_table(lua_State* L, const char* name, float x, float y) {
    lua_newtable(L);
    lua_pushnumber(L, x); lua_setfield(L, -2, "x");
    lua_pushnumber(L, y); lua_setfield(L, -2, "y");
    lua_setglobal(L, name);
}

static bool exec_file(lua_State* L, const std::string& path, const char* name) {
    int rc = luaL_loadfile(L, path.c_str());
    if (rc == 0) rc = lua_pcall(L, 0, 0, 0);
    if (rc != 0) {
        std::printf("[stage5] %s FAIL: %s\n", name, lua_tostring(L, -1));
        lua_pop(L, 1);
        return false;
    }
    return true;
}

static bool run_chunk(lua_State* L, const char* text, const char* name) {
    int rc = luaL_loadbuffer(L, text, std::strlen(text), name);
    if (rc == 0) rc = lua_pcall(L, 0, 0, 0);
    if (rc != 0) {
        std::printf("[stage5] %s FAIL: %s\n", name, lua_tostring(L, -1));
        lua_pop(L, 1);
        return false;
    }
    return true;
}

int main(int argc, char** argv) {
    std::setvbuf(stdout, nullptr, _IONBF, 0);
    std::setvbuf(stderr, nullptr, _IONBF, 0);

    if (argc != 2) {
        std::fprintf(stderr, "usage: %s <angry-scripts-dir>\n", argv[0]);
        return 2;
    }

    std::printf("[angry-stage5] PERIOD-CORRECT BOX2D 2.1.2 / REAL GAMELUA PHYSICS BRIDGE / ARM64\n");

    PhysicsBridge bridge;
    g = &bridge;

    lua_State* L = luaL_newstate();
    if (!L) return 3;

    open_lib(L, luaopen_base, "");
    open_lib(L, luaopen_table, LUA_TABLIBNAME);
    open_lib(L, luaopen_string, LUA_STRLIBNAME);
    open_lib(L, luaopen_math, LUA_MATHLIBNAME);

    lua_newtable(L);
    setfn(L, "time", l_os_time);
    // setfn wrote into globals; rebuild os explicitly.
    lua_pop(L, 1);
    lua_newtable(L);
    lua_pushcfunction(L, l_os_time);
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

    // First install the complete recovered API surface as traceable stubs.
    for (const char* n : kBindings) register_stub(L, n);

    // Then replace the first physics tranche with real Box2D 2.1.2 implementations.
    setfn(L, "setPhysicsSimulationScale", l_setPhysicsSimulationScale);
    setfn(L, "setPhysicsEnabled", l_setPhysicsEnabled);
    setfn(L, "isPhysicsEnabled", l_isPhysicsEnabled);
    setfn(L, "createBox", l_createBox);
    setfn(L, "createCircle", l_createCircle);
    setfn(L, "setVelocity", l_setVelocity);
    setfn(L, "setAngularVelocity", l_setAngularVelocity);
    setfn(L, "setPosition", l_setPosition);
    setfn(L, "setRotation", l_setRotation);
    setfn(L, "getAngle", l_getAngle);
    setfn(L, "getWorldPoint", l_getWorldPoint);
    setfn(L, "applyImpulse", l_applyImpulse);
    setfn(L, "applyForce", l_applyForce);
    setfn(L, "removeObject", l_removeObject);
    setfn(L, "setSleeping", l_setSleeping);
    setfn(L, "requestAd", l_requestAd);
    setfn(L, "initializeMenu", l_initializeMenu);

    // Let the ORIGINAL game initialize our physics bridge.
    lua_getglobal(L, "initialize");
    if (lua_pcall(L, 0, 0, 0) != 0) {
        std::printf("[stage5] initialize FAIL: %s\n", lua_tostring(L, -1));
        lua_close(L);
        return 5;
    }

    std::printf("[stage5] original initialize() configured scale=%.6f enabled=%s\n",
                (double)bridge.simulationScale,
                bridge.physicsEnabled ? "true" : "false");

    // Controlled bridge probe using the exact recovered Lua-visible API names/signatures.
    const char* probe = R"LUA(
setPhysicsEnabled(true)
createBox("probe_box", "none", 0, 0, 2, 2, 1, 0.3, 0.1, false, false, 0)
setVelocity("probe_box", 1.25, 0)
applyImpulse("probe_box", 1.0, 0.0, 0.0, 0.0)
setRotation("probe_box", 7.0)

createCircle("probe_circle", "none", 10, 0, 0.5, 2, 0.2, 0.0, false, 0)
setVelocity("probe_circle", -0.5, 0)
)LUA";
    if (!run_chunk(L, probe, "physics-bridge-probe")) {
        lua_close(L);
        return 6;
    }

    b2Body* box = bridge.find("probe_box");
    b2Body* circle = bridge.find("probe_circle");
    if (!box || !circle) {
        std::fprintf(stderr, "[stage5] bodies were not created\n");
        lua_close(L);
        return 7;
    }

    const float initialBoxMass = box->GetMass();
    const float initialCircleMass = circle->GetMass();
    const b2Vec2 initialBoxVel = box->GetLinearVelocity();
    const float normalizedAngle = box->GetAngle();

    std::printf("[stage5] before step: box mass=%.6f vel=(%.6f,%.6f) angle=%.6f\n",
                (double)initialBoxMass,
                (double)initialBoxVel.x, (double)initialBoxVel.y,
                (double)normalizedAngle);
    std::printf("[stage5] before step: circle mass=%.6f vel=(%.6f,%.6f)\n",
                (double)initialCircleMass,
                (double)circle->GetLinearVelocity().x,
                (double)circle->GetLinearVelocity().y);

    for (int i = 0; i < 60; ++i) bridge.step(1.0f / 60.0f);

    const b2Vec2 p = box->GetPosition();
    const b2Vec2 v = box->GetLinearVelocity();
    const b2Vec2 cp = circle->GetPosition();

    std::printf("[stage5] after 60x1/60: box pos=(%.6f,%.6f) vel=(%.6f,%.6f)\n",
                (double)p.x, (double)p.y, (double)v.x, (double)v.y);
    std::printf("[stage5] after 60x1/60: circle pos=(%.6f,%.6f)\n",
                (double)cp.x, (double)cp.y);

    const float expectedAngle = std::fmod(7.0f, 6.2831853071795864769f);
    bool ok = true;
    ok = std::fabs(initialBoxMass - 4.0f) < 0.001f && ok;
    ok = std::fabs(initialCircleMass - 1.5707963f) < 0.002f && ok;
    ok = std::fabs(initialBoxVel.x - 1.5f) < 0.01f && ok; // 1.25 + impulse(1)/mass(4)
    ok = std::fabs(normalizedAngle - expectedAngle) < 0.001f && ok;
    ok = std::fabs(p.x - 1.5f) < 0.05f && p.y > 4.5f && v.y > 9.0f && ok;
    ok = std::fabs(cp.x - 9.5f) < 0.05f && cp.y > 4.5f && ok;
    ok = bridge.simulationScale == 20.0f && ok;
    ok = g_menu_bypass == 1 && ok;

    lua_close(L);
    g = nullptr;

    if (!ok) {
        std::fprintf(stderr, "[angry-stage5] FAIL physics semantic verification\n");
        return 8;
    }

    std::printf("[angry-stage5] ORIGINAL initialize() -> REAL BOX2D 2.1.2 BRIDGE\n");
    std::printf("[angry-stage5] createBox/createCircle/velocity/impulse/transform/step VERIFIED\n");
    std::printf("[angry-stage5] PASS\n");
    return 0;
}
