#include <EGL/egl.h>
#include <GLES/gl.h>

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

constexpr int kRectX = 182;
constexpr int kRectY = 463;
constexpr int kRectW = 46;
constexpr int kRectH = 45;
constexpr int kZoom = 8;

struct PvrV2 {
    uint32_t headerLength = 0;
    uint32_t height = 0;
    uint32_t width = 0;
    uint32_t mipMapCount = 0;
    uint32_t flags = 0;
    uint32_t dataLength = 0;
    uint32_t bitCount = 0;
    uint32_t redMask = 0;
    uint32_t greenMask = 0;
    uint32_t blueMask = 0;
    uint32_t alphaMask = 0;
    uint32_t pvrTag = 0;
    uint32_t numSurfaces = 0;
};

uint32_t readLe32(const uint8_t* p) {
    return static_cast<uint32_t>(p[0]) |
           (static_cast<uint32_t>(p[1]) << 8u) |
           (static_cast<uint32_t>(p[2]) << 16u) |
           (static_cast<uint32_t>(p[3]) << 24u);
}

bool readFile(const std::string& path, std::vector<uint8_t>& out) {
    std::ifstream f(path, std::ios::binary);
    if (!f) return false;
    f.seekg(0, std::ios::end);
    const std::streamoff size = f.tellg();
    if (size < 0) return false;
    f.seekg(0, std::ios::beg);
    out.resize(static_cast<size_t>(size));
    if (!out.empty()) f.read(reinterpret_cast<char*>(out.data()), size);
    return f.good() || f.eof();
}

bool parsePvrV2(const std::vector<uint8_t>& bytes, PvrV2& h, std::string& error) {
    if (bytes.size() < 52) {
        error = "file smaller than 52-byte PVR v2 header";
        return false;
    }
    h.headerLength = readLe32(bytes.data() + 0);
    h.height       = readLe32(bytes.data() + 4);
    h.width        = readLe32(bytes.data() + 8);
    h.mipMapCount  = readLe32(bytes.data() + 12);
    h.flags        = readLe32(bytes.data() + 16);
    h.dataLength   = readLe32(bytes.data() + 20);
    h.bitCount     = readLe32(bytes.data() + 24);
    h.redMask      = readLe32(bytes.data() + 28);
    h.greenMask    = readLe32(bytes.data() + 32);
    h.blueMask     = readLe32(bytes.data() + 36);
    h.alphaMask    = readLe32(bytes.data() + 40);
    h.pvrTag       = readLe32(bytes.data() + 44);
    h.numSurfaces  = readLe32(bytes.data() + 48);

    if (h.headerLength != 52) {
        std::ostringstream oss;
        oss << "unexpected headerLength=" << h.headerLength;
        error = oss.str();
        return false;
    }
    if (h.pvrTag != 0x21525650u) { // 'PVR!'
        std::ostringstream oss;
        oss << "unexpected PVR tag 0x" << std::hex << h.pvrTag;
        error = oss.str();
        return false;
    }
    if ((h.flags & 0xffu) != 0x10u || h.bitCount != 16u ||
        h.redMask != 0x0000f000u || h.greenMask != 0x00000f00u ||
        h.blueMask != 0x000000f0u || h.alphaMask != 0x0000000fu) {
        error = "PVR is not the proven Angry Birds GL_RGBA_4444 layout";
        return false;
    }
    const uint64_t expected = static_cast<uint64_t>(h.width) * h.height * 2ull;
    if (expected != h.dataLength || bytes.size() != h.headerLength + h.dataLength) {
        std::ostringstream oss;
        oss << "payload size mismatch expected=" << expected
            << " dataLength=" << h.dataLength << " file=" << bytes.size();
        error = oss.str();
        return false;
    }
    if (kRectX < 0 || kRectY < 0 ||
        kRectX + kRectW > static_cast<int>(h.width) ||
        kRectY + kRectH > static_cast<int>(h.height)) {
        error = "BIRD_RED rect is outside texture bounds";
        return false;
    }
    return true;
}

