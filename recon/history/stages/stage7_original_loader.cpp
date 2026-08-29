#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iterator>
#include <map>
#include <string>
#include <vector>

extern "C" {
#include "vendor/lua-5.1.5/src/lua.h"
#include "vendor/lua-5.1.5/src/lauxlib.h"
#include "vendor/lua-5.1.5/src/lualib.h"
}

#include <Box2D/Box2D.h>

struct SpriteInfo {
    int x = 0;
    int y = 0;
    int width = 0;
    int height = 0;
    int pivotX = 0;
    int pivotY = 0;
};

class SpriteDB {
public:
    bool loadSheet(const std::string& path) {
        std::ifstream f(path.c_str(), std::ios::binary);
        if (!f) {
            std::printf("[stage6] sprite sheet open FAIL: %s\n", path.c_str());
            return false;
        }
        std::vector<unsigned char> d(
            (std::istreambuf_iterator<char>(f)),
            std::istreambuf_iterator<char>());

        size_t sprt = std::string::npos;
        for (size_t i = 0; i + 4 <= d.size(); ++i) {
            if (d[i] == 'S' && d[i+1] == 'P' && d[i+2] == 'R' && d[i+3] == 'T') {
                sprt = i;
                break;
            }
        }
        if (sprt == std::string::npos || sprt + 8 > d.size()) {
            std::printf("[stage6] SPRT chunk missing: %s\n", path.c_str());
            return false;
        }

        size_t p = sprt + 8; // skip "SPRT" + big-endian chunk size
        auto need = [&](size_t n) -> bool { return p + n <= d.size(); };
        auto u16 = [&]() -> uint16_t {
            if (!need(2)) return 0;
            uint16_t v = static_cast<uint16_t>((d[p] << 8) | d[p+1]);
            p += 2;
            return v;
        };
        auto i16 = [&]() -> int {
            uint16_t u = u16();
            return (u & 0x8000u) ? static_cast<int>(u) - 65536 : static_cast<int>(u);
        };
        auto str16 = [&]() -> std::string {
            const uint16_t n = u16();
            if (!need(n)) return std::string();
            std::string s(reinterpret_cast<const char*>(&d[p]), n);
            p += n;
            return s;
        };

        if (!need(2)) return false;
        const uint16_t textureCount = u16();
        for (uint16_t i = 0; i < textureCount; ++i) {
            (void)str16();
        }

        if (!need(2)) return false;
        const uint16_t spriteCount = u16();
        int loaded = 0;
        for (uint16_t i = 0; i < spriteCount; ++i) {
            const std::string name = str16();
            if (!need(12) || name.empty()) {
                std::printf("[stage6] malformed sprite entry in %s\n", path.c_str());
                return false;
            }
            SpriteInfo s;
            s.x = i16();
            s.y = i16();
            s.width = i16();
            s.height = i16();
            s.pivotX = i16();
            s.pivotY = i16();
            sprites_[name] = s;
            ++loaded;
        }

        std::printf("[stage6] sprite sheet %-24s loaded=%d\n",
                    path.substr(path.find_last_of("/\\") + 1).c_str(), loaded);
        return true;
    }

    const SpriteInfo* find(const char* name) const {
        auto it = sprites_.find(name ? name : "");
        return it == sprites_.end() ? nullptr : &it->second;
    }

    size_t size() const { return sprites_.size(); }

private:
    std::map<std::string, SpriteInfo> sprites_;
};

struct PhysicsBridge {
    b2World world;
    std::map<std::string, b2Body*> bodies;
    float simulationScale = 1.0f;
    bool physicsEnabled = true;
    int boxesCreated = 0;
    int circlesCreated = 0;

    PhysicsBridge() : world(b2Vec2(0.0f, 10.0f), true) {}

    b2Body* find(const char* name) {
        auto it = bodies.find(name ? name : "");
        return it == bodies.end() ? nullptr : it->second;
    }

    b2Body* findPrefix(const char* prefix, std::string* matchedName = nullptr) {
        const std::string p = prefix ? prefix : "";
        for (auto& kv : bodies) {
            if (kv.first.rfind(p, 0) == 0) {
                if (matchedName) *matchedName = kv.first;
                return kv.second;
            }
        }
        return nullptr;
    }

    b2Body* findPrefixWithType(const char* prefix, b2BodyType type,
                               std::string* matchedName = nullptr) {
        const std::string p = prefix ? prefix : "";
        for (auto& kv : bodies) {
            if (kv.first.rfind(p, 0) == 0 && kv.second->GetType() == type) {
                if (matchedName) *matchedName = kv.first;
                return kv.second;
            }
        }
        return nullptr;
    }

