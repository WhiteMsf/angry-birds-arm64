#include <EGL/egl.h>
#include <GLES/gl.h>

#include <algorithm>
#include <array>
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
#include "vendor/lua-5.1.5/src/lopcodes.h"
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

static void stage17_print_constant(const TValue* value) {
    if (!value) {
        std::printf("<null>");
        return;
    }

    if (ttisnil(value)) {
        std::printf("nil");
    } else if (ttisboolean(value)) {
        std::printf("%s", bvalue(value) ? "true" : "false");
    } else if (ttisnumber(value)) {
        std::printf("%.9g", (double)nvalue(value));
    } else if (ttisstring(value)) {
        std::printf("'%s'", svalue(value));
    } else {
        std::printf("<tt=%d>", ttype(value));
    }
}

static void stage17_print_rk(const Proto* p, int operand) {
    if (!p || !ISK(operand))
        return;

    const int k = INDEXK(operand);
    if (k < 0 || k >= p->sizek)
        return;

    std::printf(" K[%d]=", k);
    stage17_print_constant(&p->k[k]);
}

static void dump_stage17_selection_bytecode(lua_State* L) {
    lua_getglobal(L, "updateGame");
    if (!lua_isfunction(L, -1) || lua_iscfunction(L, -1)) {
        std::printf(
            "[stage17-bytecode] updateGame is not an original Lua function\n");
        lua_pop(L, 1);
        return;
    }

    const void* ptr = lua_topointer(L, -1);
    const Closure* cl = static_cast<const Closure*>(ptr);
    const Proto* p = cl ? cl->l.p : nullptr;

    if (!p || !p->code) {
        std::printf("[stage17-bytecode] updateGame Proto missing\n");
        lua_pop(L, 1);
        return;
    }

    std::printf(
        "[stage17-bytecode] updateGame proto=%p sizecode=%d sizek=%d; "
        "selection window PC 620..780\n",
        static_cast<const void*>(p), p->sizecode, p->sizek);

    // First surface every interesting global/string constant and its exact
    // K index. This makes GETGLOBAL/SETGLOBAL Bx operands readable.
    static const char* interesting[] = {
        "LBUTTON",
        "touchcount",
        "currentBirdName",
        "selectedBird",
        "birdReady",
        "cursor",
        "cursorPhysics",
        "cursorWorld",
        "dragStarted",
        "draggingStartPosPhysics",
        "shootRange",
        "shootMaxLength",
        "rubberBandPos",
        "rubberBandLength",
        "levelStartPosition",
        "objects",
        "world"
    };

    for (int i = 0; i < p->sizek; ++i) {
        const TValue* k = &p->k[i];
        if (!ttisstring(k))
            continue;
        const char* text = svalue(k);
        for (const char* wanted : interesting) {
            if (std::strcmp(text, wanted) == 0) {
                std::printf(
                    "[stage17-bytecode] K[%d] = '%s'\n",
                    i, text);
                break;
            }
        }
    }

    const int begin = 620;
    const int end = p->sizecode < 781 ? p->sizecode : 781;

    for (int pc = begin; pc < end; ++pc) {
        const Instruction ins = p->code[pc];
        const OpCode op = GET_OPCODE(ins);
        const int a = GETARG_A(ins);
        const int b = GETARG_B(ins);
        const int c = GETARG_C(ins);
        const int bx = GETARG_Bx(ins);
        const int sbx = GETARG_sBx(ins);

        std::printf(
            "[stage17-bytecode] pc=%4d op=%-10s "
            "A=%d B=%d C=%d Bx=%d sBx=%d",
            pc,
            (op >= 0 && op < NUM_OPCODES)
                ? luaP_opnames[op] : "<bad-op>",
            a, b, c, bx, sbx);

        switch (op) {
            case OP_LOADK:
            case OP_GETGLOBAL:
            case OP_SETGLOBAL:
                if (bx >= 0 && bx < p->sizek) {
                    std::printf(" K[%d]=", bx);
                    stage17_print_constant(&p->k[bx]);
                }
                break;

            case OP_GETTABLE:
                stage17_print_rk(p, c);
                break;

            case OP_SETTABLE:
                stage17_print_rk(p, b);
                stage17_print_rk(p, c);
                break;

            case OP_EQ:
            case OP_LT:
            case OP_LE:
            case OP_ADD:
            case OP_SUB:
            case OP_MUL:
            case OP_DIV:
            case OP_MOD:
            case OP_POW:
                stage17_print_rk(p, b);
                stage17_print_rk(p, c);
                break;

            default:
                break;
        }

        std::printf("\n");
    }

    lua_pop(L, 1);
}

static bool stage17_get_table_bool(lua_State* L,
                                   const char* tableName,
                                   const char* key,
                                   bool* out) {
    if (!out)
        return false;

    lua_getglobal(L, tableName);
    if (!lua_istable(L, -1)) {
        lua_pop(L, 1);
        return false;
    }

    lua_getfield(L, -1, key);
    const bool valid = lua_isboolean(L, -1);
    if (valid)
        *out = lua_toboolean(L, -1) != 0;
    lua_pop(L, 2);
    return valid;
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
    std::string sheetName;
    std::string textureName;
};

struct SpriteSheetInfo {
    std::string sheetName;
    std::vector<std::string> textures;
    int spriteCount = 0;
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

        const std::string sheetName =
            path.substr(path.find_last_of("/\\") + 1);

        if (!need(2)) return false;
        const uint16_t textureCount = u16();
        std::vector<std::string> textures;
        textures.reserve(textureCount);
        for (uint16_t i = 0; i < textureCount; ++i) {
            const std::string texture = str16();
            if (texture.empty()) {
                std::printf("[stage23.0] malformed texture entry in %s\n", path.c_str());
                return false;
            }
            textures.push_back(texture);
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
            s.sheetName = sheetName;
            if (textures.size() == 1)
                s.textureName = textures[0];
            sprites_[name] = s;
            ++loaded;
        }

        SpriteSheetInfo sheet;
        sheet.sheetName = sheetName;
        sheet.textures = textures;
        sheet.spriteCount = loaded;
        sheets_.push_back(sheet);

        std::printf("[stage23.0-sheet] %-24s textures=%u sprites=%d",
                    sheetName.c_str(), (unsigned)textureCount, loaded);
        for (size_t i = 0; i < textures.size(); ++i)
            std::printf(" texture[%zu]='%s'", i, textures[i].c_str());
        std::printf("\n");
        return true;
    }

    const SpriteInfo* find(const char* name) const {
        auto it = sprites_.find(name ? name : "");
        return it == sprites_.end() ? nullptr : &it->second;
    }

    size_t size() const { return sprites_.size(); }
    const std::vector<SpriteSheetInfo>& sheets() const { return sheets_; }
    const std::map<std::string, SpriteInfo>& all() const { return sprites_; }

private:
    std::map<std::string, SpriteInfo> sprites_;
    std::vector<SpriteSheetInfo> sheets_;
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

struct RenderTransformState {
    float sample[2][3] = {{0.f,0.f,0.f},{0.f,0.f,0.f}};
    float x = 0.f, y = 0.f, angle = 0.f;
    bool initialized = false;
};

struct PhysicsBridge : public b2ContactListener {
    b2World world;
    std::map<std::string, b2Body*> bodies;
    float simulationScale = 1.0f;
    bool physicsEnabled = true;
    int boxesCreated = 0;
    int circlesCreated = 0;

    std::map<std::string, RenderTransformState> renderTransforms;
    int renderHistoryIndex = 0;
    float renderAlpha = 0.0f;
    int renderHistoryCaptures = 0;
    int renderHistoryCatchupSkips = 0;
    int renderInterpolationPublishes = 0;

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

    // Exact non-bird strength/defence/destruction core recovered
    // from ARMv7 GameLua::BeginContact and runtime-validated in Stage 13.
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

        const std::string spriteBefore = objectString(name, "damageSprite");

        // ARMv7 writes new strength before the <= 0 branch.
        if (!setObjectNumber(name, "strength", newStrength))
            return false;

        DamageTrace d;
        d.frame = contactFrame;
        d.objectName = name;
        d.collisionMetric = collisionMetric;
        d.defence = defence;
        d.strengthBefore = strength;
        d.strengthAfter = newStrength;
        d.spriteBefore = spriteBefore;

        if (newStrength <= 0.0f) {
            // Stage 13 recovered accounting saturates actual damage at the
            // victim's remaining strength instead of counting overkill.
            d.actualDamage = strength;
            damageTraces.push_back(d);

            ++damageMutationCount;
            totalActualDamage += strength;

            if (!queueDeadObject(name)) {
                callbackError = true;
                callbackErrorText =
                    "failed to queue destroyed object in deadBlocks";
                return false;
            }

            std::printf(
                "[stage21-blockdamage] frame=%3d %-18s DESTROY "
                "strength=%8.4f -> %8.4f defence=%6.3f metric=%7.4f "
                "actualDamage=%7.4f\n",
                contactFrame, name.c_str(),
                (double)strength, (double)newStrength,
                (double)defence, (double)collisionMetric,
                (double)strength);
            return true;
        }

        d.actualDamage = requestedDamage;
        damageTraces.push_back(d);

        ++damageMutationCount;
        totalActualDamage += requestedDamage;

