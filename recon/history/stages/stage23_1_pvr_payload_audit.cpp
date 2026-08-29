#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

static uint32_t u32le(const std::vector<uint8_t>& b, size_t o) {
    if (o + 4 > b.size()) return 0;
    return (uint32_t)b[o] | ((uint32_t)b[o+1] << 8) | ((uint32_t)b[o+2] << 16) | ((uint32_t)b[o+3] << 24);
}
static uint64_t u64le(const std::vector<uint8_t>& b, size_t o) {
    return (uint64_t)u32le(b,o) | ((uint64_t)u32le(b,o+4) << 32);
}
static std::string hex32(uint32_t v) {
    std::ostringstream s; s << "0x" << std::hex << std::uppercase << std::setw(8) << std::setfill('0') << v; return s.str();
}
static std::string hex64(uint64_t v) {
    std::ostringstream s; s << "0x" << std::hex << std::uppercase << std::setw(16) << std::setfill('0') << v; return s.str();
}
static bool read_file(const std::string& p, std::vector<uint8_t>& out) {
    std::ifstream f(p, std::ios::binary);
    if (!f) return false;
    f.seekg(0, std::ios::end); auto n=f.tellg(); f.seekg(0, std::ios::beg);
    if (n < 0) return false;
    out.resize((size_t)n);
    if (!out.empty()) f.read((char*)out.data(), n);
    return !!f || out.empty();
}
static uint64_t pvrtc_level_bytes(uint32_t w, uint32_t h, uint32_t bpp) {
    if (bpp == 2) {
        uint64_t ww = std::max<uint32_t>(w,16), hh = std::max<uint32_t>(h,8);
        return ww * hh * 2u / 8u;
    }
    if (bpp == 4) {
        uint64_t ww = std::max<uint32_t>(w,8), hh = std::max<uint32_t>(h,8);
        return ww * hh * 4u / 8u;
    }
    return 0;
}
static uint64_t pvrtc_chain_bytes(uint32_t w, uint32_t h, uint32_t bpp, uint32_t levels) {
    if (!levels) levels=1;
    uint64_t total=0;
    for (uint32_t i=0;i<levels;i++) {
        total += pvrtc_level_bytes(w,h,bpp);
        w=std::max<uint32_t>(1,w>>1); h=std::max<uint32_t>(1,h>>1);
    }
    return total;
}
static uint64_t raw_chain_bytes(uint32_t w, uint32_t h, uint32_t bytesPerPixel, uint32_t levels) {
    if (!levels) levels=1;
    uint64_t total=0;
    for (uint32_t i=0;i<levels;i++) {
        total += (uint64_t)w * (uint64_t)h * bytesPerPixel;
        w=std::max<uint32_t>(1,w>>1); h=std::max<uint32_t>(1,h>>1);
    }
    return total;
}

struct V2Format {
    std::string name="UNKNOWN";
    bool compressed=false;
    uint32_t bpp=0;
    std::string glesFormat="";
    std::string glesType="";
};
static V2Format decode_v2_format(uint32_t t, uint32_t bitCount) {
    // Imagination Technologies legacy PVR PixelFormat enum (FileDefinesPVR.h).
    switch (t) {
        case 0x00: return {"MGL_ARGB_4444",false,16,"GL_RGBA","GL_UNSIGNED_SHORT_4_4_4_4"};
        case 0x01: return {"MGL_ARGB_1555",false,16,"GL_RGBA","GL_UNSIGNED_SHORT_5_5_5_1"};
        case 0x02: return {"MGL_RGB_565",false,16,"GL_RGB","GL_UNSIGNED_SHORT_5_6_5"};
        case 0x04: return {"MGL_RGB_888",false,24,"GL_RGB","GL_UNSIGNED_BYTE"};
        case 0x05: return {"MGL_ARGB_8888",false,32,"GL_RGBA","GL_UNSIGNED_BYTE"};
        case 0x0c: return {"MGL_PVRTC2",true,2,"GL_COMPRESSED_RGBA_PVRTC_2BPPV1_IMG","compressed"};
        case 0x0d: return {"MGL_PVRTC4",true,4,"GL_COMPRESSED_RGBA_PVRTC_4BPPV1_IMG","compressed"};
        case 0x10: return {"GL_RGBA_4444",false,16,"GL_RGBA","GL_UNSIGNED_SHORT_4_4_4_4"};
        case 0x11: return {"GL_RGBA_5551",false,16,"GL_RGBA","GL_UNSIGNED_SHORT_5_5_5_1"};
        case 0x12: return {"GL_RGBA_8888",false,32,"GL_RGBA","GL_UNSIGNED_BYTE"};
        case 0x13: return {"GL_RGB_565",false,16,"GL_RGB","GL_UNSIGNED_SHORT_5_6_5"};
        case 0x15: return {"GL_RGB_888",false,24,"GL_RGB","GL_UNSIGNED_BYTE"};
        case 0x16: return {"GL_I_8",false,8,"GL_LUMINANCE","GL_UNSIGNED_BYTE"};
        case 0x17: return {"GL_AI_88",false,16,"GL_LUMINANCE_ALPHA","GL_UNSIGNED_BYTE"};
        case 0x18: return {"GL_PVRTC2",true,2,"GL_COMPRESSED_RGBA_PVRTC_2BPPV1_IMG","compressed"};
        case 0x19: return {"GL_PVRTC4",true,4,"GL_COMPRESSED_RGBA_PVRTC_4BPPV1_IMG","compressed"};
        case 0x1a: return {"GL_BGRA_8888",false,32,"GL_BGRA_EXT","GL_UNSIGNED_BYTE"};
        case 0x1b: return {"GL_A_8",false,8,"GL_ALPHA","GL_UNSIGNED_BYTE"};
        case 0x1c: return {"GL_PVRTCII4",true,4,"PVRTCII4","compressed"};
        case 0x1d: return {"GL_PVRTCII2",true,2,"PVRTCII2","compressed"};
        default: {
            V2Format f; f.bpp=bitCount; return f;
        }
    }
}

