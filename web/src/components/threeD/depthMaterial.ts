// Djupfärger i 3D-vyn (METHODS.md 2d4): the stone's ordinary lit material with the depth below the reference surface
// looked up per pixel (src/lib/depthField.ts). The light and the raking light stay, the colour lies on top; the peel
// slider and the contours are uniforms, so they move in real time.
import * as THREE from "three";
import type { DepthField } from "@/lib/depthField";

export interface DepthUniforms {
  [k: string]: THREE.IUniform;
}

export function makeDepthMaterial(): { material: THREE.MeshStandardMaterial; uniforms: DepthUniforms } {
  const uniforms: DepthUniforms = {
    uDepthTex: { value: null },
    uU: { value: new THREE.Vector3(1, 0, 0) },
    uV: { value: new THREE.Vector3(0, 1, 0) },
    uN: { value: new THREE.Vector3(0, 0, 1) },
    uOrigin: { value: new THREE.Vector2(0, 0) },
    uSize: { value: new THREE.Vector2(1, 1) },
    uEdges: { value: new THREE.Vector4(0.5, 1, 2, 3) },
    uC0: { value: new THREE.Color("#e9c46a") },
    uC1: { value: new THREE.Color("#f4a261") },
    uC2: { value: new THREE.Color("#b7410e") },
    uC3: { value: new THREE.Color("#5c1f05") },
    uStrength: { value: 0.85 },
    uPeel: { value: -5 },
    uPeelMode: { value: 0 },
    uPlane: { value: 1e9 },
    uContour: { value: 0 },
  };
  const material = new THREE.MeshStandardMaterial({ color: "#a0a5aa", roughness: 0.7, metalness: 0 });
  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = shader.vertexShader
      .replace("#include <common>", "#include <common>\nvarying vec3 vObjPos;\nvarying vec3 vObjNormal;")
      .replace("#include <begin_vertex>", "#include <begin_vertex>\nvObjPos = position;\nvObjNormal = normal;");
    shader.fragmentShader = shader.fragmentShader
      .replace("#include <common>", `#include <common>
uniform sampler2D uDepthTex;
uniform vec3 uU; uniform vec3 uV; uniform vec3 uN;
uniform vec2 uOrigin; uniform vec2 uSize;
uniform vec4 uEdges; uniform vec3 uC0; uniform vec3 uC1; uniform vec3 uC2; uniform vec3 uC3;
uniform float uStrength; uniform float uPeel; uniform int uPeelMode; uniform float uPlane; uniform float uContour;
varying vec3 vObjPos; varying vec3 vObjNormal;`)
      .replace("#include <color_fragment>", `#include <color_fragment>
{
  // a flat cut from the top along the view, as a 3D-print slicer: everything above the plane is gone
  if (uPeelMode == 1 && dot(vObjPos, uN) > uPlane) discard;
  vec2 uv = (vec2(dot(vObjPos, uU), dot(vObjPos, uV)) - uOrigin) / uSize;
  float d = -1000.0;
  // only the carved face (the side the depth is measured from), and only inside the grid
  if (gl_FrontFacing && dot(normalize(vObjNormal), uN) > 0.2 && uv.x >= 0.0 && uv.x <= 1.0 && uv.y >= 0.0 && uv.y <= 1.0)
    d = texture2D(uDepthTex, uv).r;
  if (d > -999.0) {
    if (uPeelMode == 0 && d < uPeel) {
      diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.94, 0.93, 0.91), 0.8);  // peeled off: pale
    } else if (d >= uEdges.x) {
      vec3 c = d >= uEdges.w ? uC3 : d >= uEdges.z ? uC2 : d >= uEdges.y ? uC1 : uC0;
      diffuseColor.rgb = mix(diffuseColor.rgb, c, uStrength);
    }
    if (uContour > 0.0) {
      float x = d / uContour;
      float f = abs(fract(x - 0.5) - 0.5) / max(fwidth(x), 1e-4);
      diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.08, 0.08, 0.1), (1.0 - min(f, 1.0)) * 0.7);
    }
  }
  if (!gl_FrontFacing) diffuseColor.rgb = vec3(0.22, 0.24, 0.27);  // the inside, seen through a flat cut
}`);
  };
  material.customProgramCacheKey = () => "vitki-depth-colour-1";
  return { material, uniforms };
}

/** The grid as a float texture (NaN → −1000, read as "no depth"). */
export function depthTexture(field: DepthField): THREE.DataTexture {
  const data = new Float32Array(field.depth.length);
  for (let i = 0; i < data.length; i++) data[i] = Number.isFinite(field.depth[i]) ? field.depth[i] : -1000;
  const tex = new THREE.DataTexture(data, field.width, field.height, THREE.RedFormat, THREE.FloatType);
  tex.minFilter = THREE.NearestFilter;
  tex.magFilter = THREE.NearestFilter;
  tex.needsUpdate = true;
  return tex;
}

/** The highest and lowest point of the model along n (for the flat cut's slider). */
export function heightRange(geometry: THREE.BufferGeometry, n: [number, number, number]): [number, number] {
  const p = geometry.attributes.position.array as ArrayLike<number>;
  let lo = Infinity, hi = -Infinity;
  for (let i = 0; i < p.length; i += 3) {
    const h = p[i] * n[0] + p[i + 1] * n[1] + p[i + 2] * n[2];
    if (h < lo) lo = h;
    if (h > hi) hi = h;
  }
  return [lo, hi];
}

/** Sets the depth material from the field and the panel (a function, so the component does not mutate its state). */
export function applyDepth(material: THREE.MeshStandardMaterial, u: DepthUniforms, v: {
  tex: THREE.Texture | null; field: DepthField; edges: [number, number, number, number]; strength: number; peel: number;
  plan: boolean; plane: number; contour: number;
}) {
  const f = v.field;
  u.uDepthTex.value = v.tex;
  (u.uU.value as THREE.Vector3).set(...f.u);
  (u.uV.value as THREE.Vector3).set(...f.v);
  (u.uN.value as THREE.Vector3).set(...f.n);
  (u.uOrigin.value as THREE.Vector2).set(f.origin[0], f.origin[1]);
  (u.uSize.value as THREE.Vector2).set(f.width * f.res_mm, f.height * f.res_mm);
  (u.uEdges.value as THREE.Vector4).set(...v.edges);
  u.uStrength.value = v.strength;
  u.uPeel.value = v.peel;
  u.uPeelMode.value = v.plan ? 1 : 0;
  u.uPlane.value = v.plane;
  u.uContour.value = v.contour;
  const side = v.plan ? THREE.DoubleSide : THREE.FrontSide;  // the inside shows through a flat cut
  if (material.side !== side) {
    material.side = side;
    material.needsUpdate = true;
  }
}
