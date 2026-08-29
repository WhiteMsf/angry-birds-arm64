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

    // Recovered Stage 10 collision-damage state, now running on the native
    // 30 Hz fixed-step driver recovered in Stage 11.
    lua_State* L = nullptr;
    bool enableRecoveredBlockDamage = false;
    bool enableRecoveredBirdDamage = false;
    bool callbackError = false;
    bool unsupportedDestructionReached = false;
    std::string callbackErrorText;
    int originalBlockCollisionCalls = 0;
    int originalBirdCollisionCalls = 0;
    int birdDamageMutationCount = 0;
    int queuedDeadObjects = 0;
    int nativeRemoveObjectCalls = 0;
    std::vector<std::string> removedObjectNames;

    bool birdLegacyDestructionObserved = false;
    bool birdContactDisabledOnDestruction = false;
    float birdLegacyOverkill = NAN;
    float birdLegacyVelocityScale = NAN;
    b2Vec2 birdLegacyVelocityBefore = b2Vec2(0.0f, 0.0f);
    b2Vec2 birdLegacyVelocitySet = b2Vec2(0.0f, 0.0f);
    bool birdDamageProbeApplied = false;
    float recoveredBirdCollisionForce = NAN;
    float recoveredBirdActualDamage = NAN;
    float recoveredBirdDamageMultiplier = NAN;
    float recoveredBirdVelocityMultiplier = NAN;
    float recoveredBirdStrengthBefore = NAN;
    float recoveredBirdStrengthAfter = NAN;
    float recoveredBirdDefence = NAN;
    float recoveredBirdScoreBefore = NAN;
    float recoveredBirdScoreAfter = NAN;
    std::string recoveredBirdProfile;
    std::string recoveredBirdTargetMaterial;
    std::string recoveredBirdSpriteBefore;
    std::string recoveredBirdSpriteAfter;
    bool recoveredBirdLegacyFieldPresent = false;

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

    void dumpContactCandidates(const char* tag,
                               const std::string& focusA,
                               const std::string& focusB) {
        int index = 0;
        for (b2Contact* c = world.GetContactList(); c; c = c->GetNext()) {
            b2Fixture* fa = c->GetFixtureA();
            b2Fixture* fb = c->GetFixtureB();
            const std::string a = nameOf(fa->GetBody());
            const std::string b = nameOf(fb->GetBody());

            const bool relevant =
                a == focusA || b == focusA ||
                a == focusB || b == focusB;
            if (!relevant)
                continue;

            const b2Manifold* m = c->GetManifold();

            std::printf(
                "[stage16-contactdump] %s #%d %s <-> %s "
                "touching=%s enabled=%s sensorA=%s sensorB=%s "
                "manifoldPoints=%d "
                "bodyTypeA=%d bodyTypeB=%d\n",
                tag ? tag : "<tag>",
                index,
                a.c_str(), b.c_str(),
                c->IsTouching() ? "true" : "false",
                c->IsEnabled() ? "true" : "false",
                fa->IsSensor() ? "true" : "false",
                fb->IsSensor() ? "true" : "false",
                m ? m->pointCount : -1,
                (int)fa->GetBody()->GetType(),
                (int)fb->GetBody()->GetType());

            const b2Filter filterA = fa->GetFilterData();
            const b2Filter filterB = fb->GetFilterData();
            std::printf(
                "[stage16-contactdump]   filters "
                "A(cat=0x%04x mask=0x%04x group=%d) "
                "B(cat=0x%04x mask=0x%04x group=%d)\n",
                (unsigned)filterA.categoryBits,
                (unsigned)filterA.maskBits,
                (int)filterA.groupIndex,
                (unsigned)filterB.categoryBits,
                (unsigned)filterB.maskBits,
                (int)filterB.groupIndex);

            ++index;
        }

        if (index == 0) {
            std::printf(
                "[stage16-contactdump] %s no contacts involving "
                "'%s' or '%s'\n",
                tag ? tag : "<tag>",
                focusA.c_str(), focusB.c_str());
        }
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

    bool objectFieldIsBoolean(const std::string& name,
                              const char* field) const {
        if (!L)
            return false;

        bool out = false;
        lua_getglobal(L, "objects");
        if (lua_istable(L, -1)) {
            lua_getfield(L, -1, "world");
            if (lua_istable(L, -1)) {
                lua_getfield(L, -1, name.c_str());
                if (lua_istable(L, -1)) {
                    lua_getfield(L, -1, field);
                    out = lua_isboolean(L, -1) != 0;
                    lua_pop(L, 1);
                }
                lua_pop(L, 1);
            }
            lua_pop(L, 1);
        }
        lua_pop(L, 1);
        return out;
    }

    bool damageFactorNumber(const std::string& profile,
                            const char* tableName,
                            const std::string& material,
                            float* value) const {
        if (!L || !value || profile.empty() || !tableName ||
            material.empty())
            return false;

        bool ok = false;

        // Exact ARMv7 table walk recovered from GameLua::BeginContact:
        //
        // blockTable.damageFactors[bird.damageFactors]
        //          [damageMultiplier|velocityMultiplier][block.material]
        lua_getglobal(L, "blockTable");
        if (lua_istable(L, -1)) {
            lua_getfield(L, -1, "damageFactors");
            if (lua_istable(L, -1)) {
                lua_getfield(L, -1, profile.c_str());
                if (lua_istable(L, -1)) {
                    lua_getfield(L, -1, tableName);
                    if (lua_istable(L, -1)) {
                        lua_getfield(L, -1, material.c_str());
                        if (lua_isnumber(L, -1)) {
                            *value = static_cast<float>(
                                lua_tonumber(L, -1));
                            ok = true;
                        }
                        lua_pop(L, 1);
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

    float blockScore() const {
        if (!L)
            return NAN;

        float out = NAN;
        lua_getglobal(L, "scoreTable");
        if (lua_istable(L, -1)) {
            lua_getfield(L, -1, "blocks");
            if (lua_istable(L, -1)) {
                lua_getfield(L, -1, "score");
                if (lua_isnumber(L, -1))
                    out = static_cast<float>(lua_tonumber(L, -1));
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

    // Exact non-bird strength/defence core recovered from ARMv7
    // GameLua::BeginContact.
    bool applyRecoveredDamageToObject(const std::string& name,
                                      float collisionMetric,
                                      bool* damageFlag) {
        if (!L || !damageFlag)
            return false;

        float strength = 0.0f;
        if (!objectNumber(name, "strength", &strength))
            return true;

        float defence = 0.0f;
        (void)objectNumber(name, "defence", &defence);

        if (collisionMetric < defence)
            return true;

        const float requestedDamage = collisionMetric - defence;
        const float newStrength = strength - requestedDamage;
        *damageFlag = true;

        // The original ARMv7 path queues dead objects for the native
        // removeBlocks/removeObject pipeline. That destructive boundary is
        // intentionally not guessed here.
        if (newStrength <= 0.0f) {
            unsupportedDestructionReached = true;
            std::fprintf(stderr,
                "[stage12-damage] DESTRUCTION BOUNDARY frame=%d object=%s "
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
            "[stage12-damage] frame=%3d %-18s strength=%8.4f -> %8.4f "
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
                "[stage12-callback] blockCollision ERROR frame=%d: %s\n",
                contactFrame, callbackErrorText.c_str());
            lua_pop(L, 1);
            return false;
        }

        ++originalBlockCollisionCalls;
        return true;
    }

    bool queueDeadObject(const std::string& name) {
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
        if (!lua_istable(L, -1)) {
            lua_pop(L, 3);
            return false;
        }

        lua_getglobal(L, "deadBlocks");
        if (!lua_istable(L, -1)) {
            lua_pop(L, 4);
            return false;
        }

        // Stack: objects, world, objectTable, deadBlocks
        lua_pushvalue(L, -2);
        lua_setfield(L, -2, name.c_str());
        lua_pop(L, 4);

        ++queuedDeadObjects;
        std::printf(
            "[stage16-queue] frame=%d deadBlocks['%s'] = "
            "objects.world['%s']\n",
            contactFrame, name.c_str(), name.c_str());
        return true;
    }


    bool callOriginalBirdCollision(const std::string& birdName,
                                   const std::string& targetName,
                                   float collisionForce,
                                   float actualDamageFloor) {
        if (!L)
            return false;

        lua_getglobal(L, "birdCollision");
        if (!lua_isfunction(L, -1)) {
            lua_pop(L, 1);
            callbackError = true;
            callbackErrorText = "global birdCollision is not a function";
            return false;
        }

        lua_pushstring(L, birdName.c_str());
        lua_pushstring(L, targetName.c_str());
        lua_pushnumber(L, collisionForce);
        lua_pushnumber(L, actualDamageFloor);

        if (lua_pcall(L, 4, 0, 0) != 0) {
            callbackError = true;
            callbackErrorText =
                lua_tostring(L, -1) ? lua_tostring(L, -1)
                                    : "<non-string Lua error>";
            std::fprintf(stderr,
                "[stage16-callback] birdCollision ERROR frame=%d: %s\n",
                contactFrame, callbackErrorText.c_str());
            lua_pop(L, 1);
            return false;
        }

        ++originalBirdCollisionCalls;
        return true;
    }

    bool applyRecoveredOneBirdCollision(
        b2Contact* contact,
        const std::string& nameA,
        const std::string& nameB,
        b2Body* bodyA,
        b2Body* bodyB,
        bool controllableA,
        bool controllableB) {

        if (!L || callbackError || birdDamageProbeApplied)
            return !callbackError;

        // Stage 15 is deliberately the exactly-one-special-object ARMv7 path.
        if (controllableA == controllableB)
            return true;

        const std::string birdName = controllableA ? nameA : nameB;
        const std::string targetName = controllableA ? nameB : nameA;
        b2Body* birdBody = controllableA ? bodyA : bodyB;

        // Keep the first mutation corpus pinned to the Stage 14 pair.
        if (birdName != "RedBird_4" || targetName != "WoodBlock2_6")
            return true;

        const std::string material = objectString(targetName, "material");
        const std::string profile = objectString(birdName, "damageFactors");

        float damageMultiplier = 1.0f;
        float velocityMultiplier = 1.0f;
        const bool hasDamageMultiplier =
            damageFactorNumber(profile, "damageMultiplier",
                               material, &damageMultiplier);
        const bool hasVelocityMultiplier =
            damageFactorNumber(profile, "velocityMultiplier",
                               material, &velocityMultiplier);

        // Exact ARMv7 behavior is LuaTable::isBoolean(), i.e. TYPE presence,
        // not the boolean's truth value.
        const bool legacyFieldPresent =
            objectFieldIsBoolean(birdName, "useLegacyCollisionPath");

        const b2Vec2 birdVelocity = birdBody->GetLinearVelocity();
        const float birdSpeed = birdVelocity.Length();
        const float birdMass = birdBody->GetMass();

        // Exact exactly-one-special ARMv7 scalar:
        //
        // collisionForce =
        //   (|birdVelocity| * birdMass / 10.0f) * damageMultiplier
        const float collisionForce =
            (birdSpeed * birdMass / 10.0f) * damageMultiplier;

        float strength = 0.0f;
        float defence = 0.0f;
        const bool hasStrength =
            objectNumber(targetName, "strength", &strength);
        (void)objectNumber(targetName, "defence", &defence);

        float actualDamage = 0.0f;
        float newStrength = strength;

        recoveredBirdProfile = profile;
        recoveredBirdTargetMaterial = material;
        recoveredBirdDamageMultiplier = damageMultiplier;
        recoveredBirdVelocityMultiplier = velocityMultiplier;
        recoveredBirdLegacyFieldPresent = legacyFieldPresent;
        recoveredBirdCollisionForce = collisionForce;
        recoveredBirdDefence = defence;
        recoveredBirdStrengthBefore = hasStrength ? strength : NAN;
        recoveredBirdScoreBefore = blockScore();
        recoveredBirdSpriteBefore =
            objectString(targetName, "damageSprite");

        std::printf(
            "[stage16-native] frame=%d bird=%s target=%s "
            "profile='%s' material='%s' "
            "damageMultiplier=%.6f%s velocityMultiplier=%.6f%s "
            "legacyBooleanField=%s\n",
            contactFrame,
            birdName.c_str(), targetName.c_str(),
            profile.c_str(), material.c_str(),
            (double)damageMultiplier,
            hasDamageMultiplier ? "" : "(default)",
            (double)velocityMultiplier,
            hasVelocityMultiplier ? "" : "(default)",
            legacyFieldPresent ? "present" : "absent");

        std::printf(
            "[stage16-native] bird mass=%.6f speed=%.6f "
            "velocity=(%.6f,%.6f) => collisionForce=%.6f\n",
            (double)birdMass, (double)birdSpeed,
            (double)birdVelocity.x, (double)birdVelocity.y,
            (double)collisionForce);

        if (hasStrength && collisionForce >= defence) {
            const float requestedDamage = collisionForce - defence;
            newStrength = strength - requestedDamage;

            if (!setObjectNumber(targetName, "strength", newStrength))
                return false;

            ++birdDamageMutationCount;

            if (newStrength <= 0.0f) {
                // Exact ARMv7 ordering:
                //   1) write negative/zero strength
                //   2) queue deadBlocks[target] = objectTable
                //   3) saturate actualDamage to old remaining strength
                //   4) execute the bird post-destruction velocity path
                //   5) disable this contact for the current solver step
                if (!queueDeadObject(targetName)) {
                    callbackError = true;
                    callbackErrorText =
                        "failed to queue bird-destroyed object in deadBlocks";
                    return false;
                }

                actualDamage = strength;

                if (!legacyFieldPresent) {
                    // RedBird_4 in this exact Level1 corpus has a Boolean
                    // useLegacyCollisionPath field. The alternate ARMv7 path
                    // writes a deferred RenderObjectData velocity cache and is
                    // intentionally left for a later corpus rather than
                    // guessed here.
                    callbackError = true;
                    callbackErrorText =
                        "Stage16 corpus unexpectedly entered non-legacy "
                        "bird destruction path";
                    return false;
                }

                // Exact ARMv7 legacy branch at 0x56FE8..0x57050:
                //
                // overkill = -newStrength
                // scale = min(
                //   (((overkill / birdMass) / collisionForce) * 10) * 1.75,
                //   1.0)
                // setVelocity(birdName, oldVx*scale, oldVy*scale)
                // contact.enabled = false
                const float overkill = -newStrength;
                float velocityScale =
                    (((overkill / birdMass) / collisionForce) * 10.0f)
                    * 1.75f;
                if (velocityScale > 1.0f)
                    velocityScale = 1.0f;

                const b2Vec2 scaledVelocity =
                    birdVelocity * velocityScale;

                birdBody->SetLinearVelocity(scaledVelocity);
                contact->SetEnabled(false);

                birdLegacyDestructionObserved = true;
                birdContactDisabledOnDestruction = !contact->IsEnabled();
                birdLegacyOverkill = overkill;
                birdLegacyVelocityScale = velocityScale;
                birdLegacyVelocityBefore = birdVelocity;
                birdLegacyVelocitySet = scaledVelocity;

                std::printf(
                    "[stage16-legacy] overkill=%.6f mass=%.6f "
                    "force=%.6f scale=%.6f "
                    "birdVelocity (%.6f,%.6f)->(%.6f,%.6f) "
                    "contactEnabled=%s\n",
                    (double)overkill,
                    (double)birdMass,
                    (double)collisionForce,
                    (double)velocityScale,
                    (double)birdVelocity.x,
                    (double)birdVelocity.y,
                    (double)scaledVelocity.x,
                    (double)scaledVelocity.y,
                    contact->IsEnabled() ? "true" : "false");
            } else {
                actualDamage = requestedDamage;
            }
        }

        // The helper called at ARMv7 0x4F3A4 receives the special-object
        // name, normal-object name, collisionForce, and floor(actualDamage).
        // Its call site and the original Lua 4-argument signature identify
        // this boundary as birdCollision.
        const float damageFloor = std::floor(actualDamage);

        std::printf(
            "[stage16-native] target strength=%.6f defence=%.6f "
            "actualDamage=%.6f floorDamage=%.0f newStrength=%.6f\n",
            (double)strength, (double)defence,
            (double)actualDamage, (double)damageFloor,
            (double)newStrength);

        if (!callOriginalBirdCollision(
                birdName, targetName,
                collisionForce, damageFloor)) {
            return false;
        }

        recoveredBirdStrengthAfter = newStrength;
        recoveredBirdActualDamage = actualDamage;
        recoveredBirdSpriteAfter =
            objectString(targetName, "damageSprite");
        recoveredBirdScoreAfter = blockScore();
        birdDamageProbeApplied = true;

        std::printf(
            "[stage16-callback] birdCollision('%s','%s',%.6f,%.0f) "
            "sprite '%s'->'%s' score %.3f->%.3f\n",
            birdName.c_str(), targetName.c_str(),
            (double)collisionForce, (double)damageFloor,
            recoveredBirdSpriteBefore.c_str(),
            recoveredBirdSpriteAfter.c_str(),
            (double)recoveredBirdScoreBefore,
            (double)recoveredBirdScoreAfter);

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

        if (!L || callbackError || unsupportedDestructionReached)
            return;

        const bool controllableA = objectBool(nameA, "controllable", false);
        const bool controllableB = objectBool(nameB, "controllable", false);

        if (controllableA || controllableB) {
            if (enableRecoveredBirdDamage) {
                (void)applyRecoveredOneBirdCollision(
                    contact,
                    nameA, nameB, bodyA, bodyB,
                    controllableA, controllableB);
            }
            return;
        }

        if (!enableRecoveredBlockDamage)
            return;

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
                "[stage12-callback] frame=%3d blockCollision('%s','%s',"
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

    void stepFixed(float dt, int frame = 0) {
        if (physicsEnabled) {
            contactFrame = frame;
            // Exact iteration counts recovered from ARMv7 GameLua::update(float):
            // b2World::Step(fixedDt, 10, 10).
            world.Step(dt, 10, 10);
        }
    }

    void clearForces() {
        if (physicsEnabled)
            world.ClearForces();
    }
};

static PhysicsBridge* gPhysics = nullptr;
static SpriteDB* gSprites = nullptr;
static int gGenericStubCalls = 0;
static int gMenuBypassCalls = 0;
static int gHeadlessParticleSpawnCalls = 0;

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

    if (it == gPhysics->bodies.end()) {
        std::printf(
            "[stage16-removeObject] name='%s' already absent "
            "from native map\n",
            name);
        return 0;
    }

    b2Body* body = it->second;
    const b2Vec2 p = body->GetPosition();

    // Architectural core recovered from ARMv7 GameLua::removeObject:
    // native object lookup -> b2World::DestroyBody -> remove native record.
    // WoodBlock2_6 is an ordinary unjointed Level1 block.
    gPhysics->world.DestroyBody(body);
    gPhysics->bodies.erase(it);

    ++gPhysics->nativeRemoveObjectCalls;
    gPhysics->removedObjectNames.emplace_back(name);

    std::printf(
        "[stage16-removeObject] DestroyBody('%s') "
        "pos=(%.6f,%.6f) nativeBodiesNow=%zu\n",
        name, (double)p.x, (double)p.y,
        gPhysics->bodies.size());
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


static int l_headless_particle_addParticles(lua_State* L) {
    ++gHeadlessParticleSpawnCalls;

    const char* type =
        lua_isstring(L, 1) ? lua_tostring(L, 1) : "<non-string>";
    const double x = lua_isnumber(L, 2) ? lua_tonumber(L, 2) : 0.0;
    const double y = lua_isnumber(L, 3) ? lua_tonumber(L, 3) : 0.0;

    std::printf(
        "[stage16-particles] headless particles.addParticles "
        "type='%s' x=%.3f y=%.3f argc=%d\n",
        type ? type : "<null>", x, y, lua_gettop(L));
    return 0;
}


static bool install_particle_environment_bridge(lua_State* L) {
    // Original split recovered in Stage 13:
    //
    //   particleTable.particles[type]  -> definitions from particles.lua
    //   _G.particles.addParticles(...) -> runtime/native particle surface
    //
    // Executing particles.lua directly in the bootstrap leaves only the
    // definitions table in _G.particles, so preserve it under particleTable.
    lua_getglobal(L, "particles");
    if (!lua_istable(L, -1)) {
        lua_pop(L, 1);
        std::fprintf(stderr,
            "[stage16-particles] particles.lua definitions table missing\n");
        return false;
    }

    const int definitions = lua_gettop(L);
    int definitionCount = 0;
    lua_pushnil(L);
    while (lua_next(L, definitions) != 0) {
        ++definitionCount;
        lua_pop(L, 1);
    }

    lua_newtable(L);
    lua_pushvalue(L, definitions);
    lua_setfield(L, -2, "particles");
    lua_setglobal(L, "particleTable");

    // Temporary runtime table. initialize()/loadLevelInternal() will recreate
    // _G.particles, so the method surface is attached again after loading.
    lua_newtable(L);
    lua_setglobal(L, "particles");

    lua_pop(L, 1);  // definitions

    lua_pushnumber(L, 0.0f);
    lua_setglobal(L, "particleAmount");

    std::printf(
        "[stage16-particles] reconstructed namespace split: "
        "particleTable.particles definitions=%d\n",
        definitionCount);
    return true;
}


static bool attach_particle_runtime_surface(lua_State* L) {
    // Exact original Lua resets:
    //   initialize()       -> _G.particles = {}
    //   loadLevelInternal()-> _G.particles = {}
    //
    // Attach the native runtime method only after the final level-loader reset.
    lua_getglobal(L, "particles");
    if (!lua_istable(L, -1)) {
        lua_pop(L, 1);
        std::fprintf(stderr,
            "[stage16-particles] post-loader runtime particles table missing\n");
        return false;
    }

    const int runtimeTable = lua_gettop(L);

    // Keep addParticles out of pairs(particles) by exposing it through __index.
    lua_newtable(L);  // runtime, mt
    lua_newtable(L);  // runtime, mt, methods
    lua_pushcfunction(L, l_headless_particle_addParticles);
    lua_setfield(L, -2, "addParticles");
    lua_setfield(L, -2, "__index");
    lua_setmetatable(L, runtimeTable);

    lua_getfield(L, runtimeTable, "addParticles");
    const bool ok = lua_isfunction(L, -1);
    lua_pop(L, 2);

    std::printf(
        "[stage16-particles] post-loader runtime surface attached: "
        "_G.particles.addParticles=%s\n",
        ok ? "function" : "MISSING");
    return ok;
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

static bool table_has_key(lua_State* L,
                          const char* globalName,
                          const char* key) {
    lua_getglobal(L, globalName);
    if (!lua_istable(L, -1)) {
        lua_pop(L, 1);
        return false;
    }
    lua_getfield(L, -1, key);
    const bool present = !lua_isnil(L, -1);
    lua_pop(L, 2);
    return present;
}

static bool nested_table_has_key(lua_State* L,
                                 const char* globalName,
                                 const char* childName,
                                 const char* key) {
    lua_getglobal(L, globalName);
    if (!lua_istable(L, -1)) {
        lua_pop(L, 1);
        return false;
    }
    lua_getfield(L, -1, childName);
    if (!lua_istable(L, -1)) {
        lua_pop(L, 2);
        return false;
    }
    lua_getfield(L, -1, key);
    const bool present = !lua_isnil(L, -1);
    lua_pop(L, 3);
    return present;
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

    std::printf("[angry-stage16] RED BIRD DESTRUCTION / LEGACY VELOCITY BRANCH / ARM64\n");

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

    if (!install_particle_environment_bridge(L)) {
        lua_close(L);
        return 51;
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


    if (!attach_particle_runtime_surface(L)) {
        lua_close(L);
        return 93;
    }

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

-- GameLua::BeginContact queues destroyed object tables here in the original
-- native runtime. Stage 11 keeps collision mutation disabled, so it remains
-- empty, but original removeBlocks() is called after every fixed physics step.
deadBlocks = deadBlocks or {}

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

    // Re-enable Stage 10's recovered collision mutation only after the
    // original level is fully materialized. It now runs *inside* BeginContact
    // during the correctly scheduled 30 Hz Box2D Step.
    physics.enableRecoveredBlockDamage = false;
    physics.enableRecoveredBirdDamage = true;

    b2Body* probeTarget = physics.find("WoodBlock2_6");
    if (!probeTarget) {
        std::fprintf(stderr,
            "[stage14] controlled target WoodBlock2_6 missing\n");
        lua_close(L);
        return 25;
    }

    const bool activeBirdControllable =
        get_object_bool(L, activeBirdName, "controllable", false);
    const std::string activeBirdDefinition =
        physics.objectString(activeBirdName, "definition");
    const std::string activeBirdSprite =
        physics.objectString(activeBirdName, "sprite");

    const int activeBirdBodyType = (int)activeBird->GetType();

    std::printf(
        "[stage16] bird preflight: name=%s controllable=%s "
        "definition='%s' sprite='%s' mass=%.6f bodyType=%d "
        "pos=(%.6f,%.6f)\n",
        activeBirdName.c_str(),
        activeBirdControllable ? "true" : "false",
        activeBirdDefinition.c_str(),
        activeBirdSprite.c_str(),
        (double)activeBird->GetMass(),
        activeBirdBodyType,
        (double)activeBird->GetPosition().x,
        (double)activeBird->GetPosition().y);

    std::printf(
        "[stage16] target preflight: WoodBlock2_6 mass=%.6f "
        "pos=(%.6f,%.6f) angle=%.6f rad\n",
        (double)probeTarget->GetMass(),
        (double)probeTarget->GetPosition().x,
        (double)probeTarget->GetPosition().y,
        (double)probeTarget->GetAngle());


    float stage15TargetStrengthInitial = NAN;
    float stage15TargetDefenceInitial = 0.0f;
    (void)physics.objectNumber(
        "WoodBlock2_6", "strength", &stage15TargetStrengthInitial);
    (void)physics.objectNumber(
        "WoodBlock2_6", "defence", &stage15TargetDefenceInitial);

    const std::string stage15Profile =
        physics.objectString("RedBird_4", "damageFactors");
    const std::string stage15Material =
        physics.objectString("WoodBlock2_6", "material");

    float stage15DamageMultiplier = 1.0f;
    float stage15VelocityMultiplier = 1.0f;
    const bool stage15HasDamageMultiplier =
        physics.damageFactorNumber(
            stage15Profile, "damageMultiplier",
            stage15Material, &stage15DamageMultiplier);
    const bool stage15HasVelocityMultiplier =
        physics.damageFactorNumber(
            stage15Profile, "velocityMultiplier",
            stage15Material, &stage15VelocityMultiplier);

    std::printf(
        "[stage16] preflight native-table inputs: "
        "bird.damageFactors='%s' target.material='%s' "
        "damageMultiplier=%.6f%s velocityMultiplier=%.6f%s "
        "targetStrength=%.6f targetDefence=%.6f "
        "legacyBooleanField=%s\n",
        stage15Profile.c_str(),
        stage15Material.c_str(),
        (double)stage15DamageMultiplier,
        stage15HasDamageMultiplier ? "" : "(default)",
        (double)stage15VelocityMultiplier,
        stage15HasVelocityMultiplier ? "" : "(default)",
        (double)stage15TargetStrengthInitial,
        (double)stage15TargetDefenceInitial,
        physics.objectFieldIsBoolean(
            "RedBird_4", "useLegacyCollisionPath")
            ? "present" : "absent");


    // Controlled destructive corpus: change only remaining strength.
    // Material, defence, body geometry, mass, filters and bird velocity stay
    // identical to Stage 15. With force ~=10.895 and wood defence=2.5,
    // strength=4 guarantees the recovered <=0 branch.
    const float stage16ControlledStrength = 4.0f;
    if (!physics.setObjectNumber(
            "WoodBlock2_6", "strength",
            stage16ControlledStrength)) {
        std::fprintf(stderr,
            "[stage16] failed to arm WoodBlock2_6 strength\n");
        lua_close(L);
        return 94;
    }

    const float stage16ScoreBefore = physics.blockScore();
    const bool stage16ObjectPresentBefore =
        nested_table_has_key(
            L, "objects", "world", "WoodBlock2_6");
    const bool stage16DeadQueuedBefore =
        table_has_key(L, "deadBlocks", "WoodBlock2_6");

    std::printf(
        "[stage16] armed destructive target WoodBlock2_6: "
        "strength %.6f -> %.6f; score=%.3f "
        "objects.world=%s deadBlocks=%s\n",
        (double)stage15TargetStrengthInitial,
        (double)stage16ControlledStrength,
        (double)stage16ScoreBefore,
        stage16ObjectPresentBefore ? "present" : "nil",
        stage16DeadQueuedBefore ? "present" : "nil");

    const float dt = 1.0f / 60.0f;
    const float fixedPhysicsDt = 1.0f / 30.0f;

    size_t processedContactEvents = 0;
    int classifiedBirdCollision = 0;
    int classifiedBlockCollision = 0;
    int printedContactEvents = 0;

    int activeBirdContactCount = 0;
    int firstActiveBirdContactFrame = -1;
    std::string firstActiveBirdOther;
    float firstActiveBirdRelativeSpeed = NAN;
    float firstActiveBirdBlockMetricDiagnostic = NAN;

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

                if (ev.a == activeBirdName || ev.b == activeBirdName) {
                    ++activeBirdContactCount;
                    if (firstActiveBirdContactFrame < 0) {
                        firstActiveBirdContactFrame = frame;
                        firstActiveBirdOther =
                            (ev.a == activeBirdName) ? ev.b : ev.a;
                        firstActiveBirdRelativeSpeed = ev.relativeSpeed;

                        // This scalar is the exact ordinary block/block ARMv7
                        // momentum metric already recovered in Stage 9.
                        // It is kept only as telemetry here; the one-bird
                        // native branch computes a different data-driven
                        // force/damage path and must not be guessed.
                        firstActiveBirdBlockMetricDiagnostic =
                            ev.armv7MomentumForce;
                    }
                }
            } else {
                ++classifiedBlockCollision;
                expectedLuaCallback = "blockCollision";
            }

            if (printedContactEvents < 32) {
                std::printf(
                    "[stage11-contact] frame=%3d %-18s <-> %-18s "
                    "relSpeed=%8.4f blockMetricDiag=%8.4f point=(%7.3f,%7.3f) "
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

    // Static ARMv7 GameLua::update(float) reconstruction:
    //
    //   if physicsEnabled:
    //       accumulator += dt
    //       while accumulator >= 1/30:
    //           world.Step(1/30, 10, 10)
    //           accumulator -= 1/30
    //           LuaObject::call("removeBlocks")
    //       world.ClearForces()
    //       interpolate/synchronize body state
    //   call Lua member "update"(dt, dt)
    //
    // The original interpolation/history buffers are not reconstructed yet;
    // Stage 11 uses the existing direct physics->Lua sync at the same
    // architectural position, immediately before the original Lua update().
    float physicsAccumulator = 0.0f;
    int fixedStepCount = 0;
    int removeBlocksCalls = 0;
    int updateCalls = 0;
    int firstFixedStepFrame = -1;
    int physicsEnabledFrame = physics.physicsEnabled ? 0 : -1;
    bool sawPhysicsEnable = physics.physicsEnabled;
    bool steppedOnEnableFrame = false;

    bool birdProbeInjected = false;
    int birdProbeFrame = -1;
    int birdProbeHoldSteps = 0;
    b2Vec2 stage16BirdVelocityAfterStep(0.0f, 0.0f);
    b2Vec2 birdProbeStart(0.0f, 0.0f);
    b2Vec2 birdProbeVelocity(0.0f, 0.0f);

    lua_getglobal(L, "removeBlocks");
    const bool removeBlocksAvailable = lua_isfunction(L, -1);
    lua_pop(L, 1);
    if (!removeBlocksAvailable) {
        std::fprintf(stderr,
            "[stage11] original removeBlocks is not a Lua function\n");
        lua_close(L);
        return 20;
    }

    const auto callOriginalRemoveBlocks = [&](int frame) -> bool {
        lua_getglobal(L, "removeBlocks");
        if (!lua_isfunction(L, -1)) {
            lua_pop(L, 1);
            std::fprintf(stderr,
                "[stage11] removeBlocks disappeared at frame %d\n", frame);
            return false;
        }

        if (lua_pcall(L, 0, 0, 0) != 0) {
            std::fprintf(stderr,
                "[stage11] ORIGINAL removeBlocks() FAIL frame=%d: %s\n",
                frame,
                lua_tostring(L, -1) ? lua_tostring(L, -1) : "<no message>");
            lua_pop(L, 1);
            return false;
        }

        ++removeBlocksCalls;
        return true;
    };

    std::printf(
        "[stage11] native driver constants: renderDt=%.9f fixedDt=%.9f "
        "velocityIterations=10 positionIterations=10\n",
        (double)dt, (double)fixedPhysicsDt);

    for (int frame = 1; frame <= 78; ++frame) {
        const bool physicsAtFrameStart = physics.physicsEnabled;
        int fixedStepsThisFrame = 0;

        // Native ARMv7 order: physics is evaluated BEFORE the Lua update at
        // the end of this frame. Therefore the frame that first enables
        // physics from updateGame() cannot itself execute a Box2D Step.
        if (physicsAtFrameStart) {
            physicsAccumulator += dt;

            int catchupGuard = 0;
            while (physicsAccumulator >= fixedPhysicsDt) {
                if (firstFixedStepFrame < 0) {
                    firstFixedStepFrame = frame;
                    std::printf(
                        "[stage11] FIRST native-order fixed Step frame=%d "
                        "accumulator=%.9f dt=%.9f iter=10/10\n",
                        frame,
                        (double)physicsAccumulator,
                        (double)fixedPhysicsDt);
                }

                if (frame == 67) {
                    const b2Vec2 targetPos = probeTarget->GetPosition();

                    // Stage 14 proved that exact center overlap yields a
                    // touching manifold and BeginContact in this same native
                    // fixed Step. Stage 16 injects only once because the target
                    // is expected to be destroyed immediately afterward.
                    // v0.15.2 proved a new Box2D contact object was
                    // created (world contact count 20 -> 21) but it never
                    // became touching. Remove the remaining shape-orientation
                    // ambiguity completely: place the bird center exactly at
                    // the target body's center for this diagnostic probe.
                    //
                    // This is intentionally NOT gameplay. It is a one-purpose
                    // contact-state microscope.
                    birdProbeStart = targetPos;
                    birdProbeVelocity = b2Vec2(8.0f, 0.0f);

                    activeBird->SetTransform(
                        birdProbeStart, activeBird->GetAngle());
                    activeBird->SetLinearVelocity(birdProbeVelocity);
                    activeBird->SetAngularVelocity(0.0f);
                    activeBird->SetAwake(true);

                    if (!birdProbeInjected) {
                        birdProbeInjected = true;
                        birdProbeFrame = frame;
                    }
                    ++birdProbeHoldSteps;

                    const b2Vec2 armedPos = activeBird->GetPosition();
                    const b2Vec2 armedVel = activeBird->GetLinearVelocity();

                    physics.dumpContactCandidates(
                        "BEFORE_STEP", activeBirdName, "WoodBlock2_6");

                    std::printf(
                        "[stage16-launch] HOLD center-overlap probe frame=%d "
                        "holdStep=%d bird=%s "
                        "requestedStart=(%.6f,%.6f) "
                        "actualStart=(%.6f,%.6f) "
                        "requestedVel=(%.6f,%.6f) actualVel=(%.6f,%.6f) "
                        "bodyType=%d target=WoodBlock2_6 "
                        "targetPos=(%.6f,%.6f) worldContactsBefore=%d "
                        "beginCallbacksBefore=%d\n",
                        frame, birdProbeHoldSteps,
                        activeBirdName.c_str(),
                        (double)birdProbeStart.x,
                        (double)birdProbeStart.y,
                        (double)armedPos.x,
                        (double)armedPos.y,
                        (double)birdProbeVelocity.x,
                        (double)birdProbeVelocity.y,
                        (double)armedVel.x,
                        (double)armedVel.y,
                        (int)activeBird->GetType(),
                        (double)targetPos.x,
                        (double)targetPos.y,
                        physics.world.GetContactCount(),
                        physics.beginContactCount);
                }

                physics.stepFixed(fixedPhysicsDt, frame);

                if (frame == 67) {
                    const b2Vec2 afterPos = activeBird->GetPosition();
                    const b2Vec2 afterVel = activeBird->GetLinearVelocity();
                    stage16BirdVelocityAfterStep = afterVel;
                    std::printf(
                        "[stage16-launch] AFTER fixed Step frame=%d "
                        "birdPos=(%.6f,%.6f) birdVel=(%.6f,%.6f) "
                        "worldContacts=%d beginCallbacks=%d\n",
                        frame,
                        (double)afterPos.x,
                        (double)afterPos.y,
                        (double)afterVel.x,
                        (double)afterVel.y,
                        physics.world.GetContactCount(),
                        physics.beginContactCount);

                    physics.dumpContactCandidates(
                        "AFTER_STEP", activeBirdName, "WoodBlock2_6");
                }

                ++fixedStepCount;
                ++fixedStepsThisFrame;
                physicsAccumulator -= fixedPhysicsDt;

                if (physics.callbackError) {
                    std::fprintf(stderr,
                        "[stage12] original blockCollision callback failed "
                        "at frame %d: %s\n",
                        frame, physics.callbackErrorText.c_str());
                    lua_close(L);
                    return 23;
                }
                // Exact call-site order recovered from ARMv7:
                // Step -> LuaObject::call(...) -> later ClearForces.
                if (!callOriginalRemoveBlocks(frame)) {
                    lua_close(L);
                    return 21;
                }

                if (frame == 67) {
                    const bool objectPresent =
                        nested_table_has_key(
                            L, "objects", "world",
                            "WoodBlock2_6");
                    const bool deadQueued =
                        table_has_key(
                            L, "deadBlocks",
                            "WoodBlock2_6");
                    const bool goalPresent =
                        table_has_key(
                            L, "levelGoals",
                            "WoodBlock2_6");
                    const bool nativePresent =
                        physics.find("WoodBlock2_6") != nullptr;

                    std::printf(
                        "[stage16-removeBlocks] AFTER frame=67 "
                        "objects.world=%s deadBlocks=%s "
                        "levelGoals=%s nativeBody=%s "
                        "bodies=%zu score=%.3f\n",
                        objectPresent ? "present" : "nil",
                        deadQueued ? "present" : "nil",
                        goalPresent ? "present" : "nil",
                        nativePresent ? "present" : "gone",
                        physics.bodies.size(),
                        (double)physics.blockScore());
                }

                processNewContacts(frame);

                if (++catchupGuard > 8) {
                    std::fprintf(stderr,
                        "[stage11] fixed-step catch-up guard tripped frame=%d\n",
                        frame);
                    lua_close(L);
                    return 22;
                }
            }

            // ARMv7 reaches b2World::ClearForces even on a physics-enabled
            // frame where the accumulator has not yet reached 1/30.
            physics.clearForces();
        }

        // Temporary replacement for the original RenderObjectData transform
        // interpolation/history path. Crucially this sync now occurs AFTER
        // physics and BEFORE the original Lua update, matching native order.
        if (!sync_physics_to_lua(L)) {
            std::fprintf(stderr,
                "[stage11] physics->Lua sync failed before Lua update frame=%d\n",
                frame);
            lua_close(L);
            return 13;
        }

        if (frame >= 58 && frame <= 66)
            lua_sethook(L, exact_vm_hook, LUA_MASKCOUNT, 1);
        else
            lua_sethook(L, nullptr, 0, 0);

        lua_pushcfunction(L, traced_error_handler);
        const int errfunc = lua_gettop(L);

        lua_getglobal(L, "update");
        if (!lua_isfunction(L, -1)) {
            std::fprintf(stderr,
                "[stage11] update is not a function at frame %d\n", frame);
            lua_close(L);
            return 14;
        }

        lua_pushnumber(L, dt);
        lua_pushnumber(L, dt);

        if (lua_pcall(L, 2, 0, errfunc) != 0) {
            const double t = get_global_number(L, "time");
            const double cf = get_global_number(L, "currentFrame");
            std::printf(
                "[stage11] ORIGINAL update() FAIL frame=%d "
                "time=%.6f currentFrame=%.0f: %s\n",
                frame, t, cf,
                lua_tostring(L, -1) ? lua_tostring(L, -1) : "<no message>");
            lua_pop(L, 1);
            lua_remove(L, errfunc);
            lua_sethook(L, nullptr, 0, 0);
            lua_close(L);
            return 15;
        }

        lua_remove(L, errfunc);
        lua_sethook(L, nullptr, 0, 0);
        ++updateCalls;

        if (!sawPhysicsEnable && physics.physicsEnabled) {
            sawPhysicsEnable = true;
            physicsEnabledFrame = frame;
            steppedOnEnableFrame = (fixedStepsThisFrame != 0);
            std::printf(
                "[stage11] ORIGINAL updateGame enabled Box2D at Lua frame=%d "
                "time=%.6f; fixedStepsThisFrame=%d\n",
                frame, get_global_number(L, "time"), fixedStepsThisFrame);
        }

        if (frame == 1 || frame == 30 || frame == 60 ||
            frame == 61 || frame == 62 || frame == 63 ||
            frame == 67 || frame == 68 || frame == 69 || frame == 78) {
            std::printf(
                "[stage11] frame=%3d time=%.6f currentFrame=%.0f "
                "gameTimer=%.6f physics=%s accumulator=%.9f "
                "fixedSteps=%d pig=(%.4f,%.4f)\n",
                frame,
                get_global_number(L, "time"),
                get_global_number(L, "currentFrame"),
                get_global_number(L, "gameTimer"),
                physics.physicsEnabled ? "on" : "off",
                (double)physicsAccumulator,
                fixedStepCount,
                (double)pig->GetPosition().x,
                (double)pig->GetPosition().y);
        }
    }

    const double timeValue = get_global_number(L, "time");
    const double frameValue = get_global_number(L, "currentFrame");
    const double gameTimer = get_global_number(L, "gameTimer");

    processNewContacts(78);

    const b2Vec2 finalBirdPos = activeBird->GetPosition();
    const b2Vec2 finalBirdVel = activeBird->GetLinearVelocity();

    std::printf(
        "[stage16] after 78 frames: time=%.6f currentFrame=%.0f "
        "gameTimer=%.6f fixedSteps=%d removeBlocksCalls=%d\n",
        timeValue, frameValue, gameTimer,
        fixedStepCount, removeBlocksCalls);
    std::printf(
        "[stage16] bird-contact summary: injected=%s probeFrame=%d "
        "classifiedBirdContacts=%d activeBirdContacts=%d "
        "firstFrame=%d other='%s'\n",
        birdProbeInjected ? "yes" : "no",
        birdProbeFrame,
        classifiedBirdCollision,
        activeBirdContactCount,
        firstActiveBirdContactFrame,
        firstActiveBirdOther.c_str());
    std::printf(
        "[stage16] first active-bird contact telemetry: "
        "relativeSpeed=%.6f blockMetricDiagnostic=%.6f\n",
        (double)firstActiveBirdRelativeSpeed,
        (double)firstActiveBirdBlockMetricDiagnostic);
    std::printf(
        "[stage16] active bird final: pos=(%.6f,%.6f) "
        "vel=(%.6f,%.6f) controllable=%s\n",
        (double)finalBirdPos.x, (double)finalBirdPos.y,
        (double)finalBirdVel.x, (double)finalBirdVel.y,
        activeBirdControllable ? "true" : "false");

    bool allFinite = true;
    for (const auto& kv : physics.bodies) {
        allFinite = finite_body(kv.second) && allFinite;
    }

    bool ok = true;
    ok = birdProbeInjected && ok;
    ok = (birdProbeFrame == 67) && ok;
    ok = (birdProbeHoldSteps == 1) && ok;
    ok = activeBirdControllable && ok;
    ok = (activeBirdBodyType == (int)b2_dynamicBody) && ok;

    // Native-order schedule still holds.
    ok = (physicsEnabledFrame == 61) && ok;
    ok = (firstFixedStepFrame == 63) && ok;
    ok = (fixedStepCount == 8) && ok;
    ok = (removeBlocksCalls == fixedStepCount) && ok;
    ok = (updateCalls == 78) && ok;

    // The controlled probe must produce at least one contact classified via
    // the active RedBird's original `controllable` state, without invoking
    // guessed bird damage semantics.
    ok = (classifiedBirdCollision > 0) && ok;
    ok = (activeBirdContactCount > 0) && ok;
    // v0.15.3 proved that once geometry ambiguity is removed by placing
    // the RedBird at the exact target-body center, Box2D emits BeginContact in
    // the SAME fixed Step (frame 67): touching=true, manifoldPoints=1, and the
    // callback is classified as birdCollision.
    ok = (firstActiveBirdContactFrame == 67) && ok;
    ok = (!firstActiveBirdOther.empty()) && ok;
    ok = std::isfinite(firstActiveBirdRelativeSpeed) && ok;
    ok = (firstActiveBirdRelativeSpeed > 0.1f) && ok;

    // Ordinary block/block mutation remains disabled. The only damage in
    // Stage 16 must come from the recovered one-bird branch.
    ok = (physics.damageMutationCount == 0) && ok;
    ok = (physics.originalBlockCollisionCalls == 0) && ok;

    ok = physics.birdDamageProbeApplied && ok;
    ok = (physics.birdDamageMutationCount == 1) && ok;
    ok = (physics.originalBirdCollisionCalls == 1) && ok;
    ok = (physics.queuedDeadObjects == 1) && ok;
    ok = physics.birdLegacyDestructionObserved && ok;
    ok = physics.birdContactDisabledOnDestruction && ok;
    ok = std::isfinite(physics.recoveredBirdCollisionForce) && ok;
    ok = std::isfinite(physics.recoveredBirdActualDamage) && ok;
    ok = std::isfinite(physics.recoveredBirdStrengthBefore) && ok;
    ok = std::isfinite(physics.recoveredBirdStrengthAfter) && ok;

    // Destructive accounting saturates actualDamage at old remaining
    // strength, not the larger overkill request.
    ok = (std::fabs(
        physics.recoveredBirdActualDamage -
        physics.recoveredBirdStrengthBefore) < 0.001f) && ok;
    ok = (physics.recoveredBirdStrengthAfter <= 0.0f) && ok;

    const float expectedOverkill =
        -physics.recoveredBirdStrengthAfter;
    const float expectedLegacyScale = std::min(
        (((expectedOverkill /
           activeBird->GetMass()) /
          physics.recoveredBirdCollisionForce) * 10.0f) * 1.75f,
        1.0f);

    ok = (std::fabs(
        physics.birdLegacyOverkill -
        expectedOverkill) < 0.001f) && ok;
    ok = (std::fabs(
        physics.birdLegacyVelocityScale -
        expectedLegacyScale) < 0.001f) && ok;

    const b2Vec2 expectedSetVelocity =
        physics.birdLegacyVelocityBefore *
        physics.birdLegacyVelocityScale;
    ok = ((physics.birdLegacyVelocitySet -
           expectedSetVelocity).Length() < 0.001f) && ok;

    // Original removeBlocks() must consume the bird-created deadBlocks entry
    // on the same native fixed step.
    const bool finalObjectPresent =
        nested_table_has_key(
            L, "objects", "world", "WoodBlock2_6");
    const bool finalDeadQueued =
        table_has_key(
            L, "deadBlocks", "WoodBlock2_6");
    const bool finalGoalPresent =
        table_has_key(
            L, "levelGoals", "WoodBlock2_6");
    const bool finalNativePresent =
        physics.find("WoodBlock2_6") != nullptr;
    const float finalScore = physics.blockScore();

    ok = !finalObjectPresent && ok;
    ok = !finalDeadQueued && ok;
    ok = !finalGoalPresent && ok;
    ok = !finalNativePresent && ok;
    ok = (physics.nativeRemoveObjectCalls == 1) && ok;
    ok = (physics.bodies.size() == 20) && ok;
    ok = std::isfinite(finalScore) && ok;
    ok = (finalScore > stage16ScoreBefore) && ok;

    // Expected visual side effects in this exact corpus:
    // one redBuff from birdCollision + one woodenBuff from removeBlocks.
    ok = (gHeadlessParticleSpawnCalls >= 2) && ok;

    std::printf(
        "[stage16] destruction summary: "
        "force=%.6f defence=%.6f "
        "strength %.6f->%.6f actualDamage=%.6f "
        "overkill=%.6f legacyScale=%.6f "
        "velocitySet=(%.6f,%.6f) "
        "velocityAfterStep=(%.6f,%.6f) "
        "queued=%d removeObjectCalls=%d "
        "bodies=%zu score %.3f->%.3f "
        "particleSpawnCalls=%d\n",
        (double)physics.recoveredBirdCollisionForce,
        (double)physics.recoveredBirdDefence,
        (double)physics.recoveredBirdStrengthBefore,
        (double)physics.recoveredBirdStrengthAfter,
        (double)physics.recoveredBirdActualDamage,
        (double)physics.birdLegacyOverkill,
        (double)physics.birdLegacyVelocityScale,
        (double)physics.birdLegacyVelocitySet.x,
        (double)physics.birdLegacyVelocitySet.y,
        (double)stage16BirdVelocityAfterStep.x,
        (double)stage16BirdVelocityAfterStep.y,
        physics.queuedDeadObjects,
        physics.nativeRemoveObjectCalls,
        physics.bodies.size(),
        (double)stage16ScoreBefore,
        (double)finalScore,
        gHeadlessParticleSpawnCalls);

    std::printf(
        "[stage16] target final: objects.world=%s "
        "deadBlocks=%s levelGoals=%s nativeBody=%s\n",
        finalObjectPresent ? "present" : "nil",
        finalDeadQueued ? "present" : "nil",
        finalGoalPresent ? "present" : "nil",
        finalNativePresent ? "present" : "gone");

    ok = allFinite && ok;
    ok = !physics.callbackError && ok;

    lua_close(L);
    gPhysics = nullptr;
    gSprites = nullptr;

    if (!ok) {
        std::fprintf(stderr,
            "[angry-stage16] FAIL RedBird destruction verification\n");
        return 17;
    }

    std::printf(
        "[angry-stage16] RED BIRD DROVE WoodBlock2_6 THROUGH "
        "THE RECOVERED <=0 DAMAGE BRANCH\n");
    std::printf(
        "[angry-stage16] ARMV7 LEGACY OVERKILL VELOCITY SCALE "
        "WAS APPLIED TO THE BIRD\n");
    std::printf(
        "[angry-stage16] THE DESTRUCTIVE CONTACT WAS DISABLED "
        "BEFORE THE SOLVER\n");
    std::printf(
        "[angry-stage16] ORIGINAL Lua birdCollision() RAN, THEN "
        "ORIGINAL removeBlocks() CONSUMED deadBlocks\n");
    std::printf(
        "[angry-stage16] removeObject() DESTROYED THE Box2D BODY "
        "AND THE ORIGINAL Lua AWARDED DESTRUCTION SCORE\n");
    std::printf(
        "[angry-stage16] THE 20-BODY LEVEL1 WORLD CONTINUED "
        "AFTER A BIRD-CAUSED DESTRUCTION\n");
    std::printf("[angry-stage16] PASS\n");
    return 0;
}
