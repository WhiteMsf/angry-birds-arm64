#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iterator>
#include <map>
#include <set>
#include <string>
#include <vector>

extern "C" {
#include "vendor/lua-5.1.5/src/lua.h"
#include "vendor/lua-5.1.5/src/lauxlib.h"
#include "vendor/lua-5.1.5/src/lualib.h"
#include "vendor/lua-5.1.5/src/lstate.h"
#include "vendor/lua-5.1.5/src/lobject.h"
}

#include <Box2D/Box2D.h>

static const Proto* gLastLuaProto = nullptr;
static int gLastLuaPc = -1;
static std::map<const Proto*, std::string> gLuaProtoNames;

static void index_global_lua_functions(lua_State* L) {
    gLuaProtoNames.clear();

    lua_pushvalue(L, LUA_GLOBALSINDEX);
    const int globals = lua_gettop(L);
    lua_pushnil(L);

    while (lua_next(L, globals) != 0) {
        if (lua_type(L, -2) == LUA_TSTRING &&
            lua_isfunction(L, -1) &&
            !lua_iscfunction(L, -1)) {
            const void* ptr = lua_topointer(L, -1);
            if (ptr) {
                const Closure* cl = static_cast<const Closure*>(ptr);
                gLuaProtoNames[cl->l.p] = lua_tostring(L, -2);
            }
        }
        lua_pop(L, 1);
    }

    lua_pop(L, 1);
}

static const char* proto_name(const Proto* p) {
    const auto it = gLuaProtoNames.find(p);
    if (it != gLuaProtoNames.end())
        return it->second.c_str();
    return "<unmapped-lua-proto>";
}

static void exact_vm_hook(lua_State* L, lua_Debug*) {
    if (!L || !L->ci || !L->ci->func)
        return;

    const TValue* fn = L->ci->func;
    if (!isLfunction(fn))
        return;

    const Closure* cl = clvalue(fn);
    const Proto* p = cl->l.p;
    gLastLuaProto = p;

    // Lua 5.1's VM increments pc before invoking the count hook.
    if (L->savedpc && p && p->code)
        gLastLuaPc = static_cast<int>(L->savedpc - p->code - 1);
    else
        gLastLuaPc = -1;
}

static int traced_error_handler(lua_State* L) {
    const char* msg = lua_tostring(L, 1);
    std::fprintf(stderr,
        "[stage8-debug] error='%s'\n",
        msg ? msg : "<non-string error>");
    std::fprintf(stderr,
        "[stage8-debug] last stripped Lua instruction: function=%s pc=%d proto=%p\n",
        proto_name(gLastLuaProto),
        gLastLuaPc,
        static_cast<const void*>(gLastLuaProto));

    for (int level = 0; level < 16; ++level) {
        lua_Debug ar;
        if (!lua_getstack(L, level, &ar))
            break;
        if (!lua_getinfo(L, "nS", &ar))
            continue;

        std::fprintf(stderr,
            "[stage8-debug] stack[%d] name=%s namewhat=%s what=%s source=%s line=%d\n",
            level,
            ar.name ? ar.name : "?",
            ar.namewhat ? ar.namewhat : "?",
            ar.what ? ar.what : "?",
            ar.short_src,
            ar.currentline);
    }

    // Preserve the original error object for lua_pcall().
    lua_settop(L, 1);
    return 1;
}

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


struct ContactTrace {
    int frame = 0;
    std::string a;
    std::string b;
    float relativeSpeed = 0.0f;
    float armv7MomentumForce = 0.0f;
    float x = 0.0f;
    float y = 0.0f;
};


struct DamageTrace {
    int frame = 0;
    std::string objectName;
    float collisionMetric = 0.0f;
    float defence = 0.0f;
    float strengthBefore = 0.0f;
    float strengthAfter = 0.0f;
    float actualDamage = 0.0f;
    std::string spriteBefore;
    std::string spriteAfter;
};

struct PhysicsBridge : public b2ContactListener {
    b2World world;
    std::map<std::string, b2Body*> bodies;
    float simulationScale = 1.0f;
    bool physicsEnabled = true;
    int boxesCreated = 0;
    int circlesCreated = 0;

    int contactFrame = 0;
    int beginContactCount = 0;
    int endContactCount = 0;
    int postSolveCount = 0;
    float maxArmv7MomentumForce = 0.0f;
    float maxSolverNormalImpulse = 0.0f;
    std::vector<ContactTrace> beginContacts;
    std::set<std::string> uniqueContactPairs;

    // Stage 10: non-destructive reconstruction of the ARMv7 block/block
    // strength/defence path. The Lua state is owned by main(); Box2D callbacks
    // occur only after it has been attached here.
    lua_State* L = nullptr;
    bool enableRecoveredBlockDamage = false;
    bool callbackError = false;
    bool unsupportedDestructionReached = false;
    std::string callbackErrorText;
    int originalBlockCollisionCalls = 0;
    int damageMutationCount = 0;
    float totalActualDamage = 0.0f;
    std::vector<DamageTrace> damageTraces;

    PhysicsBridge() : world(b2Vec2(0.0f, 10.0f), true) {
        // The original ARMv7 GameLua is itself a b2ContactListener.
        // Stage 9 restores that native architectural boundary first as
        // telemetry, before mutating gameplay state from collisions.
        world.SetContactListener(this);
    }

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


    std::string nameOf(const b2Body* body) const {
        for (const auto& kv : bodies) {
            if (kv.second == body)
                return kv.first;
        }
        return std::string();
    }

    static std::string canonicalPair(const std::string& a,
                                     const std::string& b) {
        return a < b ? (a + "|" + b) : (b + "|" + a);
    }


    bool objectIsTable(const std::string& name) const {
        if (!L)
            return false;

        lua_getglobal(L, "objects");
        if (!lua_istable(L, -1)) {
            lua_pop(L, 1);
            return false;
        }

        lua_getfield(L, -1, "world");
        if (!lua_istable(L, -1)) {
            lua_pop(L, 2);
            return false;
        }

        lua_getfield(L, -1, name.c_str());
        const bool ok = lua_istable(L, -1);
        lua_pop(L, 3);
        return ok;
    }