        std::printf(
            "[stage21-blockdamage] frame=%3d %-18s strength=%8.4f -> %8.4f "
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

        if (!L || callbackError)
            return !callbackError;

        // Stage 15 is deliberately the exactly-one-special-object ARMv7 path.
        if (controllableA == controllableB)
            return true;

        const std::string birdName = controllableA ? nameA : nameB;
        const std::string targetName = controllableA ? nameB : nameA;
        b2Body* birdBody = controllableA ? bodyA : bodyB;

        // Stage 15/16 validated this exact ARMv7 branch on RedBird_4,
        // and Stage 18/19 validated it on natural gameplay contacts.
        // The recovered native branch itself is keyed by the exactly-one-
        // controllable classification, not by a hard-coded object name.
        // Stage 21 keeps the recovered controllable-bird path generalized so the
        // second naturally selected Red Bird uses the same recovered path.

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
                        "recovered bird destruction entered the still-unreconstructed "
                        "non-legacy deferred-velocity path";
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

    void initRenderTransform(const std::string& name, const b2Body* body) {
        if (!body) return;
        const b2Vec2 p = body->GetPosition();
        const float a = body->GetAngle();
        RenderTransformState st;
        for (int i = 0; i < 2; ++i) { st.sample[i][0]=p.x; st.sample[i][1]=p.y; st.sample[i][2]=a; }
        st.x=p.x; st.y=p.y; st.angle=a; st.initialized=true;
        renderTransforms[name] = st;
    }

    void eraseRenderTransform(const std::string& name) { renderTransforms.erase(name); }

    void forceRenderPosition(const std::string& name, float x, float y) {
        auto it = renderTransforms.find(name);
        if (it == renderTransforms.end()) return;
        for (int i=0;i<2;++i) { it->second.sample[i][0]=x; it->second.sample[i][1]=y; }
        it->second.x=x; it->second.y=y;
    }

    void forceRenderAngle(const std::string& name, float a) {
        auto it = renderTransforms.find(name);
        if (it == renderTransforms.end()) return;
        for (int i=0;i<2;++i) it->second.sample[i][2]=a;
        it->second.angle=a;
    }

    void captureRenderHistoryAfterFixedStep() {
        renderHistoryIndex = 1 - renderHistoryIndex;
        for (const auto& kv : bodies) {
            const b2Body* body = kv.second; if (!body || !body->IsAwake()) continue;
            auto it = renderTransforms.find(kv.first);
            if (it == renderTransforms.end() || !it->second.initialized) { initRenderTransform(kv.first, body); it = renderTransforms.find(kv.first); }
            const b2Vec2 p = body->GetPosition();
            it->second.sample[renderHistoryIndex][0]=p.x;
            it->second.sample[renderHistoryIndex][1]=p.y;
            it->second.sample[renderHistoryIndex][2]=body->GetAngle();
        }
        ++renderHistoryCaptures;
    }

    void publishInterpolatedRenderTransforms(float alpha) {
        alpha = std::max(0.0f, std::min(1.0f, alpha));
        renderAlpha = alpha;
        const int cur=renderHistoryIndex, prev=1-cur;
        const float oneMinus=1.0f-alpha;
        const float pi=3.14159265358979323846f, twoPi=6.28318530717958647692f;
        for (const auto& kv : bodies) {
            const b2Body* body=kv.second; if(!body || !body->IsAwake()) continue;
            auto it=renderTransforms.find(kv.first);
            if(it==renderTransforms.end() || !it->second.initialized){ initRenderTransform(kv.first,body); it=renderTransforms.find(kv.first); }
            RenderTransformState& st=it->second;
            st.x=oneMinus*st.sample[prev][0]+alpha*st.sample[cur][0];
            st.y=oneMinus*st.sample[prev][1]+alpha*st.sample[cur][1];
            float pa=st.sample[prev][2]; const float ca=st.sample[cur][2];
            if(std::fabs(ca-pa)>=pi){ if(ca<=pa) pa-=twoPi; else pa+=twoPi; }
            st.angle=oneMinus*pa+alpha*ca;
        }
        ++renderInterpolationPublishes;
    }

    bool getRenderTransform(const std::string& name,float* x,float* y,float* angle) const {
        auto it=renderTransforms.find(name); if(it==renderTransforms.end() || !it->second.initialized) return false;
        if(x)*x=it->second.x; if(y)*y=it->second.y; if(angle)*angle=it->second.angle; return true;
    }

    b2Body* createBox(const char* name, float x, float y,
                      float width, float height,
                      float density, float friction, float restitution) {
        if (b2Body* old = find(name)) {
            world.DestroyBody(old);
            bodies.erase(name);
            eraseRenderTransform(name ? name : "");
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

        // Stage 22.6 A/B audit strongly confirmed the ARMv7-recovered
        // Rovio polygon skin radius. This is now production behavior, not
        // an experiment: every box/polygon fixture created through this
        // reconstructed GameLua path uses the recovered 0.1f radius.
        shape.m_radius = 0.1f;

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
        initRenderTransform(name ? name : "", body);
        ++boxesCreated;
        return body;
    }

    b2Body* createCircle(const char* name, float x, float y,
                         float radius, float density,
                         float friction, float restitution) {
        if (b2Body* old = find(name)) {
            world.DestroyBody(old);
            bodies.erase(name);
            eraseRenderTransform(name ? name : "");
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
        initRenderTransform(name ? name : "", body);
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

static bool gStage17CaptureLaunch = false;
static std::string gStage17BirdName;
static int gStage17ApplyImpulseCalls = 0;
static b2Vec2 gStage17Impulse(0.0f, 0.0f);
static b2Vec2 gStage17ImpulsePoint(0.0f, 0.0f);
static b2Vec2 gStage17VelocityBeforeImpulse(0.0f, 0.0f);
static b2Vec2 gStage17VelocityAfterImpulse(0.0f, 0.0f);

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
    gPhysics->forceRenderAngle(name ? name : "", a);
    set_object_field_number(L, name, "angle", a);
    return 0;
}

static int l_setPosition(lua_State* L) {
    const char* name = luaL_checkstring(L, 1);
    b2Body* b = require_body(L, 1);
    const float x = (float)luaL_checknumber(L, 2);
    const float y = (float)luaL_checknumber(L, 3);
    b->SetTransform(b2Vec2(x, y), b->GetAngle());
    gPhysics->forceRenderPosition(name ? name : "", x, y);
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
    const char* name = luaL_checkstring(L, 1);
    b2Body* b = require_body(L, 1);
    const b2Vec2 impulse((float)luaL_checknumber(L, 2),
                         (float)luaL_checknumber(L, 3));
    const b2Vec2 point((float)luaL_checknumber(L, 4),
                       (float)luaL_checknumber(L, 5));

    const b2Vec2 before = b->GetLinearVelocity();
    if (b->GetType() == b2_dynamicBody)
        b->ApplyLinearImpulse(impulse, point);
    const b2Vec2 after = b->GetLinearVelocity();

    if (gStage17CaptureLaunch &&
        gStage17BirdName == (name ? name : "")) {
        ++gStage17ApplyImpulseCalls;
        gStage17Impulse = impulse;
        gStage17ImpulsePoint = point;
        gStage17VelocityBeforeImpulse = before;
        gStage17VelocityAfterImpulse = after;

        std::printf(
            "[stage17-impulse] applyImpulse('%s', "
            "impulse=(%.6f,%.6f), point=(%.6f,%.6f)) "
            "velocity (%.6f,%.6f)->(%.6f,%.6f)\n",
            name ? name : "<null>",
            (double)impulse.x, (double)impulse.y,
            (double)point.x, (double)point.y,
            (double)before.x, (double)before.y,
            (double)after.x, (double)after.y);
    }

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
    gPhysics->eraseRenderTransform(name);

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
            float renderX=p.x, renderY=p.y, renderAngle=body->GetAngle();
            gPhysics->getRenderTransform(kv.first, &renderX, &renderY, &renderAngle);

            set_number_field(L, "x", renderX);
            set_number_field(L, "y", renderY);
            set_number_field(L, "xVel", v.x);
            set_number_field(L, "yVel", v.y);
            set_number_field(L, "angle", renderAngle);
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

static std::string get_global_table_string_field(lua_State* L,
                                                 const char* globalName,
                                                 const char* fieldName) {
    std::string out;
    lua_getglobal(L, globalName);
    if (lua_istable(L, -1)) {
        lua_getfield(L, -1, fieldName);
        if (lua_isstring(L, -1))
            out = lua_tostring(L, -1);
        lua_pop(L, 1);
    }
    lua_pop(L, 1);
    return out;
}


// Forward declaration needed by Stage227ReplayWriter::capture().
// The actual helper implementation remains unchanged later in this file.
static double get_global_number(lua_State* L, const char* name);

static std::string stage227_json_escape(const std::string& in) {
    std::string out;
    out.reserve(in.size() + 8);
    for (char ch : in) {
        switch (ch) {
            case '\\': out += "\\\\"; break;
            case '"':  out += "\\\""; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default:
                if ((unsigned char)ch < 0x20) {
                    char buf[8];
                    std::snprintf(
                        buf, sizeof(buf), "\\u%04x",
                        (unsigned)(unsigned char)ch);
                    out += buf;
                } else {
                    out += ch;
                }
                break;
        }
    }
    return out;
}

struct Stage232ReplayWriter {
    std::ofstream out;
    bool opened = false;
    bool firstFrame = true;
    int frameCount = 0;
    std::string path;

    bool begin(const char* outputPath,
               const PhysicsBridge& physics,
               const SpriteDB& sprites) {
        path = outputPath ? outputPath : "";
        out.open(path.c_str(),
                 std::ios::out | std::ios::trunc);
        if (!out) {
            std::fprintf(
                stderr,
                "[stage22.7-render] could not open replay output: %s\n",
                path.c_str());
            return false;
        }

        opened = true;

        out << R"HTML(<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Angry Birds ARM64 — Stage 23.2 original sprite replay</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body {
  margin: 0;
  background: #15171a;
  color: #f1f3f5;
  font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
}
.wrap { max-width: 1180px; margin: 0 auto; padding: 16px; }
h1 { font: 700 20px/1.2 system-ui,sans-serif; margin: 0 0 6px; }
.note { color: #aeb6bf; font-size: 12px; margin-bottom: 12px; }
.panel {
  background: #20242a;
  border: 1px solid #353b44;
  border-radius: 12px;
  overflow: hidden;
}
canvas {
  display: block;
  width: 100%;
  height: auto;
  background: #9edcf7;
}
.controls {
  display: grid;
  grid-template-columns: auto auto 1fr auto auto;
  gap: 10px;
  align-items: center;
  padding: 10px;
}
button, select {
  background: #303640; color: #fff;
  border: 1px solid #505966;
  border-radius: 7px; padding: 7px 10px;
}
input[type=range] { width: 100%; }
.status {
  display: grid;
  grid-template-columns: repeat(4, minmax(0,1fr));
  gap: 8px;
  padding: 0 10px 10px;
  font-size: 12px;
}
.status > div {
  background: #181b20;
  border-radius: 7px;
  padding: 8px;
  min-height: 45px;
}
.k { color: #8e99a7; display: block; font-size: 10px; }
.v { color: #fff; overflow-wrap: anywhere; }
.legend {
  display:flex; flex-wrap:wrap; gap:12px;
  padding: 10px; font-size: 11px; color:#bac2cc;
  border-top:1px solid #353b44;
}
.dot { width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:4px; }
@media(max-width:700px) {
  .controls { grid-template-columns:auto auto 1fr; }
  .status { grid-template-columns:1fr 1fr; }
}
</style>
</head>
<body>
<div class="wrap">
<h1>Angry Birds Classic 1.4.2 — ARM64 Stage 23.2</h1>
<div class="note">
Original-sprite replay generated from the reconstructed ARM64 gameplay core.
Real Box2D/Lua transforms plus untouched 1.4.2 atlas pixels decoded from PVR RGBA4444.
Use the atlas-Y toggle only as an orientation audit; geometry remains available as an overlay.
</div>
<div class="panel">
<canvas id="c" width="960" height="540"></canvas>
<div class="controls">
<button id="play">Pause</button>
<button id="restart">Restart</button>
<input id="seek" type="range" min="0" value="0" step="1">
<select id="speed">
<option value="0.5">0.5×</option>
<option value="1" selected>1×</option>
<option value="2">2×</option>
<option value="4">4×</option>
</select>
<label><input id="labels" type="checkbox"> labels</label>
<label><input id="geometry" type="checkbox"> geometry overlay</label>
<label><input id="flipAtlasY" type="checkbox"> flip atlas Y</label>
</div>
<div class="status">
<div><span class="k">FRAME / TIME</span><span class="v" id="stFrame"></span></div>
<div><span class="k">SCORE / SHOTS</span><span class="v" id="stScore"></span></div>
<div><span class="k">CURRENT / FLYING</span><span class="v" id="stBird"></span></div>
<div><span class="k">LEVEL STATE</span><span class="v" id="stLevel"></span></div>
</div>
<div class="legend">
<span><i class="dot" style="background:#d4372f"></i>bird</span>
<span><i class="dot" style="background:#75b843"></i>pig</span>
<span><i class="dot" style="background:#9c693d"></i>wood</span>
<span><i class="dot" style="background:#d6e1e7"></i>light block</span>
<span><i class="dot" style="background:#777f88"></i>static/platform</span>
<span>sprite pixels: original 1.4.2 RGBA4444 atlas</span>
</div>
</div>
</div>
<script>
const defs = {
)HTML";

        bool firstBody = true;
        for (const auto& kv : physics.bodies) {
            const std::string& name = kv.first;
            const b2Body* body = kv.second;
            if (!body)
                continue;

            if (!firstBody)
                out << ",\n";
            firstBody = false;

            out << "\"" << stage227_json_escape(name) << "\":{";
            out << "\"bt\":" << (int)body->GetType();
            out << ",\"sh\":[";

            bool firstShape = true;
            for (const b2Fixture* fixture = body->GetFixtureList();
                 fixture;
                 fixture = fixture->GetNext()) {
                const b2Shape* shape = fixture->GetShape();
                if (!shape)
                    continue;

                if (!firstShape)
                    out << ",";
                firstShape = false;

                if (shape->GetType() == b2Shape::e_circle) {
                    const b2CircleShape* c =
                        static_cast<const b2CircleShape*>(shape);
                    out << "{\"t\":\"c\",\"r\":"
                        << (double)c->m_radius
                        << ",\"x\":" << (double)c->m_p.x
                        << ",\"y\":" << (double)c->m_p.y
                        << "}";
                } else if (shape->GetType() == b2Shape::e_polygon) {
                    const b2PolygonShape* p =
                        static_cast<const b2PolygonShape*>(shape);
                    out << "{\"t\":\"p\",\"v\":[";
                    for (int32 i = 0; i < p->m_vertexCount; ++i) {
                        if (i) out << ",";
                        out << "[" << (double)p->m_vertices[i].x
                            << "," << (double)p->m_vertices[i].y
                            << "]";
                    }
                    out << "]}";
                } else {
                    out << "{\"t\":\"?\"}";
                }
            }

            out << "]}";
        }

        out << "}\n;\n";
        out << "const spriteDefs = {\n";
        bool firstSprite = true;
        for (const auto& kv : sprites.all()) {
            if (!firstSprite)
                out << ",\n";
            firstSprite = false;
            const SpriteInfo& sp = kv.second;
            out << "\"" << stage227_json_escape(kv.first) << "\":{"
                << "\"x\":" << sp.x
                << ",\"y\":" << sp.y
                << ",\"w\":" << sp.width
                << ",\"h\":" << sp.height
                << ",\"px\":" << sp.pivotX
                << ",\"py\":" << sp.pivotY
                << ",\"tex\":\"" << stage227_json_escape(sp.textureName) << "\"}";
        }
        out << "\n};\n";
        out << R"HTML(
const atlasPaths = {
  "INGAME_BLOCKS_1.pvr": "INGAME_BLOCKS_1.png",
  "INGAME_BIRDS_1.pvr": "INGAME_BIRDS_1.png"
};
const atlasImages = {};
for (const [k,v] of Object.entries(atlasPaths)) {
  const im = new Image();
  im.src = v;
  atlasImages[k] = im;
}
const frames = [
)HTML";

        std::printf(
            "[stage23.2-render] replay writer opened: %s bodies=%zu sprites=%zu\n",
            path.c_str(), physics.bodies.size(), sprites.size());
        return true;
    }

    void capture(int frame,
                 lua_State* L,
                 const PhysicsBridge& physics) {
        if (!opened || !out)
            return;

        if (!firstFrame)
            out << ",\n";
        firstFrame = false;

        const std::string current =
            get_global_string(L, "currentBirdName");
        const std::string flying =
            get_global_table_string_field(
                L, "flyingBird", "name");

        const bool ready =
            get_global_bool(L, "birdReady", false) != 0;
        const bool completed =
            get_global_bool(L, "levelCompleted", false) != 0;

        const double score = physics.blockScore();
        const double birdsShot =
            get_global_number(L, "birdsShot");

        out.setf(std::ios::fixed);
        out.precision(3);

        out << "{\"f\":" << frame
            << ",\"score\":" << score
            << ",\"shots\":" << birdsShot
            << ",\"ready\":" << (ready ? "true" : "false")
            << ",\"done\":" << (completed ? "true" : "false")
            << ",\"cur\":\""
            << stage227_json_escape(current) << "\""
            << ",\"fly\":\""
            << stage227_json_escape(flying) << "\""
            << ",\"b\":[";

        bool firstBody = true;
        for (const auto& kv : physics.bodies) {
            const b2Body* body = kv.second;
            if (!body)
                continue;

            const b2Vec2 p = body->GetPosition();
            const float a = body->GetAngle();

            if (!std::isfinite(p.x) ||
                !std::isfinite(p.y) ||
                !std::isfinite(a))
                continue;

            if (!firstBody)
                out << ",";
            firstBody = false;

            const std::string frameSprite =
                physics.objectString(kv.first, "sprite");

            out << "[\"" << stage227_json_escape(kv.first)
                << "\"," << (double)p.x
                << "," << (double)p.y
                << "," << (double)a
                << ",\"" << stage227_json_escape(frameSprite) << "\""
                << "]";
        }

        out << "]}";
        ++frameCount;
    }

    bool finish() {
        if (!opened)
            return false;

        out << R"HTML(
];

const c = document.getElementById('c');
const ctx = c.getContext('2d');
const seek = document.getElementById('seek');
const playBtn = document.getElementById('play');
const restartBtn = document.getElementById('restart');
const speedSel = document.getElementById('speed');
const labels = document.getElementById('labels');
const geometry = document.getElementById('geometry');
const flipAtlasY = document.getElementById('flipAtlasY');
const stFrame = document.getElementById('stFrame');
const stScore = document.getElementById('stScore');
const stBird = document.getElementById('stBird');
const stLevel = document.getElementById('stLevel');

seek.max = Math.max(0, frames.length - 1);

const VIEW = { xmin:-22, xmax:65, ymin:-28, ymax:8 };
const W = c.width, H = c.height;
const sx0 = W / (VIEW.xmax - VIEW.xmin);
const sy0 = H / (VIEW.ymax - VIEW.ymin);
const S = Math.min(sx0, sy0);
const ox = (W - (VIEW.xmax - VIEW.xmin) * S) * 0.5 - VIEW.xmin * S;
const oy = (H - (VIEW.ymax - VIEW.ymin) * S) * 0.5 - VIEW.ymin * S;
const X = x => ox + x*S;
const Y = y => oy + y*S;

function colorFor(name, bt) {
  if (name.startsWith('RedBird')) return '#d4372f';
  if (name.includes('Pig')) return '#75b843';
  if (name.startsWith('Wood')) return '#9c693d';
  if (name.startsWith('Light')) return '#d6e1e7';
  if (name === 'ground') return '#5c8548';
  if (name.startsWith('Estrade')) return '#777f88';
  return bt === 0 ? '#777f88' : '#b18b65';
}

function bodyMap(fr) {
  const m = new Map();
  for (const b of fr.b) m.set(b[0], b);
  return m;
}

function drawTrail(i, fr) {
  if (!fr.fly) return;
  ctx.save();
  ctx.strokeStyle = 'rgba(255,255,255,.4)';
  ctx.lineWidth = 2;
  ctx.setLineDash([2,6]);
  ctx.beginPath();
  let started = false;
  for (let j=Math.max(0,i-120); j<=i; j+=4) {
    const f = frames[j];
    if (!f || f.fly !== fr.fly) continue;
    const b = bodyMap(f).get(fr.fly);
    if (!b) continue;
    if (!started) { ctx.moveTo(X(b[1]),Y(b[2])); started=true; }
    else ctx.lineTo(X(b[1]),Y(b[2]));
  }
  if (started) ctx.stroke();
  ctx.restore();
}

function drawGeometry(name, def) {
  ctx.save();
  ctx.globalAlpha = 0.42;
  ctx.fillStyle = colorFor(name, def.bt);
  ctx.strokeStyle = 'rgba(25,30,35,.9)';
  ctx.lineWidth = 1.2;

  for (const sh of def.sh) {
    if (sh.t === 'c') {
      ctx.beginPath();
      ctx.arc(sh.x*S, sh.y*S, sh.r*S, 0, Math.PI*2);
      ctx.fill();
      ctx.stroke();
    } else if (sh.t === 'p' && sh.v.length) {
      ctx.beginPath();
      ctx.moveTo(sh.v[0][0]*S, sh.v[0][1]*S);
      for (let k=1;k<sh.v.length;k++)
        ctx.lineTo(sh.v[k][0]*S, sh.v[k][1]*S);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }
  }
  ctx.restore();
}

function drawBody(name, state) {
  const def = defs[name];
  if (!def) return;

  const px = X(state[1]), py = Y(state[2]), a = state[3];
  const spriteName = state[4] || '';
  const sp = spriteDefs[spriteName];

  ctx.save();
  ctx.translate(px, py);
  ctx.rotate(a);

  let drewSprite = false;
  if (sp && sp.tex) {
    const img = atlasImages[sp.tex];
    if (img && img.complete && img.naturalWidth > 0) {
      const sy = flipAtlasY.checked
        ? (img.naturalHeight - sp.y - sp.h)
        : sp.y;
      const K = S / 20.0;
      ctx.drawImage(
        img,
        sp.x, sy, sp.w, sp.h,
        -sp.px*K, -sp.py*K, sp.w*K, sp.h*K
      );
      drewSprite = true;
    }
  }

  if (geometry.checked || !drewSprite)
    drawGeometry(name, def);

  if (labels.checked && name !== 'ground') {
    ctx.rotate(-a);
    ctx.font = '10px ui-monospace,monospace';
    ctx.textAlign = 'center';
    ctx.fillStyle = 'rgba(0,0,0,.82)';
    ctx.fillText(name + (spriteName ? ' · ' + spriteName : ''), 0, -10);
  }
  ctx.restore();
}

function draw(i) {
  i = Math.max(0, Math.min(frames.length-1, i|0));
  const fr = frames[i];

  const g = ctx.createLinearGradient(0,0,0,H);
  g.addColorStop(0,'#8fd6f4');
  g.addColorStop(1,'#d9f0fb');
  ctx.fillStyle = g;
  ctx.fillRect(0,0,W,H);

  ctx.fillStyle = '#7cac55';
  ctx.fillRect(0,Y(0),W,H-Y(0));

  ctx.strokeStyle = '#5b3527';
  ctx.lineWidth = 7;
  ctx.beginPath();
  ctx.moveTo(X(-12.25),Y(-5.8));
  ctx.lineTo(X(-12.25),Y(-8.4));
  ctx.stroke();

  drawTrail(i, fr);

  const statics = [], dynamics = [];
  for (const b of fr.b) {
    const d = defs[b[0]];
    ((d && d.bt === 0) ? statics : dynamics).push(b);
  }
  for (const b of statics) drawBody(b[0],b);
  for (const b of dynamics) drawBody(b[0],b);

  if (fr.done) {
    ctx.fillStyle = 'rgba(0,0,0,.42)';
    ctx.fillRect(0,0,W,H);
    ctx.textAlign = 'center';
    ctx.fillStyle = '#fff';
    ctx.font = '700 48px system-ui,sans-serif';
    ctx.fillText('LEVEL COMPLETE', W/2, H/2 - 8);
    ctx.font = '20px ui-monospace,monospace';
    ctx.fillText('score ' + Math.round(fr.score), W/2, H/2 + 34);
  }

  stFrame.textContent = fr.f + ' / ' + (fr.f/60).toFixed(2) + ' s';
  stScore.textContent = Math.round(fr.score) + ' / birdsShot=' + Math.round(fr.shots);
  stBird.textContent = (fr.cur || '—') + ' / ' + (fr.fly || '—');
  stLevel.textContent = fr.done ? 'COMPLETE' : (fr.ready ? 'bird ready' : 'running');
  seek.value = i;
}

let idx = 0;
let playing = true;
let last = performance.now();
let carry = 0;

function tick(now) {
  const dt = Math.min(0.1,(now-last)/1000);
  last = now;
  if (playing && frames.length) {
    carry += dt * 60 * Number(speedSel.value);
    while (carry >= 1) {
      carry -= 1;
      idx++;
      if (idx >= frames.length) {
        idx = frames.length-1;
        playing = false;
        playBtn.textContent = 'Play';
        break;
      }
    }
  }
  draw(idx);
  requestAnimationFrame(tick);
}

playBtn.onclick = () => {
  playing = !playing;
  playBtn.textContent = playing ? 'Pause' : 'Play';
  last = performance.now();
};
restartBtn.onclick = () => {
  idx = 0; carry = 0; playing = true;
  playBtn.textContent = 'Pause';
};
seek.oninput = () => {
  idx = Number(seek.value);
  carry = 0;
  draw(idx);
};
labels.onchange = () => draw(idx);
geometry.onchange = () => draw(idx);
flipAtlasY.onchange = () => draw(idx);
for (const im of Object.values(atlasImages)) im.onload = () => draw(idx);

draw(0);
requestAnimationFrame(tick);
</script>
</body>
</html>
)HTML";

        out.flush();
        const bool good = !!out;
        out.close();
        opened = false;

        std::printf(
            "[stage23.2-render] replay finalized: %s frames=%d status=%s\n",
            path.c_str(), frameCount, good ? "OK" : "FAIL");
        return good;
    }
};

static bool set_global_xy_table(lua_State* L,
                                const char* globalName,
                                float x, float y) {
    lua_getglobal(L, globalName);
    if (!lua_istable(L, -1)) {
        lua_pop(L, 1);
        lua_newtable(L);
        lua_pushvalue(L, -1);
        lua_setglobal(L, globalName);
    }

    lua_pushnumber(L, x);
    lua_setfield(L, -2, "x");
    lua_pushnumber(L, y);
    lua_setfield(L, -2, "y");
    lua_pop(L, 1);
    return true;
}

static bool get_global_xy_table(lua_State* L,
                                const char* globalName,
                                b2Vec2* out) {
    if (!out)
        return false;

    lua_getglobal(L, globalName);
    if (!lua_istable(L, -1)) {
        lua_pop(L, 1);
        return false;
    }

    lua_getfield(L, -1, "x");
    const bool xok = lua_isnumber(L, -1);
    const float x = xok ? (float)lua_tonumber(L, -1) : 0.0f;
    lua_pop(L, 1);

    lua_getfield(L, -1, "y");
    const bool yok = lua_isnumber(L, -1);
    const float y = yok ? (float)lua_tonumber(L, -1) : 0.0f;
    lua_pop(L, 2);

    if (!xok || !yok)
        return false;

    *out = b2Vec2(x, y);
    return true;
}

static void set_input_button(lua_State* L,
                             const char* tableName,
                             const char* button,
                             bool value) {
    lua_getglobal(L, tableName);
    if (!lua_istable(L, -1)) {
        lua_pop(L, 1);
        lua_newtable(L);
        lua_pushvalue(L, -1);
        lua_setglobal(L, tableName);
    }

    lua_pushboolean(L, value ? 1 : 0);
    lua_setfield(L, -2, button);
    lua_pop(L, 1);
}

static double get_global_number(lua_State* L, const char* name);

static b2Vec2 stage17_headless_screen_from_physics(
    lua_State* L,
    const b2Vec2& physicsPoint) {

    const float physicsToWorld =
        (float)get_global_number(L, "physicsToWorld");

    if (!std::isfinite(physicsToWorld) ||
        std::fabs(physicsToWorld) < 1.0e-6f) {
        return physicsPoint;
    }

    return b2Vec2(
        physicsPoint.x * physicsToWorld,
        physicsPoint.y * physicsToWorld);
}


static void clear_stage17_mouse(lua_State* L) {
    set_input_button(L, "keyPressed",  "LBUTTON", false);
    set_input_button(L, "keyReleased", "LBUTTON", false);
    set_input_button(L, "keyHold",     "LBUTTON", false);
    lua_pushnumber(L, 0.0f);
    lua_setglobal(L, "touchcount");
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

static std::string stage23_field_or_dash(const std::string& value) {
    return value.empty() ? std::string("-") : value;
}

static bool write_stage23_sprite_manifest(const char* path,
                                          lua_State* L,
                                          const PhysicsBridge& physics,
                                          const SpriteDB& sprites) {
    std::ofstream out(path, std::ios::out | std::ios::trunc);
    if (!out) {
        std::fprintf(stderr, "[stage23.0] manifest open FAIL: %s\n", path);
        return false;
    }

    out << "ANGRY_STAGE23_0_SPRITE_MANIFEST\t1\n";
    out << "# Metadata is decoded from the original KA3D SPRT chunks.\n";
    out << "# A one-texture sheet gives an exact sprite->texture association; multi-texture sheets are intentionally marked unresolved.\n";

    int ambiguousSheets = 0;
    for (const SpriteSheetInfo& sheet : sprites.sheets()) {
        if (sheet.textures.size() != 1)
            ++ambiguousSheets;
        out << "SHEET\t" << sheet.sheetName
            << "\ttextures=" << sheet.textures.size()
            << "\tsprites=" << sheet.spriteCount;
        for (size_t i = 0; i < sheet.textures.size(); ++i)
            out << "\ttexture[" << i << "]=" << sheet.textures[i];
        out << "\n";
    }

    out << "OBJECT_HEADER\tname\tdefinition\tsprite\tsheet\ttexture\tx\ty\tw\th\tpivotX\tpivotY\tdamageSprite\ttextureOverride\n";

    int spriteObjects = 0;
    int mapped = 0;
    int missing = 0;
    int unresolvedTexture = 0;

    // PhysicsBridge::bodies is a std::map, so this is deterministic by object name.
    for (const auto& kv : physics.bodies) {
        const std::string& name = kv.first;
        const std::string definition = physics.objectString(name, "definition");
        const std::string sprite = physics.objectString(name, "sprite");
        const std::string damageSprite = physics.objectString(name, "damageSprite");
        const std::string textureOverride = physics.objectString(name, "texture");

        if (sprite.empty()) {
            out << "OBJECT_NO_SPRITE\t" << name
                << "\tdefinition=" << stage23_field_or_dash(definition)
                << "\n";
            continue;
        }

        ++spriteObjects;
        const SpriteInfo* info = sprites.find(sprite.c_str());
        if (!info) {
            ++missing;
            out << "OBJECT_MISSING\t" << name
                << "\t" << stage23_field_or_dash(definition)
                << "\t" << sprite << "\n";
            continue;
        }

        ++mapped;
        if (info->textureName.empty())
            ++unresolvedTexture;

        out << "OBJECT\t" << name
            << "\t" << stage23_field_or_dash(definition)
            << "\t" << sprite
            << "\t" << info->sheetName
            << "\t" << stage23_field_or_dash(info->textureName)
            << "\t" << info->x
            << "\t" << info->y
            << "\t" << info->width
            << "\t" << info->height
            << "\t" << info->pivotX
            << "\t" << info->pivotY
            << "\t" << stage23_field_or_dash(damageSprite)
            << "\t" << stage23_field_or_dash(textureOverride)
            << "\n";
    }

    out << "BINDING_HEADER\tname\tstage23_0_status\n";
    out << "BINDING\tdrawRect\tstub\n";
    out << "BINDING\tdrawTexturedRect\tstub\n";
    out << "BINDING\tsetRenderState\tstub\n";
    out << "BINDING\tdrawGameNative\tstub\n";
    out << "BINDING\tdrawBackgroundNative\tstub\n";
    out << "BINDING\tdrawParticlesNative\tstub\n";
    out << "BINDING\tsetSprite\theadless_noop\n";
    out << "BINDING\tsetTexture\tmetadata_only\n";
    out << "BINDING\tdrawLine2D\tstub\n";
    out << "BINDING\tdrawForegroundNative\tstub\n";
    out << "BINDING\tdrawSome\tstub\n";
    out << "BINDING\tsetBGColor\theadless_noop\n";
    out << "BINDING\tsetWorldScale\theadless_noop\n";
    out << "BINDING\tres.drawString\theadless_noop\n";

    out << "SUMMARY\tsheets=" << sprites.sheets().size()
        << "\tambiguousSheets=" << ambiguousSheets
        << "\tbodyCount=" << physics.bodies.size()
        << "\tspriteObjects=" << spriteObjects
        << "\tmapped=" << mapped
        << "\tmissing=" << missing
        << "\tunresolvedTexture=" << unresolvedTexture
        << "\n";
    out.close();

    std::printf(
        "[stage23.0-manifest] sheets=%zu ambiguousSheets=%d bodies=%zu "
        "spriteObjects=%d mapped=%d missing=%d unresolvedTexture=%d\n",
        sprites.sheets().size(), ambiguousSheets, physics.bodies.size(),
        spriteObjects, mapped, missing, unresolvedTexture);

    if (sprites.sheets().size() != 2) {
        std::fprintf(stderr, "[stage23.0] expected exactly two loaded Level1 object sheets\n");
        return false;
    }
    if (ambiguousSheets != 0) {
        std::fprintf(stderr, "[stage23.0] sheet texture association is ambiguous; do not guess atlas mapping\n");
        return false;
    }
    if (missing != 0 || unresolvedTexture != 0) {
        std::fprintf(stderr, "[stage23.0] one or more Level1 object sprites lack an exact sheet/texture mapping\n");
        return false;
    }
    if (spriteObjects < 20 || mapped != spriteObjects) {
        std::fprintf(stderr, "[stage23.0] Level1 sprite-object coverage unexpectedly low\n");
        return false;
    }

    std::printf("[angry-stage23.0] EXACT LEVEL1 SPRITE -> SHEET/TEXTURE/RECT/PIVOT MANIFEST PASS\n");
    return true;
}


// -----------------------------------------------------------------------------
// Stage 23.5: real ARM64 GLES1 multi-sprite scene audit.
//
// Fidelity contract recovered from the original ARMv7 renderer in Stage 23.4:
//   * fixed-function GLES1 / client arrays
//   * GL_LINEAR texture filtering for non-mipped 2D textures
//   * GL_CLAMP_TO_EDGE on S/T
//   * texture storage allocation followed by glTexSubImage2D upload
//   * glPixelStorei(GL_UNPACK_ALIGNMENT, 1) on the upload/blt path
//   * standard alpha templates use GL_SRC_ALPHA / GL_ONE_MINUS_SRC_ALPHA
//   * matrices are submitted with glMatrixMode + glLoadMatrixf (not shaders)
//
// This stage intentionally does NOT claim final camera or original draw order.
// It renders three deterministic gameplay snapshots using the Stage 23.2 audit
// view so GPU state, sprite rects, pivots, rotations and dynamic damage sprites
// can be validated before Android-window/lifecycle integration.
// -----------------------------------------------------------------------------

struct Stage235PvrAtlas {
    std::string name;
    std::vector<uint8_t> bytes;
    uint32_t width = 0;
    uint32_t height = 0;
    uint32_t headerLength = 0;
    GLuint texture = 0;
};

static uint32_t stage235_le32(const uint8_t* p) {
    return static_cast<uint32_t>(p[0]) |
           (static_cast<uint32_t>(p[1]) << 8u) |
           (static_cast<uint32_t>(p[2]) << 16u) |
           (static_cast<uint32_t>(p[3]) << 24u);
}

static bool stage235_read_file(const char* path, std::vector<uint8_t>* out) {
    std::ifstream f(path, std::ios::binary);
    if (!f) return false;
    f.seekg(0, std::ios::end);
    const std::streamoff n = f.tellg();
    if (n < 0) return false;
    f.seekg(0, std::ios::beg);
    out->resize(static_cast<size_t>(n));
    if (n > 0) f.read(reinterpret_cast<char*>(out->data()), n);
    return f.good() || f.eof();
}

static bool stage235_parse_rgba4444_pvr(const char* path,
                                         const char* logicalName,
                                         Stage235PvrAtlas* atlas) {
    atlas->name = logicalName;
    if (!stage235_read_file(path, &atlas->bytes)) {
        std::fprintf(stderr, "[stage23.6A-pvr] read FAIL: %s\n", path);
        return false;
    }
    if (atlas->bytes.size() < 52) {
        std::fprintf(stderr, "[stage23.6A-pvr] short PVR: %s\n", path);
        return false;
    }
    const uint8_t* p = atlas->bytes.data();
    const uint32_t header = stage235_le32(p + 0);
    const uint32_t height = stage235_le32(p + 4);
    const uint32_t width = stage235_le32(p + 8);
    const uint32_t mipField = stage235_le32(p + 12);
    const uint32_t flags = stage235_le32(p + 16);
    const uint32_t dataLength = stage235_le32(p + 20);
    const uint32_t bitCount = stage235_le32(p + 24);
    const uint32_t rMask = stage235_le32(p + 28);
    const uint32_t gMask = stage235_le32(p + 32);
    const uint32_t bMask = stage235_le32(p + 36);
    const uint32_t aMask = stage235_le32(p + 40);
    const uint32_t tag = stage235_le32(p + 44);
    const uint32_t surfaces = stage235_le32(p + 48);
    const uint64_t expected = static_cast<uint64_t>(width) * height * 2ull;

    const bool exact =
        header == 52u && tag == 0x21525650u && mipField == 0u &&
        (flags & 0xffu) == 0x10u && bitCount == 16u && surfaces == 1u &&
        rMask == 0x0000f000u && gMask == 0x00000f00u &&
        bMask == 0x000000f0u && aMask == 0x0000000fu &&
        expected == dataLength && atlas->bytes.size() == header + dataLength;
    if (!exact) {
        std::fprintf(stderr,
            "[stage23.6A-pvr] %s is not the proven one-level RGBA4444 PVR v2 layout\n",
            logicalName);
        return false;
    }
    atlas->headerLength = header;
    atlas->width = width;
    atlas->height = height;
    std::printf(
        "[stage23.6A-pvr] %s size=%ux%u payload=%u RGBA4444 exact=yes\n",
        logicalName, width, height, dataLength);
    return true;
}

static std::string stage235_gl_error(GLenum e) {
    char buf[32];
    std::snprintf(buf, sizeof(buf), "0x%04x", (unsigned)e);
    return std::string(buf);
}

static std::string stage235_egl_error() {
    char buf[32];
    std::snprintf(buf, sizeof(buf), "0x%04x", (unsigned)eglGetError());
    return std::string(buf);
}

static const char* stage235_gl_string(GLenum e) {
    const GLubyte* s = glGetString(e);
    return s ? reinterpret_cast<const char*>(s) : "";
}

static bool stage235_write_bmp24(const std::string& path,
                                  const std::vector<uint8_t>& rgbaTopDown,
                                  int width,
                                  int height) {
    const uint32_t rowStride = static_cast<uint32_t>((width * 3 + 3) & ~3);
    const uint32_t pixelBytes = rowStride * static_cast<uint32_t>(height);
    const uint32_t fileBytes = 54u + pixelBytes;
    std::ofstream f(path, std::ios::binary);
    if (!f) return false;
    auto put16 = [&](uint16_t v) {
        char b[2] = {static_cast<char>(v & 255u), static_cast<char>((v >> 8u) & 255u)};
        f.write(b, 2);
    };
    auto put32 = [&](uint32_t v) {
        char b[4] = {
            static_cast<char>(v & 255u), static_cast<char>((v >> 8u) & 255u),
            static_cast<char>((v >> 16u) & 255u), static_cast<char>((v >> 24u) & 255u)};
        f.write(b, 4);
    };
    f.put('B'); f.put('M'); put32(fileBytes); put16(0); put16(0); put32(54);
    put32(40); put32(static_cast<uint32_t>(width)); put32(static_cast<uint32_t>(height));
    put16(1); put16(24); put32(0); put32(pixelBytes); put32(2835); put32(2835);
    put32(0); put32(0);
    std::vector<uint8_t> row(rowStride, 0);
    for (int yBottom = 0; yBottom < height; ++yBottom) {
        const int yTop = height - 1 - yBottom;
        std::fill(row.begin(), row.end(), 0);
        for (int x = 0; x < width; ++x) {
            const size_t s = (static_cast<size_t>(yTop) * width + x) * 4u;
            const size_t d = static_cast<size_t>(x) * 3u;
            row[d + 0] = rgbaTopDown[s + 2];
            row[d + 1] = rgbaTopDown[s + 1];
            row[d + 2] = rgbaTopDown[s + 0];
        }
        f.write(reinterpret_cast<const char*>(row.data()), row.size());
    }
    return static_cast<bool>(f);
}

class Stage235GpuRenderer {
public:
    static constexpr int W = 960;
    static constexpr int H = 540;

    bool init(const char* blocksPvr,
              const char* birdsPvr,
              const char* outputDir) {
        outDir = outputDir ? outputDir : ".";
        if (!stage235_parse_rgba4444_pvr(blocksPvr, "INGAME_BLOCKS_1.pvr", &blocks) ||
            !stage235_parse_rgba4444_pvr(birdsPvr, "INGAME_BIRDS_1.pvr", &birds)) {
            return false;
        }

        display = eglGetDisplay(EGL_DEFAULT_DISPLAY);
        if (display == EGL_NO_DISPLAY) {
            std::fprintf(stderr, "[stage23.6A-egl] eglGetDisplay FAIL %s\n", stage235_egl_error().c_str());
            return false;
        }
        EGLint maj = 0, min = 0;
        if (!eglInitialize(display, &maj, &min) || !eglBindAPI(EGL_OPENGL_ES_API)) {
            std::fprintf(stderr, "[stage23.6A-egl] EGL init/bind FAIL %s\n", stage235_egl_error().c_str());
            return false;
        }
        eglMajor = maj; eglMinor = min;
        const EGLint cfgAttrs[] = {
            EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
            EGL_RENDERABLE_TYPE, EGL_OPENGL_ES_BIT,
            EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8,
            EGL_NONE
        };
        EGLint count = 0;
        if (!eglChooseConfig(display, cfgAttrs, &config, 1, &count) || count < 1) {
            std::fprintf(stderr, "[stage23.6A-egl] eglChooseConfig FAIL %s\n", stage235_egl_error().c_str());
            return false;
        }
        const EGLint surfAttrs[] = {EGL_WIDTH, W, EGL_HEIGHT, H, EGL_NONE};
        surface = eglCreatePbufferSurface(display, config, surfAttrs);
        const EGLint ctxAttrs[] = {EGL_CONTEXT_CLIENT_VERSION, 1, EGL_NONE};
        context = eglCreateContext(display, config, EGL_NO_CONTEXT, ctxAttrs);
        if (surface == EGL_NO_SURFACE || context == EGL_NO_CONTEXT ||
            !eglMakeCurrent(display, surface, surface, context)) {
            std::fprintf(stderr, "[stage23.6A-egl] context/pbuffer FAIL %s\n", stage235_egl_error().c_str());
            return false;
        }

        glVendor = stage235_gl_string(GL_VENDOR);
        glRenderer = stage235_gl_string(GL_RENDERER);
        glVersion = stage235_gl_string(GL_VERSION);
        GLint maxTex = 0;
        glGetIntegerv(GL_MAX_TEXTURE_SIZE, &maxTex);
        std::printf(
            "[stage23.6A-gl] EGL=%d.%d vendor='%s' renderer='%s' version='%s' maxTexture=%d\n",
            eglMajor, eglMinor, glVendor.c_str(), glRenderer.c_str(), glVersion.c_str(), maxTex);
        if (maxTex < static_cast<GLint>(std::max(
                std::max(blocks.width, blocks.height),
                std::max(birds.width, birds.height)))) {
            std::fprintf(stderr, "[stage23.6A-gl] GL_MAX_TEXTURE_SIZE too small\n");
            return false;
        }

        // Stage 23.4 recovered state contract.
        glDisable(GL_DITHER);
        glDisable(GL_DEPTH_TEST);
        glDisable(GL_CULL_FACE);
        glDisable(GL_LIGHTING);
        glDisable(GL_FOG);
        glActiveTexture(GL_TEXTURE0);
        glClientActiveTexture(GL_TEXTURE0);
        glEnable(GL_TEXTURE_2D);
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        glColor4f(1.f, 1.f, 1.f, 1.f);
        glEnableClientState(GL_VERTEX_ARRAY);
        glEnableClientState(GL_TEXTURE_COORD_ARRAY);
        glDisableClientState(GL_COLOR_ARRAY);

        if (!upload(blocks) || !upload(birds)) return false;

        GLint unpack = 0;
        glGetIntegerv(GL_UNPACK_ALIGNMENT, &unpack);
        std::printf(
            "[stage23.6A-state] min=GL_LINEAR mag=GL_LINEAR wrap=GL_CLAMP_TO_EDGE "
            "unpackAlignment=%d blend=GL_SRC_ALPHA/GL_ONE_MINUS_SRC_ALPHA "
            "matrix=glLoadMatrixf\n", unpack);
        if (unpack != 1) {
            std::fprintf(stderr, "[stage23.6A-state] recovered GL_UNPACK_ALIGNMENT=1 did not stick\n");
            return false;
        }
        return glGetError() == GL_NO_ERROR;
    }

    bool renderSnapshot(int frame,
                        const PhysicsBridge& physics,
                        const SpriteDB& sprites) {
        if (display == EGL_NO_DISPLAY || context == EGL_NO_CONTEXT) return false;
        glViewport(0, 0, W, H);
        glClearColor(0.5608f, 0.8392f, 0.9569f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);

        const float xmin = -22.f, xmax = 65.f, ymin = -28.f, ymax = 8.f;
        const float sx = static_cast<float>(W) / (xmax - xmin);
        const float sy = static_cast<float>(H) / (ymax - ymin);
        const float S = std::min(sx, sy);
        const float ox = (W - (xmax - xmin) * S) * 0.5f - xmin * S;
        const float oy = (H - (ymax - ymin) * S) * 0.5f - ymin * S;
        const float K = S / 20.f;

        // glOrthof/glTranslatef/glRotatef were not imported by the original
        // ARMv7 binary. Reproduce its matrix-upload style with glLoadMatrixf.
        const GLfloat proj[16] = {
            2.f / W, 0.f, 0.f, 0.f,
            0.f, -2.f / H, 0.f, 0.f,
            0.f, 0.f, -1.f, 0.f,
            -1.f, 1.f, 0.f, 1.f
        };
        glMatrixMode(GL_PROJECTION);
        glLoadMatrixf(proj);
        glMatrixMode(GL_MODELVIEW);

        int draws = 0;
        int missing = 0;
        int changedFromBaseline = 0;
        float maxRawToRenderPosDelta = 0.0f;
        float maxRawToRenderAngleDelta = 0.0f;
        GLuint bound = 0;

        for (const auto& kv : physics.bodies) {
            const b2Body* body = kv.second;
            if (!body) continue;
            const std::string spriteName = physics.objectString(kv.first, "sprite");
            if (spriteName.empty()) continue;
            const SpriteInfo* sp = sprites.find(spriteName.c_str());
            if (!sp || sp->textureName.empty()) {
                ++missing;
                continue;
            }
            Stage235PvrAtlas* atlas = nullptr;
            if (sp->textureName == blocks.name) atlas = &blocks;
            else if (sp->textureName == birds.name) atlas = &birds;
            if (!atlas || atlas->texture == 0) {
                ++missing;
                continue;
            }

            auto base = baselineSprites.find(kv.first);
            if (baselineCaptured && base != baselineSprites.end() && base->second != spriteName)
                ++changedFromBaseline;
            if (!baselineCaptured) baselineSprites[kv.first] = spriteName;

            if (bound != atlas->texture) {
                glBindTexture(GL_TEXTURE_2D, atlas->texture);
                bound = atlas->texture;
            }

            const b2Vec2 rawP = body->GetPosition();
            const float rawA = body->GetAngle();
            float rx=rawP.x, ry=rawP.y, a=rawA;
            physics.getRenderTransform(kv.first, &rx, &ry, &a);
            const float c = std::cos(a), sn = std::sin(a);
            const float screenX = ox + rx * S;
            const float screenY = oy + ry * S;
            const float posDelta = std::sqrt((rx-rawP.x)*(rx-rawP.x)+(ry-rawP.y)*(ry-rawP.y));
            const float angleDelta = std::fabs(std::remainder(a - rawA, 6.28318530717958647692f));
            maxRawToRenderPosDelta = std::max(maxRawToRenderPosDelta, posDelta);
            maxRawToRenderAngleDelta = std::max(maxRawToRenderAngleDelta, angleDelta);
            const GLfloat model[16] = {
                c * K, sn * K, 0.f, 0.f,
                -sn * K, c * K, 0.f, 0.f,
                0.f, 0.f, 1.f, 0.f,
                screenX, screenY, 0.f, 1.f
            };
            glLoadMatrixf(model);

            const GLfloat x0 = static_cast<GLfloat>(-sp->pivotX);
            const GLfloat y0 = static_cast<GLfloat>(-sp->pivotY);
            const GLfloat x1 = x0 + static_cast<GLfloat>(sp->width);
            const GLfloat y1 = y0 + static_cast<GLfloat>(sp->height);
            const GLfloat verts[8] = {x0,y0, x1,y0, x0,y1, x1,y1};

            const GLfloat u0 = static_cast<GLfloat>(sp->x) / atlas->width;
            const GLfloat v0 = static_cast<GLfloat>(sp->y) / atlas->height;
            const GLfloat u1 = static_cast<GLfloat>(sp->x + sp->width) / atlas->width;
            const GLfloat v1 = static_cast<GLfloat>(sp->y + sp->height) / atlas->height;
            const GLfloat uv[8] = {u0,v0, u1,v0, u0,v1, u1,v1};

            glVertexPointer(2, GL_FLOAT, 0, verts);
            glTexCoordPointer(2, GL_FLOAT, 0, uv);
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4);
            ++draws;
        }
        if (!baselineCaptured) baselineCaptured = true;

        glFinish();
        const GLenum drawErr = glGetError();
        if (drawErr != GL_NO_ERROR) {
            std::fprintf(stderr, "[stage23.6A-gpu] frame=%d draw GL error=%s\n",
                         frame, stage235_gl_error(drawErr).c_str());
            return false;
        }

        std::vector<uint8_t> bottom(static_cast<size_t>(W) * H * 4u);
        glReadPixels(0, 0, W, H, GL_RGBA, GL_UNSIGNED_BYTE, bottom.data());
        const GLenum readErr = glGetError();
        if (readErr != GL_NO_ERROR) {
            std::fprintf(stderr, "[stage23.6A-gpu] frame=%d readback GL error=%s\n",
                         frame, stage235_gl_error(readErr).c_str());
            return false;
        }
        std::vector<uint8_t> top(bottom.size());
        for (int y = 0; y < H; ++y) {
            const size_t src = static_cast<size_t>(H - 1 - y) * W * 4u;
            const size_t dst = static_cast<size_t>(y) * W * 4u;
            std::memcpy(top.data() + dst, bottom.data() + src, static_cast<size_t>(W) * 4u);
        }
        const std::string bmp = outDir + "/stage23-6a-frame" + std::to_string(frame) + "-gpu.bmp";
        if (!stage235_write_bmp24(bmp, top, W, H)) {
            std::fprintf(stderr, "[stage23.6A-gpu] BMP write FAIL: %s\n", bmp.c_str());
            return false;
        }
        snapshots.push_back(frame);
        drawCounts.push_back(draws);
        changedCounts.push_back(changedFromBaseline);
        snapshotAlphas.push_back(physics.renderAlpha);
        maxPositionDeltas.push_back(maxRawToRenderPosDelta);
        maxAngleDeltas.push_back(maxRawToRenderAngleDelta);
        std::printf(
            "[stage23.6A-gpu] frame=%d alpha=%.6f draws=%d missing=%d changedSpritesFromFrame70=%d maxRawToRenderPosDelta=%.9f maxRawToRenderAngleDelta=%.9f output='%s'\n",
            frame, (double)physics.renderAlpha, draws, missing, changedFromBaseline,
            (double)maxRawToRenderPosDelta, (double)maxRawToRenderAngleDelta, bmp.c_str());
        return missing == 0 && draws >= 1;
    }

    bool interpolationEvidenceOk() const {
        if (snapshots.size() < 5 || snapshotAlphas.size() != snapshots.size()) return false;
        float minAlpha = 1.0f, maxAlpha = 0.0f;
        float maxPosDelta = 0.0f, maxAngDelta = 0.0f;
        for (float a : snapshotAlphas) { minAlpha = std::min(minAlpha, a); maxAlpha = std::max(maxAlpha, a); }
        for (float d : maxPositionDeltas) maxPosDelta = std::max(maxPosDelta, d);
        for (float d : maxAngleDeltas) maxAngDelta = std::max(maxAngDelta, d);
        // The 60 Hz driver over the recovered 30 Hz solver should expose both
        // zero-ish and half-step interpolation phases, and post-launch motion
        // must produce a measurable raw-body -> published-render difference.
        return minAlpha < 0.10f && maxAlpha > 0.40f &&
               (maxPosDelta > 1.0e-5f || maxAngDelta > 1.0e-5f);
    }

    bool finishReport(const PhysicsBridge& physics) {
        const std::string path = outDir + "/stage23-6a-renderobject-interpolation-report.txt";
        std::ofstream r(path);
        if (!r) return false;
        r << "ANGRY_STAGE23_6A_RENDEROBJECT_INTERPOLATION 1\n";
        r << "egl.version=" << eglMajor << "." << eglMinor << "\n";
        r << "gl.vendor=" << glVendor << "\n";
        r << "gl.renderer=" << glRenderer << "\n";
        r << "gl.version=" << glVersion << "\n";
        r << "recovered.texture.min=GL_LINEAR\n";
        r << "recovered.texture.mag=GL_LINEAR\n";
        r << "recovered.texture.wrapS=GL_CLAMP_TO_EDGE\n";
        r << "recovered.texture.wrapT=GL_CLAMP_TO_EDGE\n";
        r << "recovered.unpackAlignment=1\n";
        r << "recovered.uploadPattern=glTexImage2D-null-then-glTexSubImage2D\n";
        r << "recovered.alphaTemplate=GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA\n";
        r << "recovered.matrixPattern=glMatrixMode+glLoadMatrixf\n";
        r << "audit.spriteY=direct-pvr-row-coordinate\n";
        r << "audit.spritePixelsPerWorldUnit=20\n";
        r << "recovered.renderHistorySlots=2x(x,y,angle)\n";
        r << "recovered.renderPublishedOffsets=116,120,124\n";
        r << "recovered.renderAlpha=physicsAccumulator/(1/30)\n";
        r << "recovered.renderAngleShortestPath=yes\n";
        r << "recovered.renderAwakeBodyGate=b2Body-e_awakeFlag-0x0002\n";
        r << "recovered.renderCatchupHistoryGate=record-when-accumulator<=2*(1/30)\n";
        r << "runtime.renderHistoryCaptures=" << physics.renderHistoryCaptures << "\n";
        r << "runtime.renderHistoryCatchupSkips=" << physics.renderHistoryCatchupSkips << "\n";
        r << "runtime.renderInterpolationPublishes=" << physics.renderInterpolationPublishes << "\n";
        r << "audit.angleWrapConstant=pi-from-ARMv7-control-flow-and-Box2D-domain\n";
        r << "audit.camera=stage23.2-debug-view-NOT-final-original-camera\n";
        r << "audit.drawOrder=object-name-map-order-NOT-final-original-order\n";
        r << "audit.quadPrimitive=GL_TRIANGLE_STRIP-harness-choice\n";
        for (size_t i = 0; i < snapshots.size(); ++i) {
            r << "snapshot.frame" << i << "=" << snapshots[i]
              << " alpha=" << snapshotAlphas[i]
              << " draws=" << drawCounts[i]
              << " changedSpritesFromFrame70=" << changedCounts[i]
              << " maxRawToRenderPosDelta=" << maxPositionDeltas[i]
              << " maxRawToRenderAngleDelta=" << maxAngleDeltas[i] << "\n";
        }
        r.close();
        std::printf("[stage23.6A-report] %s\n", path.c_str());
        return true;
    }

    void shutdown() {
        if (display != EGL_NO_DISPLAY && context != EGL_NO_CONTEXT && surface != EGL_NO_SURFACE)
            eglMakeCurrent(display, surface, surface, context);
        if (blocks.texture) glDeleteTextures(1, &blocks.texture);
        if (birds.texture) glDeleteTextures(1, &birds.texture);
        if (display != EGL_NO_DISPLAY) {
            eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
            if (context != EGL_NO_CONTEXT) eglDestroyContext(display, context);
            if (surface != EGL_NO_SURFACE) eglDestroySurface(display, surface);
            eglTerminate(display);
        }
        display = EGL_NO_DISPLAY;
        surface = EGL_NO_SURFACE;
        context = EGL_NO_CONTEXT;
    }

    ~Stage235GpuRenderer() { shutdown(); }

private:
    bool upload(Stage235PvrAtlas& a) {
        glGenTextures(1, &a.texture);
        glBindTexture(GL_TEXTURE_2D, a.texture);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);

        // Mirror the recovered KA3D allocate + blt route rather than the
        // simpler direct payload upload used by Stage 23.3.
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA,
                     static_cast<GLsizei>(a.width), static_cast<GLsizei>(a.height), 0,
                     GL_RGBA, GL_UNSIGNED_SHORT_4_4_4_4, nullptr);
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
        const uint8_t* payload = a.bytes.data() + a.headerLength;
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0,
                        static_cast<GLsizei>(a.width), static_cast<GLsizei>(a.height),
                        GL_RGBA, GL_UNSIGNED_SHORT_4_4_4_4, payload);
        const GLenum e = glGetError();
        std::printf(
            "[stage23.6A-upload] %s texture=%u %ux%u allocate+subimage glError=%s\n",
            a.name.c_str(), a.texture, a.width, a.height, stage235_gl_error(e).c_str());
        return e == GL_NO_ERROR;
    }

    std::string outDir;
    Stage235PvrAtlas blocks, birds;
    EGLDisplay display = EGL_NO_DISPLAY;
    EGLConfig config = nullptr;
    EGLSurface surface = EGL_NO_SURFACE;
    EGLContext context = EGL_NO_CONTEXT;
    int eglMajor = 0, eglMinor = 0;
    std::string glVendor, glRenderer, glVersion;
    bool baselineCaptured = false;
    std::map<std::string, std::string> baselineSprites;
    std::vector<int> snapshots;
    std::vector<int> drawCounts;
    std::vector<int> changedCounts;
    std::vector<float> snapshotAlphas;
    std::vector<float> maxPositionDeltas;
    std::vector<float> maxAngleDeltas;
};

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

    if (argc != 10) {
        std::fprintf(stderr,
            "usage: %s <scripts-dir> <Level1.lua> <INGAME_BLOCKS_1.dat> "
            "<INGAME_BIRDS_1.dat> <INGAME_BLOCKS_1.pvr> <INGAME_BIRDS_1.pvr> "
            "<replay-output.html> <sprite-manifest.tsv> <gpu-output-dir>\n",
            argv[0]);
        return 2;
    }

    std::printf("[angry-stage23.6A] RENDEROBJECTDATA TRANSFORM HISTORY + INTERPOLATED LEVEL1 GPU SCENE / ARM64\n");

    PhysicsBridge physics;
    SpriteDB sprites;
    gPhysics = &physics;
    gSprites = &sprites;

    if (!sprites.loadSheet(argv[3]) || !sprites.loadSheet(argv[4]))
        return 3;

    const SpriteInfo* stage232Red = sprites.find("BIRD_RED");
    if (!stage232Red ||
        stage232Red->textureName != "INGAME_BIRDS_1.pvr" ||
        stage232Red->width <= 0 || stage232Red->height <= 0) {
        std::fprintf(stderr,
            "[stage23.2] BIRD_RED exact sprite metadata missing or unexpected\n");
        return 31;
    }
    std::printf(
        "[stage23.2-red] BIRD_RED texture='%s' rect=(%d,%d %dx%d) pivot=(%d,%d)\n",
        stage232Red->textureName.c_str(),
        stage232Red->x, stage232Red->y,
        stage232Red->width, stage232Red->height,
        stage232Red->pivotX, stage232Red->pivotY);

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

    // Headless camera boundary for Stage 17.
    //
    // The slingshot path itself is original Lua. During the first held-drag
    // frame updateGame() assigns:
    //
    //   cameraFunction = doItAllCamera
    //
    // and invokes cameraFunction(dt) near the end of the same update.
    // doItAllCamera/getTempBirdCamera depend on the full initCameras()
    // renderer/viewport state (currentZoomedScale, minWorldScale, limits,
    // screen transforms...). That subsystem is intentionally not part of
    // this launch milestone, so keep it headless instead of manufacturing
    // camera values one-by-one.
    setfn(L, "doItAllCamera", l_noop);
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

-- Native platform input state used by the original sling code.
-- createMenuPages() normally initializes these UI hitbox extents.
-- The headless bootstrap intentionally does not build menu pages, but
-- updateGame() still executes the pause-button guard before sling selection.
-- Headless input has no rendered pause button. Use unreachable extents
-- because the identity headless camera may map valid world points to negative
-- synthetic screen coordinates.
pauseButtonW = -1000000000
pauseButtonH = -1000000000

-- Original initCameras() writes both of these to 1.0 before normal gameplay.
-- Stage 17 keeps camera rendering headless, but updateGame() still adjusts the
-- slider while the player drags the bird (PC 2019..2021).
cameraAnimationSlider = 1
cameraAnimationSliderTarget = 1

-- Screen-space cursor must stay separate from world/physics cursor.
-- A safe positive headless screen point avoids the pause-button hitbox.
cursor = {x=100, y=100}
oldCursor = {x=100, y=100}
cursorPhysics = {x=0, y=0}
cursorWorld = {x=0, y=0}
draggingStartPosPhysics = {x=0, y=0}
draggingStartPosScreen = {x=0, y=0}
tapPosWorld = {x=0, y=0}
touchcount = 0

-- Original initializeMenu() supplies persistent-settings defaults before
-- gameplay. Stage 17 intentionally bypasses the menu subsystem, but the
-- original LBUTTON release path increments settings.birdsShooted before it
-- performs the sling launch. ARM64 runtime stopped at updateGame PC 2117
-- because that one field had never received its original default.
--
-- Exact original bytecode (initializeMenu, root child 31):
--   if settings.birdsShooted == nil then
--       settings.birdsShooted = 0
--   end
--
-- Reproduce only that proven missing boundary; do not initialize unrelated
-- menu/settings state.
settings = settings or {}
if settings.birdsShooted == nil then
    settings.birdsShooted = 0
end

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

    if (!write_stage23_sprite_manifest(argv[8], L, physics, sprites)) {
        lua_close(L);
        gPhysics = nullptr;
        gSprites = nullptr;
        return 26;
    }

    Stage232ReplayWriter replay;
    if (!replay.begin(argv[7], physics, sprites)) {
        lua_close(L);
        gPhysics = nullptr;
        gSprites = nullptr;
        return 25;
    }

    Stage235GpuRenderer gpuScene;
    if (!gpuScene.init(argv[5], argv[6], argv[9])) {
        std::fprintf(stderr, "[angry-stage23.6A] GPU scene initialization FAIL\n");
        lua_close(L);
        gPhysics = nullptr;
        gSprites = nullptr;
        return 27;
    }

    replay.capture(0, L, physics);

    // Re-enable Stage 10's recovered collision mutation only after the
    // original level is fully materialized. It now runs *inside* BeginContact
    // during the correctly scheduled 30 Hz Box2D Step.
    // Stage 19 removes the last gameplay isolation boundary.
    // Both recovered collision families now run together.
    physics.enableRecoveredBlockDamage = true;
    physics.enableRecoveredBirdDamage = true;

    const bool activeBirdControllable =
        get_object_bool(L, activeBirdName, "controllable", false);
    const std::string activeBirdDefinition =
        physics.objectString(activeBirdName, "definition");
    const std::string activeBirdSprite =
        physics.objectString(activeBirdName, "sprite");
    const int activeBirdBodyType = (int)activeBird->GetType();

    dump_stage17_selection_bytecode(L);

    std::printf(
        "[stage17] initial controllable bird candidate: "
        "name=%s controllable=%s definition='%s' sprite='%s' "
        "mass=%.6f bodyType=%d pos=(%.6f,%.6f)\n",
        activeBirdName.c_str(),
        activeBirdControllable ? "true" : "false",
        activeBirdDefinition.c_str(),
        activeBirdSprite.c_str(),
        (double)activeBird->GetMass(),
        activeBirdBodyType,
        (double)activeBird->GetPosition().x,
        (double)activeBird->GetPosition().y);

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

    enum class SlingPhase {
        WAIT_READY,
        PRESS,
        DRAG,
        RELEASE,
        FLYING
    };

    struct ShotTrace {
        int number = 0;
        std::string bird;
        int readyFrame = -1;
        int pressFrame = -1;
        int dragFrame = -1;
        int releaseFrame = -1;
        int terminalFrame = -1;
        int nextReadyFrame = -1;
        std::string nextBird;
        bool levelCompleted = false;
        bool levelFailed = false;

        float rubberBandLength = NAN;
        float shootMaxLength = NAN;
        float birdsShotBefore = NAN;
        float birdsShotAfter = NAN;

        bool selectedAfterPress = false;
        bool flyingBirdAfterRelease = false;
        bool birdFiredAfterRelease = false;
        bool currentBirdClearedAfterRelease = false;
        bool selectedBirdClearedAfterRelease = false;
        bool shotFlagAfterRelease = false;

        int applyImpulseCallsBefore = 0;
        int applyImpulseCallsAfter = 0;
        b2Vec2 impulse = b2Vec2(0.0f, 0.0f);
        b2Vec2 velocityAfterImpulse = b2Vec2(0.0f, 0.0f);
        b2Vec2 releasePosition = b2Vec2(0.0f, 0.0f);
        b2Vec2 positionAfter30 = b2Vec2(0.0f, 0.0f);
        bool sawPlus30 = false;

        int fixedStepsAtRelease = 0;
        int fixedStepsAtTerminal = 0;
        int blockCallbacksAtRelease = 0;
        int blockCallbacksAtTerminal = 0;
        int blockDamageAtRelease = 0;
        int blockDamageAtTerminal = 0;
        int birdCallbacksAtRelease = 0;
        int birdCallbacksAtTerminal = 0;
        int birdDamageAtRelease = 0;
        int birdDamageAtTerminal = 0;
        int bodiesAtRelease = 0;
        int bodiesAtTerminal = 0;
        float scoreAtRelease = 0.0f;
        float scoreAtTerminal = 0.0f;
    };

    constexpr int kTargetShots = 3;
    // Let the reconstructed Level1 idle past the Stage 22.5 failure window
    // before the first synthetic platform input. This turns Stage 22.7 into
    // a combined idle-soak + complete-gameplay regression.
    constexpr int kFirstInputNotBeforeFrame = 120;
    std::vector<ShotTrace> shots;
    int currentShotNumber = 0;
    int applyImpulseCallsAtShotStart = 0;

    SlingPhase slingPhase = SlingPhase::WAIT_READY;
    int readyFrame = -1;
    int pressFrame = -1;
    int dragFrame = -1;
    int releaseFrame = -1;
    int postLaunchFixedSteps = 0;

    std::string slingBirdName;
    b2Body* slingBirdBody = nullptr;

    b2Vec2 slingStart(0.0f, 0.0f);
    b2Vec2 pullCursor(0.0f, 0.0f);
    b2Vec2 releasePosition(0.0f, 0.0f);
    b2Vec2 positionAfter30Frames(0.0f, 0.0f);

    float dragRubberBandLength = NAN;
    float dragShootMaxLength = NAN;
    float birdsShotBefore = NAN;
    float birdsShotAfterRelease = NAN;

    bool selectedAfterPress = false;
    bool flyingBirdAfterRelease = false;
    bool birdFiredAfterRelease = false;
    bool currentBirdClearedAfterRelease = false;
    bool selectedBirdClearedAfterRelease = false;
    bool shotFlagAfterRelease = false;

    // Stage 19 post-shot lifecycle.
    int terminalFrame = -1;
    int firstBirdClearedFrame = -1;
    int nextBirdReadyFrame = -1;
    int levelCompletedFrame = -1;
    int levelFailedFrame = -1;
    float levelFailedTimerBaseline =
        (float)get_global_number(L, "levelFailedTimer");
    std::string nextBirdName;
    std::string lastLifecycleCurrentBird;
    std::string lastLifecycleFlyingBird;
    bool lastLifecycleBirdReady = false;
    bool lastLifecycleLevelCompleted = false;
    bool lastLifecycleLevelFailed = false;
    bool sawBlockActivityAfterRelease = false;

    // Stage 21 v0.22.1 input-routing observer.
    // A ready next bird is not necessarily clickable yet: original updateGame
    // gives LBUTTON to the still-flying bird while its specialty remains
    // available. Log that gate once per wait interval and simply wait.
    bool specialtyInputGateLogged = false;

    int blockCollisionCallsAtRelease = 0;
    int blockDamageMutationsAtRelease = 0;
    int birdCollisionCallsAtRelease = 0;
    int bodyCountAtRelease = 0;

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

    const int maxLifecycleFrames = 2400; // 40 seconds at 60 Hz render cadence
    int lastFrameRun = 0;
    for (int frame = 1; frame <= maxLifecycleFrames; ++frame) {
        lastFrameRun = frame;
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

                physics.stepFixed(fixedPhysicsDt, frame);

                ++fixedStepCount;
                ++fixedStepsThisFrame;
                if (slingPhase == SlingPhase::FLYING)
                    ++postLaunchFixedSteps;
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

                processNewContacts(frame);

                // ARMv7 GameLua::update skips intermediate history snapshots while
                // the accumulator is still more than two fixed steps behind, then
                // records the last two solver states. At the normal 60 Hz harness
                // cadence this records every 30 Hz step; the branch also preserves
                // the original catch-up behavior if a larger dt is introduced.
                if (physicsAccumulator <= 2.0f * fixedPhysicsDt)
                    physics.captureRenderHistoryAfterFixedStep();
                else
                    ++physics.renderHistoryCatchupSkips;

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

        // Recovered ARMv7 RenderObjectData history/interpolation path.
        // Publish after physics and before original Lua update, matching native order.
        physics.publishInterpolatedRenderTransforms(physicsAccumulator / fixedPhysicsDt);
        if (!sync_physics_to_lua(L)) {
            std::fprintf(stderr,
                "[stage11] physics->Lua sync failed before Lua update frame=%d\n",
                frame);
            lua_close(L);
            return 13;
        }

        // -----------------------------------------------------------------
        // Stage 17 platform-input emulation.
        //
        // No direct SetTransform(), SetLinearVelocity() or ApplyImpulse()
        // occurs here. The harness only publishes the same LBUTTON/cursor
        // globals consumed by ORIGINAL updateGame().
        // -----------------------------------------------------------------
        clear_stage17_mouse(L);

        if (slingPhase == SlingPhase::WAIT_READY) {
            const bool ready =
                get_global_bool(L, "birdReady", false) != 0;
            const std::string currentBird =
                get_global_string(L, "currentBirdName");

            // Exact original updateGame LBUTTON routing recovered from the
            // Lua 5.1 bytecode:
            //
            //   if flyingBird == nil then
            //       -> sling/tap drag setup
            //   elseif birdSpecialtyAvailable then
            //       -> active flying-bird specialty
            //   else
            //       -> sling/tap drag setup
            //
            // v0.22 pressed RedBird_3 one frame after birdReady while
            // RedBird_2 was still flying with its specialty route active.
            // The press was therefore consumed before sling selection.
            const std::string activeFlyingBird =
                get_global_table_string_field(
                    L, "flyingBird", "name");
            const bool specialtyAvailable =
                get_global_bool(
                    L, "birdSpecialtyAvailable", false) != 0;
            const bool slingInputRouteOpen =
                activeFlyingBird.empty() || !specialtyAvailable;

            if (ready && !currentBird.empty() &&
                !slingInputRouteOpen &&
                !specialtyInputGateLogged) {
                std::printf(
                    "[stage21-inputgate] frame=%d nextBird='%s' is ready "
                    "but LBUTTON still routes to flyingBird='%s' "
                    "because birdSpecialtyAvailable=true; waiting without "
                    "pressing\n",
                    frame,
                    currentBird.c_str(),
                    activeFlyingBird.c_str());
                specialtyInputGateLogged = true;
            }

            const bool firstInputSoakComplete =
                !shots.empty() || frame >= kFirstInputNotBeforeFrame;

            if (ready && !currentBird.empty() &&
                slingInputRouteOpen && firstInputSoakComplete) {
                specialtyInputGateLogged = false;

                if ((int)shots.size() >= kTargetShots) {
                    // After all three Level1 birds are released, Stage 21 only
                    // observes the original victory/failure terminal state.
                } else {
                    currentShotNumber = (int)shots.size() + 1;

                    // Reset only per-shot harness telemetry. No Lua/gameplay
                    // state is synthesized here.
                    readyFrame = -1;
                    pressFrame = -1;
                    dragFrame = -1;
                    releaseFrame = -1;
                    postLaunchFixedSteps = 0;
                    slingStart.Set(0.0f, 0.0f);
                    pullCursor.Set(0.0f, 0.0f);
                    releasePosition.Set(0.0f, 0.0f);
                    positionAfter30Frames.Set(0.0f, 0.0f);
                    dragRubberBandLength = NAN;
                    dragShootMaxLength = NAN;
                    birdsShotBefore = NAN;
                    birdsShotAfterRelease = NAN;
                    selectedAfterPress = false;
                    flyingBirdAfterRelease = false;
                    birdFiredAfterRelease = false;
                    currentBirdClearedAfterRelease = false;
                    selectedBirdClearedAfterRelease = false;
                    shotFlagAfterRelease = false;
                    sawBlockActivityAfterRelease = false;
                    applyImpulseCallsAtShotStart =
                        gStage17ApplyImpulseCalls;

                    slingBirdName = currentBird;
                    slingBirdBody = physics.find(slingBirdName.c_str());

                if (!slingBirdBody ||
                    !get_global_xy_table(
                        L, "levelStartPosition", &slingStart)) {
                    std::fprintf(stderr,
                        "[stage17] ready bird/slingshot state missing "
                        "at frame %d bird='%s'\n",
                        frame, slingBirdName.c_str());
                    lua_close(L);
                    return 94;
                }

                readyFrame = frame;
                birdsShotBefore =
                    (float)get_global_number(L, "birdsShot");

                const b2Vec2 birdPos =
                    slingBirdBody->GetPosition();

                // Press ON the actual bird so original selection logic
                // passes its shootRange distance test.
                set_global_xy_table(
                    L, "cursorPhysics",
                    birdPos.x, birdPos.y);
                set_global_xy_table(
                    L, "cursorWorld",
                    birdPos.x, birdPos.y);

                // ORIGINAL updateGame recomputes cursorWorld and
                // cursorPhysics from screen-space `cursor` before the bird
                // hit-test. v0.18.5 proved the active headless transform is:
                //
                //   cursorWorld   = cursor
                //   cursorPhysics = cursorWorld / physicsToWorld
                //
                // Feed the inverse screen point so the original conversion
                // lands exactly on the real bird body.
                const b2Vec2 pressScreen =
                    stage17_headless_screen_from_physics(
                        L, birdPos);

                set_global_xy_table(
                    L, "cursor",
                    pressScreen.x, pressScreen.y);
                set_global_xy_table(
                    L, "oldCursor",
                    pressScreen.x, pressScreen.y);

                lua_pushnumber(L, 1.0f);
                lua_setglobal(L, "touchcount");
                set_input_button(
                    L, "keyPressed", "LBUTTON", true);
                set_input_button(
                    L, "keyHold", "LBUTTON", true);

                pressFrame = frame;
                slingPhase = SlingPhase::PRESS;

                gStage17BirdName = slingBirdName;
                gStage17CaptureLaunch = true;

                float luaBirdX = NAN;
                float luaBirdY = NAN;
                (void)physics.objectNumber(
                    slingBirdName, "x", &luaBirdX);
                (void)physics.objectNumber(
                    slingBirdName, "y", &luaBirdY);

                b2Vec2 cursorPhysicsNow(0.0f, 0.0f);
                b2Vec2 cursorWorldNow(0.0f, 0.0f);
                b2Vec2 cursorScreenNow(0.0f, 0.0f);
                (void)get_global_xy_table(
                    L, "cursorPhysics", &cursorPhysicsNow);
                (void)get_global_xy_table(
                    L, "cursorWorld", &cursorWorldNow);
                (void)get_global_xy_table(
                    L, "cursor", &cursorScreenNow);

                bool pressed = false;
                bool held = false;
                (void)stage17_get_table_bool(
                    L, "keyPressed", "LBUTTON", &pressed);
                (void)stage17_get_table_bool(
                    L, "keyHold", "LBUTTON", &held);

                std::printf(
                    "[stage17-selectdiag] BEFORE PRESS "
                    "birdReady=%s currentBirdName='%s' "
                    "touchcount=%.3f "
                    "keyPressed=%s keyHold=%s "
                    "body=(%.6f,%.6f) luaObject=(%.6f,%.6f) "
                    "cursorPhysics=(%.6f,%.6f) "
                    "cursorWorld=(%.6f,%.6f) "
                    "cursorScreenSynthetic=(%.6f,%.6f) "
                    "shootRange=%.6f "
                    "flyingBird='%s' specialtyAvailable=%s\n",
                    get_global_bool(
                        L, "birdReady", false)
                        ? "true" : "false",
                    get_global_string(
                        L, "currentBirdName").c_str(),
                    get_global_number(L, "touchcount"),
                    pressed ? "true" : "false",
                    held ? "true" : "false",
                    (double)birdPos.x, (double)birdPos.y,
                    (double)luaBirdX, (double)luaBirdY,
                    (double)cursorPhysicsNow.x,
                    (double)cursorPhysicsNow.y,
                    (double)cursorWorldNow.x,
                    (double)cursorWorldNow.y,
                    (double)cursorScreenNow.x,
                    (double)cursorScreenNow.y,
                    get_global_number(L, "shootRange"),
                    get_global_table_string_field(
                        L, "flyingBird", "name").c_str(),
                    get_global_bool(
                        L, "birdSpecialtyAvailable", false)
                        ? "true" : "false");

                const b2Vec2 pressScreenDiag =
                    stage17_headless_screen_from_physics(
                        L, birdPos);

                std::printf(
                    "[stage17-ui] headless input/camera guard: "
                    "pauseButtonW=-1e9 pauseButtonH=-1e9 "
                    "cameraAnimationSlider=1 "
                    "cameraAnimationSliderTarget=1 "
                    "doItAllCamera=headless-noop "
                    "screenCursor=(%.6f,%.6f); "
                    "expectedPhysicsCursor=(%.6f,%.6f)\n",
                    (double)pressScreenDiag.x,
                    (double)pressScreenDiag.y,
                    (double)birdPos.x,
                    (double)birdPos.y);

                std::printf(
                    "[stage17-input] READY frame=%d bird=%s "
                    "bodyPos=(%.6f,%.6f) "
                    "levelStart=(%.6f,%.6f) -> PRESS\n",
                    frame, slingBirdName.c_str(),
                    (double)birdPos.x, (double)birdPos.y,
                    (double)slingStart.x,
                    (double)slingStart.y);
                }
            }
        } else if (slingPhase == SlingPhase::PRESS) {
            // Keep the button held and pull backward/downward. Original
            // updateGame() computes rubberBandAngle/Length/Pos itself.
            //
            // launch vector = levelStart - cursor = (+5, -2)
            // max pull ~= sqrt(29)=5.385, just below shootMaxLength~5.4.
            pullCursor =
                b2Vec2(slingStart.x - 5.0f,
                       slingStart.y + 2.0f);

            set_global_xy_table(
                L, "cursorPhysics",
                pullCursor.x, pullCursor.y);
            set_global_xy_table(
                L, "cursorWorld",
                pullCursor.x, pullCursor.y);

            const b2Vec2 dragScreen =
                stage17_headless_screen_from_physics(
                    L, pullCursor);
            set_global_xy_table(
                L, "cursor",
                dragScreen.x, dragScreen.y);

            lua_pushnumber(L, 1.0f);
            lua_setglobal(L, "touchcount");
            set_input_button(
                L, "keyHold", "LBUTTON", true);

            dragFrame = frame;
            slingPhase = SlingPhase::DRAG;

            std::printf(
                "[stage17-input] DRAG frame=%d "
                "physicsTarget=(%.6f,%.6f) "
                "screenCursor=(%.6f,%.6f) "
                "desiredLaunchVector=(5.000000,-2.000000)\n",
                frame,
                (double)pullCursor.x,
                (double)pullCursor.y,
                (double)dragScreen.x,
                (double)dragScreen.y);
        } else if (slingPhase == SlingPhase::DRAG) {
            // Release at the exact same pulled cursor position.
            set_global_xy_table(
                L, "cursorPhysics",
                pullCursor.x, pullCursor.y);
            set_global_xy_table(
                L, "cursorWorld",
                pullCursor.x, pullCursor.y);

            const b2Vec2 releaseScreen =
                stage17_headless_screen_from_physics(
                    L, pullCursor);
            set_global_xy_table(
                L, "cursor",
                releaseScreen.x, releaseScreen.y);

            lua_pushnumber(L, 1.0f);
            lua_setglobal(L, "touchcount");
            set_input_button(
                L, "keyReleased", "LBUTTON", true);

            dragRubberBandLength =
                (float)get_global_number(
                    L, "rubberBandLength");
            dragShootMaxLength =
                (float)get_global_number(
                    L, "shootMaxLength");

            releaseFrame = frame;
            slingPhase = SlingPhase::RELEASE;

            lua_getglobal(L, "settings");
            lua_getfield(L, -1, "birdsShooted");
            const double birdsShootedBeforeRelease =
                lua_isnumber(L, -1)
                    ? (double)lua_tonumber(L, -1)
                    : NAN;
            lua_pop(L, 2);

            std::printf(
                "[stage17-input] RELEASE frame=%d "
                "rubberBandLength=%.6f shootMaxLength=%.6f "
                "physicsTarget=(%.6f,%.6f) "
                "screenCursor=(%.6f,%.6f) "
                "settings.birdsShooted=%.0f\n",
                frame,
                (double)dragRubberBandLength,
                (double)dragShootMaxLength,
                (double)pullCursor.x,
                (double)pullCursor.y,
                (double)releaseScreen.x,
                (double)releaseScreen.y,
                birdsShootedBeforeRelease);
        }

        if ((frame >= 58 && frame <= 66) ||
            slingPhase == SlingPhase::PRESS ||
            slingPhase == SlingPhase::DRAG ||
            slingPhase == SlingPhase::RELEASE)
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

        if (slingPhase == SlingPhase::PRESS &&
            frame == pressFrame) {
            lua_getglobal(L, "selectedBird");
            selectedAfterPress = lua_istable(L, -1);
            lua_pop(L, 1);

            const bool dragStartedAfterPress =
                get_global_bool(
                    L, "dragStarted", false) != 0;

            std::printf(
                "[stage17-state] AFTER PRESS frame=%d "
                "selectedBird=%s dragStarted=%s\n",
                frame,
                selectedAfterPress ? "table" : "nil",
                dragStartedAfterPress ? "true" : "false");

            if (!selectedAfterPress) {
                float luaBirdX = NAN;
                float luaBirdY = NAN;
                (void)physics.objectNumber(
                    slingBirdName, "x", &luaBirdX);
                (void)physics.objectNumber(
                    slingBirdName, "y", &luaBirdY);

                b2Vec2 cp(0.0f, 0.0f);
                b2Vec2 cw(0.0f, 0.0f);
                b2Vec2 cs(0.0f, 0.0f);
                (void)get_global_xy_table(
                    L, "cursorPhysics", &cp);
                (void)get_global_xy_table(
                    L, "cursorWorld", &cw);
                (void)get_global_xy_table(
                    L, "cursor", &cs);

                const float dx = luaBirdX - cp.x;
                const float dy = luaBirdY - cp.y;
                const float distance =
                    std::sqrt(dx * dx + dy * dy);

                std::fprintf(stderr,
                    "[stage17-selectdiag] SELECTION FAILED: "
                    "luaBird=(%.6f,%.6f) "
                    "cursorPhysics=(%.6f,%.6f) "
                    "distance=%.9f touchcount=%.3f "
                    "birdReady=%s currentBirdName='%s' "
                    "shootRange=%.6f "
                    "cursorWorld=(%.6f,%.6f) "
                    "cursorScreen=(%.6f,%.6f)\n",
                    (double)luaBirdX, (double)luaBirdY,
                    (double)cp.x, (double)cp.y,
                    (double)distance,
                    get_global_number(L, "touchcount"),
                    get_global_bool(
                        L, "birdReady", false)
                        ? "true" : "false",
                    get_global_string(
                        L, "currentBirdName").c_str(),
                    get_global_number(L, "shootRange"),
                    (double)cw.x, (double)cw.y,
                    (double)cs.x, (double)cs.y);

                lua_close(L);
                gPhysics = nullptr;
                gSprites = nullptr;
                return 24;
            }
        }

        if (slingPhase == SlingPhase::DRAG &&
            frame == dragFrame) {
            dragRubberBandLength =
                (float)get_global_number(
                    L, "rubberBandLength");
            dragShootMaxLength =
                (float)get_global_number(
                    L, "shootMaxLength");

            b2Vec2 rubber(0.0f, 0.0f);
            (void)get_global_xy_table(
                L, "rubberBandPos", &rubber);

            lua_getglobal(L, "selectedBird");
            const bool selectedDuringDrag =
                lua_istable(L, -1);
            lua_pop(L, 1);

            std::printf(
                "[stage17-state] AFTER DRAG frame=%d "
                "rubberBandPos=(%.6f,%.6f) "
                "length=%.6f max=%.6f "
                "selectedBird=%s currentBirdName='%s'\n",
                frame,
                (double)rubber.x, (double)rubber.y,
                (double)dragRubberBandLength,
                (double)dragShootMaxLength,
                selectedDuringDrag ? "table" : "nil",
                get_global_string(
                    L, "currentBirdName").c_str());
        }

        if (slingPhase == SlingPhase::RELEASE &&
            frame == releaseFrame) {
            lua_getglobal(L, "flyingBird");
            if (lua_istable(L, -1)) {
                lua_getfield(L, -1, "name");
                flyingBirdAfterRelease =
                    lua_isstring(L, -1) &&
                    slingBirdName ==
                        lua_tostring(L, -1);
                lua_pop(L, 1);
            }
            lua_pop(L, 1);

            birdFiredAfterRelease =
                get_global_bool(
                    L, "birdFired", false) != 0;
            currentBirdClearedAfterRelease =
                get_global_string(
                    L, "currentBirdName").empty();

            lua_getglobal(L, "selectedBird");
            selectedBirdClearedAfterRelease =
                lua_isnil(L, -1);
            lua_pop(L, 1);

            shotFlagAfterRelease =
                get_object_bool(
                    L, slingBirdName, "shot", false);

            birdsShotAfterRelease =
                (float)get_global_number(
                    L, "birdsShot");

            releasePosition =
                slingBirdBody
                    ? slingBirdBody->GetPosition()
                    : b2Vec2(0.0f, 0.0f);

            std::printf(
                "[stage17-state] AFTER RELEASE frame=%d "
                "flyingBird=%s birdFired=%s "
                "currentBirdName=%s selectedBird=%s "
                "shot=%s birdsShot %.0f->%.0f "
                "bodyPos=(%.6f,%.6f) bodyVel=(%.6f,%.6f)\n",
                frame,
                flyingBirdAfterRelease ? slingBirdName.c_str()
                                       : "<unexpected>",
                birdFiredAfterRelease ? "true" : "false",
                currentBirdClearedAfterRelease ? "nil"
                                               : "<present>",
                selectedBirdClearedAfterRelease ? "nil"
                                                : "<present>",
                shotFlagAfterRelease ? "true" : "false",
                (double)birdsShotBefore,
                (double)birdsShotAfterRelease,
                slingBirdBody
                    ? (double)slingBirdBody->GetPosition().x
                    : 0.0,
                slingBirdBody
                    ? (double)slingBirdBody->GetPosition().y
                    : 0.0,
                slingBirdBody
                    ? (double)slingBirdBody->GetLinearVelocity().x
                    : 0.0,
                slingBirdBody
                    ? (double)slingBirdBody->GetLinearVelocity().y
                    : 0.0);

            blockCollisionCallsAtRelease =
                physics.originalBlockCollisionCalls;
            blockDamageMutationsAtRelease =
                physics.damageMutationCount;
            birdCollisionCallsAtRelease =
                physics.originalBirdCollisionCalls;
            bodyCountAtRelease = (int)physics.bodies.size();

            ShotTrace trace;
            trace.number = currentShotNumber;
            trace.bird = slingBirdName;
            trace.readyFrame = readyFrame;
            trace.pressFrame = pressFrame;
            trace.dragFrame = dragFrame;
            trace.releaseFrame = releaseFrame;
            trace.rubberBandLength = dragRubberBandLength;
            trace.shootMaxLength = dragShootMaxLength;
            trace.birdsShotBefore = birdsShotBefore;
            trace.birdsShotAfter = birdsShotAfterRelease;
            trace.selectedAfterPress = selectedAfterPress;
            trace.flyingBirdAfterRelease = flyingBirdAfterRelease;
            trace.birdFiredAfterRelease = birdFiredAfterRelease;
            trace.currentBirdClearedAfterRelease =
                currentBirdClearedAfterRelease;
            trace.selectedBirdClearedAfterRelease =
                selectedBirdClearedAfterRelease;
            trace.shotFlagAfterRelease = shotFlagAfterRelease;
            trace.applyImpulseCallsBefore =
                applyImpulseCallsAtShotStart;
            trace.applyImpulseCallsAfter =
                gStage17ApplyImpulseCalls;
            trace.impulse = gStage17Impulse;
            trace.velocityAfterImpulse =
                gStage17VelocityAfterImpulse;
            trace.releasePosition = releasePosition;
            trace.fixedStepsAtRelease = fixedStepCount;
            trace.blockCallbacksAtRelease =
                physics.originalBlockCollisionCalls;
            trace.blockDamageAtRelease =
                physics.damageMutationCount;
            trace.birdCallbacksAtRelease =
                physics.originalBirdCollisionCalls;
            trace.birdDamageAtRelease =
                physics.birdDamageMutationCount;
            trace.bodiesAtRelease = (int)physics.bodies.size();
            trace.scoreAtRelease = physics.blockScore();
            shots.push_back(trace);

            std::printf(
                "[stage21-shot] #%d RELEASED bird='%s' "
                "applyImpulseDelta=%d birdsShot %.0f->%.0f "
                "impulse=(%.6f,%.6f) velocity=(%.6f,%.6f)\\n",
                trace.number,
                trace.bird.c_str(),
                trace.applyImpulseCallsAfter -
                    trace.applyImpulseCallsBefore,
                (double)trace.birdsShotBefore,
                (double)trace.birdsShotAfter,
                (double)trace.impulse.x,
                (double)trace.impulse.y,
                (double)trace.velocityAfterImpulse.x,
                (double)trace.velocityAfterImpulse.y);

            clear_stage17_mouse(L);
            slingPhase = SlingPhase::FLYING;
        }

        // Stage 21 observes original post-shot lifecycle only. It never
        // synthesizes the next bird, victory, or failure state.
        if (slingPhase == SlingPhase::FLYING && releaseFrame > 0) {
            slingBirdBody = physics.find(slingBirdName.c_str());

            const std::string lifecycleCurrentBird =
                get_global_string(L, "currentBirdName");
            const std::string lifecycleFlyingBird =
                get_global_table_string_field(L, "flyingBird", "name");
            const bool lifecycleBirdReady =
                get_global_bool(L, "birdReady", false) != 0;
            const bool lifecycleLevelCompleted =
                get_global_bool(L, "levelCompleted", false) != 0;
            const float lifecycleLevelFailedTimer =
                (float)get_global_number(L, "levelFailedTimer");
            // Exact original updateGame ordering matters here:
            //
            //   checkLevelComplete()
            //     -> initLevelComplete() sets levelCompleted=true and
            //        levelCompleteTimer=1
            //   checkLevelFailed()
            //     -> initLevelFailed(dt) can STILL run later in the SAME
            //        update and increment levelFailedTimer by one dt
            //
            // Therefore a one-frame levelFailedTimer pulse is not itself a
            // failed terminal when levelCompleted has already won this frame.
            // On the next frame levelCompleteTimer>0 routes updateGame into
            // updateLevelEnding(), so the failure timer does not continue.
            const bool lifecycleLevelFailedTimerAdvanced =
                std::isfinite(lifecycleLevelFailedTimer) &&
                std::isfinite(levelFailedTimerBaseline) &&
                lifecycleLevelFailedTimer >
                    levelFailedTimerBaseline + 0.000001f;

            const bool lifecycleLevelFailed =
                lifecycleLevelFailedTimerAdvanced &&
                !lifecycleLevelCompleted;

            if (lifecycleLevelCompleted &&
                lifecycleLevelFailedTimerAdvanced) {
                std::printf(
                    "[stage21-terminal] frame=%d ORIGINAL ordering quirk: "
                    "levelCompleted=true while initLevelFailed(dt) also "
                    "advanced levelFailedTimer to %.6f in the same update; "
                    "classifying terminal as COMPLETE because "
                    "levelCompleteTimer now owns subsequent updateLevelEnding()"
                    "\n",
                    frame,
                    (double)lifecycleLevelFailedTimer);
            }

            if (physics.originalBlockCollisionCalls >
                    blockCollisionCallsAtRelease ||
                physics.damageMutationCount >
                    blockDamageMutationsAtRelease) {
                sawBlockActivityAfterRelease = true;
            }

            const bool lifecycleChanged =
                lifecycleCurrentBird != lastLifecycleCurrentBird ||
                lifecycleFlyingBird != lastLifecycleFlyingBird ||
                lifecycleBirdReady != lastLifecycleBirdReady ||
                lifecycleLevelCompleted != lastLifecycleLevelCompleted ||
                lifecycleLevelFailed != lastLifecycleLevelFailed;

            if (lifecycleChanged) {
                std::printf(
                    "[stage21-lifecycle] frame=%d "
                    "currentBird='%s' flyingBird='%s' "
                    "birdReady=%s birdFired=%s "
                    "hasMovingObjects=%s levelCompleted=%s "
                    "levelFailed=%s failedTimer=%.3f "
                    "bodies=%zu score=%.0f "
                    "blockCallbacks=%d birdCallbacks=%d\n",
                    frame,
                    lifecycleCurrentBird.c_str(),
                    lifecycleFlyingBird.c_str(),
                    lifecycleBirdReady ? "true" : "false",
                    get_global_bool(L, "birdFired", false)
                        ? "true" : "false",
                    get_global_bool(L, "hasMovingObjects", false)
                        ? "true" : "false",
                    lifecycleLevelCompleted ? "true" : "false",
                    lifecycleLevelFailed ? "true" : "false",
                    (double)lifecycleLevelFailedTimer,
                    physics.bodies.size(),
                    (double)physics.blockScore(),
                    physics.originalBlockCollisionCalls,
                    physics.originalBirdCollisionCalls);

                lastLifecycleCurrentBird = lifecycleCurrentBird;
                lastLifecycleFlyingBird = lifecycleFlyingBird;
                lastLifecycleBirdReady = lifecycleBirdReady;
                lastLifecycleLevelCompleted = lifecycleLevelCompleted;
                lastLifecycleLevelFailed = lifecycleLevelFailed;
            }

            if (firstBirdClearedFrame < 0 &&
                lifecycleFlyingBird != slingBirdName) {
                firstBirdClearedFrame = frame;
                std::printf(
                    "[stage21-lifecycle] first flying bird cleared "
                    "at frame=%d (now '%s')\n",
                    frame, lifecycleFlyingBird.c_str());
            }

            if (lifecycleBirdReady &&
                !lifecycleCurrentBird.empty() &&
                lifecycleCurrentBird != slingBirdName) {
                if (!shots.empty()) {
                    ShotTrace& completed = shots.back();
                    if (completed.terminalFrame < 0) {
                        completed.terminalFrame = frame;
                        completed.nextReadyFrame = frame;
                        completed.nextBird = lifecycleCurrentBird;
                        completed.fixedStepsAtTerminal = fixedStepCount;
                        completed.blockCallbacksAtTerminal =
                            physics.originalBlockCollisionCalls;
                        completed.blockDamageAtTerminal =
                            physics.damageMutationCount;
                        completed.birdCallbacksAtTerminal =
                            physics.originalBirdCollisionCalls;
                        completed.birdDamageAtTerminal =
                            physics.birdDamageMutationCount;
                        completed.bodiesAtTerminal =
                            (int)physics.bodies.size();
                        completed.scoreAtTerminal =
                            physics.blockScore();
                    }
                }

                if ((int)shots.size() < kTargetShots) {
                    std::printf(
                        "[stage21-lifecycle] SHOT #%zu COMPLETE: "
                        "next bird ready frame=%d name='%s'; "
                        "re-arming input state machine for shot #%zu\n",
                        shots.size(), frame,
                        lifecycleCurrentBird.c_str(),
                        shots.size() + 1);

                    // This is only harness control. The next bird, its ready
                    // state and currentBirdName were all produced by original
                    // Lua. Stage 21 merely permits the platform input probe
                    // to press it on the next render frame.
                    slingPhase = SlingPhase::WAIT_READY;
                    lastLifecycleCurrentBird.clear();
                    lastLifecycleFlyingBird.clear();
                    lastLifecycleBirdReady = false;
                    lastLifecycleLevelCompleted = false;
                    lastLifecycleLevelFailed = false;
                } else if (nextBirdReadyFrame < 0) {
                    // Level1 has three controllable birds in this corpus.
                    // If original Lua somehow presents a fourth, record it
                    // but do not treat it as a successful level terminal.
                    nextBirdReadyFrame = frame;
                    nextBirdName = lifecycleCurrentBird;
                    std::printf(
                        "[stage21-lifecycle] AFTER THREE SHOTS: "
                        "unexpected NEXT BIRD READY frame=%d name='%s'; "
                        "waiting for original level terminal\n",
                        frame, nextBirdName.c_str());
                }
            }

            if (levelCompletedFrame < 0 &&
                lifecycleLevelCompleted) {
                levelCompletedFrame = frame;

                if (!shots.empty()) {
                    ShotTrace& completed = shots.back();
                    if (completed.terminalFrame < 0) {
                        completed.terminalFrame = frame;
                        completed.levelCompleted = true;
                        completed.fixedStepsAtTerminal = fixedStepCount;
                        completed.blockCallbacksAtTerminal =
                            physics.originalBlockCollisionCalls;
                        completed.blockDamageAtTerminal =
                            physics.damageMutationCount;
                        completed.birdCallbacksAtTerminal =
                            physics.originalBirdCollisionCalls;
                        completed.birdDamageAtTerminal =
                            physics.birdDamageMutationCount;
                        completed.bodiesAtTerminal =
                            (int)physics.bodies.size();
                        completed.scoreAtTerminal =
                            physics.blockScore();
                    }
                }

                terminalFrame = frame;
                std::printf(
                    "[stage21-lifecycle] LEVEL COMPLETED frame=%d "
                    "after %zu released shot(s)\n",
                    frame, shots.size());
            }

            if (levelFailedFrame < 0 &&
                lifecycleLevelFailed &&
                (int)shots.size() >= kTargetShots) {
                levelFailedFrame = frame;

                if (!shots.empty()) {
                    ShotTrace& completed = shots.back();
                    if (completed.terminalFrame < 0) {
                        completed.terminalFrame = frame;
                        completed.levelFailed = true;
                        completed.fixedStepsAtTerminal = fixedStepCount;
                        completed.blockCallbacksAtTerminal =
                            physics.originalBlockCollisionCalls;
                        completed.blockDamageAtTerminal =
                            physics.damageMutationCount;
                        completed.birdCallbacksAtTerminal =
                            physics.originalBirdCollisionCalls;
                        completed.birdDamageAtTerminal =
                            physics.birdDamageMutationCount;
                        completed.bodiesAtTerminal =
                            (int)physics.bodies.size();
                        completed.scoreAtTerminal =
                            physics.blockScore();
                    }
                }

                terminalFrame = frame;
                std::printf(
                    "[stage21-lifecycle] LEVEL FAILED frame=%d "
                    "after %zu released shot(s); "
                    "original levelFailedTimer=%.6f\n",
                    frame, shots.size(),
                    (double)lifecycleLevelFailedTimer);
            }
        }

        if (slingPhase == SlingPhase::FLYING &&
            releaseFrame > 0 &&
            frame == releaseFrame + 30) {
            slingBirdBody = physics.find(slingBirdName.c_str());
            if (slingBirdBody) {
                positionAfter30Frames =
                    slingBirdBody->GetPosition();

            if (!shots.empty() &&
                shots.back().bird == slingBirdName) {
                shots.back().positionAfter30 =
                    positionAfter30Frames;
                shots.back().sawPlus30 = true;
            }

            std::printf(
                "[stage21-flight] shot=%d bird='%s' +30 render frames "
                "pos=(%.6f,%.6f) vel=(%.6f,%.6f) "
                "birdContacts=%d\n",
                currentShotNumber,
                slingBirdName.c_str(),
                (double)positionAfter30Frames.x,
                (double)positionAfter30Frames.y,
                (double)slingBirdBody->GetLinearVelocity().x,
                (double)slingBirdBody->GetLinearVelocity().y,
                activeBirdContactCount);
            }
        }

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
            frame == 90 || frame == 120 || frame == 150 ||
            frame == 180 || frame == 240 || frame == 300 ||
            frame == 360 || frame == 480 || frame == 600 ||
            frame == 900 || frame == 1200 ||
            frame == readyFrame || frame == pressFrame ||
            frame == dragFrame || frame == releaseFrame) {
            b2Body* pigNow = physics.find("SmallPiglette_7");
            std::printf(
                "[stage21-driver] frame=%3d time=%.6f currentFrame=%.0f "
                "gameTimer=%.6f physics=%s accumulator=%.9f "
                "fixedSteps=%d pig=(%.4f,%.4f)\n",
                frame,
                get_global_number(L, "time"),
                get_global_number(L, "currentFrame"),
                get_global_number(L, "gameTimer"),
                physics.physicsEnabled ? "on" : "off",
                (double)physicsAccumulator,
                fixedStepCount,
                pigNow ? (double)pigNow->GetPosition().x : (double)NAN,
                pigNow ? (double)pigNow->GetPosition().y : (double)NAN);
        }

        replay.capture(frame, L, physics);

        if (frame == 70 || frame == 71 || frame == 220 || frame == 221 || frame == 420) {
            if (!gpuScene.renderSnapshot(frame, physics, sprites)) {
                std::fprintf(stderr, "[angry-stage23.6A] GPU snapshot FAIL frame=%d\n", frame);
                lua_close(L);
                gPhysics = nullptr;
                gSprites = nullptr;
                return 28;
            }
        }

        if (terminalFrame > 0) {
            std::printf(
                "[stage21] original level terminal reached "
                "at frame=%d; stopping bounded observer\n",
                terminalFrame);
            break;
        }
    }

