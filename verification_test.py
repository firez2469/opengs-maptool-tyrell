import sys
import os
import numpy as np
import json
from PIL import Image

# Ensure project root is in path
sys.path.append(r"d:\UnityGames\Experimental\Strategy Game API\client\Map Generation\opengs-maptool-windows")

import logic.province_generator as pg
import logic.biome_manager as bm
import config

# Create a mock layout and manager test
def run_test():
    print("Testing Biome Manager Fuzzy Matching...")
    
    # Create a temporary manager with known biomes
    # We will use the real class but maybe mock the loading or just use the real file.
    # The real file has "Hot Desert" as [255, 0, 0] (from user edit)
    # Let's test with a color close to Red, e.g., [250, 10, 10]
    
    manager = bm.BiomeManager("biomes.json")
    
    # Test Exact Match (Hot Desert is 255,0,0)
    exact = manager.get_biome(255, 0, 0)
    if exact and exact['id'] == 'hot_desert':
        print("SUCCESS: Exact match found.")
    else:
        print(f"FAILURE: Exact match failed. Got {exact}")

    # Test Fuzzy Match
    # Color [200, 50, 50] should be closer to Hot Desert [255, 0, 0] 
    # than say Polar Ice [171, 183, 177]
    fuzzy_color = (200, 50, 50) 
    fuzzy = manager.get_biome(*fuzzy_color)
    
    if fuzzy and fuzzy['id'] == 'hot_desert':
        print(f"SUCCESS: Fuzzy match found for {fuzzy_color} -> {fuzzy['name']}")
    else:
        print(f"FAILURE: Fuzzy match failed for {fuzzy_color}. Got {fuzzy}")

    # Test another fuzzy match
    # Color [0, 255, 10] should be closer to potentially... 
    # Humid Subtropical [72, 188, 27] or Cold Rainforest [19, 146, 58]?
    # Let's try something very close to High Mountains [0,0,0] -> [10, 10, 10]
    fuzzy_mountain = manager.get_biome(10, 10, 10)
    if fuzzy_mountain and fuzzy_mountain['id'] == 'high_mountains':
        print(f"SUCCESS: Fuzzy match found for Mountains.")
    else:
        print(f"FAILURE: Fuzzy match failed for Mountains. Got {fuzzy_mountain}")

if __name__ == "__main__":
    run_test()