    int countPrefixWithType(const char* prefix, b2BodyType type) const {
        const std::string p = prefix ? prefix : "";
        int count = 0;
        for (const auto& kv : bodies) {
            if (kv.first.rfind(p, 0) == 0 && kv.second->GetType() == type)
                ++count;
        }
        return count;
    }

    b2Body* createBox(const char* name, float x, float y,
                      float width, float height,
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
        ++boxesCreated;
        return body;
    }

    b2Body* createCircle(const char* name, float x, float y,
                         float radius, float density,
                         float friction, float restitution) {
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
        ++circlesCreated;
        return body;
    }

    void step(float dt) {
        if (physicsEnabled) {
            world.Step(dt, 8, 3);
            world.ClearForces();
        }
    }
};

static PhysicsBridge* gPhysics = nullptr;
static SpriteDB* gSprites = nullptr;
static int gGenericStubCalls = 0;
static int gMenuBypassCalls = 0;

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

static void setfn(lua_State* L, const char* name, lua_CFunction fn) {
    lua_pushcfunction(L, fn);
    lua_setglobal(L, name);
}

static int generic_stub(lua_State* L) {
    const char* name = lua_tostring(L, lua_upvalueindex(1));
    ++gGenericStubCalls;
    std::printf("[GameLua stub] %s argc=%d\n",
                name ? name : "<unknown>", lua_gettop(L));
    return 0;
}

static void register_stub(lua_State* L, const char* name) {
    lua_pushstring(L, name);
    lua_pushcclosure(L, generic_stub, 1);
    lua_setglobal(L, name);
}

static void ensure_objects_world(lua_State* L) {
    lua_getglobal(L, "objects");
    if (!lua_istable(L, -1)) {
        lua_pop(L, 1);
        lua_newtable(L);
        lua_pushvalue(L, -1);
        lua_setglobal(L, "objects");
    }

    lua_getfield(L, -1, "world");
    if (!lua_istable(L, -1)) {
        lua_pop(L, 1);
        lua_newtable(L);
        lua_pushvalue(L, -1);
        lua_setfield(L, -3, "world");
    }
    // stack: objects, world
}

static void set_number_field(lua_State* L, const char* key, float value) {
    lua_pushnumber(L, value);
    lua_setfield(L, -2, key);
}

static void set_string_field(lua_State* L, const char* key, const char* value) {
    lua_pushstring(L, value ? value : "");
    lua_setfield(L, -2, key);
}

static void create_lua_object_box(lua_State* L, const char* name, const char* sprite,
                                  float x, float y, float width, float height) {
    ensure_objects_world(L);
    lua_newtable(L);
    set_string_field(L, "name", name);
    set_string_field(L, "sprite", sprite);
    set_number_field(L, "x", x);
    set_number_field(L, "y", y);
    set_number_field(L, "width", width);
    set_number_field(L, "height", height);
    lua_pushvalue(L, -1);
    lua_setfield(L, -3, name);
    lua_pop(L, 3); // object copy + world + objects
}

static void create_lua_object_circle(lua_State* L, const char* name, const char* sprite,
                                     float x, float y, float radius) {
    ensure_objects_world(L);
    lua_newtable(L);
    set_string_field(L, "name", name);
    set_string_field(L, "sprite", sprite);
    set_number_field(L, "x", x);
    set_number_field(L, "y", y);
    set_number_field(L, "radius", radius);
    lua_pushvalue(L, -1);
    lua_setfield(L, -3, name);
    lua_pop(L, 3);
}

static bool set_object_field_string(lua_State* L, const char* name,
                                    const char* key, const char* value) {
    lua_getglobal(L, "objects");
    if (!lua_istable(L, -1)) { lua_pop(L, 1); return false; }
    lua_getfield(L, -1, "world");
    if (!lua_istable(L, -1)) { lua_pop(L, 2); return false; }
    lua_getfield(L, -1, name);
    if (!lua_istable(L, -1)) { lua_pop(L, 3); return false; }
    lua_pushstring(L, value ? value : "");
    lua_setfield(L, -2, key);
    lua_pop(L, 3);
    return true;
}

static bool set_object_field_number(lua_State* L, const char* name,
                                    const char* key, float value) {
    lua_getglobal(L, "objects");
    if (!lua_istable(L, -1)) { lua_pop(L, 1); return false; }
    lua_getfield(L, -1, "world");
    if (!lua_istable(L, -1)) { lua_pop(L, 2); return false; }
    lua_getfield(L, -1, name);
    if (!lua_istable(L, -1)) { lua_pop(L, 3); return false; }
    lua_pushnumber(L, value);
    lua_setfield(L, -2, key);
    lua_pop(L, 3);
    return true;
}

