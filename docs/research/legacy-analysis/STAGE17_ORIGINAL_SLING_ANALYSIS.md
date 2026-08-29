# Stage 17 — original Lua slingshot input and release

Stage 16 closes the bird-caused destruction pipeline. The next missing piece
for basic gameplay is no longer collision physics; it is the actual slingshot
state machine.

Stage 17 does **not** teleport the bird and does **not** set its launch
velocity directly. It publishes only native input globals and lets the
original `updateGame()` do the launch.

## Static Lua 5.1 bytecode reconstruction

`updateGame` is root child 136. The relevant original bytecode is:

### Mouse press / bird selection

At PCs 669+:

```text
if keyPressed.LBUTTON and not levelCompleted:
    draggingStartPosPhysics = cursorPhysics
    draggingStartPosScreen  = cursor
    oldCursor               = cursor

    dragStarted = true
    ...

    if touchcount == 1 and currentBirdName ~= nil:
        if distance(currentBird, cursorPhysics) < selectionRange:
            selectedBird = objects.world[currentBirdName]
```

### Drag

At PCs 1730+:

```text
if keyHold.LBUTTON and dragStarted and selectedBird ~= nil and birdReady:
    draggingStartPosPhysics = levelStartPosition

    delta = levelStartPosition - cursorPhysics
    rubberBandAngle = atan2(delta.y, delta.x)
    shootMaxLength = shootRange + 3.2

    rubberBandPos = clamped cursor position
    rubberBandLength = distance(levelStartPosition, rubberBandPos)
```

### Release

At PCs 2129..2326:

```text
if dragStarted and selectedBird ~= nil and not levelCompleted:
    stretch = clamp(rubberBandLength / shootMaxLength, 0, 1)

    scalar =
        (-defaultForce) * physicsScale * selectedBird.mass

    setPosition(selectedBird.name, rubberBandPos.x, rubberBandPos.y)
    setVelocity(selectedBird.name, 0, 0)

    applyImpulse(
        selectedBird.name,
        normalize(levelStartPosition - cursorPhysics).x * scalar * stretch,
        normalize(levelStartPosition - cursorPhysics).y * scalar * stretch,
        selectedBird.x,
        selectedBird.y
    )

    cameraTargetObject = selectedBird
    flyingBird = selectedBird
    selectedBird.shot = true
    selectedBird.hasCollided = false

    birdSpecialtyAvailable = true
    birdReady = false
    birdFired = true
    birdsShot = birdsShot + 1
    currentBirdName = nil
    selectedBird = nil
```

The original constants recovered from `initialize()` are:

```text
defaultForce = -800
physicsToWorld = 20
physicsScale = 1 / physicsToWorld = 0.05
shootRange = 2.2
shootMaxLength = shootRange + 3.2 = 5.4
```

## Stage 17 input corpus

The harness waits until original `animateBirdToSlingShot()` sets:

```text
birdReady = true
currentBirdName = <real Level1 bird>
```

It then publishes three native input frames:

```text
PRESS:
  LBUTTON pressed+held at the real bird body position

DRAG:
  LBUTTON held
  cursorPhysics = levelStartPosition + (-5, +2)

RELEASE:
  LBUTTON released at the same cursor
```

Therefore the intended launch vector is:

```text
levelStartPosition - cursorPhysics = (+5, -2)
```

with pull length `sqrt(29) ~= 5.385`, just under the original max of `5.4`.

The recovered native `applyImpulse` binding is instrumented only to record the
call and before/after body velocity. The harness never calls it itself.

Collision damage is disabled in Stage 17 so the launch proof remains isolated.
Any naturally occurring bird contact is logged as bonus telemetry but is not
required for PASS.
