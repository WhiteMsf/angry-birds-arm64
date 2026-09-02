#include "presentation_geometry.h"

#include <algorithm>

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

}  // namespace presentation
}  // namespace runtime
}  // namespace angry