static b2Body* require_body(lua_State* L, int index) {
    const char* name = luaL_checkstring(L, index);
    b2Body* b = gPhysics->find(name);
    if (!b) luaL_error(L, "unknown physics object '%s'", name);
    return b;
}

static int l_setPhysicsSimulationScale(lua_State* L) {
    gPhysics->simulationScale = (float)luaL_checknumber(L, 1);
    std::printf("[GameLua/Box2D] setPhysicsSimulationScale(%.6f)\n",
                (double)gPhysics->simulationScale);
    return 0;
}

static int l_setPhysicsEnabled(lua_State* L) {
    gPhysics->physicsEnabled = lua_toboolean(L, 1) != 0;
    std::printf("[GameLua/Box2D] setPhysicsEnabled(%s)\n",
                gPhysics->physicsEnabled ? "true" : "false");
    return 0;
}

static int l_isPhysicsEnabled(lua_State* L) {
    lua_pushboolean(L, gPhysics->physicsEnabled ? 1 : 0);
    return 1;
}

static int l_createBox(lua_State* L) {
    const char* name = luaL_checkstring(L, 1);
    const char* sprite = luaL_checkstring(L, 2);
    const float x = (float)luaL_checknumber(L, 3);
    const float y = (float)luaL_checknumber(L, 4);
    const float w = (float)luaL_checknumber(L, 5);
    const float h = (float)luaL_checknumber(L, 6);
    const float density = (float)luaL_checknumber(L, 7);
    const float friction = (float)luaL_checknumber(L, 8);
    const float restitution = (float)luaL_checknumber(L, 9);
    (void)lua_toboolean(L, 10);
    (void)lua_toboolean(L, 11);
    (void)luaL_checknumber(L, 12);

    b2Body* b = gPhysics->createBox(name, x, y, w, h, density, friction, restitution);
    create_lua_object_box(L, name, sprite, x, y, w, h);

    std::printf("[Level1/GameLua] BOX    %-18s pos=(%7.3f,%7.3f) size=(%6.3f,%6.3f) density=%5.2f mass=%8.5f\n",
                name, (double)x, (double)y, (double)w, (double)h,
                (double)density, (double)b->GetMass());
    return 0;
}

static int l_createCircle(lua_State* L) {
    const char* name = luaL_checkstring(L, 1);
    const char* sprite = luaL_checkstring(L, 2);
    const float x = (float)luaL_checknumber(L, 3);
    const float y = (float)luaL_checknumber(L, 4);
    const float radius = (float)luaL_checknumber(L, 5);
    const float density = (float)luaL_checknumber(L, 6);
    const float friction = (float)luaL_checknumber(L, 7);
    const float restitution = (float)luaL_checknumber(L, 8);
    (void)lua_toboolean(L, 9);
    (void)luaL_checknumber(L, 10);

    b2Body* b = gPhysics->createCircle(name, x, y, radius, density, friction, restitution);
    create_lua_object_circle(L, name, sprite, x, y, radius);

    std::printf("[Level1/GameLua] CIRCLE %-18s pos=(%7.3f,%7.3f) r=%5.3f density=%5.2f mass=%8.5f\n",
                name, (double)x, (double)y, (double)radius,
                (double)density, (double)b->GetMass());
    return 0;
}

static int l_setRotation(lua_State* L) {
    const char* name = luaL_checkstring(L, 1);
    b2Body* b = require_body(L, 1);
    float a = (float)luaL_checknumber(L, 2);
    const float twoPi = 6.2831853071795864769f;
    a = std::fmod(a, twoPi);
    if (a < 0.0f) a += twoPi;
    b->SetTransform(b->GetPosition(), a);
    set_object_field_number(L, name, "angle", a);
    return 0;
}

static int l_setPosition(lua_State* L) {
    const char* name = luaL_checkstring(L, 1);
    b2Body* b = require_body(L, 1);
    const float x = (float)luaL_checknumber(L, 2);
    const float y = (float)luaL_checknumber(L, 3);
    b->SetTransform(b2Vec2(x, y), b->GetAngle());
    set_object_field_number(L, name, "x", x);
    set_object_field_number(L, name, "y", y);
    return 0;
}

static int l_setVelocity(lua_State* L) {
    b2Body* b = require_body(L, 1);
    if (b->GetType() != b2_staticBody) {
        b->SetLinearVelocity(b2Vec2((float)luaL_checknumber(L, 2),
                                    (float)luaL_checknumber(L, 3)));
    }
    return 0;
}

static int l_setAngularVelocity(lua_State* L) {
    b2Body* b = require_body(L, 1);
    if (b->GetType() != b2_staticBody)
        b->SetAngularVelocity((float)luaL_checknumber(L, 2));
    return 0;
}

