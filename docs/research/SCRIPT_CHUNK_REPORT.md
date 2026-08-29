# Angry Birds 1.4.2 script chunk report

All six uploaded files are stripped Lua 5.1 binary chunks with the same ABI:

- signature: `1B 4C 75 61`
- version: `0x51` (Lua 5.1)
- format: `0`
- little endian
- `sizeof(int) = 4`
- serialized `sizeof(size_t) = 4`
- `sizeof(Instruction) = 4`
- `sizeof(lua_Number) = 4`
- floating point (not integral)

They were recursively decoded to **exact EOF** by the Stage 1 decoder.

| file | bytes | prototypes | instructions | constants | strings | max prototype depth |
|---|---:|---:|---:|---:|---:|---:|
| animations.lua | 2,630 | 1 | 403 | 49 | 46 | 0 |
| blocks.lua | 61,604 | 1 | 10,370 | 1,069 | 906 | 0 |
| gamelogic.lua | 416,960 | 255 | 61,656 | 10,000 | 8,670 | 2 |
| loadlist.lua | 3,645 | 1 | 471 | 68 | 68 | 0 |
| particles.lua | 3,719 | 1 | 472 | 129 | 83 | 0 |
| starLimits.lua | 10,439 | 1 | 1,467 | 376 | 247 | 0 |

All debug tables are stripped: no line info, locals, or upvalue names are present.
That explains why decompilers recover useful logic but invent local names.

`gamelogic.lua` is by far the only structurally complex script in this set.
