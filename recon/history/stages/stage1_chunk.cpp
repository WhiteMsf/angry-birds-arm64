#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
#include <filesystem>

namespace fs = std::filesystem;

struct Stats {
    std::uint64_t protos = 0;
    std::uint64_t instructions = 0;
    std::uint64_t constants = 0;
    std::uint64_t strings = 0;
    std::uint64_t stringBytes = 0;
    std::uint64_t lineInfo = 0;
    std::uint64_t locvars = 0;
    std::uint64_t upvalueNames = 0;
    std::uint32_t maxDepth = 0;
};

class Reader {
public:
    explicit Reader(std::vector<std::uint8_t> bytes)
        : data_(std::move(bytes)) {}

    struct Header {
        std::uint8_t version{};
        std::uint8_t format{};
        std::uint8_t endian{};
        std::uint8_t intSize{};
        std::uint8_t sizeTSize{};
        std::uint8_t instructionSize{};
        std::uint8_t numberSize{};
        std::uint8_t integral{};
    };

    Header readHeader() {
        static constexpr std::uint8_t sig[4] = {0x1B, 'L', 'u', 'a'};
        for (std::uint8_t b : sig) {
            if (u8() != b) fail("bad Lua signature");
        }
        Header h;
        h.version = u8();
        h.format = u8();
        h.endian = u8();
        h.intSize = u8();
        h.sizeTSize = u8();
        h.instructionSize = u8();
        h.numberSize = u8();
        h.integral = u8();

        if (h.version != 0x51) fail("not Lua 5.1 bytecode");
        if (h.format != 0) fail("unsupported Lua format");
        if (h.endian != 1) fail("chunk is not little-endian");
        if (h.intSize != 4) fail("expected 32-bit int");
        if (h.sizeTSize != 4) fail("expected serialized 32-bit size_t");
        if (h.instructionSize != 4) fail("expected 32-bit Instruction");
        if (h.numberSize != 4) fail("expected 32-bit lua_Number");
        if (h.integral != 0) fail("expected floating-point lua_Number");
        return h;
    }

    void parsePrototype(Stats& st, std::uint32_t depth = 0) {
        if (depth > 1000) fail("prototype nesting too deep");
        st.protos++;
        if (depth > st.maxDepth) st.maxDepth = depth;

        (void)readString(st); // source name; stripped chunks use null
        (void)i32(); // linedefined
        (void)i32(); // lastlinedefined
        (void)u8();  // nups
        (void)u8();  // numparams
        (void)u8();  // is_vararg
        (void)u8();  // maxstacksize

        const std::int32_t ncode = checkedCount(i32(), "instruction count");
        st.instructions += static_cast<std::uint64_t>(ncode);
        skip(checkedBytes(static_cast<std::uint64_t>(ncode), 4, "code"));

        const std::int32_t nk = checkedCount(i32(), "constant count");
        st.constants += static_cast<std::uint64_t>(nk);
        for (std::int32_t i = 0; i < nk; ++i) {
            const std::uint8_t t = u8();
            switch (t) {
                case 0: // nil
                    break;
                case 1: // bool
                    (void)u8();
                    break;
                case 3: // number: float32 in these chunks
                    skip(4);
                    break;
                case 4: // string
                    (void)readString(st);
                    break;
                default:
                    fail("bad constant type " + std::to_string(t));
            }
        }

        const std::int32_t np = checkedCount(i32(), "child prototype count");
        for (std::int32_t i = 0; i < np; ++i)
            parsePrototype(st, depth + 1);

        const std::int32_t nline = checkedCount(i32(), "lineinfo count");
        st.lineInfo += static_cast<std::uint64_t>(nline);
        skip(checkedBytes(static_cast<std::uint64_t>(nline), 4, "lineinfo"));

        const std::int32_t nloc = checkedCount(i32(), "local variable count");
        st.locvars += static_cast<std::uint64_t>(nloc);
        for (std::int32_t i = 0; i < nloc; ++i) {
            (void)readString(st);
            (void)i32();
            (void)i32();
        }

        const std::int32_t nup = checkedCount(i32(), "upvalue-name count");
        st.upvalueNames += static_cast<std::uint64_t>(nup);
        for (std::int32_t i = 0; i < nup; ++i)
            (void)readString(st);
    }

    bool atEnd() const { return pos_ == data_.size(); }
    std::size_t position() const { return pos_; }
    std::size_t size() const { return data_.size(); }

private:
    std::vector<std::uint8_t> data_;
    std::size_t pos_ = 0;

    [[noreturn]] void fail(const std::string& why) const {
        throw std::runtime_error(why + " at offset " + std::to_string(pos_));
    }