static int l_applyImpulse(lua_State* L) {
    b2Body* b = require_body(L, 1);
    const b2Vec2 impulse((float)luaL_checknumber(L, 2),
                         (float)luaL_checknumber(L, 3));
    const b2Vec2 point((float)luaL_checknumber(L, 4),
                       (float)luaL_checknumber(L, 5));
    if (b->GetType() == b2_dynamicBody) b->ApplyLinearImpulse(impulse, point);
    return 0;
}

static int l_applyForce(lua_State* L) {
    b2Body* b = require_body(L, 1);
    const b2Vec2 force((float)luaL_checknumber(L, 2),
                       (float)luaL_checknumber(L, 3));
    const b2Vec2 point((float)luaL_checknumber(L, 4),
                       (float)luaL_checknumber(L, 5));
    if (b->GetType() == b2_dynamicBody) b->ApplyForce(force, point);
    return 0;
}

static int l_setSleeping(lua_State* L) {
    b2Body* b = require_body(L, 1);
    b->SetAwake(lua_toboolean(L, 2) ? false : true);
    return 0;
}

static int l_removeObject(lua_State* L) {
    const char* name = luaL_checkstring(L, 1);
    auto it = gPhysics->bodies.find(name);
    if (it != gPhysics->bodies.end()) {
        gPhysics->world.DestroyBody(it->second);
        gPhysics->bodies.erase(it);
    }
    return 0;
}

static int l_getAngle(lua_State* L) {
    lua_pushnumber(L, require_body(L, 1)->GetAngle());
    return 1;
}

static int l_getWorldPoint(lua_State* L) {
    b2Body* b = require_body(L, 1);
    const b2Vec2 p = b->GetWorldPoint(
        b2Vec2((float)luaL_checknumber(L, 2),
               (float)luaL_checknumber(L, 3)));
    lua_pushnumber(L, p.x);
    lua_pushnumber(L, p.y);
    return 2;
}

static int l_setMaterial(lua_State* L) {
    const char* name = luaL_checkstring(L, 1);
    const char* material = luaL_checkstring(L, 2);
    set_object_field_string(L, name, "material", material);
    return 0;
}

static int l_setTexture(lua_State* L) {
    const char* name = luaL_checkstring(L, 1);
    const char* texture = luaL_checkstring(L, 2);
    set_object_field_string(L, name, "texture", texture);
    return 0;
}

static int l_setObjectParameter(lua_State* L) {
    const char* name = luaL_checkstring(L, 1);
    const int selector = (int)luaL_checknumber(L, 2);
    const int value = (int)luaL_checknumber(L, 3);

    set_object_field_number(L, name, "lastObjectParameterSelector", (float)selector);
    set_object_field_number(L, name, "lastObjectParameterValue", (float)value);

    // Recovered from the original ARMv7 GameLua:
    // selector 2 toggles Box2D body type (0=static, nonzero=dynamic).
    if (selector == 2) {
        b2Body* b = gPhysics->find(name);
        if (b) {
            b->SetType(value != 0 ? b2_dynamicBody : b2_staticBody);
        }
    }
    return 0;
}

static int l_requestAd(lua_State*) {
    return 0;
}

static int l_initializeMenu(lua_State*) {
    ++gMenuBypassCalls;
    return 0;
}

static int l_os_time(lua_State* L) {
    lua_pushnumber(L, 1281398400.0f);
    return 1;
}

static int l_getSpriteBounds(lua_State* L) {
    (void)luaL_checkstring(L, 1); // bundle/group, empty in createObject
    const char* sprite = luaL_checkstring(L, 2);
    const SpriteInfo* s = gSprites->find(sprite);
    if (!s)
        return luaL_error(L, "sprite bounds not found for '%s'", sprite);
    lua_pushnumber(L, (lua_Number)s->width);
    lua_pushnumber(L, (lua_Number)s->height);
    return 2;
}

static int l_getSpritePivot(lua_State* L) {
    (void)luaL_checkstring(L, 1);
    const char* sprite = luaL_checkstring(L, 2);
    const SpriteInfo* s = gSprites->find(sprite);
    if (!s)
        return luaL_error(L, "sprite pivot not found for '%s'", sprite);
    lua_pushnumber(L, (lua_Number)s->pivotX);
    lua_pushnumber(L, (lua_Number)s->pivotY);
    return 2;
}


static int l_noop(lua_State*) {
    return 0;
}