std::string eglErrorHex() {
    std::ostringstream oss;
    oss << "0x" << std::hex << std::uppercase << eglGetError();
    return oss.str();
}

std::string glErrorHex(GLenum e) {
    std::ostringstream oss;
    oss << "0x" << std::hex << std::uppercase << e;
    return oss.str();
}

const char* safeGlString(GLenum name) {
    const GLubyte* s = glGetString(name);
    return s ? reinterpret_cast<const char*>(s) : "";
}

uint8_t expand4(uint16_t nibble) {
    return static_cast<uint8_t>((nibble & 0x0fu) * 17u);
}

void decodeExpectedCrop(const std::vector<uint8_t>& bytes,
                        const PvrV2& h,
                        std::vector<uint8_t>& rgbaTopDown) {
    rgbaTopDown.resize(static_cast<size_t>(kRectW) * kRectH * 4u);
    const uint8_t* payload = bytes.data() + h.headerLength;
    for (int y = 0; y < kRectH; ++y) {
        for (int x = 0; x < kRectW; ++x) {
            const uint64_t pixelIndex = static_cast<uint64_t>(kRectY + y) * h.width + (kRectX + x);
            const uint8_t* p = payload + pixelIndex * 2ull;
            const uint16_t v = static_cast<uint16_t>(p[0]) |
                               static_cast<uint16_t>(static_cast<uint16_t>(p[1]) << 8u);
            const size_t o = (static_cast<size_t>(y) * kRectW + x) * 4u;
            rgbaTopDown[o + 0] = expand4(v >> 12u);
            rgbaTopDown[o + 1] = expand4(v >> 8u);
            rgbaTopDown[o + 2] = expand4(v >> 4u);
            rgbaTopDown[o + 3] = expand4(v);
        }
    }
}

bool writeBmp24(const std::string& path,
                const std::vector<uint8_t>& rgbaTopDown,
                int width,
                int height,
                int zoom) {
    const int outW = width * zoom;
    const int outH = height * zoom;
    const uint32_t rowStride = static_cast<uint32_t>((outW * 3 + 3) & ~3);
    const uint32_t pixelBytes = rowStride * static_cast<uint32_t>(outH);
    const uint32_t fileBytes = 54u + pixelBytes;

    std::ofstream f(path, std::ios::binary);
    if (!f) return false;

    auto put16 = [&](uint16_t v) {
        const char b[2] = {static_cast<char>(v & 0xffu), static_cast<char>((v >> 8u) & 0xffu)};
        f.write(b, 2);
    };
    auto put32 = [&](uint32_t v) {
        const char b[4] = {
            static_cast<char>(v & 0xffu),
            static_cast<char>((v >> 8u) & 0xffu),
            static_cast<char>((v >> 16u) & 0xffu),
            static_cast<char>((v >> 24u) & 0xffu)};
        f.write(b, 4);
    };

    f.put('B'); f.put('M');
    put32(fileBytes);
    put16(0); put16(0);
    put32(54);
    put32(40);
    put32(static_cast<uint32_t>(outW));
    put32(static_cast<uint32_t>(outH)); // positive: BMP rows stored bottom-up
    put16(1);
    put16(24);
    put32(0);
    put32(pixelBytes);
    put32(2835); put32(2835);
    put32(0); put32(0);

    std::vector<uint8_t> row(rowStride, 0);
    for (int outYBottom = 0; outYBottom < outH; ++outYBottom) {
        const int outYTop = outH - 1 - outYBottom;
        const int srcY = outYTop / zoom;
        std::fill(row.begin(), row.end(), 0);
        for (int outX = 0; outX < outW; ++outX) {
            const int srcX = outX / zoom;
            const size_t s = (static_cast<size_t>(srcY) * width + srcX) * 4u;
            const uint8_t sr = rgbaTopDown[s + 0];
            const uint8_t sg = rgbaTopDown[s + 1];
            const uint8_t sb = rgbaTopDown[s + 2];
            const uint8_t sa = rgbaTopDown[s + 3];

            // Composite the GPU-read sprite on the same sky-blue family used by
            // the Stage 23.2 debug replay so transparent edges are easy to see.
            constexpr uint8_t br = 158, bg = 220, bb = 247;
            const uint32_t a = sa;
            const uint8_t r = static_cast<uint8_t>((sr * a + br * (255u - a) + 127u) / 255u);
            const uint8_t g = static_cast<uint8_t>((sg * a + bg * (255u - a) + 127u) / 255u);
            const uint8_t b = static_cast<uint8_t>((sb * a + bb * (255u - a) + 127u) / 255u);
            const size_t d = static_cast<size_t>(outX) * 3u;
            row[d + 0] = b;
            row[d + 1] = g;
            row[d + 2] = r;
        }
        f.write(reinterpret_cast<const char*>(row.data()), static_cast<std::streamsize>(row.size()));
    }
    return static_cast<bool>(f);
}

} // namespace

