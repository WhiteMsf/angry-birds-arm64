# Box2D 2.1.2 source note

This repository vendors a period-appropriate Box2D 2.1.2 source baseline under:

`vendor/box2d-v2.1.2/Box2D/Box2D/`

The baseline used during reconstruction corresponds to commit:

`20100c5e81ed18619b0fbd5d78bd60e7b13c7fe9`

The vendored tree retains the original Box2D license at:

`vendor/box2d-v2.1.2/Box2D/License.txt`

This is an **altered source version** used for compatibility with the
historical Angry Birds runtime. It must not be represented as an untouched
or original Erin Catto / Box2D distribution.

Reconstruction work included evidence-driven compatibility changes and build
constraints required to reproduce relevant historical game behavior. The
current Android ARM64 build uses the repository's top-level CMake project;
the historical upstream Box2D build system, examples, documentation and
unrelated platform contributions are intentionally not redistributed here.

The original Box2D copyright and license notice remain authoritative.
