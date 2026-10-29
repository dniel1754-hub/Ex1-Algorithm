"""Numba kernel for NumbaProjector. Same arithmetic as NumpyProjector, pixel by pixel."""
import numpy as np
from numba import njit, prange


@njit(parallel=True, cache=True)
def project_rows(volume, a1_rows, dp, d12, left, out, half_pixel):
    h, w = out.shape
    sx, sy, sz = volume.shape
    for y in prange(h):
        end = d12[y]
        for x in range(w):
            x1 = x - left[y]
            if x1 < -half_pixel or x1 > end + half_pixel:
                out[y, x] = 0
                continue
            x1 = min(max(x1, 0.0), end)
            i = np.rint(x1 * dp[y, 0] + a1_rows[y, 0])
            j = np.rint(x1 * dp[y, 1] + a1_rows[y, 1])
            k = np.rint(x1 * dp[y, 2] + a1_rows[y, 2])
            if 0 <= i < sx and 0 <= j < sy and 0 <= k < sz:
                out[y, x] = volume[int(i), int(j), int(k)]
            else:
                out[y, x] = 0
