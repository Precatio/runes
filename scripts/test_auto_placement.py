import trimesh
import os
import numpy as np

from src.slice_analysis import find_auto_slice, create_mock_v_groove_mesh

def test_auto_placement():
    print("--- Testing Auto Placement (Auto-Slice) ---")
    
    mesh_path = 'test_runestone_groove_75deg.obj'
    
    if os.path.exists(mesh_path):
        print(f"Loading mesh: {mesh_path}")
        mesh = trimesh.load(mesh_path)
    else:
        print("Test mesh not found, using mock mesh...")
        mesh = create_mock_v_groove_mesh()
        
    print(f"Loaded mesh with {len(mesh.vertices)} vertices")
    
    # Let's test a few click points
    if mesh.bounds is not None:
        center = (mesh.bounds[0] + mesh.bounds[1]) / 2.0
        
        test_points = [
            center, # center
            center + np.array([5.0, 0, 0]),
            center + np.array([0, 5.0, 0])
        ]
        
        for i, pt in enumerate(test_points):
            print(f"\nTest {i+1} with click point {pt}:")
            p1, p2 = find_auto_slice(mesh, pt, radius=10.0)
            
            if p1 and p2:
                print("  SUCCESS! Auto placed points:")
                print(f"  P1: {p1}")
                print(f"  P2: {p2}")
            else:
                print("  FAILED! Not enough geometry near click point.")
    else:
        print("Mesh has no bounds.")

if __name__ == '__main__':
    test_auto_placement()
