#include "presentation_geometry.h"

#include <algorithm>
#include <cmath>

namespace angry {
namespace runtime {
namespace presentation {

int effective_logical_extent(
    int surface_extent,
    int fixed_logical_extent) noexcept {

    if (fixed_logical_extent > 0) {
        return fixed_logical_extent;
    }

    return std::max(1, surface_extent);
}

PresentationGeometry resolve_geometry(
    int surface_width,
    int surface_height,
    int fixed_logical_width,
    int fixed_logical_height) noexcept {

    const bool fixed_logical =
        fixed_logical_width > 0 &&
        fixed_logical_height > 0;

    PresentationGeometry geometry{};

    geometry.logical_width = effective_logical_extent(
        surface_width,
        fixed_logical ? fixed_logical_width : 0);

    geometry.logical_height = effective_logical_extent(
        surface_height,
        fixed_logical ? fixed_logical_height : 0);

    if (!fixed_logical) {
        geometry.raster = {
            0,
            0,
            surface_width,
            surface_height,
        };

        geometry.output = geometry.raster;
        return geometry;
    }

    geometry.raster.width =
        std::min(geometry.logical_width, surface_width);
    geometry.raster.height =
        std::min(geometry.logical_height, surface_height);

    geometry.raster.x =
        (surface_width - geometry.raster.width) / 2;
    geometry.raster.y =
        (surface_height - geometry.raster.height) / 2;

    const double present_scale = std::min(
        static_cast<double>(surface_width) /
            static_cast<double>(std::max(1, geometry.logical_width)),
        static_cast<double>(surface_height) /
            static_cast<double>(std::max(1, geometry.logical_height)));

    geometry.output.width = std::max(
        1,
        std::min(
            surface_width,
            static_cast<int>(
                std::lround(geometry.logical_width * present_scale))));

    geometry.output.height = std::max(
        1,
        std::min(
            surface_height,
            static_cast<int>(
                std::lround(geometry.logical_height * present_scale))));

    geometry.output.x =
        (surface_width - geometry.output.width) / 2;
    geometry.output.y =
        (surface_height - geometry.output.height) / 2;

    return geometry;
}

}  // namespace presentation
}  // namespace runtime
}  // namespace angry
