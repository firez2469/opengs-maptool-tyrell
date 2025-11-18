import numpy as np


def generate_grid_jitter_seeds(land_mask: np.ndarray, num_points: int):
    """
    Generate seed points in a grid + jitter fashion over land pixels (white area).
    land_mask: bool array (H, W), True where land (non-border).
    num_points: desired approximate number of seeds.

    Returns a list of (x, y) integer coordinates.
    """
    h, w = land_mask.shape
    if num_points <= 0:
        return []

    # approximate a square grid
    grid_size = int(np.sqrt(num_points))
    if grid_size < 1:
        grid_size = 1

    # grid cell size in pixels
    cell_h = h / grid_size
    cell_w = w / grid_size

    seeds = []

    rng = np.random.default_rng(12345)  # global RNG for jitter

    for gy in range(grid_size):
        for gx in range(grid_size):
            # cell bounds (float)
            y0 = int(gy * cell_h)
            y1 = int(min((gy + 1) * cell_h, h))
            x0 = int(gx * cell_w)
            x1 = int(min((gx + 1) * cell_w, w))

            if y1 <= y0 or x1 <= x0:
                continue

            cell_land = land_mask[y0:y1, x0:x1]
            ys, xs = np.where(cell_land)
            if len(xs) == 0:
                # no land in this cell
                continue

            # choose a random pixel in this cell's land as seed
            idx = rng.integers(0, len(xs))
            sx = int(x0 + xs[idx])
            sy = int(y0 + ys[idx])
            seeds.append((sx, sy))

    return seeds
