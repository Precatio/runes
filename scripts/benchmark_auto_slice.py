import trimesh
import os
import time

from src.slice_analysis import find_auto_slice

def benchmark():
    mesh_path = 'So 113_1_4 thin_closed holes.stl'
    if not os.path.exists(mesh_path):
        print(f"File {mesh_path} not found.")
        return

    print(f"Loading {mesh_path}...")
    t0 = time.time()
    mesh = trimesh.load(mesh_path)
    t1 = time.time()
    print(f"Loaded mesh with {len(mesh.vertices):,} vertices in {t1-t0:.2f} seconds.")
    
    if mesh.bounds is not None:
        center = (mesh.bounds[0] + mesh.bounds[1]) / 2.0
        
        print("\nRunning auto_slice...")
        t2 = time.time()
        p1, p2 = find_auto_slice(mesh, center, radius=10.0)
        t3 = time.time()
        
        print(f"find_auto_slice took {t3-t2:.2f} seconds.")
        if p1 and p2:
            print("Auto placement successful!")
        else:
            print("Auto placement failed (not enough vertices in radius).")
            
if __name__ == '__main__':
    benchmark()