static int l_loadLevel(lua_State* L) {
    const char* path = luaL_checkstring(L, 1);
    std::printf("[GameLua] loadLevel('%s')\n", path);

    int rc = luaL_loadfile(L, path);
    if (rc != 0) {
        return luaL_error(L, "loadLevel: luaL_loadfile failed: %s",
                          lua_tostring(L, -1));
    }

    // Reconstruct the old GameLua level-loading environment:
    // level globals are written into a private table while reads fall through
    // to the game global environment. The resulting table becomes loadedObjects.
    lua_newtable(L);                 // func, env
    lua_newtable(L);                 // func, env, mt
    lua_pushvalue(L, LUA_GLOBALSINDEX);
    lua_setfield(L, -2, "__index");
    lua_setmetatable(L, -2);         // func, env

    lua_pushvalue(L, -1);            // func, env, env-copy
    lua_setfenv(L, -3);              // func, env

    lua_insert(L, -2);               // env, func
    rc = lua_pcall(L, 0, 0, 0);     // env
    if (rc != 0) {
        const char* err = lua_tostring(L, -1);
        return luaL_error(L, "loadLevel: level chunk failed: %s",
                          err ? err : "<no message>");
    }

    // Stack now holds the private environment.
    lua_getfield(L, -1, "world");
    int worldCount = 0;
    if (lua_istable(L, -1)) {
        lua_pushnil(L);
        while (lua_next(L, -2) != 0) {
            ++worldCount;
            lua_pop(L, 1);
        }
    }
    lua_pop(L, 1);

    lua_getfield(L, -1, "physicsToWorld");
    const double ptw = lua_isnumber(L, -1) ? (double)lua_tonumber(L, -1) : -1.0;
    lua_pop(L, 1);

    lua_pushvalue(L, -1);
    lua_setglobal(L, "loadedObjects");
    lua_pop(L, 1);

    std::printf("[GameLua] loadLevel -> loadedObjects world=%d physicsToWorld=%.6f\n",
                worldCount, ptw);
    return 0;
}

static bool exec_file(lua_State* L, const std::string& path, const char* name) {
    int rc = luaL_loadfile(L, path.c_str());
    if (rc == 0) rc = lua_pcall(L, 0, 0, 0);
    if (rc != 0) {
        std::printf("[stage6] %-18s FAIL: %s\n",
                    name, lua_tostring(L, -1));
        lua_pop(L, 1);
        return false;
    }
    std::printf("[stage6] %-18s EXEC OK\n", name);
    return true;
}

static bool run_chunk(lua_State* L, const char* text, const char* name) {
    int rc = luaL_loadbuffer(L, text, std::strlen(text), name);
    if (rc == 0) rc = lua_pcall(L, 0, 0, 0);
    if (rc != 0) {
        std::printf("[stage6] %s FAIL: %s\n",
                    name, lua_tostring(L, -1));
        lua_pop(L, 1);
        return false;
    }
    return true;
}

static double get_global_number(lua_State* L, const char* name) {
    lua_getglobal(L, name);
    const double v = lua_isnumber(L, -1) ? (double)lua_tonumber(L, -1) : NAN;
    lua_pop(L, 1);
    return v;
}

static int table_count(lua_State* L, const char* globalName) {
    lua_getglobal(L, globalName);
    if (!lua_istable(L, -1)) { lua_pop(L, 1); return -1; }
    int count = 0;
    lua_pushnil(L);
    while (lua_next(L, -2) != 0) {
        ++count;
        lua_pop(L, 1);
    }
    lua_pop(L, 1);
    return count;
}

static bool finite_body(const b2Body* b) {
    const b2Vec2 p = b->GetPosition();
    const b2Vec2 v = b->GetLinearVelocity();
    return std::isfinite(p.x) && std::isfinite(p.y) &&
           std::isfinite(v.x) && std::isfinite(v.y) &&
           std::isfinite(b->GetAngle());
}