int main(int argc, char** argv) {
    if (argc != 4) {
        std::cerr << "usage: stage23_3_gles1_pbuffer_sprite <INGAME_BIRDS_1.pvr> <report.txt> <gpu-bird-red.bmp>\n";
        return 2;
    }

    const std::string pvrPath = argv[1];
    const std::string reportPath = argv[2];
    const std::string bmpPath = argv[3];

    std::cout << "[angry-stage23.3] ORIGINAL GLES1 FIXED-FUNCTION / EGL PBUFFER / BIRD_RED / ARM64\n";

    std::vector<uint8_t> pvrBytes;
    if (!readFile(pvrPath, pvrBytes)) {
        std::cerr << "[stage23.3] could not read PVR: " << pvrPath << "\n";
        return 3;
    }

    PvrV2 pvr;
    std::string parseError;
    if (!parsePvrV2(pvrBytes, pvr, parseError)) {
        std::cerr << "[stage23.3] PVR validation failed: " << parseError << "\n";
        return 4;
    }

    std::vector<uint8_t> expected;
    decodeExpectedCrop(pvrBytes, pvr, expected);

    EGLDisplay display = eglGetDisplay(EGL_DEFAULT_DISPLAY);
    if (display == EGL_NO_DISPLAY) {
        std::cerr << "[stage23.3-egl] eglGetDisplay failed error=" << eglErrorHex() << "\n";
        return 5;
    }
    EGLint eglMajor = 0, eglMinor = 0;
    if (!eglInitialize(display, &eglMajor, &eglMinor)) {
        std::cerr << "[stage23.3-egl] eglInitialize failed error=" << eglErrorHex() << "\n";
        return 6;
    }
    if (!eglBindAPI(EGL_OPENGL_ES_API)) {
        std::cerr << "[stage23.3-egl] eglBindAPI failed error=" << eglErrorHex() << "\n";
        eglTerminate(display);
        return 7;
    }

    const EGLint configAttrs[] = {
        EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES_BIT,
        EGL_RED_SIZE, 8,
        EGL_GREEN_SIZE, 8,
        EGL_BLUE_SIZE, 8,
        EGL_ALPHA_SIZE, 8,
        EGL_NONE
    };
    EGLConfig config = nullptr;
    EGLint configCount = 0;
    if (!eglChooseConfig(display, configAttrs, &config, 1, &configCount) || configCount < 1) {
        std::cerr << "[stage23.3-egl] eglChooseConfig failed error=" << eglErrorHex() << " count=" << configCount << "\n";
        eglTerminate(display);
        return 8;
    }

    const EGLint surfaceAttrs[] = {EGL_WIDTH, kRectW, EGL_HEIGHT, kRectH, EGL_NONE};
    EGLSurface surface = eglCreatePbufferSurface(display, config, surfaceAttrs);
    if (surface == EGL_NO_SURFACE) {
        std::cerr << "[stage23.3-egl] eglCreatePbufferSurface failed error=" << eglErrorHex() << "\n";
        eglTerminate(display);
        return 9;
    }

    const EGLint contextAttrs[] = {EGL_CONTEXT_CLIENT_VERSION, 1, EGL_NONE};
    EGLContext context = eglCreateContext(display, config, EGL_NO_CONTEXT, contextAttrs);
    if (context == EGL_NO_CONTEXT) {
        std::cerr << "[stage23.3-egl] eglCreateContext(ES1) failed error=" << eglErrorHex() << "\n";
        eglDestroySurface(display, surface);
        eglTerminate(display);
        return 10;
    }

    if (!eglMakeCurrent(display, surface, surface, context)) {
        std::cerr << "[stage23.3-egl] eglMakeCurrent failed error=" << eglErrorHex() << "\n";
        eglDestroyContext(display, context);
        eglDestroySurface(display, surface);
        eglTerminate(display);
        return 11;
    }

    const std::string eglVendor = eglQueryString(display, EGL_VENDOR) ? eglQueryString(display, EGL_VENDOR) : "";
    const std::string eglVersion = eglQueryString(display, EGL_VERSION) ? eglQueryString(display, EGL_VERSION) : "";
    const std::string glVendor = safeGlString(GL_VENDOR);
    const std::string glRenderer = safeGlString(GL_RENDERER);
    const std::string glVersion = safeGlString(GL_VERSION);
    const std::string glExtensions = safeGlString(GL_EXTENSIONS);
    const bool npot = glExtensions.find("GL_OES_texture_npot") != std::string::npos;
    GLint maxTextureSize = 0;
    glGetIntegerv(GL_MAX_TEXTURE_SIZE, &maxTextureSize);

    std::cout << "[stage23.3-egl] EGL " << eglMajor << "." << eglMinor
              << " vendor='" << eglVendor << "' version='" << eglVersion << "'\n";
    std::cout << "[stage23.3-gl] vendor='" << glVendor << "' renderer='" << glRenderer
              << "' version='" << glVersion << "' maxTextureSize=" << maxTextureSize
              << " GL_OES_texture_npot=" << (npot ? "yes" : "no") << "\n";

    if (maxTextureSize < static_cast<GLint>(std::max(pvr.width, pvr.height))) {
        std::cerr << "[stage23.3-gl] atlas exceeds GL_MAX_TEXTURE_SIZE\n";
        return 12;
    }
    if ((pvr.width & (pvr.width - 1u)) != 0u || (pvr.height & (pvr.height - 1u)) != 0u) {
        if (!npot) {
            std::cerr << "[stage23.3-gl] original atlas is NPOT but GL_OES_texture_npot is missing\n";
            return 13;
        }
    }

    glDisable(GL_DITHER);
    glDisable(GL_BLEND);
    glDisable(GL_DEPTH_TEST);
    glDisable(GL_CULL_FACE);
    glDisable(GL_LIGHTING);
    glDisable(GL_FOG);
    glEnable(GL_TEXTURE_2D);
    glPixelStorei(GL_UNPACK_ALIGNMENT, 2); // 1015 * 2 = 2030 bytes: default alignment 4 is invalid for this payload.

    GLint unpackAlignment = 0;
    glGetIntegerv(GL_UNPACK_ALIGNMENT, &unpackAlignment);

    GLuint texture = 0;
    glGenTextures(1, &texture);
    glBindTexture(GL_TEXTURE_2D, texture);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE);

    const uint8_t* payload = pvrBytes.data() + pvr.headerLength;
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA,
                 static_cast<GLsizei>(pvr.width), static_cast<GLsizei>(pvr.height), 0,
                 GL_RGBA, GL_UNSIGNED_SHORT_4_4_4_4, payload);
    const GLenum uploadError = glGetError();
    std::cout << "[stage23.3-upload] texture=" << pvr.width << "x" << pvr.height
              << " format=GL_RGBA type=GL_UNSIGNED_SHORT_4_4_4_4 unpackAlignment=" << unpackAlignment
              << " glError=" << glErrorHex(uploadError) << "\n";
    if (uploadError != GL_NO_ERROR) return 14;

    glViewport(0, 0, kRectW, kRectH);
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    glOrthof(0.0f, static_cast<GLfloat>(kRectW),
             static_cast<GLfloat>(kRectH), 0.0f,
             -1.0f, 1.0f);
    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();

    glClearColor(0.f, 0.f, 0.f, 0.f);
    glClear(GL_COLOR_BUFFER_BIT);

    const GLfloat verts[] = {
        0.0f, 0.0f,
        static_cast<GLfloat>(kRectW), 0.0f,
        0.0f, static_cast<GLfloat>(kRectH),
        static_cast<GLfloat>(kRectW), static_cast<GLfloat>(kRectH)
    };
    const GLfloat u0 = static_cast<GLfloat>(kRectX) / static_cast<GLfloat>(pvr.width);
    const GLfloat v0 = static_cast<GLfloat>(kRectY) / static_cast<GLfloat>(pvr.height);
    const GLfloat u1 = static_cast<GLfloat>(kRectX + kRectW) / static_cast<GLfloat>(pvr.width);
    const GLfloat v1 = static_cast<GLfloat>(kRectY + kRectH) / static_cast<GLfloat>(pvr.height);
    const GLfloat uv[] = {
        u0, v0,
        u1, v0,
        u0, v1,
        u1, v1
    };

    glEnableClientState(GL_VERTEX_ARRAY);
    glEnableClientState(GL_TEXTURE_COORD_ARRAY);
    glDisableClientState(GL_COLOR_ARRAY);
    glVertexPointer(2, GL_FLOAT, 0, verts);
    glTexCoordPointer(2, GL_FLOAT, 0, uv);
    glDrawArrays(GL_TRIANGLE_STRIP, 0, 4);
    glFinish();
    const GLenum drawError = glGetError();
    if (drawError != GL_NO_ERROR) {
        std::cerr << "[stage23.3-draw] glError=" << glErrorHex(drawError) << "\n";
        return 15;
    }

    std::vector<uint8_t> gpuBottomUp(static_cast<size_t>(kRectW) * kRectH * 4u);
    glReadPixels(0, 0, kRectW, kRectH, GL_RGBA, GL_UNSIGNED_BYTE, gpuBottomUp.data());
    const GLenum readError = glGetError();
    if (readError != GL_NO_ERROR) {
        std::cerr << "[stage23.3-readback] glError=" << glErrorHex(readError) << "\n";
        return 16;
    }

    std::vector<uint8_t> gpuTopDown(gpuBottomUp.size());
    for (int y = 0; y < kRectH; ++y) {
        const size_t src = static_cast<size_t>(kRectH - 1 - y) * kRectW * 4u;
        const size_t dst = static_cast<size_t>(y) * kRectW * 4u;
        std::memcpy(gpuTopDown.data() + dst, gpuBottomUp.data() + src, static_cast<size_t>(kRectW) * 4u);
    }

    size_t mismatchPixels = 0;
    int maxChannelError = 0;
    uint64_t totalAbsError = 0;
    size_t nonzeroAlphaExpected = 0;
    size_t nonzeroAlphaGpu = 0;
    for (int y = 0; y < kRectH; ++y) {
        for (int x = 0; x < kRectW; ++x) {
            const size_t o = (static_cast<size_t>(y) * kRectW + x) * 4u;
            if (expected[o + 3] != 0) ++nonzeroAlphaExpected;
            if (gpuTopDown[o + 3] != 0) ++nonzeroAlphaGpu;
            int pixelMax = 0;
            for (int c = 0; c < 4; ++c) {
                const int d = std::abs(static_cast<int>(expected[o + c]) - static_cast<int>(gpuTopDown[o + c]));
                pixelMax = std::max(pixelMax, d);
                maxChannelError = std::max(maxChannelError, d);
                totalAbsError += static_cast<uint64_t>(d);
            }
            if (pixelMax > 1) ++mismatchPixels;
        }
    }

    std::cout << "[stage23.3-readback] BIRD_RED rect=(" << kRectX << "," << kRectY
              << " " << kRectW << "x" << kRectH << ") directY=yes"
              << " expectedAlphaPixels=" << nonzeroAlphaExpected
              << " gpuAlphaPixels=" << nonzeroAlphaGpu
              << " mismatchPixels(gt1)=" << mismatchPixels
              << " maxChannelError=" << maxChannelError
              << " totalAbsError=" << totalAbsError << "\n";

    const bool pixelsMatch = mismatchPixels == 0 && maxChannelError <= 1;
    if (!writeBmp24(bmpPath, gpuTopDown, kRectW, kRectH, kZoom)) {
        std::cerr << "[stage23.3] failed writing BMP: " << bmpPath << "\n";
        return 17;
    }

    std::ofstream report(reportPath);
    if (!report) {
        std::cerr << "[stage23.3] failed writing report: " << reportPath << "\n";
        return 18;
    }
    report << "ANGRY_STAGE23_3_GLES1_PBUFFER_AUDIT 1\n";
    report << "egl.major=" << eglMajor << "\n";
    report << "egl.minor=" << eglMinor << "\n";
    report << "egl.vendor=" << eglVendor << "\n";
    report << "egl.version=" << eglVersion << "\n";
    report << "gl.vendor=" << glVendor << "\n";
    report << "gl.renderer=" << glRenderer << "\n";
    report << "gl.version=" << glVersion << "\n";
    report << "gl.maxTextureSize=" << maxTextureSize << "\n";
    report << "gl.OES_texture_npot=" << (npot ? "yes" : "no") << "\n";
    report << "texture.width=" << pvr.width << "\n";
    report << "texture.height=" << pvr.height << "\n";
    report << "texture.format=GL_RGBA\n";
    report << "texture.type=GL_UNSIGNED_SHORT_4_4_4_4\n";
    report << "texture.unpackAlignment=" << unpackAlignment << "\n";
    report << "sprite.name=BIRD_RED\n";
    report << "sprite.rect=182,463,46,45\n";
    report << "sprite.pivot=27,27\n";
    report << "sprite.rectYInterpretation=direct-pvr-row-coordinate\n";
    report << "gpu.mismatchPixelsGt1=" << mismatchPixels << "\n";
    report << "gpu.maxChannelError=" << maxChannelError << "\n";
    report << "gpu.totalAbsError=" << totalAbsError << "\n";
    report << "gpu.expectedAlphaPixels=" << nonzeroAlphaExpected << "\n";
    report << "gpu.readbackAlphaPixels=" << nonzeroAlphaGpu << "\n";
    report << "gpu.byteFaithfulWithin1=" << (pixelsMatch ? "yes" : "no") << "\n";
    report.close();

    glDeleteTextures(1, &texture);
    eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
    eglDestroyContext(display, context);
    eglDestroySurface(display, surface);
    eglTerminate(display);

    if (!pixelsMatch) {
        std::cerr << "[angry-stage23.3] FAIL: GLES1 readback differs from original RGBA4444 BIRD_RED crop\n";
        return 19;
    }

    std::cout << "[angry-stage23.3] EGL + libGLESv1_CM CONTEXT CREATED NATIVELY ON ARM64\n";
    std::cout << "[angry-stage23.3] ORIGINAL INGAME_BIRDS_1 RGBA4444 BYTES UPLOADED WITHOUT TRANSCODING\n";
    std::cout << "[angry-stage23.3] ORIGINAL BIRD_RED SPRT RECT RENDERED THROUGH GLES1 FIXED-FUNCTION VERTEX/TEXCOORD ARRAYS\n";
    std::cout << "[angry-stage23.3] GPU READBACK MATCHES THE ORIGINAL SOURCE CROP WITH <=1 CHANNEL ERROR\n";
    std::cout << "[angry-stage23.3] PASS\n";
    return 0;
}