    const double timeValue = get_global_number(L, "time");
    const double frameValue = get_global_number(L, "currentFrame");
    const double gameTimer = get_global_number(L, "gameTimer");

    processNewContacts(lastFrameRun);

    slingBirdBody = physics.find(slingBirdName.c_str());
    const b2Vec2 finalBirdPos =
        slingBirdBody ? slingBirdBody->GetPosition()
                      : b2Vec2(0.0f, 0.0f);
    const b2Vec2 finalBirdVel =
        slingBirdBody ? slingBirdBody->GetLinearVelocity()
                      : b2Vec2(0.0f, 0.0f);

    std::printf(
        "[stage21] after %d frames: time=%.6f currentFrame=%.0f "
        "gameTimer=%.6f fixedSteps=%d removeBlocksCalls=%d "
        "postLaunchFixedSteps=%d\n",
        lastFrameRun, timeValue, frameValue, gameTimer,
        fixedStepCount, removeBlocksCalls,
        postLaunchFixedSteps);

    for (const ShotTrace& shot : shots) {
        std::printf(
            "[stage21-shot] #%d summary: bird='%s' "
            "ready=%d press=%d drag=%d release=%d "
            "rubberBandLength=%.6f max=%.6f "
            "applyImpulseDelta=%d "
            "impulse=(%.6f,%.6f) velocity=(%.6f,%.6f) "
            "birdsShot %.0f->%.0f "
            "terminal=%d nextReady=%d nextBird='%s' "
            "levelCompleted=%s levelFailed=%s "
            "fixedStepsAfterRelease=%d "
            "blockCallbacksDelta=%d birdCallbacksDelta=%d "
            "bodies %d->%d score %.0f->%.0f\n",
            shot.number,
            shot.bird.c_str(),
            shot.readyFrame,
            shot.pressFrame,
            shot.dragFrame,
            shot.releaseFrame,
            (double)shot.rubberBandLength,
            (double)shot.shootMaxLength,
            shot.applyImpulseCallsAfter -
                shot.applyImpulseCallsBefore,
            (double)shot.impulse.x,
            (double)shot.impulse.y,
            (double)shot.velocityAfterImpulse.x,
            (double)shot.velocityAfterImpulse.y,
            (double)shot.birdsShotBefore,
            (double)shot.birdsShotAfter,
            shot.terminalFrame,
            shot.nextReadyFrame,
            shot.nextBird.c_str(),
            shot.levelCompleted ? "true" : "false",
            shot.levelFailed ? "true" : "false",
            shot.fixedStepsAtTerminal -
                shot.fixedStepsAtRelease,
            shot.blockCallbacksAtTerminal -
                shot.blockCallbacksAtRelease,
            shot.birdCallbacksAtTerminal -
                shot.birdCallbacksAtRelease,
            shot.bodiesAtRelease,
            shot.bodiesAtTerminal,
            (double)shot.scoreAtRelease,
            (double)shot.scoreAtTerminal);
    }

