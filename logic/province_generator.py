from scipy.ndimage import distance_transform_edt
from collections import deque
from typing import List, Tuple

import numpy as np
from PIL import Image

from .color_utils import color_from_id
from .seed_generator import generate_grid_jitter_seeds


def generate_province_map(img: Image.Image, num_points: int) -> Image.Image:
    """
    Full province map generator:
    - border pixels (<128) are walls during filling
    - land pixels are filled by flood-fill from seeds
    - after filling: borders are recolored to the nearest province (Option A)
    """
    arr = np.array(img)  # shape (H, W), grayscale
    h, w = arr.shape

    # Borders & land masks
    border_mask = arr < 128          # True where boundary
    land_mask = ~border_mask         # True where fillable

    if not land_mask.any():
        raise ValueError("No land (white) area found in the image.")

    # Create seeds using grid+jitter
    seeds = generate_grid_jitter_seeds(land_mask, num_points)
    if not seeds:
        raise ValueError("No seed points generated.")

    # Ensure seeds aren't on borders
    seeds = [(x, y) for (x, y) in seeds if not border_mask[y, x]]
    if not seeds:
        raise ValueError(
            "All seeds placed on borders. Increase density or adjust image.")

    # Flood fill
    province_map = _flood_fill_provinces(border_mask, land_mask, seeds)

    # Post-process: recolor border pixels using nearest province
    _fill_borders_from_neighbors(province_map, border_mask)

    # Convert to RGB output
    rgb = _province_map_to_rgb(province_map)
    return Image.fromarray(rgb, mode="RGB")


# -------------------------------------------------------------------
#   FLOOD FILL (Method B — respects borders as walls)
# -------------------------------------------------------------------

def _flood_fill_provinces(
    border_mask: np.ndarray,
    land_mask: np.ndarray,
    seeds: List[Tuple[int, int]],
) -> np.ndarray:
    """
    Multi-source BFS flood-fill:
    - border_mask: walls (never crossed)
    - seeds: initial province ID positions
    Returns province_map:
        -2 = border pixel
        -1 = unassigned land (should be rare)
        >=0 = province ID
    """
    h, w = border_mask.shape
    province_map = np.full((h, w), -1, dtype=np.int32)

    # Borders remain -2 during fill
    province_map[border_mask] = -2

    q = deque()
    for pid, (sx, sy) in enumerate(seeds):
        province_map[sy, sx] = pid
        q.append((sx, sy, pid))

    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    while q:
        x, y, pid = q.popleft()

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if nx < 0 or nx >= w or ny < 0 or ny >= h:
                continue
            if province_map[ny, nx] != -1:
                continue
            if border_mask[ny, nx]:
                continue

            # valid land pixel: assign province
            province_map[ny, nx] = pid
            q.append((nx, ny, pid))

    return province_map


# -------------------------------------------------------------------
#   POST-PROCESS: RECOLOR BORDERS (Option A)
# -------------------------------------------------------------------


def _fill_borders_from_neighbors(province_map: np.ndarray, border_mask: np.ndarray):
    """
    Option A (improved):
    Recolor border pixels (-2) using the nearest non-border pixel
    by Euclidean distance transform.
    Much better than 4-neighbor logic for long boundaries.
    """

    h, w = province_map.shape

    # Valid province locations: pid >= 0
    province_mask = province_map >= 0

    # We compute distance transform from PROVINCES to BORDERS.
    # For each border pixel, we need the nearest province pixel.
    #
    # EDM trick: The distance transform also gives the index of the nearest
    # source pixel using "return_indices=True".

    distances, (nearest_y, nearest_x) = distance_transform_edt(
        ~province_mask,      # distance = 0 where province_mask == True
        return_indices=True
    )

    # Now nearest_x,nearest_y is for EVERY pixel the coordinate of
    # the nearest PROVINCE pixel.
    for y in range(h):
        for x in range(w):
            if border_mask[y, x]:
                ny = nearest_y[y, x]
                nx = nearest_x[y, x]
                pid = province_map[ny, nx]
                if pid >= 0:
                    province_map[y, x] = pid
                else:
                    # fallback (should not happen)
                    province_map[y, x] = -1


# -------------------------------------------------------------------
#   CONVERT TO RGB
# -------------------------------------------------------------------

def _province_map_to_rgb(province_map: np.ndarray) -> np.ndarray:
    """
    Convert province_map to an RGB array.
    -1 pixels -> painted white
    >=0      -> colored by deterministic random color_from_id()
    """
    h, w = province_map.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)

    max_pid = province_map.max()
    color_cache = {}

    for pid in range(max_pid + 1):
        color_cache[pid] = color_from_id(pid)

    for y in range(h):
        for x in range(w):
            pid = province_map[y, x]
            if pid < 0:
                # unassigned or border fill fallback
                rgb[y, x] = (255, 255, 255)
            else:
                rgb[y, x] = color_cache[pid]

    return rgb