    bool objectBool(const std::string& name, const char* field,
                    bool fallback = false) const {
        if (!L)
            return fallback;

        bool out = fallback;
        lua_getglobal(L, "objects");
        if (lua_istable(L, -1)) {
            lua_getfield(L, -1, "world");
            if (lua_istable(L, -1)) {
                lua_getfield(L, -1, name.c_str());
                if (lua_istable(L, -1)) {
                    lua_getfield(L, -1, field);
                    if (lua_isboolean(L, -1))
                        out = lua_toboolean(L, -1) != 0;
                    lua_pop(L, 1);
                }
                lua_pop(L, 1);
            }
            lua_pop(L, 1);
        }
        lua_pop(L, 1);
        return out;
    }

    bool objectNumber(const std::string& name, const char* field,
                      float* value) const {
        if (!L || !value)
            return false;

        bool ok = false;
        lua_getglobal(L, "objects");
        if (lua_istable(L, -1)) {
            lua_getfield(L, -1, "world");
            if (lua_istable(L, -1)) {
                lua_getfield(L, -1, name.c_str());
                if (lua_istable(L, -1)) {
                    lua_getfield(L, -1, field);
                    if (lua_isnumber(L, -1)) {
                        *value = static_cast<float>(lua_tonumber(L, -1));
                        ok = true;
                    }
                    lua_pop(L, 1);
                }
                lua_pop(L, 1);
            }
            lua_pop(L, 1);
        }
        lua_pop(L, 1);
        return ok;
    }

    bool setObjectNumber(const std::string& name, const char* field,
                         float value) const {
        if (!L)
            return false;

        bool ok = false;
        lua_getglobal(L, "objects");
        if (lua_istable(L, -1)) {
            lua_getfield(L, -1, "world");
            if (lua_istable(L, -1)) {
                lua_getfield(L, -1, name.c_str());
                if (lua_istable(L, -1)) {
                    lua_pushnumber(L, value);
                    lua_setfield(L, -2, field);
                    ok = true;
                }
                lua_pop(L, 1);
            }
            lua_pop(L, 1);
        }
        lua_pop(L, 1);
        return ok;
    }

    std::string objectString(const std::string& name,
                             const char* field) const {
        std::string out;
        if (!L)
            return out;

        lua_getglobal(L, "objects");
        if (lua_istable(L, -1)) {
            lua_getfield(L, -1, "world");
            if (lua_istable(L, -1)) {
                lua_getfield(L, -1, name.c_str());
                if (lua_istable(L, -1)) {
                    lua_getfield(L, -1, field);
                    if (lua_isstring(L, -1))
                        out = lua_tostring(L, -1);
                    lua_pop(L, 1);
                }
                lua_pop(L, 1);
            }
            lua_pop(L, 1);
        }
        lua_pop(L, 1);
        return out;
    }

    // Recovered ARMv7 non-bird damage core for one object.
    //
    // Exact behavior recovered from GameLua::BeginContact:
    //   if strength is numeric:
    //      defence defaults to 0 if missing
    //      if collisionMetric >= defence:
    //          damage = collisionMetric - defence
    //          strength -= damage
    //          actualDamage += min(damage, oldStrength)
    //          damagedFlag = true
    //
    // The <=0 path additionally queues the object for native destruction.
    // That queue is not yet reconstructed, so Stage 10 deliberately refuses
    // to fake that state transition.
    bool applyRecoveredDamageToObject(const std::string& name,
                                      float collisionMetric,
                                      bool* damageFlag) {
        if (!L || !damageFlag)
            return false;

        float strength = 0.0f;
        if (!objectNumber(name, "strength", &strength))
            return true; // exact native path simply has nothing to mutate.

        float defence = 0.0f;
        (void)objectNumber(name, "defence", &defence);

        if (collisionMetric < defence)
            return true;

        const float requestedDamage = collisionMetric - defence;
        const float newStrength = strength - requestedDamage;
        *damageFlag = true;

        if (newStrength <= 0.0f) {
            unsupportedDestructionReached = true;
            std::fprintf(stderr,
                "[stage10-damage] DESTRUCTION BOUNDARY frame=%d object=%s "
                "strength=%.6f defence=%.6f metric=%.6f proposed=%.6f\n",
                contactFrame, name.c_str(),
                (double)strength, (double)defence,
                (double)collisionMetric, (double)newStrength);
            return false;
        }

        const std::string spriteBefore = objectString(name, "damageSprite");
        if (!setObjectNumber(name, "strength", newStrength))
            return false;

        DamageTrace d;
        d.frame = contactFrame;
        d.objectName = name;
        d.collisionMetric = collisionMetric;
        d.defence = defence;
        d.strengthBefore = strength;
        d.strengthAfter = newStrength;
        d.actualDamage = requestedDamage;
        d.spriteBefore = spriteBefore;
        damageTraces.push_back(d);

        ++damageMutationCount;
        totalActualDamage += requestedDamage;

        std::printf(
            "[stage10-damage] frame=%3d %-18s strength=%8.4f -> %8.4f "
            "defence=%6.3f metric=%7.4f damage=%7.4f\n",
            contactFrame, name.c_str(),
            (double)strength, (double)newStrength,
            (double)defence, (double)collisionMetric,
            (double)requestedDamage);
        return true;
    }