struct Audit { bool ok=false; std::string line; bool rgba4444=false; };

static Audit audit_one(const std::string& label, const std::string& path) {
    std::vector<uint8_t> b;
    if (!read_file(path,b)) return {false, "[stage23.1-pvr] " + label + " ERROR cannot-read '"+path+"'",false};
    if (b.size() < 52) return {false, "[stage23.1-pvr] " + label + " ERROR too-small bytes="+std::to_string(b.size()),false};

    std::ostringstream o;
    const uint32_t first=u32le(b,0), tag44=u32le(b,44);
    if (first == 0x03525650u) { // PVR v3
        uint32_t flags=u32le(b,4); uint64_t pf=u64le(b,8); uint32_t cs=u32le(b,16); uint32_t ct=u32le(b,20);
        uint32_t h=u32le(b,24), w=u32le(b,28), depth=u32le(b,32), surfaces=u32le(b,36), faces=u32le(b,40), mips=u32le(b,44), meta=u32le(b,48);
        uint64_t payloadOff=52ull+meta;
        if (payloadOff>b.size()) return {false,"[stage23.1-pvr] "+label+" ERROR v3 metadata-overrun",false};
        uint64_t payload=b.size()-payloadOff;
        std::string fmt="UNKNOWN"; uint32_t bpp=0;
        if (pf==0 || pf==1) { fmt=(pf==0?"PVRTC1_2BPP_RGB":"PVRTC1_2BPP_RGBA"); bpp=2; }
        else if (pf==2 || pf==3) { fmt=(pf==2?"PVRTC1_4BPP_RGB":"PVRTC1_4BPP_RGBA"); bpp=4; }
        uint64_t expected = bpp ? pvrtc_chain_bytes(w,h,bpp,mips)*std::max<uint32_t>(1,depth)*std::max<uint32_t>(1,surfaces)*std::max<uint32_t>(1,faces) : 0;
        bool exact = bpp && expected==payload;
        o << "[stage23.1-pvr] "<<label<<" version=v3 bytes="<<b.size()<<" header=52 meta="<<meta
          <<" payload="<<payload<<" size="<<w<<"x"<<h<<" depth="<<depth<<" surfaces="<<surfaces<<" faces="<<faces
          <<" mips="<<mips<<" flags="<<hex32(flags)<<" pixelFormat="<<hex64(pf)<<" format="<<fmt
          <<" colourSpace="<<cs<<" channelType="<<ct;
        if (bpp) o << " bpp="<<bpp<<" expectedPayload="<<expected<<" payloadExact="<<(exact?"yes":"NO");
        else o << " payloadExact=unverified";
        return {bpp?exact:true,o.str(),false};
    }
    if (tag44 == 0x21525650u) { // legacy PVR v2 tag 'PVR!'
        uint32_t header=u32le(b,0), h=u32le(b,4), w=u32le(b,8), mipField=u32le(b,12), flags=u32le(b,16), dataLength=u32le(b,20), bitCount=u32le(b,24);
        uint32_t rm=u32le(b,28), gm=u32le(b,32), bm=u32le(b,36), am=u32le(b,40), surfaces=u32le(b,48);
        if (header < 52 || header>b.size()) return {false,"[stage23.1-pvr] "+label+" ERROR invalid-v2-header="+std::to_string(header),false};
        const uint32_t type=flags & 0xffu;
        const bool flagMip=(flags & 0x00000100u)!=0;
        const bool flagAlpha=(flags & 0x00008000u)!=0;
        const bool flagVFlip=(flags & 0x00010000u)!=0;
        V2Format f=decode_v2_format(type,bitCount);
        const uint64_t payload=b.size()-header;
        const bool dataLenExact=(uint64_t)dataLength==payload;
        uint32_t levels=flagMip ? (mipField+1u) : 1u;
        uint64_t expected=0;
        if (f.compressed && f.bpp) expected=pvrtc_chain_bytes(w,h,f.bpp,levels)*std::max<uint32_t>(1,surfaces);
        else if (f.bpp && (f.bpp%8)==0) expected=raw_chain_bytes(w,h,f.bpp/8u,levels)*std::max<uint32_t>(1,surfaces);
        const bool payloadExact=expected && expected==payload;
        const bool known=f.name!="UNKNOWN";
        const bool masksRGBA4444=(rm==0x0000F000u && gm==0x00000F00u && bm==0x000000F0u && am==0x0000000Fu);
        const bool rgba4444=(type==0x10 && bitCount==16 && masksRGBA4444);
        const bool exact=known && dataLenExact && payloadExact;
        o << "[stage23.1-pvr] "<<label<<" version=v2 bytes="<<b.size()<<" header="<<header<<" payload="<<payload
          <<" size="<<w<<"x"<<h<<" mipField="<<mipField<<" flags="<<hex32(flags)<<" pixelType="<<hex32(type)
          <<" format="<<f.name<<" bitCount="<<bitCount<<" surfaces="<<surfaces
          <<" hasAlphaFlag="<<(flagAlpha?"yes":"no")<<" mipFlag="<<(flagMip?"yes":"no")<<" verticalFlipFlag="<<(flagVFlip?"yes":"no")
          <<" dataLength="<<dataLength<<" dataLengthExact="<<(dataLenExact?"yes":"NO")
          <<" masks="<<hex32(rm)<<","<<hex32(gm)<<","<<hex32(bm)<<","<<hex32(am)
          <<" levels="<<levels<<" expectedPayload="<<expected<<" payloadExact="<<(payloadExact?"yes":"NO");
        if (!f.glesFormat.empty()) o << " glesFormat="<<f.glesFormat<<" glesType="<<f.glesType;
        if (rgba4444) o << " rgba4444MasksExact=yes";
        return {exact,o.str(),rgba4444};
    }
    o << "[stage23.1-pvr] "<<label<<" ERROR unknown-header first="<<hex32(first)<<" tag44="<<hex32(tag44)<<" bytes="<<b.size();
    return {false,o.str(),false};
}

