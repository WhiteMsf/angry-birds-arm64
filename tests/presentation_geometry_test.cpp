#include "presentation_geometry.h"

#include <cstdlib>
#include <iostream>
#include <string>

using angry::runtime::presentation::PresentationGeometry;
using angry::runtime::presentation::Viewport;
using angry::runtime::presentation::resolve_geometry;

static void fail(
    const char* test,
    const std::string& field,
    int expected,
    int actual) {

    std::cerr
        << "[FAIL] " << test
        << " field=" << field
        << " expected=" << expected
        << " actual=" << actual
        << "\n";

    std::exit(1);
}

static void expect_int(
    const char* test,
    const std::string& field,
    int expected,
    int actual) {

    if (expected != actual) {
        fail(test, field, expected, actual);
    }
}

static void expect_viewport(
    const char* test,
    const char* prefix,
    const Viewport& actual,
    int x,
    int y,
    int width,
    int height) {

    const std::string p(prefix);

    expect_int(test, p + ".x", x, actual.x);
    expect_int(test, p + ".y", y, actual.y);
    expect_int(test, p + ".width", width, actual.width);
    expect_int(test, p + ".height", height, actual.height);
}

static void test_native_1920x1080() {
    const char* name = "native_1920x1080";

    const PresentationGeometry g =
        resolve_geometry(1920, 1080, 0, 0);

    expect_int(name, "logical_width", 1920, g.logical_width);
    expect_int(name, "logical_height", 1080, g.logical_height);

    expect_viewport(name, "raster", g.raster, 0, 0, 1920, 1080);
    expect_viewport(name, "output", g.output, 0, 0, 1920, 1080);
}

static void test_exact_legacy_surface() {
    const char* name = "exact_legacy_surface";

    const PresentationGeometry g =
        resolve_geometry(854, 480, 854, 480);

    expect_int(name, "logical_width", 854, g.logical_width);
    expect_int(name, "logical_height", 480, g.logical_height);

    expect_viewport(name, "raster", g.raster, 0, 0, 854, 480);
    expect_viewport(name, "output", g.output, 0, 0, 854, 480);
}

static void test_wvga_on_1920x1080() {
    const char* name = "wvga_on_1920x1080";

    const PresentationGeometry g =
        resolve_geometry(1920, 1080, 854, 480);

    expect_int(name, "logical_width", 854, g.logical_width);
    expect_int(name, "logical_height", 480, g.logical_height);

    expect_viewport(name, "raster", g.raster, 533, 300, 854, 480);

    // Width is the limiting dimension:
    // 1920 / 854 gives an output height of ~1079.157 -> lround = 1079.
    expect_viewport(name, "output", g.output, 0, 0, 1920, 1079);
}

static void test_wvga_on_2400x1080() {
    const char* name = "wvga_on_2400x1080";

    const PresentationGeometry g =
        resolve_geometry(2400, 1080, 854, 480);

    expect_int(name, "logical_width", 854, g.logical_width);
    expect_int(name, "logical_height", 480, g.logical_height);

    expect_viewport(name, "raster", g.raster, 773, 300, 854, 480);

    // Height is the limiting dimension:
    // 854 * 2.25 = 1921.5 -> std::lround = 1922.
    expect_viewport(name, "output", g.output, 239, 0, 1922, 1080);
}

static void test_surface_smaller_than_legacy_raster() {
    const char* name = "surface_smaller_than_legacy_raster";

    const PresentationGeometry g =
        resolve_geometry(640, 360, 854, 480);

    expect_int(name, "logical_width", 854, g.logical_width);
    expect_int(name, "logical_height", 480, g.logical_height);

    expect_viewport(name, "raster", g.raster, 0, 0, 640, 360);
    expect_viewport(name, "output", g.output, 0, 0, 640, 360);
}

static void test_partial_fixed_dimensions_fall_back_to_native() {
    const char* name = "partial_fixed_dimensions_fall_back_to_native";

    const PresentationGeometry g =
        resolve_geometry(1280, 720, 854, 0);

    expect_int(name, "logical_width", 1280, g.logical_width);
    expect_int(name, "logical_height", 720, g.logical_height);

    expect_viewport(name, "raster", g.raster, 0, 0, 1280, 720);
    expect_viewport(name, "output", g.output, 0, 0, 1280, 720);
}

int main() {
    test_native_1920x1080();
    test_exact_legacy_surface();
    test_wvga_on_1920x1080();
    test_wvga_on_2400x1080();
    test_surface_smaller_than_legacy_raster();
    test_partial_fixed_dimensions_fall_back_to_native();

    std::cout << "[PASS] presentation geometry contract tests\n";
    return 0;
}
