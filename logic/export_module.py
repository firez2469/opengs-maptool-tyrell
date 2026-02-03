import os
import json
from PyQt6.QtWidgets import QFileDialog
import csv
from logic.shape_extractor import extract_shapes


def export_image(parent_layout, image, text):
    if image:
        try:
            path, _ = QFileDialog.getSaveFileName(
                parent_layout, text, "", "PNG Files (*.png)")
            if not path:
                return None
            image.save(path)
            return path

        except Exception as error:
            print(f"Error saving image: {error}")
            return None


def export_provinces_csv(main_layout):
    metadata = getattr(main_layout, "province_data", None)
    if not metadata:
        print("No province data to export.")
        return

    path, _ = QFileDialog.getSaveFileName(
        main_layout, "Export Province CSV", "", "CSV Files (*.csv)")
    if not path:
        return None

    return export_provinces_csv_to_path(main_layout, path)


def export_provinces_csv_to_path(main_layout, path):
    metadata = getattr(main_layout, "province_data", None)
    if not metadata:
        return None

    try:
        with open(path, "w", newline="") as f:
            w = csv.writer(f, delimiter=';')
            w.writerow(["province_id", "R", "G", "B",
                       "province_type", "x", "y", "Biome_R", "Biome_G", "Biome_B", "Biome_ID", "Biome_Name"])
            for d in metadata:
                w.writerow([d["province_id"], d["R"], d["G"], d["B"],
                            d["province_type"], round(d["x"], 2), round(d["y"], 2),
                            d.get("Biome_R", 0), d.get("Biome_G", 0), d.get("Biome_B", 0),
                            d.get("Biome_ID", ""), d.get("Biome_Name", "")])
        return path
    except Exception as e:
        print("Error saving province data:", e)
        return None


def export_territories_csv(main_layout):
    metadata = getattr(main_layout, "territory_data", None)
    if not metadata:
        print("No territory data to export.")
        return

    path, _ = QFileDialog.getSaveFileName(
        main_layout, "Export territory CSV", "", "CSV Files (*.csv)")
    if not path:
        return None

    return export_territories_csv_to_path(main_layout, path)


def export_territories_csv_to_path(main_layout, path):
    metadata = getattr(main_layout, "territory_data", None)
    if not metadata:
        return None

    try:
        with open(path, "w", newline="") as f:
            w = csv.writer(f, delimiter=';')
            w.writerow(["territory_id", "R", "G", "B",
                       "territory_type", "x", "y"])
            for d in metadata:
                w.writerow([d["territory_id"], d["R"], d["G"], d["B"],
                            d["territory_type"], round(d["x"], 2), round(d["y"], 2)])
        return path
    except Exception as e:
        print("Error saving territory data:", e)
        return None


def export_territories_json(main_layout):

    # Ask user for export directory
    export_dir = QFileDialog.getExistingDirectory(
        main_layout,
        "Select Territory Export Folder",
        "",
        QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
    )

    if not export_dir:
        print("Territory export cancelled.")
        return None

    return export_territories_to_dir(main_layout, export_dir)


def export_territories_to_dir(main_layout, export_dir):
    territories = main_layout.territory_data

    for terr in territories:
        tid = terr["territory_id"]
        provinces = terr.get("province_ids", [])

        data = {
            "territory_id": tid,
            "provinces": provinces
        }

        filename = os.path.join(export_dir, f"{tid}.json")

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    print(f"Exported {len(territories)} territories to: {export_dir}")
    return export_dir


def export_province_shapes_json(main_layout):
    index_map = getattr(main_layout.province_image_display, "_index_map", None)
    metadata = getattr(main_layout, "province_data", None)

    if index_map is None or metadata is None:
        print("No province data or index map available.")
        return

    path, _ = QFileDialog.getSaveFileName(
        main_layout, "Export Province Shapes JSON", "", "JSON Files (*.json)")
    if not path:
        return None

    return export_province_shapes_to_path(main_layout, path)


