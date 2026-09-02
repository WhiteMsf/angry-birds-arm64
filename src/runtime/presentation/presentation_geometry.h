#pragma once

namespace angry {
namespace runtime {
namespace presentation {

struct Viewport {
    int x;
    int y;
    int width;
    int height;
};

struct PresentationGeometry {
    int logical_width;
    int logical_height;

    // Raster region used by the reconstructed legacy renderer.
    Viewport raster;

    // Final aspect-fit viewport used to present the composited frame.
    Viewport output;
};

// Resolve one logical presentation extent.
//
// fixed_logical_extent > 0 selects the recovered fixed logical raster.
// Otherwise the physical surface extent is used, clamped to at least 1.
int effective_logical_extent(
    int surface_extent,
    int fixed_logical_extent) noexcept;

// Resolve the complete presentation geometry.
//
// When both fixed logical dimensions are positive, the legacy raster keeps
// the recovered fixed logical contract and the final composited image is
// aspect-fitted into the physical surface.
//
// Otherwise logical and presentation geometry follow the physical surface.
PresentationGeometry resolve_geometry(
    int surface_width,
    int surface_height,
    int fixed_logical_width,
    int fixed_logical_height) noexcept;

}  // namespace presentation
}  // namespace runtime
}  // namespace angry
