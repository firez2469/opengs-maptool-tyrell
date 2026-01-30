import config
import numpy as np
from collections import deque
from PIL import Image
from scipy.ndimage import distance_transform_edt
from logic.numb_gen import NumberSeries
from logic.biome_manager import BiomeManager

used_colors = set()


def generate_province_map(main_layout):
    used_colors.clear()
    main_layout.progress.setVisible(True)
    main_layout.progress.setValue(10)

    boundary_image = main_layout.boundary_image_display.get_image()
    land_image = main_layout.land_image_display.get_image()
    biome_image = main_layout.biome_image_display.get_image()

    if boundary_image is None and land_image is None:
        raise ValueError(
            "Need at least boundary OR ocean image to determine map size.")

    # BOUNDARY MASK
    if boundary_image is not None:
        b_arr = np.array(boundary_image, copy=False)

        if b_arr.ndim == 3:
            r, g, b = config.BOUNDARY_COLOR
            boundary_mask = (
                (b_arr[..., 0] == r) &
                (b_arr[..., 1] == g) &
                (b_arr[..., 2] == b)
            )
        else:
            (val,) = config.BOUNDARY_COLOR[:1]
            boundary_mask = (b_arr == val)

        map_h, map_w = boundary_mask.shape

    else:
        boundary_mask = None

    # LAND / SEA MASKS
    if land_image is not None:
        o_arr = np.array(land_image, copy=False)
        sea_mask = is_sea_color(o_arr)
        land_mask = ~sea_mask

        if boundary_mask is None:
            map_h, map_w = sea_mask.shape
    else:
        if boundary_mask is None:
            raise ValueError("Could not determine map size.")

        sea_mask = np.zeros((map_h, map_w), dtype=bool)
        land_mask = np.ones((map_h, map_w), dtype=bool)

    if boundary_mask is None:
        land_fill = land_mask
        land_border = sea_mask

        sea_fill = sea_mask
        sea_border = land_mask
    else:
        land_fill = land_mask & ~boundary_mask
        land_border = boundary_mask | sea_mask

        sea_fill = sea_mask & ~boundary_mask
        sea_border = boundary_mask | land_mask

    # CREATE NUMBER SERIES
    series = NumberSeries(
        config.PROVINCE_ID_PREFIX,
        config.PROVINCE_ID_START,
        config.PROVINCE_ID_END
    )

    # PREPARE BIOME DATA
    biome_arr = None
    if biome_image is not None:
        biome_arr = np.array(biome_image, copy=False)
        # Ensure it has 3 channels for RGB
        if biome_arr.ndim == 2:
             # If grayscale, convert to essentially RGB by stacking
             biome_arr = np.stack((biome_arr,)*3, axis=-1)
        elif biome_arr.shape[2] > 3:
             # Drop alpha if present
             biome_arr = biome_arr[..., :3]

    # GENERATE PROVINCES
    land_points = main_layout.land_slider.value()
    sea_points = main_layout.ocean_slider.value()

    land_map, land_meta, next_index = create_province_map(
        land_fill, land_border, land_points, 0, "land", series, biome_arr
    )

    main_layout.progress.setValue(50)

    if sea_points > 0 and land_image is not None:
        sea_map, sea_meta, _ = create_province_map(
            sea_fill, sea_border, sea_points, next_index, "ocean", series, biome_arr
        )
    else:
        sea_map = np.full((map_h, map_w), -1, np.int32)
        sea_meta = []

    metadata = land_meta + sea_meta

    # NOTE: combine_maps was removed/refactored here.
    # The return statement above was sending province_image which is no longer computed there.
    # We need to restructure this block slightly.
    # The previous block was:
    # province_image = combine_maps(...)
    # main_layout.province_image_display.set_image(province_image)
    # ...
    # return province_image, metadata
    
    # Let's target the combine_maps call instead.

    main_layout.button_gen_territories.setEnabled(True)

    # Initialize Biome Manager
    biome_manager = BiomeManager("biomes.json")
    
    # Resolve Biomes
    if biome_arr is not None:
         _resolve_biomes(metadata, biome_arr, biome_manager)

    # COMBINE MAPS (Create the grid of IDs)
    combined_indices = create_visual_index_grid(
        land_map, sea_map, land_mask, sea_mask
    )

    # RENDER PROVINCE MAP
    province_image = render_visual_map(combined_indices, metadata, "R", "G", "B")

    # RENDER BIOME MAP
    biome_map_image = render_visual_map(combined_indices, metadata, "Biome_R", "Biome_G", "Biome_B")

    main_layout.province_image_display.set_image(province_image)
    if hasattr(main_layout, 'biome_map_display'):
        main_layout.biome_map_display.set_image(biome_map_image)
        
    main_layout.province_data = metadata

    main_layout.progress.setValue(100)
    main_layout.button_exp_prov_img.setEnabled(True)
    if hasattr(main_layout, 'button_exp_biome_map'):
        main_layout.button_exp_biome_map.setEnabled(True)

    main_layout.button_exp_prov_csv.setEnabled(True)
    main_layout.button_gen_territories.setEnabled(True)

    return province_image, metadata, combined_indices