    void require(std::size_t n) const {
        if (n > data_.size() - pos_)
            fail("unexpected end of chunk");
    }

    void skip(std::size_t n) {
        require(n);
        pos_ += n;
    }

    std::uint8_t u8() {
        require(1);
        return data_[pos_++];
    }

    std::uint32_t u32() {
        require(4);
        const std::uint32_t v =
            static_cast<std::uint32_t>(data_[pos_]) |
            (static_cast<std::uint32_t>(data_[pos_ + 1]) << 8) |
            (static_cast<std::uint32_t>(data_[pos_ + 2]) << 16) |
            (static_cast<std::uint32_t>(data_[pos_ + 3]) << 24);
        pos_ += 4;
        return v;
    }

    std::int32_t i32() { return static_cast<std::int32_t>(u32()); }

    static std::int32_t checkedCount(std::int32_t n, const char* what) {
        if (n < 0 || n > 50'000'000)
            throw std::runtime_error(std::string("invalid ") + what);
        return n;
    }

    static std::size_t checkedBytes(std::uint64_t n, std::uint64_t element, const char* what) {
        if (n > std::numeric_limits<std::size_t>::max() / element)
            throw std::runtime_error(std::string("overflow in ") + what);
        return static_cast<std::size_t>(n * element);
    }

    std::string readString(Stats& st) {
        // Angry Birds chunks serialize Lua 5.1 size_t as uint32_t regardless
        // of the ARM64 host's native sizeof(size_t).
        const std::uint32_t n = u32();
        if (n == 0) return {};
        if (n > 256u * 1024u * 1024u) fail("absurd string size");
        require(n);
        const std::size_t payload = (n && data_[pos_ + n - 1] == 0) ? n - 1 : n;
        std::string s(reinterpret_cast<const char*>(&data_[pos_]), payload);
        pos_ += n;
        st.strings++;
        st.stringBytes += payload;
        return s;
    }
};

static std::vector<std::uint8_t> readFile(const fs::path& p) {
    std::ifstream f(p, std::ios::binary);
    if (!f) throw std::runtime_error("cannot open " + p.string());
    f.seekg(0, std::ios::end);
    const std::streamoff sz = f.tellg();
    if (sz < 0) throw std::runtime_error("cannot size " + p.string());
    f.seekg(0, std::ios::beg);
    std::vector<std::uint8_t> b(static_cast<std::size_t>(sz));
    if (!b.empty()) f.read(reinterpret_cast<char*>(b.data()), sz);
    if (!f && !b.empty()) throw std::runtime_error("cannot read " + p.string());
    return b;
}

static int inspect(const fs::path& p) {
    try {
        Reader r(readFile(p));
        const auto h = r.readHeader();
        (void)h;
        Stats st;
        r.parsePrototype(st);
        if (!r.atEnd())
            throw std::runtime_error("trailing data: parser stopped at " +
                                     std::to_string(r.position()) + "/" +
                                     std::to_string(r.size()));

        std::printf(
            "[angry-stage1] %-16s OK  bytes=%zu protos=%llu ins=%llu const=%llu strings=%llu depth=%u\n",
            p.filename().string().c_str(), r.size(),
            static_cast<unsigned long long>(st.protos),
            static_cast<unsigned long long>(st.instructions),
            static_cast<unsigned long long>(st.constants),
            static_cast<unsigned long long>(st.strings),
            st.maxDepth);
        return 0;
    } catch (const std::exception& e) {
        std::printf("[angry-stage1] %-16s FAIL: %s\n",
                    p.filename().string().c_str(), e.what());
        return 1;
    }
}

int main(int argc, char** argv) {
    if (argc != 2) {
        std::fprintf(stderr, "usage: %s <scripts-directory>\n", argv[0]);
        return 64;
    }

    const fs::path dir(argv[1]);
    const char* names[] = {
        "animations.lua",
        "blocks.lua",
        "gamelogic.lua",
        "loadlist.lua",
        "particles.lua",
        "starLimits.lua",
    };

    std::printf("[angry-stage1] native sizeof(size_t)=%zu\n", sizeof(std::size_t));
    std::printf("[angry-stage1] expected chunk: Lua 5.1 / LE / int32 / size_t32 / instruction32 / float32\n");

    int failures = 0;
    for (const char* name : names)
        failures += inspect(dir / name);

    if (failures == 0) {
        std::printf("[angry-stage1] ALL SIX CHUNKS DECODED EXACTLY TO EOF\n");
        std::printf("[angry-stage1] PASS\n");
        return 0;
    }

    std::printf("[angry-stage1] FAIL (%d files)\n", failures);
    return 2;
}
