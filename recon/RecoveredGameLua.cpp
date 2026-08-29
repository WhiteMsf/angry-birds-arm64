// Semantic reconstruction snippets for the ARM64 preservation port.
// NOT original Rovio source.

#include "RecoveredGameLua.hpp"

// Include the historical Box2D headers selected for the port.
// #include <Box2D/Box2D.h>

b2Body* GameLua::getBody(const lang::String& /*name*/)
{
    // ARMv7 proof:
    // objects.containsKey(name) ? objects.get(name)->body : nullptr
    //
    // Wire to the reconstructed Hashtable member when the GameLua layout is defined.
    return nullptr;
}

void GameLua::setVelocity(lang::String /*name*/, float /*x*/, float /*y*/)
{
    // Proven semantics:
    // if (b2Body* body = getBody(name))
    //     if (body->GetType() != b2_staticBody)
    //         body->SetLinearVelocity(b2Vec2(x, y));
}

void GameLua::setAngularVelocity(lang::String /*name*/, float /*w*/)
{
    // Proven semantics:
    // if (b2Body* body = getBody(name))
    //     if (body->GetType() != b2_staticBody)
    //         body->SetAngularVelocity(w);
}

void GameLua::applyForce(
    lang::String /*name*/, float /*fx*/, float /*fy*/, float /*px*/, float /*py*/)
{
    // Proven equivalent behavior:
    // if (b2Body* body = getBody(name))
    //     if (body->GetType() == b2_dynamicBody)
    //         body->ApplyForce(b2Vec2(fx, fy), b2Vec2(px, py));
    //
    // The ARMv7 build inlines the old Box2D math directly.
}

void GameLua::applyImpulse(
    lang::String /*name*/, float /*ix*/, float /*iy*/, float /*px*/, float /*py*/)
{
    // Proven equivalent behavior:
    // if (b2Body* body = getBody(name))
    //     if (body->GetType() == b2_dynamicBody)
    //         body->ApplyLinearImpulse(b2Vec2(ix, iy), b2Vec2(px, py));
}

void GameLua::setPosition(lang::String /*name*/, float /*x*/, float /*y*/)
{
    // Proven:
    // 1. body->SetTransform(b2Vec2(x,y), body->GetAngle())
    // 2. world[name].x = x; world[name].y = y
    // 3. synchronize three position caches in RenderObjectData
}

void GameLua::setRotation(lang::String /*name*/, float /*angle*/)
{
    // Proven:
    // 1. angle = fmodf(angle, 2*pi); if (angle < 0) angle += 2*pi;
    // 2. body->SetTransform(body->GetPosition(), angle)
    // 3. world[name].angle = angle
    // 4. synchronize three rotation caches in RenderObjectData
}

void GameLua::setObjectParameter(
    lang::String /*name*/, float /*parameter*/, float /*value*/)
{
    // Exact branch semantics:
    //
    // RenderObjectData* o = objects.get(name);
    // switch ((int)parameter) {
    // case 1:
    //     o->alternateRenderPass = ((int)value == 1);
    //     break;
    // case 2:
    //     o->body->SetType(value != 0.0f ? b2_dynamicBody : b2_staticBody);
    //     break;
    // }
}

b2Body* GameLua::createBox(
    RenderObjectData* /*object*/,
    lang::String /*definition*/,
    float /*x*/, float /*y*/,
    float /*width*/, float /*height*/,
    float /*density*/, float /*friction*/, float /*restitution*/)
{
    /*
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
    bd.inertiaScale = 1.0f; // historical Box2D field

    b2Body* body = world_->CreateBody(&bd);

    b2PolygonShape shape;
    shape.m_radius = 0.1f; // behavior observed in this build
    shape.SetAsBox(width * 0.5f, height * 0.5f);

    b2FixtureDef fd;
    fd.shape = &shape;
    fd.userData = object;
    fd.friction = friction;
    fd.restitution = restitution;
    fd.density = density;
    fd.isSensor = false;
    fd.filter.categoryBits = 1;
    fd.filter.maskBits = 0xFFFF;
    fd.filter.groupIndex = 0;

    body->CreateFixture(&fd);
    return body;
    */
    return nullptr;
}

b2Body* GameLua::createCircle(
    RenderObjectData* /*object*/,
    lang::String /*definition*/,
    float /*x*/, float /*y*/,
    float /*radius*/,
    float /*density*/, float /*friction*/, float /*restitution*/)
{
    // Same body/fixture defaults as createBox.
    // Uses b2CircleShape and the supplied radius.
    return nullptr;
}

b2Body* GameLua::createPolygon(
    RenderObjectData* /*object*/,
    lang::String /*definition*/,
    float /*x*/, float /*y*/,
    float /*unused1*/, float /*unused2*/,
    float /*density*/, float /*friction*/, float /*restitution*/)
{
    // Same body/fixture defaults as createBox.
    // Copies GameLua's accumulated vertex array and:
    //     b2PolygonShape shape;
    //     shape.m_radius = 0.1f;
    //     shape.Set(vertices, vertexCount);
    return nullptr;
}
