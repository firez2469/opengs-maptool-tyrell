import numpy as np


def color_from_id(pid: int):
    """
    Deterministic 'random-looking' color for each province ID.
    Avoids black and pure white. Good for Paradox province IDs.
    """
    rng = np.random.default_rng(pid + 1)  # shift to avoid trivial seed
    r = int(rng.integers(1, 256))
    g = int(rng.integers(1, 256))
    b = int(rng.integers(1, 256))

    # Optionally avoid very dark colors
    if r < 20 and g < 20 and b < 20:
        r = (r + 50) % 256
        g = (g + 50) % 256
        b = (b + 50) % 256

    return r, g, b