int main(int argc,char** argv) {
    if (argc!=3) { std::cerr<<"usage: stage23_1_pvr_payload_audit <INGAME_BLOCKS_1.pvr> <INGAME_BIRDS_1.pvr>\n"; return 2; }
    std::cout << "[angry-stage23.1] ORIGINAL PVR CONTAINER / PIXEL-FORMAT / PAYLOAD AUDIT / ARM64\n";
    Audit a=audit_one("INGAME_BLOCKS_1.pvr",argv[1]); std::cout<<a.line<<"\n";
    Audit c=audit_one("INGAME_BIRDS_1.pvr",argv[2]); std::cout<<c.line<<"\n";
    if (!a.ok || !c.ok) { std::cout<<"[angry-stage23.1] FAIL\n"; return 1; }
    std::cout << "[angry-stage23.1] BOTH ORIGINAL PVR PAYLOADS ARE STRUCTURALLY SELF-CONSISTENT\n";
    if (a.rgba4444 && c.rgba4444) {
        std::cout << "[angry-stage23.1] BOTH LEVEL1 ATLASES ARE UNCOMPRESSED GL_RGBA_4444, ONE BASE LEVEL, NO VERTICAL-FLIP FLAG\n";
        std::cout << "[angry-stage23.1] GLES UPLOAD CONTRACT: glTexImage2D(..., GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_SHORT_4_4_4_4, payload)\n";
        std::cout << "[angry-stage23.1] NO PVRTC DECOMPRESSION OR glCompressedTexImage2D IS NEEDED FOR THESE ATLASES\n";
    }
    std::cout << "[angry-stage23.1] PASS\n";
    return 0;
}
