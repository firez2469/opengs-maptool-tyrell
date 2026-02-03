import config
import json
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QProgressBar, QTabWidget, QLabel, QMenuBar, QFileDialog
from PyQt6.QtGui import QAction
from logic.province_generator import generate_province_map
from logic.territory_generator import generate_territory_map
from logic.import_module import import_image
from logic.export_module import export_image, export_provinces_csv, export_territories_csv, export_territories_json, export_province_shapes_json
from ui.buttons import create_slider, create_button
from ui.image_display import ImageDisplay
from PIL import Image


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # PROJECT STATE
        self.project_state = {
            "inputs": {
                "land_image_path": None,
                "boundary_image_path": None,
                "biome_image_path": None,
                "heightmap_image_path": None,
            },
            "settings": {
                "land_province_density": config.LAND_PROVINCES_DEFAULT,
                "ocean_province_density": config.OCEAN_PROVINCES_DEFAULT,
                "river_threshold": 10,
                "territory_land_density": config.LAND_TERRITORIES_DEFAULT,
                "territory_ocean_density": config.OCEAN_TERRITORIES_DEFAULT,
            },
            "outputs": {
                "province_map_image_path": None,
                "province_csv_path": None,
                "province_shapes_path": None,
                "territory_map_image_path": None,
                "territory_csv_path": None,
                "territory_json_path": None,
                "biome_map_image_path": None,
            }
        }

        # MAIN LAYOUT
        self.setWindowTitle(config.TITLE)
        self.resize(config.WINDOW_SIZE_WIDTH,
                    config.WINDOW_SIZE_HEIGHT)
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        # MENU BAR
        self.menu_bar = QMenuBar()
        file_menu = self.menu_bar.addMenu("File")
        
        save_action = QAction("Save Project", self)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)

        load_action = QAction("Load Project", self)
        load_action.triggered.connect(self.load_project)
        file_menu.addAction(load_action)

        main_layout.addWidget(self.menu_bar)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, stretch=1)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        main_layout.addWidget(self.progress)
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setValue(0)

        self.label_version = QLabel("Version "+config.VERSION)
        main_layout.addWidget(self.label_version)

        self.shape_data = None
        self.river_edges = None

        # TAB1 LAND IMAGE
        self.land_tab = QWidget()
        self.land_image_display = ImageDisplay()
        land_tab_layout = QVBoxLayout(self.land_tab)
        land_tab_layout.addWidget(self.land_image_display)
        self.tabs.addTab(self.land_tab, "Land Image")

        # Buttons
        create_button(land_tab_layout,
                      "Import Land Image",
                      lambda: self.import_and_track_image("Import Land Image", self.land_image_display, "land_image_path"))

        # TAB2 BOUNDARY IMAGE
        self.boundary_tab = QWidget()
        self.boundary_image_display = ImageDisplay()
        boundary_tab_layout = QVBoxLayout(self.boundary_tab)
        boundary_tab_layout.addWidget(self.boundary_image_display)
        self.tabs.addTab(self.boundary_tab, "Boundary Image")

        # Buttons
        create_button(boundary_tab_layout,
                      "Import Boundary Image",
                      lambda: self.import_and_track_image("Import Boundary Image", self.boundary_image_display, "boundary_image_path"))

        # TAB3 BIOME IMAGE
        self.biome_tab = QWidget()
        self.biome_image_display = ImageDisplay()
        biome_tab_layout = QVBoxLayout(self.biome_tab)
        biome_tab_layout.addWidget(self.biome_image_display)
        self.tabs.addTab(self.biome_tab, "Biome Image")

        self.button_import_biome = create_button(biome_tab_layout,
                                                 "Import Biome Image",
                                                 lambda: self.import_and_track_image("Import Biome Image", self.biome_image_display, "biome_image_path"))

        # TAB4 HEIGHTMAP IMAGE
        self.heightmap_tab = QWidget()
        self.heightmap_image_display = ImageDisplay()
        heightmap_tab_layout = QVBoxLayout(self.heightmap_tab)
        heightmap_tab_layout.addWidget(self.heightmap_image_display)
        self.tabs.addTab(self.heightmap_tab, "Heightmap Image")
        
        # Buttons
        create_button(heightmap_tab_layout,
                      "Import Heightmap",
                      lambda: self.import_and_track_image("Import Heightmap", self.heightmap_image_display, "heightmap_image_path"))

        # TAB3 PROVINCE IMAGE
        self.province_tab = QWidget()
        self.province_image_display = ImageDisplay()
        province_tab_layout = QVBoxLayout(self.province_tab)
        province_tab_layout.addWidget(self.province_image_display)
        self.tabs.addTab(self.province_tab, "Province Image")
        button_row = QHBoxLayout()
        province_tab_layout.addLayout(button_row)


        # Buttons
        self.land_slider = create_slider(province_tab_layout,
                                         "Land province Density:",
                                         config.LAND_PROVINCES_MIN,
                                         config.LAND_PROVINCES_MAX,
                                         config.LAND_PROVINCES_DEFAULT,
                                         config.LAND_PROVINCES_TICK,
                                         config.LAND_PROVINCES_STEP)
        self.land_slider.valueChanged.connect(lambda v: self.update_setting("land_province_density", v))

        self.ocean_slider = create_slider(province_tab_layout,
                                          "Ocean province Density",
                                          config.OCEAN_PROVINCES_MIN,
                                          config.OCEAN_PROVINCES_MAX,
                                          config.OCEAN_PROVINCES_DEFAULT,
                                          config.OCEAN_PROVINCES_TICK,
                                          config.OCEAN_PROVINCES_STEP)
        self.ocean_slider.valueChanged.connect(lambda v: self.update_setting("ocean_province_density", v))

        self.river_threshold_slider = create_slider(province_tab_layout,
                                                    "River Threshold:",
                                                    1, 100, 10, 1, 1)
        self.river_threshold_slider.valueChanged.connect(lambda v: self.update_setting("river_threshold", v))

        self.button_gen_prov = create_button(province_tab_layout,
                                             "Generate Provinces",
                                             lambda: self.run_generation())
        self.button_gen_prov.setEnabled(False)

        self.button_exp_prov_img = create_button(button_row,
                                                 "Export Province Map",
                                                 lambda: self.export_and_track(export_image, "province_map_image_path",
                                                                      self.province_image_display.get_image(),
                                                                      "Export Province Map"))
        self.button_exp_prov_img.setEnabled(False)

        self.button_exp_prov_csv = create_button(button_row,
                                                 "Export Province CSV",
                                                 lambda: self.export_and_track(export_provinces_csv, "province_csv_path"))
        self.button_exp_prov_csv.setEnabled(False)
        
        self.button_exp_prov_shapes = create_button(button_row,
                                                 "Export Province Shapes",
                                                 lambda: self.export_and_track(export_province_shapes_json, "province_shapes_path"))
        self.button_exp_prov_shapes.setEnabled(False)

        # TAB4 TERRITORY IMAGE
        self.territory_tab = QWidget()
        self.territory_image_display = ImageDisplay()
        territory_tab_layout = QVBoxLayout(self.territory_tab)
        territory_tab_layout.addWidget(self.territory_image_display)
        self.tabs.addTab(self.territory_tab, "Territory Image")
        button_territory_row = QHBoxLayout()
        territory_tab_layout.addLayout(button_territory_row)

        # Buttons
        self.territory_land_slider = create_slider(territory_tab_layout,
                                                   "Territory Land Density:",
                                                   config.LAND_TERRITORIES_MIN,
                                                   config.LAND_TERRITORIES_MAX,
                                                   config.LAND_TERRITORIES_DEFAULT,
                                                   config.LAND_TERRITORIES_TICK,
                                                   config.LAND_TERRITORIES_STEP)
        self.territory_land_slider.valueChanged.connect(lambda v: self.update_setting("territory_land_density", v))

        self.territory_ocean_slider = create_slider(territory_tab_layout,
                                                    "Territory Ocean Density:",
                                                    config.OCEAN_TERRITORIES_MIN,
                                                    config.OCEAN_TERRITORIES_MAX,
                                                    config.OCEAN_TERRITORIES_DEFAULT,
                                                    config.OCEAN_TERRITORIES_TICK,
                                                    config.OCEAN_TERRITORIES_STEP)
        self.territory_ocean_slider.valueChanged.connect(lambda v: self.update_setting("territory_ocean_density", v))

        self.button_gen_territories = create_button(territory_tab_layout,
                                                    "Generate Territories",
                                                    lambda: generate_territory_map(self))
        self.button_gen_territories.setEnabled(False)

        self.button_exp_terr_img = create_button(button_territory_row,
                                                 "Export Territory Map",
                                                 lambda: self.export_and_track(export_image, "territory_map_image_path",
                                                                      self.territory_image_display.get_image(),
                                                                      "Export Territory Map"))
        self.button_exp_terr_img.setEnabled(False)

        # TAB5 BIOME MAP
        self.biome_map_tab = QWidget()
        self.biome_map_display = ImageDisplay()
        biome_map_tab_layout = QVBoxLayout(self.biome_map_tab)
        biome_map_tab_layout.addWidget(self.biome_map_display)
        self.tabs.addTab(self.biome_map_tab, "Biome Map")
        button_biome_map_row = QHBoxLayout()
        biome_map_tab_layout.addLayout(button_biome_map_row)

        self.button_exp_biome_map = create_button(button_biome_map_row,
                                                  "Export Biome Map",
                                                  lambda: self.export_and_track(export_image, "biome_map_image_path",
                                                                         self.biome_map_display.get_image(),
                                                                         "Export Biome Map"))
        self.button_exp_biome_map.setEnabled(False)

        self.button_exp_terr_csv = create_button(button_territory_row,
                                                 "Export Territory CSV",
                                                 lambda: self.export_and_track(export_territories_csv, "territory_csv_path"))
        self.button_exp_terr_csv.setEnabled(False)

        self.button_exp_terr_json = create_button(button_territory_row,
                                                  "Export Territory JSON",
                                                  lambda: self.export_and_track(export_territories_json, "territory_json_path"))
        self.button_exp_terr_json.setEnabled(False)
        
        # Load initial values into state
        self.update_setting("land_province_density", self.land_slider.value())
        self.update_setting("ocean_province_density", self.ocean_slider.value())
        self.update_setting("river_threshold", self.river_threshold_slider.value())
        self.update_setting("territory_land_density", self.territory_land_slider.value())
        self.update_setting("territory_ocean_density", self.territory_ocean_slider.value())


    def run_generation(self):
        # Wrapper to handle the multiple return values
        _, metadata, index_map = generate_province_map(self)
        
        # Set interactive data for tooltips
        self.province_image_display.set_interactive_data(index_map, metadata)
        self.biome_map_display.set_interactive_data(index_map, metadata)

    def import_and_track_image(self, title, display, state_key):
        path, image = import_image(self, title, display)
        if path:
            self.project_state["inputs"][state_key] = path
            print(f"Imported {title} from {path}")

    def update_setting(self, key, value):
        self.project_state["settings"][key] = int(value)
        # print(f"Setting {key} updated to {value}")

    def export_and_track(self, export_func, state_key, *args):
        # Call export function with optional args (images etc)
        # Some export functions take only 'self' (main_layout), others take args
        
        path = None
        if args:
            path = export_func(self, *args)
        else:
            path = export_func(self)
            
        if path:
            self.project_state["outputs"][state_key] = path
            print(f"Exported to {path}, saved to state.")

    def save_project(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "JSON Files (*.json)")
        if not path:
            return
        
        try:
            with open(path, "w") as f:
                json.dump(self.project_state, f, indent=4)
            print(f"Project saved to {path}")
        except Exception as e:
            print(f"Error saving project: {e}")

    def load_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Project", "", "JSON Files (*.json)")
        if not path:
            return
            
        try:
            with open(path, "r") as f:
                state = json.load(f)
            
            self.project_state = state
            
            # Restore inputs
            inputs = state.get("inputs", {})
            self._load_input_image(inputs.get("land_image_path"), self.land_image_display, "land_image_path")
            self._load_input_image(inputs.get("boundary_image_path"), self.boundary_image_display, "boundary_image_path")
            self._load_input_image(inputs.get("biome_image_path"), self.biome_image_display, "biome_image_path")
            self._load_input_image(inputs.get("heightmap_image_path"), self.heightmap_image_display, "heightmap_image_path")
            
            # Restore settings (block signals if you don't want to re-trigger updates, 
            # though updating state again is harmless here)
            settings = state.get("settings", {})
            self.land_slider.setValue(settings.get("land_province_density", config.LAND_PROVINCES_DEFAULT))
            self.ocean_slider.setValue(settings.get("ocean_province_density", config.OCEAN_PROVINCES_DEFAULT))
            self.river_threshold_slider.setValue(settings.get("river_threshold", 10))
            self.territory_land_slider.setValue(settings.get("territory_land_density", config.LAND_TERRITORIES_DEFAULT))
            self.territory_ocean_slider.setValue(settings.get("territory_ocean_density", config.OCEAN_TERRITORIES_DEFAULT))

            # Enable gen button if inputs exist
            if any(inputs.values()):
                 self.button_gen_prov.setEnabled(True)

            # Restore output previews if files exist
            # Note: We cannot easily restore full state (metadata, shapes) just from output images.
            # But we can show the images if they exist.
            outputs = state.get("outputs", {})
            self._load_preview_image(outputs.get("province_map_image_path"), self.province_image_display)
            self._load_preview_image(outputs.get("territory_map_image_path"), self.territory_image_display)
            self._load_preview_image(outputs.get("biome_map_image_path"), self.biome_map_display)
            
            print(f"Project loaded from {path}")

        except Exception as e:
            print(f"Error loading project: {e}")

    def _load_input_image(self, path, display, key):
        if path and os.path.exists(path):
            try:
                image = Image.open(path)
                display.set_image(image)
                # Ensure path is in state (in case we loaded a file with missing keys)
                self.project_state["inputs"][key] = path
            except Exception as e:
                print(f"Failed to load input {path}: {e}")
        elif path:
             print(f"Input file not found: {path}")

    def _load_preview_image(self, path, display):
        if path and os.path.exists(path):
            try:
                image = Image.open(path)
                display.set_image(image)
            except Exception as e:
                print(f"Failed to load preview {path}: {e}")
