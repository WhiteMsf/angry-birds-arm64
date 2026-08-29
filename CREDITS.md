# Credits and Attribution

This repository is an **independent ARM64 reconstruction and preservation project** for the classic Android release of *Angry Birds*. It is not an official Rovio project.

The goal of the project is to make the classic Android game run on modern ARM64 Android devices while preserving the behavior of the original release as closely as practical. The project deliberately separates the **original game and its content** from the **independent reconstruction, compatibility, tooling, and validation work** performed here.

## Original game

**Angry Birds** was created and published by **Rovio Entertainment**.

All original game design, characters, names, levels, artwork, animation, audio, music, user-interface art, text, trademarks, logos, and other proprietary game content belong to Rovio Entertainment and/or their respective rights holders.

This project does **not** claim authorship or ownership of any of that original material.

## ARM64 reconstruction project

**Project lead, technical direction, hands-on testing, device validation, and release decisions:**
**WhiteMsf**

**AI-assisted engineering, reverse-engineering analysis, code reconstruction, debugging, test/tooling design, and documentation support:**
**ChatGPT by OpenAI**, working under the project maintainer's direction and iterative validation.

The maintainer remains responsible for the project, its public releases, the final technical decisions, and the validation of generated or suggested code. Attribution to ChatGPT/OpenAI acknowledges substantial development assistance; it does not imply that OpenAI owns, sponsors, endorses, or officially maintains this project.

### In-game attribution

The public ARM64 build adds one concise line to the end of the original About/Credits text flow:

`ARM64 reconstruction by WhiteMsf`

This line identifies only the independent ARM64 reconstruction work. It does not replace or rewrite Rovio's original credits and does not claim authorship of the original game or its creative content.

## What this project did

The ARM64 reconstruction work includes, among other things:

- analyzed the behavior and interfaces of the shipped legacy Android/ARMv7 game binary and runtime;
- reconstructed the native Android runtime needed to execute the classic game on **ARM64/AArch64** devices;
- rebuilt native/Lua integration and compatibility around the game's existing Lua logic;
- reconstructed resource, sprite, menu, bitmap-font, scene, and rendering paths required by the original game flow;
- restored touch and multitouch input behavior for modern Android devices;
- reconstructed gameplay-side native bridges used by the original Lua code, including physics-facing behavior;
- reproduced relevant historical Box2D behavior and game-specific numerical/solver differences where evidence showed them;
- restored menu navigation, level progression, HUD/result screens, pause flow, Golden Eggs paths, audio, save persistence, and Android lifecycle behavior;
- built a modern Android NativeActivity/GLES-based ARM64 packaging path around the reconstructed runtime;
- created regression contracts, diagnostics, binary audits, release checks, and reproducible build tooling;
- created a release pipeline that stages original proprietary game data **only from the builder's own local copy** rather than placing those assets in this repository.

This work is a **semantic/behavioral reconstruction**. It is intended to reproduce the interfaces and behavior needed by the classic release; it is not presented as the original proprietary Rovio source tree.

## What this project did not do

This project did **not**:

- create the original *Angry Birds* game;
- design the original levels or game rules;
- create the birds, pigs, characters, names, branding, or other original concepts;
- create or redraw the original artwork, animations, textures, fonts, music, sound effects, or other game assets;
- obtain, publish, or claim to possess Rovio's original proprietary game source code;
- claim that reconstructed source is leaked, recovered, or official Rovio source;
- redistribute the original commercial APK as source material;
- include the original proprietary game asset set in the public source repository;
- make this an official, licensed, sponsored, or endorsed Rovio release;
- make this an official, sponsored, or endorsed OpenAI release.

## Original content and local build inputs

The public source repository is designed so that proprietary *Angry Birds* content is not bundled with the reconstruction source.

Where the build requires original game data, that data is discovered or staged **locally from the builder's own copy**. The build/release tooling keeps the public reconstruction source separate from original game assets, original APK material, personal saves, and private signing material.

## Third-party software

The reconstruction also depends on or incorporates third-party software with its own authorship and license terms, including:

- **KA3D / Pixelgene historical compatibility** - the KA3D source tree is not redistributed in this repository. Some compatibility behavior was reconstructed after analysis of historical KA3D code and the original ARMv7 runtime; KA3D remains third-party software under its original upstream license terms;
- **Lua 5.1.5** — obtained by the build tooling from the official Lua distribution and used with compatibility changes required by the historical game chunk ABI;
- **Box2D 2.1.2 family** — the build pins a period-appropriate Box2D source baseline and applies evidence-driven compatibility changes where required by the shipped game behavior;
- Android/NDK, OpenGL ES, and other platform components under their respective terms.

Third-party copyright notices and license files remain authoritative for those components.

## No endorsement

*Angry Birds*, Rovio, and related names and marks are the property of their respective rights holders. This repository is an independent preservation, compatibility, and reverse-engineering effort and is **not affiliated with, sponsored by, or endorsed by Rovio Entertainment**.

ChatGPT and OpenAI are trademarks of OpenAI. The ChatGPT credit above describes the development assistance used during this project and does **not** imply OpenAI sponsorship, endorsement, or official maintenance.

## Why the distinction matters

A large amount of engineering went into making this build possible, but that work sits **around and underneath an existing game**. The reconstruction should receive credit for the ARM64 runtime, compatibility work, research, testing, tooling, and documentation without obscuring the authorship of the original game or suggesting ownership of Rovio's creative work.
