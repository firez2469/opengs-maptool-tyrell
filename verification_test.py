import sys
import os
import numpy as np
import json
from PIL import Image

sys.path.append(r"d:\UnityGames\Experimental\Strategy Game API\client\Map Generation\opengs-maptool-windows")

import logic.shape_extractor as se
import reconstruction

def run_test():
    print("Running Final Verification...")
    
    # 1. Feature Check: Shape Extraction
    # Run extraction on dummy data
    print("Testing Shape Extraction...")
    grid = np.zeros((5, 5), dtype=np.int32)
    grid[:, 2:] = 1
    metadata = [{"province_id": "prv-0"}, {"province_id": "prv-1"}]
    data = se.extract_shapes(grid, metadata)
    
    # Save dummy data for reconstruction test
    dummy_json_path = "dummy_shapes.json"
    dummy_csv_path = "dummy_map.csv"
    
    with open(dummy_json_path, 'w') as f:
        json.dump(data, f)
        
    with open(dummy_csv_path, 'w') as f:
        f.write("province_id,R,G,B,province_type,x,y\n")
        f.write("prv-0,255,0,0,Land,0,0\n")
        f.write("prv-1,0,255,0,Land,2,0\n")
        
    # 2. Feature Check: Reconstruction
    print("Testing Reconstruction Script...")
    try:
        reconstruction.reconstruct_map(dummy_json_path, dummy_csv_path, "dummy_reconstruction.png")
        if os.path.exists("dummy_reconstruction.png"):
            print("SUCCESS: Reconstruction image created.")
        else:
            print("FAILURE: Reconstruction image not created.")
    except Exception as e:
        print(f"FAILURE: Reconstruction script crashed: {e}")
        
    # Cleanup
    try:
        os.remove(dummy_json_path)
        os.remove(dummy_csv_path)
        if os.path.exists("dummy_reconstruction.png"):
             os.remove("dummy_reconstruction.png")
    except:
        pass

    # 3. Documentation Check
    readme_path = r"d:\UnityGames\Experimental\Strategy Game API\client\Map Generation\opengs-maptool-windows\README.md"
    doc_path = r"d:\UnityGames\Experimental\Strategy Game API\client\Map Generation\opengs-maptool-windows\example_output\DATA_FORMAT.md"
    
    if os.path.exists(readme_path):
        print("SUCCESS: README exists.")
    else:
        print("FAILURE: README missing.")
        
    if os.path.exists(doc_path):
        print("SUCCESS: DATA_FORMAT exists.")
    else:
        print("FAILURE: DATA_FORMAT missing.")

    print("Final Verification Complete.")

if __name__ == "__main__":
    run_test()