    std::printf(
        "[stage21] last active bird snapshot: bird='%s' "
        "final=(%.6f,%.6f) finalVel=(%.6f,%.6f) "
        "classifiedBirdContacts=%d firstInitialBirdContactFrame=%d "
        "firstInitialBirdOther='%s'\n",
        slingBirdName.c_str(),
        (double)finalBirdPos.x,
        (double)finalBirdPos.y,
        (double)finalBirdVel.x,
        (double)finalBirdVel.y,
        classifiedBirdCollision,
        firstActiveBirdContactFrame,
        firstActiveBirdOther.c_str());

    std::printf(
        "[stage21] full-damage summary: "
        "blockDamageMutations=%d blockCollisionCallbacks=%d "
        "birdDamageMutations=%d birdCollisionCallbacks=%d "
        "queuedDead=%d nativeRemoveObjectCalls=%d "
        "bodies %d->%zu score=%.0f\n",
        physics.damageMutationCount,
        physics.originalBlockCollisionCalls,
        physics.birdDamageMutationCount,
        physics.originalBirdCollisionCalls,
        physics.queuedDeadObjects,
        physics.nativeRemoveObjectCalls,
        bodyCountAtRelease,
        physics.bodies.size(),
        (double)physics.blockScore());

    std::printf(
        "[stage21] lifecycle summary: "
        "firstBirdClearedFrame=%d nextBirdReadyFrame=%d "
        "nextBird='%s' levelCompletedFrame=%d levelFailedFrame=%d "
        "terminalFrame=%d lastFrame=%d\n",
        firstBirdClearedFrame,
        nextBirdReadyFrame,
        nextBirdName.c_str(),
        levelCompletedFrame,
        levelFailedFrame,
        terminalFrame,
        lastFrameRun);