def export_province_shapes_to_path(main_layout, path):
    index_map = getattr(main_layout.province_image_display, "_index_map", None)
    metadata = getattr(main_layout, "province_data", None)

    print("Extracting shapes... this may take a moment.")
    try:
        # Use cached shape data if available and fresh?
        # For now, let's prefer the cached data if it exists (so we get rivers)
        # If we re-run extract_shapes, we lose river data unless we re-run river gen.
        
        shape_data = getattr(main_layout, "shape_data", None)
        river_edges = getattr(main_layout, "river_edges", set())
        
        if shape_data is None:
             print("Generating fresh shapes for export...")
             shape_data = extract_shapes(index_map, metadata)
        
        # Check for Heightmap and River Settings
        heightmap = getattr(main_layout.heightmap_image_display, "image", None)
        # Since ImageDisplay stores pixmap, we should use get_image() if available or check internal
        # The MainWindow stores heightmap_image_display
        heightmap = main_layout.heightmap_image_display.get_image()
        
        river_edges = set()
        if heightmap:
            try:
                from logic.river_generator import generate_rivers
                threshold = main_layout.river_threshold_slider.value()
                print(f"Auto-generating rivers on export... (Threshold: {threshold})")
                
                # Metadata is already loaded as 'metadata'
                river_edges, _ = generate_rivers(shape_data, heightmap, metadata, threshold)
            except Exception as e:
                print(f"Error generating rivers: {e}")

        # Add river info
        river_count = 0
        if river_edges:
            print(f"Found {len(river_edges)} river edges to export.")
            for edge in shape_data["edges"]:
                if edge["id"] in river_edges:
                    edge["is_river"] = True
                    river_count += 1
                else:
                    edge["is_river"] = False
        else:
            print("No river edges found (or Heightmap missing).")
            for edge in shape_data["edges"]:
                edge["is_river"] = False

        print(f"Exporting {len(shape_data['edges'])} edges, {river_count} marked as rivers.")
                    
        with open(path, "w", encoding="utf-8") as f:
            json.dump(shape_data, f) # Minify? indent=None default
        print(f"Exported shapes to {path}")
        return path
    except Exception as e:
        print(f"Error exporting shapes: {e}")
        return None


def export_all_project(main_layout):
    import config
    
    # 1. Ask for root directory
    root_dir = QFileDialog.getExistingDirectory(
        main_layout,
        "Select Export Directory for All Data",
        "",
        QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
    )
    if not root_dir:
        return

    # 2. Structure
    map_data_dir = os.path.join(root_dir, "map_data")
    territories_dir = os.path.join(map_data_dir, "territories")
    
    os.makedirs(map_data_dir, exist_ok=True)
    os.makedirs(territories_dir, exist_ok=True)

    provinces_path = os.path.join(map_data_dir, "provinces.json")

    # 3. Export Data
    # Images
    images_dir = os.path.join(map_data_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    if main_layout.province_image_display.get_image():
        main_layout.province_image_display.get_image().save(os.path.join(images_dir, "province_map.png"))
        
    if main_layout.territory_image_display.get_image():
        main_layout.territory_image_display.get_image().save(os.path.join(images_dir, "territory_map.png"))
        
    if main_layout.biome_map_display.get_image():
        main_layout.biome_map_display.get_image().save(os.path.join(images_dir, "biome_map.png"))

    # CSVs
    csv_dir = os.path.join(map_data_dir, "data")
    os.makedirs(csv_dir, exist_ok=True)
    
    export_provinces_csv_to_path(main_layout, os.path.join(csv_dir, "provinces.csv"))
    export_territories_csv_to_path(main_layout, os.path.join(csv_dir, "territories.csv"))

    # Export Province Shapes
    export_province_shapes_to_path(main_layout, provinces_path)
    
    # Export Territories
    export_territories_to_dir(main_layout, territories_dir)

    # 4. Master JSON
    master_data = {
        "version": config.VERSION,
        "provinces_path": "map_data/provinces.json",
        "territories_path": "map_data/territories/",
        "files": {
             "provinces": "map_data/provinces.json",
             "territories_dir": "map_data/territories",
             "images": {
                 "province_map": "map_data/images/province_map.png",
                 "territory_map": "map_data/images/territory_map.png",
                 "biome_map": "map_data/images/biome_map.png"
             },
             "data": {
                 "provinces_csv": "map_data/data/provinces.csv",
                 "territories_csv": "map_data/data/territories.csv"
             }
        }
    }
    
    master_path = os.path.join(root_dir, "master.json")
    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(master_data, f, indent=4)
        
    print(f"Export All completed to {root_dir}")

