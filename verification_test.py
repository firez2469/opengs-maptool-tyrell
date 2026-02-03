import sys
import os
import json
import numpy as np
from PIL import Image

sys.path.append(r"d:\UnityGames\Experimental\Strategy Game API\client\Map Generation\opengs-maptool-windows")

import logic.river_generator as rg

def run_test():
    print("Verifying Strict River Constraints...")
    
    # V0(High Land) -> V1(Mid Land) -> V2(Ocean)
    # Edge 100: V0-V1. (Land-Land). Should be river.
    # Edge 101: V1-V2. (Land-Ocean). Coastline. Should NOT be river.
    
    vertices = [
        {"id": 0, "x": 0, "y": 0},
        {"id": 1, "x": 1, "y": 0},
        {"id": 2, "x": 2, "y": 0}
    ]
    edges = [
        {"id": 100, "v1": 0, "v2": 1},
        {"id": 101, "v1": 1, "v2": 2} # This touches Ocean, so filtered out?
    ]
    
    # Prov 0: Land (Owns Edge 100)
    # Prov 1: Ocean (Owns Edge 101)
    
    provinces = [
        {"id": "p0", "edges": [100]},
        {"id": "p1", "edges": [101]}
    ]
    
    metadata = [
        {"province_id": "p0", "province_type": "Land"},
        {"province_id": "p1", "province_type": "Ocean"}
    ]
    
    shape_data = {
        "vertices": vertices,
        "edges": edges,
        "provinces": provinces
    }
    
    # Heightmap: V0=100, V1=50, V2=10
    hm = Image.new("L", (3, 1))
    hm.putpixel((0, 0), 100)
    hm.putpixel((1, 0), 50)
    hm.putpixel((2, 0), 10)
    
    print("Generating rivers...")
    # Flow V0 -> V1 (1.0). Edge 100 flow=1.
    # Flow V1 -> V2 (accum 2.0). Edge 101 flow=2.
    # But Edge 101 touches Ocean, so should be filtered.
    
    rv, flow = rg.generate_rivers(shape_data, hm, metadata, river_threshold=0.5)
    
    print(f"River Edges: {rv}")
    print(f"Flow Map: {dict(flow)}")
    
    if 100 in rv and 101 not in rv:
        print("SUCCESS: River formed inland but stopped at coast.")
    elif 101 in rv:
        print("FAILURE: Coast edge included as river.")
    else:
        print("FAILURE: No river formed.")

if __name__ == "__main__":
    run_test()