    bool callOriginalBlockCollision(const std::string& nameA,
                                    const std::string& nameB,
                                    float collisionMetric,
                                    bool damageFlag) {
        if (!L)
            return false;

        lua_getglobal(L, "blockCollision");
        if (!lua_isfunction(L, -1)) {
            lua_pop(L, 1);
            callbackError = true;
            callbackErrorText = "global blockCollision is not a function";
            return false;
        }

        lua_pushstring(L, nameA.c_str());
        lua_pushstring(L, nameB.c_str());
        lua_pushnumber(L, collisionMetric);
        lua_pushboolean(L, damageFlag ? 1 : 0);

        if (lua_pcall(L, 4, 0, 0) != 0) {
            callbackError = true;
            callbackErrorText =
                lua_tostring(L, -1) ? lua_tostring(L, -1)
                                    : "<non-string Lua error>";
            std::fprintf(stderr,
                "[stage10-callback] blockCollision ERROR frame=%d: %s\n",
                contactFrame, callbackErrorText.c_str());
            lua_pop(L, 1);
            return false;
        }

        ++originalBlockCollisionCalls;
        return true;
    }

    void BeginContact(b2Contact* contact) override {
        if (!contact)
            return;

        b2Fixture* fixtureA = contact->GetFixtureA();
        b2Fixture* fixtureB = contact->GetFixtureB();
        if (!fixtureA || !fixtureB)
            return;

        b2Body* bodyA = fixtureA->GetBody();
        b2Body* bodyB = fixtureB->GetBody();
        if (!bodyA || !bodyB)
            return;

        const std::string nameA = nameOf(bodyA);
        const std::string nameB = nameOf(bodyB);
        if (nameA.empty() || nameB.empty())
            return;

        const b2Vec2 vA = bodyA->GetLinearVelocity();
        const b2Vec2 vB = bodyB->GetLinearVelocity();
        const b2Vec2 dv = vA - vB;

        // Exact scalar recovered from the original ARMv7 BeginContact
        // unflagged/block branch:
        //
        //   0.1 * | massA * velocityA - massB * velocityB |
        //
        // It is intentionally named "armv7MomentumForce" rather than a
        // physical SI force; it is the game's collision metric.
        const b2Vec2 momentumDelta =
            bodyA->GetMass() * vA - bodyB->GetMass() * vB;
        const float nativeMetric = 0.1f * momentumDelta.Length();

        b2WorldManifold wm;
        contact->GetWorldManifold(&wm);
        float px = 0.0f;
        float py = 0.0f;
        if (contact->GetManifold() &&
            contact->GetManifold()->pointCount > 0) {
            px = wm.points[0].x;
            py = wm.points[0].y;
        }

        ContactTrace t;
        t.frame = contactFrame;
        t.a = nameA;
        t.b = nameB;
        t.relativeSpeed = dv.Length();
        t.armv7MomentumForce = nativeMetric;
        t.x = px;
        t.y = py;
        beginContacts.push_back(t);

        ++beginContactCount;
        uniqueContactPairs.insert(canonicalPair(nameA, nameB));
        if (nativeMetric > maxArmv7MomentumForce)
            maxArmv7MomentumForce = nativeMetric;

        if (!enableRecoveredBlockDamage || !L || callbackError ||
            unsupportedDestructionReached) {
            return;
        }

        // RenderObjectData +0x87 in the ARMv7 binary separates the
        // controllable/bird path from the ordinary block path. The Lua
        // materialized object mirrors that state as `controllable`.
        const bool controllableA = objectBool(nameA, "controllable", false);
        const bool controllableB = objectBool(nameB, "controllable", false);
        if (controllableA || controllableB) {
            // Bird/contact damageFactors + legacy path is intentionally Stage 11.
            return;
        }

        bool damageFlagA = false;
        bool damageFlagB = false;

        if (!applyRecoveredDamageToObject(nameA, nativeMetric, &damageFlagA))
            return;
        if (!applyRecoveredDamageToObject(nameB, nativeMetric, &damageFlagB))
            return;

        const bool damageFlag = damageFlagA || damageFlagB;

        const std::string spriteABefore = objectString(nameA, "damageSprite");
        const std::string spriteBBefore = objectString(nameB, "damageSprite");

        if (!callOriginalBlockCollision(nameA, nameB,
                                        nativeMetric, damageFlag)) {
            return;
        }

        const std::string spriteAAfter = objectString(nameA, "damageSprite");
        const std::string spriteBAfter = objectString(nameB, "damageSprite");

        // Associate post-callback sprite transitions with this contact's most
        // recent damage mutations for readable corpus output.
        for (auto it = damageTraces.rbegin(); it != damageTraces.rend(); ++it) {
            if (it->frame != contactFrame)
                break;
            if (it->objectName == nameA && it->spriteAfter.empty())
                it->spriteAfter = spriteAAfter;
            if (it->objectName == nameB && it->spriteAfter.empty())
                it->spriteAfter = spriteBAfter;
        }

        if (damageFlag) {
            std::printf(
                "[stage10-callback] frame=%3d blockCollision('%s','%s',"
                "%.4f,true) sprites: '%s'->'%s' | '%s'->'%s'\n",
                contactFrame,
                nameA.c_str(), nameB.c_str(), (double)nativeMetric,
                spriteABefore.c_str(), spriteAAfter.c_str(),
                spriteBBefore.c_str(), spriteBAfter.c_str());
        }
    }

    void EndContact(b2Contact*) override {
        ++endContactCount;
    }

    void PreSolve(b2Contact*, const b2Manifold*) override {
        // The original GameLua::PreSolve is a 4-byte no-op.
    }

