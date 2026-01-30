import sys
import os
import numpy as np
import json
from PIL import Image

sys.path.append(r"d:\UnityGames\Experimental\Strategy Game API\client\Map Generation\opengs-maptool-windows")

import logic.shape_extractor as se

def run_test():
    print("Testing Shape Extractor...")
    
    # Create a small 5x5 grid with 2 provinces
    # 0 0 1 1 1
    # 0 0 1 1 1
    # 0 0 1 1 1
    # 0 0 1 1 1
    # 0 0 1 1 1
    
    grid = np.zeros((5, 5), dtype=np.int32)
    grid[:, 2:] = 1
    
    metadata = [{"province_id": "prv-0"}, {"province_id": "prv-1"}]
    
    data = se.extract_shapes(grid, metadata)
    
    verts = data["vertices"]
    edges = data["edges"]
    provinces = data["provinces"]
    
    print(f"Vertices: {len(verts)}")
    print(f"Edges: {len(edges)}")
    print(f"Provinces: {len(provinces)}")
    
    # Vertices should be at Top-Middle (0, 2) and Bottom-Middle (5, 2) of padded grid? 
    # Or at least capturing the vertical line.
    
    # In our logic, nodes are degree != 2.
    # At (0, 2): T-junction with top edge?
    # At (5, 2): T-junction with bottom edge?
    
    for v in verts:
        print(f"Vertex: {v}")
        
    for e in edges:
        print(f"Edge: {e['v1']} -> {e['v2']}")
        
    if len(provinces) == 2:
        print("SUCCESS: Identified 2 provinces.")
    else:
        print(f"FAILURE: Identified {len(provinces)} provinces.")

    # Check edges
    p0 = next(p for p in provinces if p['id'] == 'prv-0')
    p1 = next(p for p in provinces if p['id'] == 'prv-1')
    
    if len(p0['edges']) > 0 and len(p1['edges']) > 0:
         print("SUCCESS: Provinces have edges.")
    else:
         print("FAILURE: Provinces missing edges.")

if __name__ == "__main__":
    run_test()
