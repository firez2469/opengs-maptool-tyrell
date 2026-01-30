import json
import os
import math

class BiomeManager:
    def __init__(self, config_path="biomes.json"):
        self.biomes = []
        self.load_biomes(config_path)

    def load_biomes(self, path):
        if not os.path.exists(path):
            print(f"Warning: Biome config file not found at {path}")
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.biomes = json.load(f)
            # Pre-parse colors into tuples for faster lookup
            for b in self.biomes:
                b['color_tuple'] = tuple(b['color'])
        except Exception as e:
            print(f"Error loading biome config: {e}")

    def get_biome(self, r, g, b, tolerance=10):
        """
        Finds the biome matching the given color within a tolerance.
        Returns the biome dict or None.
        """
        target_color = (r, g, b)
        
        # 1. Exact Match
        for biome in self.biomes:
            if biome['color_tuple'] == target_color:
                return biome

        # 2. Nearest Neighbor (Euclidean distance) if no exact match
        # Only if we want to support lossy compression artifacts or slight mismatches.
        best_biome = None
        min_dist = float('inf')

        for biome in self.biomes:
            br, bg, bb = biome['color_tuple']
            dist = math.sqrt((r - br)**2 + (g - bg)**2 + (b - bb)**2)
            if dist < min_dist:
                min_dist = dist
                best_biome = biome

        # Always return the closest match
        return best_biome
