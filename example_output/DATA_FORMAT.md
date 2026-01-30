# Data Format Documentation

This document describes the structure of the data files exported by the Map Tool.

## 1. map_data.csv (Province Data)
A CSV file containing metadata for each generated province.

| Column | Description |
| :--- | :--- |
| `province_id` | Unique identifier for the province (e.g., `prv-0, prv-1`). |
| `R`, `G`, `B` | The unique RGB color assigned to this province in the Province Map Image. |
| `province_type` | Type of province: `Land` or `Sea`. |
| `x`, `y` | Pixel coordinates of the province centroid. |
| `Biome_R`, `Biome_G`, `Biome_B` | RGB color sampled from the Biome Input Texture at the centroid. |
| `Biome_ID` | ID of the biome determined from `biomes.json`. |
| `Biome_Name` | Display name of the biome. |

## 2. ProvinceShapes.json (Topological Mesh)
A JSON file representing the topological graph of the province boundaries. This is useful for rendering game map borders or meshes.

```json
{
    "vertices": [
        { "id": 0, "x": 10, "y": 20 },
        ...
    ],
    "edges": [
        { "id": 0, "v1": 0, "v2": 1 },
        ...
    ],
    "provinces": [
        { "id": "prv-0", "edges": [0, 4, 12, ...] },
        ...
    ]
}
```

*   **vertices**: List of points where boundary lines meet (corners). `x` and `y` are image coordinates.
*   **edges**: Connections between two vertices (`v1`, `v2`). `id` is the unique edge ID.
*   **provinces**: List of provinces, referencing their `province_id` and a list of `edges` that form their boundary.

## 3. territory_data.json
A summary JSON file listing all generated territories and their consituent provinces.

```json
[
    {
        "territory_id": "terr-0",
        "territory_type": "Land",
        "center_x": 100,
        "center_y": 100,
        "color": [255, 0, 0],
        "provinces": ["prv-0", "prv-4", "prv-9"]
    },
    ...
]
```

## 4. Territory Data/[id].json
Individual JSON files for each territory, containing more detailed information if applicable.

```json
{
    "id": "terr-0",
    "type": "Land",
    "neighbors": ["terr-1", "terr-5"],
    "provinces": [ ... ]
}
```
*(Note: The exact content of individual territory files may vary based on generation parameters.)*