int main(int argc, char** argv) {
    std::setvbuf(stdout, nullptr, _IONBF, 0);
    std::setvbuf(stderr, nullptr, _IONBF, 0);

    if (argc != 5) {
        std::fprintf(stderr,
            "usage: %s <scripts-dir> <Level1.lua> <INGAME_BLOCKS_1.dat> <INGAME_BIRDS_1.dat>\n",
            argv[0]);
        return 2;
    }

    std::printf("[angry-stage7] ORIGINAL loadLevelInternal() / ORIGINAL Level1 / BOX2D 2.1.2 / ARM64\n");

    PhysicsBridge physics;
    SpriteDB sprites;
    gPhysics = &physics;
    gSprites = &sprites;

    if (!sprites.loadSheet(argv[3]) || !sprites.loadSheet(argv[4])) {
        return 3;
    }
    std::printf("[stage7] sprite database total=%zu\n", sprites.size());

    lua_State* L = luaL_newstate();
    if (!L) return 4;

    open_lib(L, luaopen_base, "");
    open_lib(L, luaopen_table, LUA_TABLIBNAME);
    open_lib(L, luaopen_string, LUA_STRLIBNAME);
    open_lib(L, luaopen_math, LUA_MATHLIBNAME);

    lua_newtable(L);
    lua_pushcfunction(L, l_os_time);
    lua_setfield(L, -2, "time");
    lua_setglobal(L, "os");

    // Original resource API used by createObject() and the slingshot placement.
    lua_newtable(L);
    lua_pushcfunction(L, l_getSpriteBounds);
    lua_setfield(L, -2, "getSpriteBounds");
    lua_pushcfunction(L, l_getSpritePivot);
    lua_setfield(L, -2, "getSpritePivot");
    lua_pushcfunction(L, l_noop);
    lua_setfield(L, -2, "stopAllAudio");
    lua_setglobal(L, "res");

    lua_pushnumber(L, 480.0f); lua_setglobal(L, "screenWidth");
    lua_pushnumber(L, 320.0f); lua_setglobal(L, "screenHeight");
    lua_pushstring(L, "android-arm64-bootstrap"); lua_setglobal(L, "deviceModel");

    lua_newtable(L);
    lua_pushnumber(L, 0.0f); lua_setfield(L, -2, "x");
    lua_pushnumber(L, 0.0f); lua_setfield(L, -2, "y");
    lua_setglobal(L, "cursor");

    const char* files[] = {
        "animations.lua", "blocks.lua", "loadlist.lua",
        "particles.lua", "starLimits.lua", "gamelogic.lua"
    };
    for (const char* f : files) {
        const std::string path = std::string(argv[1]) + "/" + f;
        if (!exec_file(L, path, f)) {
            lua_close(L);
            return 5;
        }
    }

    // Install the complete recovered 80-name native surface first.
    for (const char* n : kBindings) register_stub(L, n);

    // Real/reconstructed GameLua path.
    setfn(L, "loadLevel", l_loadLevel);
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
    setfn(L, "setMaterial", l_setMaterial);
    setfn(L, "setTexture", l_setTexture);
    setfn(L, "setObjectParameter", l_setObjectParameter);

    // Headless boundaries: these are rendering/menu/camera/platform services,
    // not level physics. Keep the original Lua control flow, but make the
    // service calls harmless.
    setfn(L, "releaseCutScenes", l_noop);
    setfn(L, "prepareMenuPage", l_noop);
    setfn(L, "setAnimationState", l_noop);
    setfn(L, "setTheme", l_noop);
    setfn(L, "setWorldScale", l_noop);
    setfn(L, "setBGColor", l_noop);
    setfn(L, "initCameras", l_noop);
    setfn(L, "addToAchievementUnlockQueue", l_noop);
    setfn(L, "setSprite", l_noop);
    setfn(L, "requestAd", l_noop);
    setfn(L, "initializeMenu", l_initializeMenu);

    // Globals that the original Android application normally creates in the
    // wider startup/menu script graph. We only supply shape/state required by
    // loadLevelInternal; the actual level loader remains original bytecode.
    const char* headlessBootstrap = R"LUA(
objects = objects or {}
objects.world = objects.world or {}
objects.joints = objects.joints or {}
objects.counts = objects.counts or {}

screen = screen or {x=0, y=0}
levelStartPosition = levelStartPosition or {x=0, y=0}
rubberBandPos = rubberBandPos or {x=0, y=0}
baitSardine = baitSardine or {x=0, y=0}

loadingPage = loadingPage or {}
tutorials = tutorials or {}
pausePage = pausePage or {offsetX=0, backgroundOverlay={shade=0}}
pausePage.backgroundOverlay = pausePage.backgroundOverlay or {shade=0}
pauseBGw = pauseBGw or 0

elementAnimations = elementAnimations or {}
elementAnimations.ingamePausePageScroll =
    elementAnimations.ingamePausePageScroll or {percentage=100}

settings = settings or {}
settings.tutorials = settings.tutorials or {}
settings.openGoldenEggLevels = settings.openGoldenEggLevels or {}

currentWorldNumber = 1
currentLevelNumberInTheme = 1
currentGameMode = false

blockDestroyedScoreIncrement = blockDestroyedScoreIncrement or 500
pigletteDestroyedScoreIncrement = pigletteDestroyedScoreIncrement or 5000
birdsLeftScoreIncrement = birdsLeftScoreIncrement or 10000

blockTable = {
    blocks = blocks,
    materials = materials,
    themes = themes,
    groups = groups,
    damageFactors = damageFactors
}
)LUA";

    if (!run_chunk(L, headlessBootstrap, "stage7-headless-bootstrap")) {
        lua_close(L);
        return 6;
    }

    // Original initialize(): establishes physicsToWorld=20, physicsScale=.05.
    // It also rebuilds several UI/game-state tables. In v0.8 that clobbered
    // the headless elementAnimations.ingamePausePageScroll seed before
    // loadLevelInternal() could use it. Re-apply the headless *shape* after
    // initialize() so the original loader sees the same structural globals
    // that the full application/menu bootstrap would normally provide.
    lua_getglobal(L, "initialize");
    if (!lua_isfunction(L, -1) || lua_pcall(L, 0, 0, 0) != 0) {
        std::printf("[stage7] initialize() FAIL: %s\n",
                    lua_tostring(L, -1));
        lua_close(L);
        return 7;
    }

    // Diagnostic: prove initialize() is the point that replaced the seed.
    lua_getglobal(L, "elementAnimations");
    if (lua_istable(L, -1)) {
        lua_getfield(L, -1, "ingamePausePageScroll");
        std::printf("[stage7] post-initialize ingamePausePageScroll type=%s\n",
                    lua_typename(L, lua_type(L, -1)));
        lua_pop(L, 1);
    } else {
        std::printf("[stage7] post-initialize elementAnimations type=%s\n",
                    lua_typename(L, lua_type(L, -1)));
    }
    lua_pop(L, 1);

    if (!run_chunk(L, headlessBootstrap, "stage7-headless-bootstrap-post-init")) {
        lua_close(L);
        return 71;
    }

    lua_getglobal(L, "elementAnimations");
    lua_getfield(L, -1, "ingamePausePageScroll");
    std::printf("[stage7] restored ingamePausePageScroll type=%s\n",
                lua_typename(L, lua_type(L, -1)));
    lua_pop(L, 2);

    std::printf("[stage7] CALL ORIGINAL loadLevelInternal('%s')\n", argv[2]);
    lua_getglobal(L, "loadLevelInternal");
    if (!lua_isfunction(L, -1)) {
        std::fprintf(stderr, "[stage7] loadLevelInternal is not a function\n");
        lua_close(L);
        return 8;
    }
    lua_pushstring(L, argv[2]);
    if (lua_pcall(L, 1, 0, 0) != 0) {
        std::printf("[stage7] loadLevelInternal() FAIL: %s\n",
                    lua_tostring(L, -1));
        lua_pop(L, 1);
        lua_close(L);
        return 9;
    }

    std::printf("[stage7] ORIGINAL loadLevelInternal() RETURNED NORMALLY\n");

    // Verify the state produced by the original loader.
    lua_getglobal(L, "objects");
    int objectCount = -1;
    if (lua_istable(L, -1)) {
        lua_getfield(L, -1, "world");
        if (lua_istable(L, -1)) {
            objectCount = 0;
            lua_pushnil(L);
            while (lua_next(L, -2) != 0) {
                ++objectCount;
                lua_pop(L, 1);
            }
        }
        lua_pop(L, 1);
    }
    lua_pop(L, 1);

    const int birdCount = table_count(L, "birds");
    const int goalCount = table_count(L, "levelGoals");
    const double leftEdge = get_global_number(L, "levelLeftEdge");
    const double rightEdge = get_global_number(L, "levelRightEdge");

    lua_getglobal(L, "levelStartPosition");
    double startX = NAN, startY = NAN;
    if (lua_istable(L, -1)) {
        lua_getfield(L, -1, "x");
        if (lua_isnumber(L, -1)) startX = lua_tonumber(L, -1);
        lua_pop(L, 1);
        lua_getfield(L, -1, "y");
        if (lua_isnumber(L, -1)) startY = lua_tonumber(L, -1);
        lua_pop(L, 1);
    }
    lua_pop(L, 1);

    int dynamicBodies = 0;
    int staticBodies = 0;
    bool finite = true;
    for (const auto& kv : physics.bodies) {
        if (kv.second->GetType() == b2_dynamicBody) ++dynamicBodies;
        if (kv.second->GetType() == b2_staticBody) ++staticBodies;
        finite = finite_body(kv.second) && finite;
    }

    std::printf("[stage7] objects.world=%d physicsBodies=%zu boxes=%d circles=%d\n",
                objectCount, physics.bodies.size(),
                physics.boxesCreated, physics.circlesCreated);
    std::printf("[stage7] birds=%d levelGoals=%d bodyTypes dynamic=%d static=%d\n",
                birdCount, goalCount, dynamicBodies, staticBodies);
    std::printf("[stage7] level edges left=%.6f right=%.6f\n",
                leftEdge, rightEdge);
    std::printf("[stage7] original loader levelStartPosition=(%.6f,%.6f)\n",
                startX, startY);

    std::string pigName, activeRedName;
    b2Body* pig = physics.findPrefix("SmallPiglette_", &pigName);
    b2Body* activeRed =
        physics.findPrefixWithType("RedBird_", b2_dynamicBody, &activeRedName);
    b2Body* ground = physics.find("ground");

    const int dynamicRedBirds =
        physics.countPrefixWithType("RedBird_", b2_dynamicBody);
    const int staticRedBirds =
        physics.countPrefixWithType("RedBird_", b2_staticBody);

    std::printf("[stage7] RedBird body states: dynamic=%d static=%d\n",
                dynamicRedBirds, staticRedBirds);
    for (const auto& kv : physics.bodies) {
        if (kv.first.rfind("RedBird_", 0) == 0) {
            std::printf("[stage7]   %-12s type=%s mass=%.6f pos=(%.6f,%.6f)\n",
                        kv.first.c_str(),
                        kv.second->GetType() == b2_dynamicBody ? "dynamic" :
                        kv.second->GetType() == b2_staticBody ? "static" : "kinematic",
                        (double)kv.second->GetMass(),
                        (double)kv.second->GetPosition().x,
                        (double)kv.second->GetPosition().y);
        }
    }

    if (!pig || !activeRed || !ground) {
        std::fprintf(stderr,
            "[stage7] expected Level1 sample bodies missing "
            "(pig=%s activeRed=%s ground=%s)\n",
            pig ? "yes" : "no",
            activeRed ? "yes" : "no",
            ground ? "yes" : "no");
        lua_close(L);
        return 10;
    }

    std::printf("[stage7] sample bodies pig=%s activeRed=%s\n",
                pigName.c_str(), activeRedName.c_str());
    std::printf("[stage7] sample masses pig=%.6f activeRed=%.6f\n",
                (double)pig->GetMass(), (double)activeRed->GetMass());

    // initialize() intentionally disables physics; the actual application enables
    // simulation as part of the outer game-mode flow. For this headless probe,
    // enable it only after the original loader has returned.
    physics.physicsEnabled = true;
    for (int i = 0; i < 120; ++i)
        physics.step(1.0f / 60.0f);

    for (const auto& kv : physics.bodies)
        finite = finite_body(kv.second) && finite;

    std::printf("[stage7] after 120x1/60 %s pos=(%.6f,%.6f) vel=(%.6f,%.6f)\n",
                pigName.c_str(),
                (double)pig->GetPosition().x,
                (double)pig->GetPosition().y,
                (double)pig->GetLinearVelocity().x,
                (double)pig->GetLinearVelocity().y);

    const double expectedRedMass =
        3.14159265358979323846 * 0.85 * 0.85 * 6.0;
    const double expectedPigMass =
        3.14159265358979323846 * 1.075 * 1.075 * 2.0;

    bool ok = true;
    ok = (sprites.size() == 360) && ok;
    ok = (objectCount == 21) && ok;
    ok = (physics.bodies.size() == 21) && ok;
    ok = (physics.boxesCreated == 17) && ok;
    ok = (physics.circlesCreated == 4) && ok;
    ok = (birdCount == 3) && ok;
    ok = (goalCount == 1) && ok;
    // Stage 6 had 18 dynamic / 3 static bodies. The original loader's
    // getNextBird/body-type path leaves two queued birds static, yielding 16/5.
    ok = (dynamicBodies == 16) && ok;
    ok = (staticBodies == 5) && ok;
    ok = (std::fabs(pig->GetMass() - expectedPigMass) < 0.003) && ok;
    ok = (std::fabs(activeRed->GetMass() - expectedRedMass) < 0.003) && ok;
    ok = (dynamicRedBirds == 1) && ok;
    ok = (staticRedBirds == 2) && ok;
    ok = (ground->GetType() == b2_staticBody) && ok;
    ok = std::isfinite(leftEdge) && std::isfinite(rightEdge) && ok;
    ok = std::isfinite(startX) && std::isfinite(startY) && ok;
    ok = finite && ok;
    ok = (gMenuBypassCalls == 1) && ok;

    lua_close(L);
    gPhysics = nullptr;
    gSprites = nullptr;

    if (!ok) {
        std::fprintf(stderr, "[angry-stage7] FAIL semantic verification\n");
        return 11;
    }

    std::printf("[angry-stage7] ORIGINAL loadLevelInternal() LOADED LEVEL1 THROUGH RECONSTRUCTED loadLevel()\n");
    std::printf("[angry-stage7] ORIGINAL filterLoadedLevel/createObject/getNextBird PATH COMPLETED\n");
    std::printf("[angry-stage7] 21 REAL BOX2D LEVEL1 BODIES SURVIVED 120 STEPS ON ANDROID ARM64\n");
    std::printf("[angry-stage7] PASS\n");
    return 0;
}
