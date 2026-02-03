import numpy as np
import collections

def generate_rivers(shape_data, heightmap_image, province_data, river_threshold=10):
    """
    Generates rivers based on shape data (graph) and heightmap.
    Restricts river sources to high-elevation land.
    
    Args:
        shape_data (dict): Output from extract_shapes.
        heightmap_image (PIL.Image): Grayscale heightmap.
        province_data (list): Metadata list matching shape_data['provinces'].
        river_threshold (int): Flow threshold.
        
    Returns:
        river_edges (set): Set of edge IDs that are rivers.
        flow_map (dict): values of flow for edges.
    """
    if not shape_data or heightmap_image is None:
        return set(), {}
        
    vertices = shape_data['vertices']
    edges = shape_data['edges']
    provinces = shape_data['provinces']
    
    # --- 0. Identify Land Vertices & Edges ---
    vertex_provinces = collections.defaultdict(list) # vid -> [is_land]
    edge_is_bad = {} # eid -> bool (True if touches Ocean province)
    
    edge_to_verts = {e['id']: (e['v1'], e['v2']) for e in edges}
    
    # Track province types for edges
    # We want to exclude edges that border Ocean (Coastlines) or are in Ocean (Sea borders)
    # So if an edge belongs to ANY province that is Ocean, it is "bad".
    
    for i, prov in enumerate(provinces):
        p_type = "Land"
        if province_data and i < len(province_data):
             p_type = province_data[i].get("province_type", "Land")
        
        is_ocean = (p_type == "Ocean")
        is_land = not is_ocean
        
        for eid in prov['edges']:
            # If this edge belongs to an Ocean province, mark it bad
            if is_ocean:
                edge_is_bad[eid] = True
            elif eid not in edge_is_bad:
                edge_is_bad[eid] = False
                
            if eid in edge_to_verts:
                v1, v2 = edge_to_verts[eid]
                vertex_provinces[v1].append(is_land)
                vertex_provinces[v2].append(is_land)

    v_is_land = {} 
    for vid, flags in vertex_provinces.items():
        v_is_land[vid] = any(flags)

    # --- 1. Map Vertex Heights ---
    from scipy.ndimage import gaussian_filter
    
    base_hm_arr = np.array(heightmap_image.convert('L'), dtype=float)
    h_h, h_w = base_hm_arr.shape
    
    # Gaussian Blur for gradients - Increased to 3.0 for smoother, longer flow
    hm_arr = gaussian_filter(base_hm_arr, sigma=3.0)
    
    # Scaling logic
    max_vx = max(v['x'] for v in vertices) if vertices else 0
    max_vy = max(v['y'] for v in vertices) if vertices else 0
    
    scale_x = h_w / (max_vx + 1) if max_vx > 0 else 1.0
    scale_y = h_h / (max_vy + 1) if max_vy > 0 else 1.0
    need_scale = abs(scale_x - 1.0) > 0.01 or abs(scale_y - 1.0) > 0.01
    
    if need_scale:
        print(f"DEBUG: Scaling Heightmap Lookups: {scale_x:.2f}, {scale_y:.2f}")

    v_heights = {}
    land_heights = []
    
    for v in vertices:
        vid = v['id']
        vx, vy = float(v['x']), float(v['y'])
        
        if need_scale:
            vx *= scale_x
            vy *= scale_y
            
        vx = max(0, min(int(vx), h_w - 1))
        vy = max(0, min(int(vy), h_h - 1))
        
        val = float(hm_arr[vy, vx])
        v_heights[vid] = val
        
        if v_is_land.get(vid, False):
            land_heights.append(val)
            
    # Calculate Percentiles for Land
    source_threshold_height = 0
    if land_heights:
        # Relaxed to top 40% (60th percentile) to allow longer rivers starting lower
        source_threshold_height = np.percentile(land_heights, 60)
        print(f"DEBUG: Land Height Stats - Min: {min(land_heights):.1f}, Max: {max(land_heights):.1f}, Source Threshold (60%): {source_threshold_height:.1f}")
    else:
        print("DEBUG: No Land Vertices found.")

    # --- 2. Build Adjacency Graph ---
    adj = collections.defaultdict(list)
    for e in edges:
        v1, v2 = e['v1'], e['v2']
        eid = e['id']
        adj[v1].append((v2, eid))
        adj[v2].append((v1, eid))

    # --- 3. Calculate Flow Direction ---
    downstream = {}
    
    for vid, neighbours in adj.items():
        if not v_is_land.get(vid, False):
            continue
            
        my_h = v_heights[vid]
        best_n = None
        max_drop = 0.0
        
        for nid, eid in neighbours:
            n_h = v_heights[nid]
            drop = my_h - n_h
            if drop > 0.0001:
                if drop > max_drop:
                    max_drop = drop
                    best_n = (nid, eid)
        
        if best_n:
            downstream[vid] = best_n
            
    # --- 4. Accumulate Flow ---
    sorted_vids = sorted(v_heights.keys(), key=lambda k: v_heights[k], reverse=True)
    
    v_flow = collections.defaultdict(float)
    
    sources_count = 0
    for vid in v_heights:
        is_land = v_is_land.get(vid, False)
        h = v_heights[vid]
        
        if is_land and h >= source_threshold_height:
            v_flow[vid] = 1.0 
            sources_count += 1
        else:
            v_flow[vid] = 0.0
            
    print(f"DEBUG: River Sources: {sources_count} vertices")
            
    edge_flow = collections.defaultdict(float)
    
    max_flow = 0
    for vid in sorted_vids:
        if vid in downstream:
            target_vid, eid = downstream[vid]
            flow = v_flow[vid]
            
            if flow > 0:
                v_flow[target_vid] += flow
                edge_flow[eid] += flow
                if edge_flow[eid] > max_flow:
                    max_flow = edge_flow[eid]
            
    print(f"DEBUG: Max Flow accumulated: {max_flow}")
            
    # --- 5. Filter Rivers ---
    river_edges = set()
    for eid, flow in edge_flow.items():
        # strict check: must meet threshold AND not be bad edge
        if flow >= river_threshold:
            if not edge_is_bad.get(eid, False):
                river_edges.add(eid)
            
    return river_edges, edge_flow