# BASIC UTILITIES
def is_sea_color(arr):
    r, g, b = config.OCEAN_COLOR
    return (arr[..., 0] == r) & (arr[..., 1] == g) & (arr[..., 2] == b)


def _color_from_id(index: int, ptype: str, used_colors=used_colors):
    rng = np.random.default_rng(index + 1)

    while True:
        if ptype == "ocean":
            r = rng.integers(0, 60)
            g = rng.integers(0, 80)
            b = rng.integers(100, 180)
        else:
            r, g, b = map(int, rng.integers(0, 256, 3))

        color = (int(r), int(g), int(b))
        if color not in used_colors:
            used_colors.add(color)
            return color


def generate_jitter_seeds(mask: np.ndarray, num_points: int):
    if num_points <= 0:
        return []

    h, w = mask.shape
    grid = max(1, int(np.sqrt(num_points)))

    cell_h = h / grid
    cell_w = w / grid
    rng = np.random.default_rng()
    seeds = []

    for gy in range(grid):
        y0 = int(gy * cell_h)
        y1 = int((gy + 1) * cell_h)

        for gx in range(grid):
            x0 = int(gx * cell_w)
            x1 = int((gx + 1) * cell_w)

            cell = mask[y0:y1, x0:x1]
            ys, xs = np.where(cell)

            if xs.size == 0:
                continue

            i = rng.integers(xs.size)
            seeds.append((x0 + xs[i], y0 + ys[i]))

    return seeds


def create_province_map(fill_mask, border_mask, num_points, start_index, ptype, series, biome_arr=None):
    if num_points <= 0 or not fill_mask.any():
        empty = np.full(fill_mask.shape, -1, np.int32)
        return empty, [], start_index

    seeds = generate_jitter_seeds(fill_mask, num_points)
    seeds = [(x, y) for x, y in seeds if fill_mask[y, x]]

    if not seeds:
        empty = np.full(fill_mask.shape, -1, np.int32)
        return empty, [], start_index

    pmap, metadata = flood_fill(fill_mask, seeds, start_index, ptype, series)
    assign_borders(pmap, border_mask)
    finalize_metadata(metadata, biome_arr)

    next_index = len(metadata)
    return pmap, list(metadata.values()), next_index