    // Stage 22.7 regression gate: Stage 22.6 proved that the recovered
    // polygon skin removes the zero-input SmallPiglette landing damage.
    // In the full Level1 run, no pig damage may occur before the first
    // player press. Later pig damage caused by launched birds/structure
    // collapse is expected and remains part of normal gameplay.
    const int firstInputFrame = shots.empty() ? -1 : shots.front().pressFrame;
    float pigDamageBeforeFirstInput = 0.0f;
    int pigDamageMutationsBeforeFirstInput = 0;
    for (const DamageTrace& d : physics.damageTraces) {
        const bool isPig =
            d.objectName.find("Pig") != std::string::npos;
        if (isPig && firstInputFrame > 0 && d.frame < firstInputFrame) {
            pigDamageBeforeFirstInput += d.actualDamage;
            ++pigDamageMutationsBeforeFirstInput;
        }
    }

    std::printf(
        "[stage22.7-fidelity] polygonRadius=0.100000 "
        "firstInputFrame=%d pigDamageMutationsBeforeInput=%d "
        "pigDamageBeforeInput=%.9f\n",
        firstInputFrame,
        pigDamageMutationsBeforeFirstInput,
        (double)pigDamageBeforeFirstInput);

    bool allFinite = true;
    for (const auto& kv : physics.bodies)
        allFinite = finite_body(kv.second) && allFinite;

