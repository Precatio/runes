import * as THREE from "three";

export const peelingVertexShader = `
  attribute float relativeDepth;
  varying float vDepth;
  varying float vRelativeDepth;
  void main() {
    vec4 worldPosition = modelMatrix * vec4(position, 1.0);
    vDepth = worldPosition.y;
    vRelativeDepth = relativeDepth;
    
    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
    gl_Position = projectionMatrix * mvPosition;
  }
`;

export const peelingFragmentShader = `
  varying float vDepth;
  varying float vRelativeDepth;
  uniform float uMinDepth;
  uniform float uMaxDepth;
  uniform float uMinRelativeDepth;
  uniform float uMaxRelativeDepth;
  
  uniform float uCutoffDepth;
  uniform float uLayerThickness;
  uniform float uOpacity;
  uniform int uSlicerMode;

  vec3 depthToColor(float depth, float cutoff, float minD, float maxD) {
    float t = clamp((cutoff - depth) / ((maxD - minD) * 0.1), 0.0, 1.0);
    return mix(vec3(0.9, 0.9, 0.9), vec3(0.1, 0.1, 0.2), t);
  }

  void main() {
    float activeDepth = vDepth;
    float minD = uMinDepth;
    float maxD = uMaxDepth;
    
    if (uSlicerMode == 1) {
      activeDepth = vRelativeDepth;
      minD = uMinRelativeDepth;
      maxD = uMaxRelativeDepth;
    }
  
    // 0 = högst upp (MaxDepth), 100 = längst ner (MinDepth)
    float sliceDepth = mix(maxD, minD, uCutoffDepth / 100.0);
    float thickness = (maxD - minD) * (uLayerThickness / 100.0);

    // 1. Kapa av toppen (Allt som är högre upp i världen än sliceDepth slängs)
    if (activeDepth > sliceDepth) {
      discard;
    }
    
    // 2. Kapa av botten (Skikttjocklek)
    if (activeDepth < (sliceDepth - thickness)) {
      discard;
    }

    vec3 color = depthToColor(activeDepth, sliceDepth, minD, maxD);
    
    gl_FragColor = vec4(color, uOpacity);
  }
`;

export function setUniforms(material: THREE.ShaderMaterial, values: Record<string, unknown>) {
  for (const [name, value] of Object.entries(values)) {
    material.uniforms[name].value = value;
  }
}
