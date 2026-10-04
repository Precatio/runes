import math
import random

def generate_obj(filename, width, height, resolution, groove_depth, groove_angle_deg):
    with open(filename, 'w') as f:
        f.write("# Simulated Runestone Groove\n")
        
        vertices = []
        # Calculate groove width at top based on depth and angle
        # tan(angle/2) = (groove_width / 2) / depth
        half_angle_rad = math.radians(groove_angle_deg / 2)
        half_groove_width = math.tan(half_angle_rad) * groove_depth
        
        # Center the groove at x=0
        for i in range(resolution + 1):
            for j in range(resolution + 1):
                x = -width/2 + (width * j / resolution)
                z = -height/2 + (height * i / resolution)
                
                # Add some noise to simulate rough stone
                y_noise = random.uniform(-0.1, 0.1)
                y = y_noise
                
                # Carve the V-groove along the Z axis (x = 0)
                if abs(x) < half_groove_width:
                    # Depth depends on distance from center
                    current_depth = groove_depth * (1 - abs(x)/half_groove_width)
                    y -= current_depth
                
                f.write(f"v {x:.4f} {y:.4f} {z:.4f}\n")
                vertices.append((x,y,z))
                
        # Write faces
        # resolution = number of quads per row/col, so resolution+1 vertices
        for i in range(resolution):
            for j in range(resolution):
                v1 = i * (resolution + 1) + j + 1
                v2 = v1 + 1
                v3 = v1 + (resolution + 1)
                v4 = v3 + 1
                
                # output two triangles per quad
                f.write(f"f {v1} {v2} {v3}\n")
                f.write(f"f {v2} {v4} {v3}\n")

if __name__ == '__main__':
    # Generate a 10x10 cm area, 100x100 resolution, groove depth 2cm, 75 degree angle
    generate_obj("test_runestone_groove_75deg.obj", 10.0, 10.0, 100, 2.0, 75.0)
    print("Created test_runestone_groove_75deg.obj")