    bool ok = true;

    // Native timing remains the recovered original schedule.
    ok = (physicsEnabledFrame == 61) && ok;
    ok = (firstFixedStepFrame == 63) && ok;

    // Recovered-physics regression: the pre-input idle state must remain
    // clean while the normal full-Level1 lifecycle still runs below.
    ok = (firstInputFrame >= kFirstInputNotBeforeFrame) && ok;
    ok = (pigDamageMutationsBeforeFirstInput == 0) && ok;
    ok = (std::fabs(pigDamageBeforeFirstInput) < 0.000001f) && ok;

    // Stage 21 drives every controllable bird in Level1 through the same
    // reusable original input/slingshot state machine.
    ok = ((int)shots.size() == kTargetShots) && ok;
    ok = (gStage17ApplyImpulseCalls == kTargetShots) && ok;

    for (size_t i = 0; i < shots.size(); ++i) {
        const ShotTrace& shot = shots[i];

        ok = (shot.number == (int)i + 1) && ok;
        ok = !shot.bird.empty() && ok;
        ok = (shot.readyFrame > 0) && ok;
        ok = (shot.pressFrame == shot.readyFrame) && ok;
        ok = (shot.dragFrame == shot.pressFrame + 1) && ok;
        ok = (shot.releaseFrame == shot.dragFrame + 1) && ok;

        ok = shot.selectedAfterPress && ok;
        ok = std::isfinite(shot.rubberBandLength) && ok;
        ok = std::isfinite(shot.shootMaxLength) && ok;
        ok = (shot.rubberBandLength > 5.0f) && ok;
        ok = (shot.rubberBandLength <=
              shot.shootMaxLength + 0.01f) && ok;

        ok = ((shot.applyImpulseCallsAfter -
               shot.applyImpulseCallsBefore) == 1) && ok;
        ok = std::isfinite(shot.impulse.x) &&
             std::isfinite(shot.impulse.y) && ok;
        ok = (shot.impulse.x > 0.0f) && ok;
        ok = (shot.impulse.y < 0.0f) && ok;
        ok = (shot.impulse.Length() > 100.0f) && ok;
        ok = (shot.velocityAfterImpulse.x > 20.0f) && ok;
        ok = (shot.velocityAfterImpulse.y < -5.0f) && ok;

        ok = shot.flyingBirdAfterRelease && ok;
        ok = shot.birdFiredAfterRelease && ok;
        ok = shot.currentBirdClearedAfterRelease && ok;
        ok = shot.selectedBirdClearedAfterRelease && ok;
        ok = shot.shotFlagAfterRelease && ok;
        ok = std::isfinite(shot.birdsShotBefore) &&
             std::isfinite(shot.birdsShotAfter) && ok;
        ok = (std::fabs(
            shot.birdsShotAfter -
            (shot.birdsShotBefore + 1.0f)) < 0.01f) && ok;

        ok = (shot.terminalFrame > shot.releaseFrame) && ok;
        ok = ((shot.fixedStepsAtTerminal -
               shot.fixedStepsAtRelease) > 0) && ok;

        if (i + 1 < shots.size()) {
            // Shot #1 must transition into the bird that the original Lua
            // subsequently selected for shot #2.
            ok = (shot.nextReadyFrame > 0) && ok;
            ok = !shot.nextBird.empty() && ok;
            ok = (shot.nextBird == shots[i + 1].bird) && ok;
            ok = (shot.nextBird != shot.bird) && ok;
        }
    }

