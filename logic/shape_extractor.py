import numpy as np
from collections import defaultdict

def extract_shapes(index_map, metadata):
    """
    Extracts topological shapes (Vertices, Edges, Provinces) from the index map.
    """
    h, w = index_map.shape
    
    # Identify Segments
    # H_segs: boundary between (y-1, *) and (y, *)
    H_segs = np.zeros((h + 1, w), dtype=bool) 
    # V_segs: boundary between (*, x-1) and (*, x)
    V_segs = np.zeros((h, w + 1), dtype=bool) 
    
    # Internal boundaries
    H_segs[1:-1, :] = index_map[:-1, :] != index_map[1:, :]
    V_segs[:, 1:-1] = index_map[:, :-1] != index_map[:, 1:]
    
    # Frame boundaries
    H_segs[0, :] = True
    H_segs[h, :] = True
    V_segs[:, 0] = True
    V_segs[:, w] = True
    
    # Padded access for ease
    H_pad = np.zeros((h+1, w+2), dtype=bool)
    H_pad[:, 1:-1] = H_segs
    V_pad = np.zeros((h+2, w+1), dtype=bool)
    V_pad[1:-1, :] = V_segs
    
    node_indices = []
    final_vertices = {}
    
    # Find Nodes (degree != 2)
    for y in range(h + 1):
        for x in range(w + 1):
            deg = 0
            if H_pad[y, x]: deg += 1
            if H_pad[y, x+1]: deg += 1
            if V_pad[y, x]: deg += 1
            if V_pad[y+1, x]: deg += 1
            
            if deg != 2:
                vid = len(final_vertices)
                final_vertices[(y, x)] = vid
                node_indices.append((y, x))
                
    final_edges = []
    edge_id_counter = 0
    adj_provinces = defaultdict(set) # map ID -> set of edge IDs
    
    visited_h = np.zeros_like(H_segs, dtype=bool)
    visited_v = np.zeros_like(V_segs, dtype=bool)
    
    def get_provinces_for_seg(cy, cx, cdir):
        # cdir: 0=R, 1=D, 2=L, 3=U
        # Return p1, p2 (ids) bounding this segment
        p1, p2 = -1, -1
        if cdir == 0: # H_seg(cy, cx)
             p1 = -1 if cy == 0 else index_map[cy-1, cx]
             p2 = -1 if cy == h else index_map[cy, cx]
        elif cdir == 1: # V_seg(cy, cx)
             p1 = -1 if cx == 0 else index_map[cy, cx-1]
             p2 = -1 if cx == w else index_map[cy, cx]
        elif cdir == 2: # H_seg(cy, cx-1)
             p1 = -1 if cy == 0 else index_map[cy-1, cx-1]
             p2 = -1 if cy == h else index_map[cy, cx-1]
        elif cdir == 3: # V_seg(cy-1, cx)
             p1 = -1 if cx == 0 else index_map[cy-1, cx-1]
             p2 = -1 if cx == w else index_map[cy-1, cx]
        return p1, p2

    def trace(start_y, start_x, start_dir):
        cy, cx = start_y, start_x
        cdir = start_dir
        
        # Determine provinces for this edge (constant along simple edge between nodes?)
        # Actually provinces can change if we pass a T-junction, but a T-junction must be a NODE.
        # So between two Nodes, the provinces bounding the edge must be constant.
        p1, p2 = get_provinces_for_seg(cy, cx, cdir)
        
        while True:
            # Mark visited
            if cdir == 0: 
                if visited_h[cy, cx]: break
                visited_h[cy, cx] = True
                nx, ny = cx + 1, cy
            elif cdir == 1: 
                if visited_v[cy, cx]: break
                visited_v[cy, cx] = True
                nx, ny = cx, cy + 1
            elif cdir == 2: 
                if visited_h[cy, cx-1]: break
                visited_h[cy, cx-1] = True
                nx, ny = cx - 1, cy
            elif cdir == 3: 
                if visited_v[cy-1, cx]: break
                visited_v[cy-1, cx] = True
                nx, ny = cx, cy - 1
            
            # Check if Node
            if (ny, nx) in final_vertices:
                return nx, ny, p1, p2
            
            # Find next dir
            # Skip reverse direction
            rev = (cdir + 2) % 4
            found = False
            for d in range(4):
                if d == rev: continue
                has = False
                if d==0: has = H_pad[ny, nx+1]
                elif d==1: has = V_pad[ny+1, nx]
                elif d==2: has = H_pad[ny, nx]
                elif d==3: has = V_pad[ny, nx]
                
                if has:
                    cdir = d
                    cx, cy = nx, ny
                    found = True
                    break
            if not found: return nx, ny, p1, p2

        return cx, cy, p1, p2

    # Trace from Nodes
    for y, x in node_indices:
        # Check Right (0) and Down (1) only to avoid duplicates?
        # No, a node can have multiple edges starting.
        # H_pad is boolean.
        
        dirs = []
        if H_pad[y, x+1]: dirs.append(0)
        if V_pad[y+1, x]: dirs.append(1)
        if H_pad[y, x]: dirs.append(2)
        if V_pad[y, x]: dirs.append(3)
        
        for d in dirs:
            # Check if visited
            is_vis = False
            if d==0: is_vis = visited_h[y, x]
            elif d==1: is_vis = visited_v[y, x]
            elif d==2: is_vis = visited_h[y, x-1]
            elif d==3: is_vis = visited_v[y-1, x]
            
            if not is_vis:
                ex, ey, p1, p2 = trace(y, x, d)
                v1 = final_vertices[(y,x)]
                v2 = final_vertices[(ey, ex)]
                
                eid = edge_id_counter
                edge_id_counter += 1
                final_edges.append({"id": eid, "v1": v1, "v2": v2})
                
                if p1 != -1: adj_provinces[p1].add(eid)
                if p2 != -1: adj_provinces[p2].add(eid)

    # Detect Islands (Loops without nodes)
    # Scan horizontal segments
    for y in range(h+1):
        for x in range(w):
            if H_segs[y, x] and not visited_h[y, x]:
                # Found unvisited loop. Force a node.
                if (y,x) not in final_vertices:
                    vid = len(final_vertices)
                    final_vertices[(y,x)] = vid
                    # node_indices.append((y,x)) 
                
                ex, ey, p1, p2 = trace(y, x, 0)
                v1 = final_vertices[(y,x)]
                eid = edge_id_counter
                edge_id_counter += 1
                final_edges.append({"id": eid, "v1": v1, "v2": v1})
                if p1 != -1: adj_provinces[p1].add(eid)
                if p2 != -1: adj_provinces[p2].add(eid)

    # Format Output
    out_verts = [{"id": v, "x": k[1], "y": k[0]} for k, v in final_vertices.items()]
    out_provs = []
    
    for i, d in enumerate(metadata):
        pid = d.get("province_id", f"chk-{i}")
        edges = list(adj_provinces[i])
        out_provs.append({"id": pid, "edges": edges})
        
    return {
        "vertices": out_verts,
        "edges": final_edges,
        "provinces": out_provs
    }