    void PostSolve(b2Contact* contact,
                   const b2ContactImpulse* impulse) override {
        // Box2D 2.1.2's b2ContactImpulse predates the later public `count`
        // member. The number of valid impulse slots comes from the contact's
        // current manifold pointCount instead.
        //
        // The original GameLua inherits the no-op PostSolve implementation.
        // We only collect solver impulse as independent telemetry; gameplay
        // still uses the recovered BeginContact metric.
        ++postSolveCount;
        if (!contact || !impulse)
            return;

        const b2Manifold* manifold = contact->GetManifold();
        if (!manifold)
            return;

        int count = manifold->pointCount;
        if (count < 0)
            count = 0;
        if (count > b2_maxManifoldPoints)
            count = b2_maxManifoldPoints;

        float total = 0.0f;
        for (int i = 0; i < count; ++i)
            total += std::fabs(impulse->normalImpulses[i]);

        if (total > maxSolverNormalImpulse)
            maxSolverNormalImpulse = total;
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

    void step(float dt, int frame = 0) {
        if (physicsEnabled) {
            contactFrame = frame;
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
    lua_pushboolean(L, gPhysics->physicsEnabled ? 1 : 0);
    lua_setglobal(L, "physicsEnabled");
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


static bool alias_camera_profile(lua_State* L, int envIndex,
                                 const char* tableName,
                                 const char* deviceModel) {
    // lua_absindex() only appeared after Lua 5.1. This project intentionally
    // builds against the original 5.1 API, so normalize ordinary negative
    // stack indices manually while preserving pseudo-indices unchanged.
    if (envIndex < 0 && envIndex > LUA_REGISTRYINDEX)
        envIndex = lua_gettop(L) + envIndex + 1;

    lua_getfield(L, envIndex, tableName);
    if (!lua_istable(L, -1)) {
        lua_pop(L, 1);
        return false;
    }

    const int cameraTable = lua_gettop(L);

    // If this level already has a native profile for the platform, keep it.
    lua_getfield(L, cameraTable, deviceModel);
    const bool alreadyPresent = lua_istable(L, -1);
    lua_pop(L, 1);
    if (alreadyPresent) {
        lua_pop(L, 1);
        return true;
    }

    // Every original 1.4.2 phone level carries an "iphone" 480x320 camera
    // profile, while the Lua runtime itself has explicit "android" platform
    // branches. The old native loadLevel path therefore has to bridge the
    // platform name to a concrete camera profile before gameplay uses
    // cameraData[deviceModel].
    //
    // Our Stage 8 viewport is the exact 480x320 phone profile, so alias the
    // original iphone camera table by reference; do not rewrite its values.
    lua_getfield(L, cameraTable, "iphone");
    if (!lua_istable(L, -1)) {
        lua_pop(L, 2);
        return false;
    }

    lua_setfield(L, cameraTable, deviceModel);
    lua_pop(L, 1);

    std::printf("[GameLua] %s.%s -> original iphone 480x320 profile\n",
                tableName, deviceModel);
    return true;
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
    const int levelEnv = lua_gettop(L);

    lua_getglobal(L, "deviceModel");
    const char* deviceModel =
        lua_isstring(L, -1) ? lua_tostring(L, -1) : "android";
    const std::string deviceModelCopy = deviceModel ? deviceModel : "android";
    lua_pop(L, 1);

    const bool birdCameraAliased =
        alias_camera_profile(L, levelEnv, "birdCameraData",
                             deviceModelCopy.c_str());
    const bool castleCameraAliased =
        alias_camera_profile(L, levelEnv, "castleCameraData",
                             deviceModelCopy.c_str());

    std::printf("[GameLua] camera profile bridge deviceModel='%s' bird=%s castle=%s\n",
                deviceModelCopy.c_str(),
                birdCameraAliased ? "OK" : "MISSING",
                castleCameraAliased ? "OK" : "MISSING");

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


static int l_res_noop(lua_State*) {
    return 0;
}

static int l_res_isAudioPlaying(lua_State* L) {
    lua_pushboolean(L, 0);
    return 1;
}

static void set_bool_field(lua_State* L, const char* key, bool value) {
    lua_pushboolean(L, value ? 1 : 0);
    lua_setfield(L, -2, key);
}

static bool sync_physics_to_lua(lua_State* L) {
    lua_getglobal(L, "objects");
    if (!lua_istable(L, -1)) {
        lua_pop(L, 1);
        return false;
    }

    lua_getfield(L, -1, "world");
    if (!lua_istable(L, -1)) {
        lua_pop(L, 2);
        return false;
    }

    bool hasMovingObjects = false;

    for (const auto& kv : gPhysics->bodies) {
        b2Body* body = kv.second;
        lua_getfield(L, -1, kv.first.c_str());

        if (lua_istable(L, -1)) {
            const b2Vec2 p = body->GetPosition();
            const b2Vec2 v = body->GetLinearVelocity();
            const float av = body->GetAngularVelocity();

            set_number_field(L, "x", p.x);
            set_number_field(L, "y", p.y);
            set_number_field(L, "xVel", v.x);
            set_number_field(L, "yVel", v.y);
            set_number_field(L, "angle", body->GetAngle());
            set_number_field(L, "angularVelocity", av);
            set_number_field(L, "mass", body->GetMass());
            set_bool_field(L, "sleeping", !body->IsAwake());

            if (body->GetType() == b2_dynamicBody) {
                const float speed2 = v.x * v.x + v.y * v.y;
                if (speed2 > 0.0001f || std::fabs(av) > 0.01f)
                    hasMovingObjects = true;
            }
        }

        lua_pop(L, 1);
    }

    lua_pop(L, 2); // world, objects

    lua_pushboolean(L, hasMovingObjects ? 1 : 0);
    lua_setglobal(L, "hasMovingObjects");
    return true;
}


static bool get_object_bool(lua_State* L, const std::string& name,
                            const char* field, bool fallback=false) {
    bool out = fallback;

    lua_getglobal(L, "objects");
    if (!lua_istable(L, -1)) {
        lua_pop(L, 1);
        return out;
    }

    lua_getfield(L, -1, "world");
    if (!lua_istable(L, -1)) {
        lua_pop(L, 2);
        return out;
    }

    lua_getfield(L, -1, name.c_str());
    if (lua_istable(L, -1)) {
        lua_getfield(L, -1, field);
        if (lua_isboolean(L, -1))
            out = lua_toboolean(L, -1) != 0;
        lua_pop(L, 1);
    }

    lua_pop(L, 3);
    return out;
}

static int get_global_bool(lua_State* L, const char* name, bool fallback=false) {
    lua_getglobal(L, name);
    const int value = lua_isboolean(L, -1) ? lua_toboolean(L, -1) : (fallback ? 1 : 0);
    lua_pop(L, 1);
    return value;
}

static std::string get_global_string(lua_State* L, const char* name) {
    lua_getglobal(L, name);
    std::string out;
    if (lua_isstring(L, -1))
        out = lua_tostring(L, -1);
    lua_pop(L, 1);
    return out;
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

    std::printf("[angry-stage10] RECOVERED BLOCK DAMAGE / ORIGINAL blockCollision / LEVEL1 / ARM64\n");

    PhysicsBridge physics;
    SpriteDB sprites;
    gPhysics = &physics;
    gSprites = &sprites;

    if (!sprites.loadSheet(argv[3]) || !sprites.loadSheet(argv[4]))
        return 3;

    lua_State* L = luaL_newstate();
    if (!L) return 4;

    physics.L = L;

    open_lib(L, luaopen_base, "");
    open_lib(L, luaopen_table, LUA_TABLIBNAME);
    open_lib(L, luaopen_string, LUA_STRLIBNAME);
    open_lib(L, luaopen_math, LUA_MATHLIBNAME);

    lua_newtable(L);
    lua_pushcfunction(L, l_os_time);
    lua_setfield(L, -2, "time");
    lua_setglobal(L, "os");

    // Resource surface used by logic. Rendering/audio remain headless.
    lua_newtable(L);
    lua_pushcfunction(L, l_getSpriteBounds);
    lua_setfield(L, -2, "getSpriteBounds");
    lua_pushcfunction(L, l_getSpritePivot);
    lua_setfield(L, -2, "getSpritePivot");
    lua_pushcfunction(L, l_res_noop);
    lua_setfield(L, -2, "stopAllAudio");
    lua_pushcfunction(L, l_res_noop);
    lua_setfield(L, -2, "stopAudio");
    lua_pushcfunction(L, l_res_noop);
    lua_setfield(L, -2, "playAudio");
    lua_pushcfunction(L, l_res_isAudioPlaying);
    lua_setfield(L, -2, "isAudioPlaying");
    lua_pushcfunction(L, l_res_noop);
    lua_setfield(L, -2, "drawString");
    lua_setglobal(L, "res");

    lua_pushnumber(L, 480.0f); lua_setglobal(L, "screenWidth");
    lua_pushnumber(L, 320.0f); lua_setglobal(L, "screenHeight");
    lua_pushstring(L, "android"); lua_setglobal(L, "deviceModel");

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

    // Map Lua closure Proto* -> global function name before native bindings
    // replace any names. This lets the stripped-bytecode VM hook report the
    // exact original function and instruction PC on a runtime failure.
    index_global_lua_functions(L);

    for (const char* n : kBindings) register_stub(L, n);

    // Reconstructed native GameLua physics/loader surface.
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

    // Headless service boundary. We deliberately keep update(), updateGame(),
    // animateBirdToSlingShot(), updateCharacterAnimations(), scoring, level
    // completion checks and camera-independent gameplay Lua ORIGINAL.
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
    setfn(L, "drawGame", l_noop);
    setfn(L, "initializeMenu", l_initializeMenu);

    const char* startupBootstrap = R"LUA(
-- Reuse the full Stage 7 structural bootstrap. Stage 8 v0.9 accidentally
-- dropped several fields that the original loadLevelInternal() still expects.

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
pausePage.offsetX = pausePage.offsetX or 0
pausePage.backgroundOverlay = pausePage.backgroundOverlay or {shade=0}
pausePage.backgroundOverlay.shade = pausePage.backgroundOverlay.shade or 0
pauseBGw = pauseBGw or 0

elementAnimations = elementAnimations or {}
elementAnimations.ingamePausePageScroll =
    elementAnimations.ingamePausePageScroll or {percentage=100, state="HIDDEN"}
elementAnimations.ingamePausePageScroll.percentage =
    elementAnimations.ingamePausePageScroll.percentage or 100
elementAnimations.ingamePausePageScroll.state =
    elementAnimations.ingamePausePageScroll.state or "HIDDEN"

settings = settings or {}
settings.tutorials = settings.tutorials or {}
settings.openGoldenEggLevels = settings.openGoldenEggLevels or {}
settings.playtime = settings.playtime or 0

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

    if (!run_chunk(L, startupBootstrap, "stage8-startup-bootstrap")) {
        lua_close(L);
        return 6;
    }

    lua_getglobal(L, "initialize");
    if (!lua_isfunction(L, -1) || lua_pcall(L, 0, 0, 0) != 0) {
        std::printf("[stage8] initialize() FAIL: %s\n", lua_tostring(L, -1));
        lua_close(L);
        return 7;
    }

    // initialize() recreates elementAnimations, same discovery as Stage 7.
    if (!run_chunk(L, startupBootstrap, "stage8-post-init-bootstrap")) {
        lua_close(L);
        return 8;
    }

    std::printf("[stage8] pre-loader scaffold: pauseBGw=%.6f levelStartPosition=%s screen=%s\n",
                get_global_number(L, "pauseBGw"),
                "table",
                "table");

    lua_getglobal(L, "loadLevelInternal");
    lua_pushstring(L, argv[2]);
    if (lua_pcall(L, 1, 0, 0) != 0) {
        std::printf("[stage8] loadLevelInternal() FAIL: %s\n",
                    lua_tostring(L, -1));
        lua_close(L);
        return 9;
    }

    std::printf("[stage8] original Level1 loader RETURNED NORMALLY; bodies=%zu\n",
                physics.bodies.size());

    // The original loader can queue first-run tutorial popups. In the real
    // application those are dismissed by rendered UI/input. A headless harness
    // has no popup renderer, so leaving the queue populated traps updateGame()
    // in its tutorial branch: physics is forced off and the function returns
    // before levelStartTimer/gameTimer advance.
    //
    // Preserve the original gameplay code, but mark the UI-only tutorial queue
    // as already dismissed for this headless Stage 8.
    const int tutorialQueueBefore = table_count(L, "birdTutorialPopups");
    const char* dismissTutorials = R"LUA(
birdTutorialPopups = {}
)LUA";
    if (!run_chunk(L, dismissTutorials, "stage8-dismiss-headless-tutorials")) {
        lua_close(L);
        return 91;
    }
    std::printf("[stage8] headless tutorial queue dismissed: before=%d after=%d\n",
                tutorialQueueBefore, table_count(L, "birdTutorialPopups"));

    const char* hideHeadlessPauseUI = R"LUA(
elementAnimations = elementAnimations or {}
elementAnimations.ingamePausePageScroll =
    elementAnimations.ingamePausePageScroll or {}
elementAnimations.ingamePausePageScroll.percentage = 100
elementAnimations.ingamePausePageScroll.state = "HIDDEN"
)LUA";
    if (!run_chunk(L, hideHeadlessPauseUI, "stage8-hide-headless-pause-ui")) {
        lua_close(L);
        return 92;
    }

    // These globals are supplied by the native input/platform layer in the
    // original application rather than by gamelogic.lua itself.
    const char* frameBootstrap = R"LUA(
keyPressed = {}
keyReleased = {}
keyHold = {}

time = 0
playtimeCounter = 0
doubleClickState = 0
doubleClick = false

prepareMenusAfterAd = false
newMenuPageNeedsPrepare = nil
newMenuPage = nil
newPopupPage = nil
newPopupPageNeedsPrepare = nil
additionalPopupPageDelay = nil
loadLevelDelayed = nil
popupPage = nil
currentMenuPage = nil

isHidingAd = false
isShowingAd = false
videoAdRequested = false
videoReady = false
assetsCreated = false
gameCenterEnabled = false
checkForCrystalEnabled = false

-- Camera/rendering is outside Stage 8. Prevent defaultCamera from becoming
-- the only non-headless dependency in the gameplay update.
cameraFunction = nil

-- Native app normally has these bookkeeping values available.
lastAdTime = time
lastVideoAdTime = time
adHidingStartedTime = nil
adShowingStartedTime = nil
scoreAdOffsetY = 0

-- Audio group metadata is normally populated by the resource/bootstrap layer.
-- In headless Stage 8 we deliberately provide an empty map. The ORIGINAL
-- getAudioName(name) function explicitly handles a missing group by returning
-- the input name unchanged; our res.playAudio/stopAudio are no-ops.
audioGroups = audioGroups or {}

-- Keep the original game-mode transition function. Its native setGameOn /
-- Crystal hooks are already harmless recovered stubs.
setGameMode(updateGame)
)LUA";

    if (!run_chunk(L, frameBootstrap, "stage8-frame-bootstrap")) {
        lua_close(L);
        return 10;
    }

    if (!sync_physics_to_lua(L)) {
        std::fprintf(stderr, "[stage8] initial physics->Lua sync failed\n");
        lua_close(L);
        return 11;
    }

    const int birdCountBefore = table_count(L, "birds");
    const int goalCountBefore = table_count(L, "levelGoals");
    const size_t bodyCountBefore = physics.bodies.size();

    std::string activeBirdName;
    b2Body* activeBird =
        physics.findPrefixWithType("RedBird_", b2_dynamicBody, &activeBirdName);
    b2Body* pig = physics.findPrefix("SmallPiglette_");

    if (!activeBird || !pig) {
        std::fprintf(stderr, "[stage8] active bird/pig missing before frame loop\n");
        lua_close(L);
        return 12;
    }

    std::printf("[stage8] before frames: birds=%d goals=%d bodies=%zu activeBird=%s physics=%s\n",
                birdCountBefore, goalCountBefore, bodyCountBefore,
                activeBirdName.c_str(),
                physics.physicsEnabled ? "on" : "off");

    // Stage 10 turns on the recovered native block/block mutation only after
    // the original level has fully materialized and the headless UI bootstrap
    // is complete. Contacts do not occur before original updateGame enables
    // Box2D at the level-start gate anyway.
    physics.enableRecoveredBlockDamage = true;

    float pigStrengthInitial = NAN;
    float wood6_3StrengthInitial = NAN;
    physics.objectNumber("SmallPiglette_7", "strength", &pigStrengthInitial);
    physics.objectNumber("WoodBlock6_3", "strength", &wood6_3StrengthInitial);
    const std::string pigSpriteInitial =
        physics.objectString("SmallPiglette_7", "damageSprite");

    std::printf(
        "[stage10] initial damage state: pig strength=%.6f sprite='%s' "
        "WoodBlock6_3 strength=%.6f\n",
        (double)pigStrengthInitial, pigSpriteInitial.c_str(),
        (double)wood6_3StrengthInitial);

    const float dt = 1.0f / 60.0f;

    size_t processedContactEvents = 0;
    int classifiedBirdCollision = 0;
    int classifiedBlockCollision = 0;
    int printedContactEvents = 0;

    const auto processNewContacts = [&](int frame) {
        while (processedContactEvents < physics.beginContacts.size()) {
            const ContactTrace& ev =
                physics.beginContacts[processedContactEvents++];

            const bool controllableA =
                get_object_bool(L, ev.a, "controllable", false);
            const bool controllableB =
                get_object_bool(L, ev.b, "controllable", false);

            const char* expectedLuaCallback = nullptr;
            if (controllableA || controllableB) {
                ++classifiedBirdCollision;
                expectedLuaCallback = "birdCollision";
            } else {
                ++classifiedBlockCollision;
                expectedLuaCallback = "blockCollision";
            }

            if (printedContactEvents < 32) {
                std::printf(
                    "[stage9-contact] frame=%3d %-18s <-> %-18s "
                    "relSpeed=%8.4f armv7Metric=%8.4f point=(%7.3f,%7.3f) "
                    "class=%s\n",
                    frame,
                    ev.a.c_str(), ev.b.c_str(),
                    (double)ev.relativeSpeed,
                    (double)ev.armv7MomentumForce,
                    (double)ev.x, (double)ev.y,
                    expectedLuaCallback);
                ++printedContactEvents;
            }
        }
    };

    bool sawPhysicsEnable = physics.physicsEnabled;
    int physicsEnabledFrame = sawPhysicsEnable ? 0 : -1;

    for (int frame = 1; frame <= 120; ++frame) {
        if (!sync_physics_to_lua(L)) {
            std::fprintf(stderr, "[stage8] sync failed before frame %d\n", frame);
            lua_close(L);
            return 13;
        }

        // The failure discovered by v0.9.4 is exactly at the transition where
        // original updateGame() enables physics (~frame 61). Enable the private
        // Lua 5.1 instruction hook only near that boundary, keeping normal
        // frames cheap while giving an exact Proto + PC if another stripped
        // bytecode access fails.
        if (frame >= 58)
            lua_sethook(L, exact_vm_hook, LUA_MASKCOUNT, 1);
        else
            lua_sethook(L, nullptr, 0, 0);

        lua_pushcfunction(L, traced_error_handler);
        const int errfunc = lua_gettop(L);

        lua_getglobal(L, "update");
        if (!lua_isfunction(L, -1)) {
            std::fprintf(stderr, "[stage8] update is not a function at frame %d\n", frame);
            lua_close(L);
            return 14;
        }

        // Static bytecode analysis: update(deltaTime, frameTime).
        // R0 advances game time/currentGameMode; R1 advances the FPS timer.
        lua_pushnumber(L, dt);
        lua_pushnumber(L, dt);

        if (lua_pcall(L, 2, 0, errfunc) != 0) {
            const double t = get_global_number(L, "time");
            const double cf = get_global_number(L, "currentFrame");
            std::printf("[stage8] ORIGINAL update() FAIL frame=%d time=%.6f currentFrame=%.0f: %s\n",
                        frame, t, cf,
                        lua_tostring(L, -1) ? lua_tostring(L, -1) : "<no message>");
            lua_pop(L, 1);       // error object
            lua_remove(L, errfunc);
            lua_sethook(L, nullptr, 0, 0);
            lua_close(L);
            return 15;
        }

        lua_remove(L, errfunc);

        // The VM PC tracer is only for failures inside original update().
        // Disable it before Box2D Step(), because Stage 10 intentionally calls
        // original blockCollision() re-entrantly from BeginContact.
        lua_sethook(L, nullptr, 0, 0);

        if (!sawPhysicsEnable && physics.physicsEnabled) {
            sawPhysicsEnable = true;
            physicsEnabledFrame = frame;
            std::printf("[stage8] ORIGINAL updateGame enabled Box2D at frame=%d time=%.6f\n",
                        frame, get_global_number(L, "time"));
        }

        // The original native GameLua frame wraps the Lua update around the
        // physics world. Until collision callbacks are reconstructed in Stage 9,
        // Step() is the recovered/native half of that frame.
        physics.step(dt, frame);
        processNewContacts(frame);

        if (physics.callbackError) {
            std::fprintf(stderr,
                "[stage10] original blockCollision callback failed at frame %d: %s\n",
                frame, physics.callbackErrorText.c_str());
            lua_close(L);
            return 18;
        }
        if (physics.unsupportedDestructionReached) {
            std::fprintf(stderr,
                "[stage10] reached native destruction queue boundary at frame %d; "
                "Stage 10 refuses to fake it\n", frame);
            lua_close(L);
            return 19;
        }

        if (!sync_physics_to_lua(L)) {
            std::fprintf(stderr, "[stage8] sync failed after frame %d\n", frame);
            lua_close(L);
            return 16;
        }

        if (frame == 1 || frame == 30 || frame == 60 ||
            frame == 90 || frame == 120) {
            std::printf(
                "[stage8] frame=%3d time=%.6f currentFrame=%.0f gameTimer=%.6f "
                "levelStartTimer=%.6f physics=%s pig=(%.4f,%.4f)\n",
                frame,
                get_global_number(L, "time"),
                get_global_number(L, "currentFrame"),
                get_global_number(L, "gameTimer"),
                get_global_number(L, "levelStartTimer"),
                physics.physicsEnabled ? "on" : "off",
                (double)pig->GetPosition().x,
                (double)pig->GetPosition().y);
        }
    }

    const double timeValue = get_global_number(L, "time");
    const double frameValue = get_global_number(L, "currentFrame");
    const double gameTimer = get_global_number(L, "gameTimer");
    const int birdCountAfter = table_count(L, "birds");
    const int goalCountAfter = table_count(L, "levelGoals");
    const bool completed = get_global_bool(L, "levelCompleted", false) != 0;
    const std::string currentBirdName = get_global_string(L, "currentBirdName");

    int dynamicBodies = 0;
    int staticBodies = 0;
    bool allFinite = true;
    for (const auto& kv : physics.bodies) {
        if (kv.second->GetType() == b2_dynamicBody) ++dynamicBodies;
        if (kv.second->GetType() == b2_staticBody) ++staticBodies;
        allFinite = finite_body(kv.second) && allFinite;
    }

    std::printf("[stage8] after 120 frames: time=%.6f currentFrame=%.0f gameTimer=%.6f\n",
                timeValue, frameValue, gameTimer);
    std::printf("[stage8] state: bodies=%zu dynamic=%d static=%d birds=%d goals=%d completed=%s\n",
                physics.bodies.size(), dynamicBodies, staticBodies,
                birdCountAfter, goalCountAfter, completed ? "true" : "false");
    std::printf("[stage8] currentBirdName='%s' active-body=%s genericStubCalls=%d\n",
                currentBirdName.c_str(), activeBirdName.c_str(), gGenericStubCalls);
    std::printf("[stage8] pig final pos=(%.6f,%.6f) vel=(%.6f,%.6f)\n",
                (double)pig->GetPosition().x,
                (double)pig->GetPosition().y,
                (double)pig->GetLinearVelocity().x,
                (double)pig->GetLinearVelocity().y);

    processNewContacts(120);

    std::printf(
        "[stage9] contact corpus: begin=%d end=%d postSolve=%d uniquePairs=%zu\n",
        physics.beginContactCount,
        physics.endContactCount,
        physics.postSolveCount,
        physics.uniqueContactPairs.size());
    std::printf(
        "[stage9] callback classification: blockCollision=%d birdCollision=%d\n",
        classifiedBlockCollision,
        classifiedBirdCollision);
    std::printf(
        "[stage9] metrics: max ARMv7 BeginContact momentum metric=%.6f "
        "max Box2D solver normal impulse=%.6f\n",
        (double)physics.maxArmv7MomentumForce,
        (double)physics.maxSolverNormalImpulse);

    float pigStrengthFinal = NAN;
    float wood6_3StrengthFinal = NAN;
    physics.objectNumber("SmallPiglette_7", "strength", &pigStrengthFinal);
    physics.objectNumber("WoodBlock6_3", "strength", &wood6_3StrengthFinal);
    const std::string pigSpriteFinal =
        physics.objectString("SmallPiglette_7", "damageSprite");

    int spriteTransitionCount = 0;
    for (const DamageTrace& d : physics.damageTraces) {
        if (!d.spriteAfter.empty() && d.spriteAfter != d.spriteBefore)
            ++spriteTransitionCount;
    }

    std::printf(
        "[stage10] damage summary: mutations=%d blockCollisionCalls=%d "
        "totalActualDamage=%.6f spriteTransitions=%d\n",
        physics.damageMutationCount,
        physics.originalBlockCollisionCalls,
        (double)physics.totalActualDamage,
        spriteTransitionCount);
    std::printf(
        "[stage10] pig: strength %.6f -> %.6f sprite '%s' -> '%s'\n",
        (double)pigStrengthInitial, (double)pigStrengthFinal,
        pigSpriteInitial.c_str(), pigSpriteFinal.c_str());
    std::printf(
        "[stage10] WoodBlock6_3: strength %.6f -> %.6f\n",
        (double)wood6_3StrengthInitial, (double)wood6_3StrengthFinal);

    bool ok = true;
    ok = (bodyCountBefore == 21) && ok;
    ok = (physics.bodies.size() == 21) && ok;
    ok = (birdCountBefore == 3 && birdCountAfter == 3) && ok;
    ok = (goalCountBefore == 1 && goalCountAfter == 1) && ok;
    ok = (std::fabs(timeValue - 2.0) < 0.01) && ok;
    ok = (std::fabs(frameValue - 120.0) < 0.01) && ok;
    ok = (std::fabs(gameTimer - 2.0) < 0.02) && ok;
    ok = sawPhysicsEnable && ok;
    ok = (physicsEnabledFrame > 0 && physicsEnabledFrame <= 120) && ok;
    ok = !completed && ok;
    ok = allFinite && ok;

    // Stage 9 contact-listener proof. We deliberately do not invoke the
    // original Lua collision callbacks yet; this pass validates the native
    // callback boundary and gathers the real Level1 contact corpus first.
    ok = (physics.beginContactCount > 0) && ok;
    ok = (physics.postSolveCount > 0) && ok;
    ok = (!physics.uniqueContactPairs.empty()) && ok;
    ok = std::isfinite(physics.maxArmv7MomentumForce) && ok;
    ok = std::isfinite(physics.maxSolverNormalImpulse) && ok;
    ok = (classifiedBlockCollision + classifiedBirdCollision ==
          physics.beginContactCount) && ok;

    // Stage 10 semantic proof for the recovered *non-destructive* block path.
    ok = !physics.callbackError && ok;
    ok = !physics.unsupportedDestructionReached && ok;
    ok = (physics.damageMutationCount > 0) && ok;
    ok = (physics.originalBlockCollisionCalls > 0) && ok;
    ok = (physics.totalActualDamage > 0.0f) && ok;

    // Level1 corpus-specific cross-checks from original block/material tables:
    // SmallPiglette starts strength 4 / defence 1 and the frame-80 collision
    // metric is ~2.4385, so the native rule leaves it alive at ~2.56.
    ok = std::isfinite(pigStrengthInitial) && ok;
    ok = std::isfinite(pigStrengthFinal) && ok;
    ok = (std::fabs(pigStrengthInitial - 4.0f) < 0.01f) && ok;
    ok = (pigStrengthFinal > 2.45f && pigStrengthFinal < 2.70f) && ok;

    // Original getDamageSprite/blockCollision should advance the small pig to
    // its damaged sprite once strength drops into the 50-90% band.
    ok = (pigSpriteFinal == "PIGLETTE_SMALL_02") && ok;

    // WoodBlock6_3 takes several >2.5-defence settling contacts but survives.
    ok = std::isfinite(wood6_3StrengthInitial) && ok;
    ok = std::isfinite(wood6_3StrengthFinal) && ok;
    ok = (std::fabs(wood6_3StrengthInitial - 70.0f) < 0.01f) && ok;
    ok = (wood6_3StrengthFinal < wood6_3StrengthInitial) && ok;
    ok = (wood6_3StrengthFinal > 65.0f) && ok;

    lua_close(L);
    gPhysics = nullptr;
    gSprites = nullptr;

    if (!ok) {
        std::fprintf(stderr, "[angry-stage10] FAIL semantic verification\n");
        return 17;
    }

    std::printf("[angry-stage10] ARMV7 NON-DESTRUCTIVE STRENGTH/DEFENCE DAMAGE CORE REPRODUCED\n");
    std::printf("[angry-stage10] ORIGINAL blockCollision() RECEIVED REAL BOX2D CONTACTS\n");
    std::printf("[angry-stage10] SMALL PIGLETTE ADVANCED TO ORIGINAL DAMAGED SPRITE\n");
    std::printf("[angry-stage10] 21 LEVEL1 BODIES SURVIVED; DESTRUCTION QUEUE NOT FAKED\n");
    std::printf("[angry-stage10] PASS\n");
    return 0;
}