    // Both recovered damage families remain live across the two-shot run.
    // Ordinary block damage need not happen after *each* shot, but it must
    // occur naturally in at least one post-release interval.
    bool anyShotBlockDamage = false;
    for (const ShotTrace& shot : shots) {
        if (shot.blockDamageAtTerminal >
            shot.blockDamageAtRelease) {
            anyShotBlockDamage = true;
        }
    }
    ok = physics.birdDamageProbeApplied && ok;
    ok = anyShotBlockDamage && ok;
    ok = (physics.originalBlockCollisionCalls > 0) && ok;
    ok = (physics.damageMutationCount > 0) && ok;

    // Full ordinary destruction is now allowed through the exact Stage 13
    // deadBlocks -> removeBlocks -> reconstructed removeObject pipeline.
    ok = (physics.nativeRemoveObjectCalls >= 1) && ok;
    ok = (physics.bodies.size() <=
          (size_t)bodyCountAtRelease) && ok;

    // After all three original Level1 birds have been released, original
    // Lua itself must reach a real level terminal. Victory is represented by
    // levelCompleted=true. Failure is represented by original
    // initLevelFailed() advancing levelFailedTimer after checkLevelFailed().
    ok = (terminalFrame > releaseFrame) && ok;
    ok = ((levelCompletedFrame > 0) ^
          (levelFailedFrame > 0)) && ok;

