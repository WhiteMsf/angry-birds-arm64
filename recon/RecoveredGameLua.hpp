#pragma once
// Semantic reconstruction scaffold for Angry Birds Classic 1.4.2.
// NOT original Rovio source. Names marked provisional are inferred from behavior.

#include <cstdint>

// Forward declarations only. Wire these to the recovered KA3D / historical Box2D tree.
namespace lang { class String; template<class K, class V, class H> class Hashtable; template<class T> class Array; }
namespace lua { class LuaState; class LuaTable; }
namespace game { class Resources; class Sprite; }
namespace gr { class Image; class Context; }
namespace framework { class App; }

class b2World;
class b2Body;
class b2Fixture;
class b2Contact;
class b2Manifold;

class GameLua {
public:
    struct RenderObjectData {
        float transform0_x{};
        float transform0_y{};
        float transform0_angle{};

        float transform1_x{};
        float transform1_y{};
        float transform1_angle{};

        std::int32_t state18{};

        // Real build embeds these by value. Keep the declarations conceptual until
        // the recovered KA3D ABI is wired in.
        // lua::LuaTable table;       // ARMv7 +0x1C
        // lang::String name;         // ARMv7 +0x34
        // lang::String spriteName;   // ARMv7 +0x4C

        b2Body* body{};
        game::Sprite* sprite{};
        gr::Image* texture{};

        float scalar70{};
        float renderX{};
        float renderY{};
        float renderAngle{};
        float zOrder{};

        bool pendingVelocity{};      // ARMv7 +0x84
        bool motionFlag{};           // +0x85, provisional
        bool collisionClass{};       // +0x86, provisional
        bool specialObject{};        // +0x87, provisional
        bool circleMotionMode{};     // +0x88, provisional
        bool alternateRenderPass{};  // +0x89
        bool zOrder999Special{};     // +0x8A
    };

    b2Body* getBody(const lang::String& name);

    void setVelocity(lang::String name, float x, float y);
    void setAngularVelocity(lang::String name, float w);
    void applyForce(lang::String name, float fx, float fy, float px, float py);
    void applyImpulse(lang::String name, float ix, float iy, float px, float py);
    void setPosition(lang::String name, float x, float y);
    void setRotation(lang::String name, float angle);

    void setObjectParameter(lang::String name, float parameter, float value);

    b2Body* createBox(
        RenderObjectData* object,
        lang::String definition,
        float x, float y,
        float width, float height,
        float density, float friction, float restitution);

    b2Body* createCircle(
        RenderObjectData* object,
        lang::String definition,
        float x, float y,
        float radius,
        float density, float friction, float restitution);

    b2Body* createPolygon(
        RenderObjectData* object,
        lang::String definition,
        float x, float y,
        float unused1, float unused2,
        float density, float friction, float restitution);

    // Raw-Lua bindings proven from constructor:
    int createJointLua(lua::LuaState*);
    int setRenderState(lua::LuaState*);
    int getWorldPoint(lua::LuaState*);

    // Major routines still requiring semantic reconstruction:
    void update(float dt);
    void BeginContact(b2Contact*);
    bool ShouldCollide(b2Fixture*, b2Fixture*);
    void loadLevel(lang::String);
    void setTheme(lang::String);
    void drawGame();
    void saveLevel(lang::String);

private:
    // Actual member ordering must be copied from the recovered KA3D class layout,
    // not from this conceptual header.
    framework::App* app_{};
    game::Resources* resources_{};
    b2World* world_{};
};