def flood_fill(fill_mask, seeds, start_index, ptype, series):
    h, w = fill_mask.shape
    pmap = np.full((h, w), -1, np.int32)

    metadata = {}
    q = deque()

    neighbors = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    for i, (sx, sy) in enumerate(seeds):
        index = start_index + i
        pid = series.get_id()

        pmap[sy, sx] = index

        r, g, b = _color_from_id(index, ptype)
        metadata[index] = {
            "province_id": pid,
            "province_type": ptype,
            "R": r, "G": g, "B": b,
            "sum_x": sx,
            "sum_y": sy,
            "count": 1
        }

        q.append((sx, sy, index))

    while q:
        x, y, index = q.popleft()
        d = metadata[index]

        for dx, dy in neighbors:
            nx = x + dx
            ny = y + dy

            if 0 <= nx < w and 0 <= ny < h:
                if pmap[ny, nx] == -1 and fill_mask[ny, nx]:
                    pmap[ny, nx] = index
                    d["sum_x"] += nx
                    d["sum_y"] += ny
                    d["count"] += 1
                    q.append((nx, ny, index))

    return pmap, metadata


def assign_borders(pmap, border_mask):
    valid = pmap >= 0
    if not valid.any() or not border_mask.any():
        return

    _, (ny, nx) = distance_transform_edt(~valid, return_indices=True)
    bm = border_mask
    pmap[bm] = pmap[ny[bm], nx[bm]]


def finalize_metadata(metadata, biome_arr):
    for d in metadata.values():
        c = d["count"]
        d["x"] = d["sum_x"] / c
        d["y"] = d["sum_y"] / c
        del d["sum_x"], d["sum_y"], d["count"]


def _resolve_biomes(metadata, biome_arr, biome_manager):
    h, w, _ = biome_arr.shape
    for d in metadata:
        # Coordinates are (y, x) in array
        ix, iy = int(d["x"]), int(d["y"])
        
        # Defaults
        d["Biome_R"] = 0
        d["Biome_G"] = 0
        d["Biome_B"] = 0
        d["Biome_ID"] = "unknown"
        d["Biome_Name"] = "Unknown"

        if 0 <= iy < h and 0 <= ix < w:
            r, g, b = biome_arr[iy, ix]
            d["Biome_R"] = int(r)
            d["Biome_G"] = int(g)
            d["Biome_B"] = int(b)
            
            biome = biome_manager.get_biome(int(r), int(g), int(b))
            if biome:
                d["Biome_ID"] = biome["id"]
                d["Biome_Name"] = biome["name"]


def create_visual_index_grid(land_map, sea_map, land_mask, sea_mask):
    if land_map is not None and land_map.size > 0:
        h, w = land_map.shape
    else:
        h, w = sea_map.shape

    combined = np.full((h, w), -1, np.int32)

    if land_map is not None:
        lm = (land_map >= 0) & land_mask
        combined[lm] = land_map[lm]

    if sea_map is not None:
        sm = (sea_map >= 0) & sea_mask
        combined[sm] = sea_map[sm]

    if (combined >= 0).any():
        valid = combined >= 0
        _, (ny, nx) = distance_transform_edt(~valid, return_indices=True)
        missing = combined < 0
        combined[missing] = combined[ny[missing], nx[missing]]
        
    return combined

def render_visual_map(combined, metadata, r_key, g_key, b_key):
    h, w = combined.shape
    out = np.zeros((h, w, 3), np.uint8)

    if not metadata:
        return Image.fromarray(out)
        
    # Create LUT
    # Metadata is list of dicts. But indices in combined map correspond to list order?
    # Yes, create_province_map uses 'start_index' and increments.
    # And pmap is filled with 'index'.
    # In generate_province_map:
    # land_map starts at 0.
    # sea_map starts at next_index.
    # metadata = land_meta + sea_meta
    # So combined indices should map perfectly to metadata list indices.
    
    color_lut = np.zeros((len(metadata), 3), np.uint8)

    for index, d in enumerate(metadata):
        color_lut[index] = (d.get(r_key, 0), d.get(g_key, 0), d.get(b_key, 0))

    valid = combined >= 0
    out[valid] = color_lut[combined[valid]]

    return Image.fromarray(out)

# Deprecating old combine_maps to avoid confusion, or keeping it as wrapper if needed? 
# It's better to remove it since we replaced its usage.

