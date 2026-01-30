import json
import csv
import sys
import os
from PIL import Image, ImageDraw, ImageOps
import random

def reconstruct_map(shapes_path, csv_path, output_image_path="reconstructed_map.png"):
    print(f"Loading shapes from {shapes_path}...")
    try:
        with open(shapes_path, 'r') as f:
            shapes = json.load(f)
    except FileNotFoundError:
        print("Error: Shapes file not found.")
        return

    # Load Vertices
    vertices = {v['id']: (v['x'], v['y']) for v in shapes['vertices']}
    
    # Load csv for colors if available
    prov_colors = {}
    if csv_path and os.path.exists(csv_path):
        print(f"Loading province data from {csv_path}...")
        try:
            with open(csv_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pid = row['province_id']
                    # Use Biome Color if available, else random or province color
                    if 'Biome_R' in row and row['Biome_R']:
                        r, g, b = int(row['Biome_R']), int(row['Biome_G']), int(row['Biome_B'])
                        prov_colors[pid] = (r, g, b)
                    else:
                        r, g, b = int(row['R']), int(row['G']), int(row['B'])
                        prov_colors[pid] = (r, g, b)
        except Exception as e:
            print(f"Warning: Could not load CSV: {e}")

    # Determine Image Size
    max_x = max(v[0] for v in vertices.values())
    max_y = max(v[1] for v in vertices.values())
    
    # Create Image
    scale = 1 # Can increase validation resolution
    w, h = int(max_x * scale) + 10, int(max_y * scale) + 10
    img = Image.new("RGB", (w, h), (20, 20, 20))
    draw = ImageDraw.Draw(img)
    
    print("Drawing edges...")
    edges = {e['id']: (vertices[e['v1']], vertices[e['v2']]) for e in shapes['edges']}
    
    # Draw Provinces (Fill is hard without ordered polygon, but shapes['provinces'] has edges list)
    # The edges list might not be ordered.
    # To fill, we'd need to order edges into a polygon.
    # For now, let's just draw the mesh.
    
    for e_id, (p1, p2) in edges.items():
        draw.line([p1, p2], fill=(200, 200, 200), width=1)

    # Draw Centroids or IDs based on CSV
    # (Optional)
    
    img.save(output_image_path)
    print(f"Saved reconstruction to {output_image_path}")

if __name__ == "__main__":
    # Default paths for easy testing if run from root
    shapes_file = "example_output/ProvinceShapes.json" 
    csv_file = "example_output/map_data.csv"
    
    if len(sys.argv) > 1:
        shapes_file = sys.argv[1]
    if len(sys.argv) > 2:
        csv_file = sys.argv[2]
        
    reconstruct_map(shapes_file, csv_file)
