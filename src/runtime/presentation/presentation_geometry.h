#pragma once

namespace angry {
namespace runtime {
namespace presentation {

// Resolve one logical presentation extent.
//
// fixed_logical_extent > 0 selects the recovered fixed logical raster.
// Otherwise the physical surface extent is used, clamped to at least 1.
int effective_logical_extent(
    int surface_extent,
    int fixed_logical_extent) noexcept;

}  // namespace presentation
}  // namespace runtime
}  // namespace angry