    if (!shots.empty()) {
        const ShotTrace& lastShot = shots.back();
        ok = (lastShot.terminalFrame == terminalFrame) && ok;
        ok = (lastShot.levelCompleted ^
              lastShot.levelFailed) && ok;
    }

    ok = allFinite && ok;
    ok = !physics.callbackError && ok;

    const bool interpolationRuntimeOk =
        physics.renderHistoryCaptures > 0 &&
        physics.renderInterpolationPublishes > 0 &&
        gpuScene.interpolationEvidenceOk();
    std::printf(
        "[stage23.6A-interpolation] historyCaptures=%d catchupSkips=%d publishes=%d evidence=%s\n",
        physics.renderHistoryCaptures, physics.renderHistoryCatchupSkips,
        physics.renderInterpolationPublishes, interpolationRuntimeOk ? "PASS" : "FAIL");
    ok = interpolationRuntimeOk && ok;

    const bool replayOk = replay.finish();
    ok = replayOk && ok;
    const bool gpuReportOk = gpuScene.finishReport(physics);
    ok = gpuReportOk && ok;

    lua_close(L);
    gPhysics = nullptr;
    gSprites = nullptr;

    if (!ok) {
        std::fprintf(stderr,
            "[angry-stage22.7] FAIL recovered-physics full-Level1 regression\n");
        return 21;
    }

    std::printf(
        "[angry-stage22.7] ORIGINAL INPUT STATE MACHINE LAUNCHED "
        "ALL THREE LEVEL1 BIRDS\n");
    std::printf(
        "[angry-stage21] EVERY SHOT WAS SELECTED/DRAGGED/RELEASED "
        "THROUGH ORIGINAL updateGame()\n");
    std::printf(
        "[angry-stage21] RECOVERED BIRD + BLOCK DAMAGE REMAINED "
        "ACTIVE THROUGH THE WHOLE LEVEL RUN\n");
    std::printf(
        "[angry-stage21] ORIGINAL Lua CHOSE SHOTS #2/#3 WITHOUT "
        "HARNESS SELECTION: '%s' -> '%s'\n",
        shots.size() > 1 ? shots[1].bird.c_str() : "<missing>",
        shots.size() > 2 ? shots[2].bird.c_str() : "<missing>");
    if (levelCompletedFrame > 0) {
        std::printf(
            "[angry-stage21] ORIGINAL Lua REACHED LEVEL COMPLETE "
            "AT FRAME %d\n",
            levelCompletedFrame);
    } else {
        std::printf(
            "[angry-stage21] ORIGINAL Lua REACHED LEVEL FAILED "
            "AT FRAME %d\n",
            levelFailedFrame);
    }
    std::printf("[angry-stage21] LEVEL1 PLAYED FROM START TO TERMINAL STATE ON ARM64\n");
    std::printf("[angry-stage21] PASS\n");
    std::printf(
        "[angry-stage23.2] ORIGINAL-SPRITE REPLAY RECORDED FROM THE "
        "FULL ARM64 LEVEL RUN\n");
    std::printf(
        "[angry-stage23.2] REPLAY CONTAINS REAL BODY TRANSFORMS, SCORE, "
        "BIRD LIFECYCLE AND LEVEL COMPLETE STATE\n");
    std::printf("[angry-stage23.2] ORIGINAL SPRITE METADATA IS ATTACHED TO EVERY CAPTURED BODY FRAME\n");
    std::printf("[angry-stage23.2] REPLAY USES 20 ORIGINAL SOURCE PIXELS PER PHYSICS WORLD UNIT\n");
    std::printf("[angry-stage23.2] ATLAS-Y ORIENTATION REMAINS AN EXPLICIT VISUAL AUDIT TOGGLE\n");
    std::printf("[angry-stage23.2] PASS\n");
    std::printf("[angry-stage23.6A] BOTH ORIGINAL RGBA4444 ATLASES RENDERED THROUGH REAL GLES1 ON ARM64\n");
    std::printf("[angry-stage23.6A] LEVEL1 MULTI-SPRITE PIVOTS / ROTATIONS / DAMAGE-SPRITE STATE CAPTURED ON GPU\n");
    std::printf("[angry-stage23.6A] RECOVERED LINEAR / CLAMP / UNPACK=1 / ALPHA-BLEND / MATRIX-UPLOAD CONTRACT APPLIED\n");
    std::printf("[angry-stage23.6A] ARMV7 RENDEROBJECTDATA TWO-SLOT TRANSFORM HISTORY / FIXED-STEP INTERPOLATION IS ACTIVE\n");
    std::printf("[angry-stage23.6A] LUA AND GLES SNAPSHOTS NOW CONSUME INTERPOLATED x/y/angle INSTEAD OF RAW b2Body TRANSFORMS\n");
    std::printf("[angry-stage23.6A] DEBUG CAMERA AND NAME-SORT DRAW ORDER REMAIN EXPLICIT NON-FINAL AUDIT BOUNDARIES\n");
    std::printf("[angry-stage23.6A] PASS\n");
    return 0;
}
