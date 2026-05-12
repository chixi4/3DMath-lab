import * as THREE from "three";
import "./style.css";

const R = 1.75;
const CYLINDER_LENGTH = 2.75;
const AXIS_LENGTH = 3.35;
const FULL_AXIS_LENGTH = 3.55;
const DURATION = 34.0;
const X_SLICE = 0.92;
const LETTER_SIZE = 148;
const LETTER_HEIGHT = 0.40;
const COLORS = {
  axis: "#fff8ea",
  blue: "#39cfff",
  blueLine: "#7fdfff",
  pink: "#ff73d8",
  pinkLine: "#ffb0e8",
  yellow: "#fff28a",
  white: "#fff9ee",
  muted: "#b5b0a2",
};
const OCTANT_DEFINITIONS = [
  { label: "blue-front", sx: 1, sy: 1, sz: 1, color: "#34d6ff", flash: "#96ecff" },
  { label: "blue-back", sx: -1, sy: 1, sz: 1, color: "#168dff", flash: "#96ecff" },
  { label: "pink-front", sx: 1, sy: 1, sz: -1, color: "#ff75d8", flash: "#ffc0f0" },
  { label: "pink-back", sx: -1, sy: 1, sz: -1, color: "#c56cff", flash: "#ffc0f0" },
  { label: "orange-front", sx: 1, sy: -1, sz: 1, color: "#ffd166", flash: "#ffe39a" },
  { label: "orange-back", sx: -1, sy: -1, sz: 1, color: "#ff9f5a", flash: "#ffe39a" },
  { label: "green-front", sx: 1, sy: -1, sz: -1, color: "#7cf29c", flash: "#b5ffc8" },
  { label: "green-back", sx: -1, sy: -1, sz: -1, color: "#2dd4bf", flash: "#b5ffc8" },
];

const canvas = document.querySelector("#scene");
const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  alpha: false,
  preserveDrawingBuffer: true,
});
renderer.setClearColor("#05070b", 1);
renderer.outputColorSpace = THREE.SRGBColorSpace;

const scene = new THREE.Scene();
const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.01, 100);
camera.up.set(0, 0, 1);

const root = new THREE.Group();
const axesGroup = new THREE.Group();
const axisXGroup = new THREE.Group();
const axisYGroup = new THREE.Group();
const axisZGroup = new THREE.Group();
const cylinderZGroup = new THREE.Group();
const cylinderYGroup = new THREE.Group();
const remnantGroup = new THREE.Group();
const tentGroup = new THREE.Group();
const firstOctantMarkerGroup = new THREE.Group();
const surfaceGuideGroup = new THREE.Group();
const projectionDetailGroup = new THREE.Group();
const domainFormulaGroup = new THREE.Group();
const annotationGroup = new THREE.Group();
const symmetryAxesGroup = new THREE.Group();
const fullCylinderGroup = new THREE.Group();
const fullCylinderZGrowGroup = new THREE.Group();
const fullCylinderYGrowGroup = new THREE.Group();
const octantGroup = new THREE.Group();
const octantBlocks = [];

scene.add(root);
axesGroup.add(axisXGroup, axisYGroup, axisZGroup);
root.add(
  fullCylinderGroup,
  octantGroup,
  cylinderZGroup,
  cylinderYGroup,
  remnantGroup,
  tentGroup,
  firstOctantMarkerGroup,
  surfaceGuideGroup,
  projectionDetailGroup,
  axesGroup,
  symmetryAxesGroup,
  annotationGroup,
  domainFormulaGroup,
);

function clamp01(value) {
  return Math.min(1, Math.max(0, value));
}

function smootherstep(value) {
  const t = clamp01(value);
  return t * t * t * (t * (t * 6 - 15) + 10);
}

function interval(t, start, end) {
  if (t <= start) return 0;
  if (t >= end) return 1;
  return smootherstep((t - start) / (end - start));
}

function radiusHeight(x) {
  return Math.sqrt(Math.max(R * R - x * x, 0));
}

function v(x, y, z) {
  return new THREE.Vector3(x, y, z);
}

function setMaterialBase(object, opacity) {
  object.userData.baseOpacity = opacity;
  if (object.material) {
    object.material.userData.baseOpacity = opacity;
  }
}

function setGroupOpacity(group, alpha) {
  const scale = clamp01(alpha);
  group.visible = scale > 0.003;
  group.traverse((object) => {
    const material = object.material;
    if (!material) return;
    const materials = Array.isArray(material) ? material : [material];
    for (const mat of materials) {
      const base = mat.userData.baseOpacity ?? object.userData.baseOpacity ?? mat.opacity ?? 1;
      mat.opacity = base * scale;
      mat.transparent = mat.opacity < 0.999;
      mat.needsUpdate = true;
    }
  });
}

function makeBasicMaterial(color, opacity, extra = {}) {
  const material = new THREE.MeshBasicMaterial({
    color,
    transparent: opacity < 1,
    opacity,
    side: THREE.DoubleSide,
    depthWrite: false,
    ...extra,
  });
  material.userData.baseOpacity = opacity;
  return material;
}

function makeLineMaterial(color, opacity, dashed = false) {
  const params = {
    color,
    transparent: opacity < 1,
    opacity,
    depthWrite: false,
    depthTest: false,
  };
  const material = dashed
    ? new THREE.LineDashedMaterial({ ...params, dashSize: 0.105, gapSize: 0.065 })
    : new THREE.LineBasicMaterial(params);
  material.userData.baseOpacity = opacity;
  return material;
}

function makeSurfaceGeometry(uSegments, vSegments, pointAt) {
  const positions = [];
  const indices = [];
  for (let i = 0; i <= uSegments; i += 1) {
    const u = i / uSegments;
    for (let j = 0; j <= vSegments; j += 1) {
      const vv = j / vSegments;
      const point = pointAt(u, vv);
      positions.push(point.x, point.y, point.z);
    }
  }
  const row = vSegments + 1;
  for (let i = 0; i < uSegments; i += 1) {
    for (let j = 0; j < vSegments; j += 1) {
      const a = i * row + j;
      const b = (i + 1) * row + j;
      const c = (i + 1) * row + j + 1;
      const d = i * row + j + 1;
      indices.push(a, b, d, b, c, d);
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return geometry;
}

function makeMeshSurface(uSegments, vSegments, pointAt, color, opacity, renderOrder = 1) {
  const mesh = new THREE.Mesh(makeSurfaceGeometry(uSegments, vSegments, pointAt), makeBasicMaterial(color, opacity));
  mesh.renderOrder = renderOrder;
  setMaterialBase(mesh, opacity);
  return mesh;
}

function makeTube(points, color, radius = 0.012, opacity = 1, renderOrder = 12) {
  const curve = new THREE.CatmullRomCurve3(points);
  const geometry = new THREE.TubeGeometry(curve, Math.max(8, points.length * 3), radius, 8, false);
  const mesh = new THREE.Mesh(geometry, makeBasicMaterial(color, opacity));
  mesh.renderOrder = renderOrder;
  setMaterialBase(mesh, opacity);
  return mesh;
}

function sampleCurve(fn, count = 96) {
  const points = [];
  for (let i = 0; i < count; i += 1) {
    points.push(fn(i / (count - 1)));
  }
  return points;
}

function makeDashedLine(points, color, opacity = 0.55) {
  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  const line = new THREE.Line(geometry, makeLineMaterial(color, opacity, true));
  line.computeLineDistances();
  line.renderOrder = 8;
  setMaterialBase(line, opacity);
  return line;
}

function makeCylinderBetween(start, end, radius, color, opacity = 1) {
  const direction = new THREE.Vector3().subVectors(end, start);
  const length = direction.length();
  const geometry = new THREE.CylinderGeometry(radius, radius, length, 14, 1);
  const mesh = new THREE.Mesh(geometry, makeBasicMaterial(color, opacity, { depthTest: false }));
  mesh.position.copy(start).addScaledVector(direction, 0.5);
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.normalize());
  mesh.renderOrder = 20;
  setMaterialBase(mesh, opacity);
  return mesh;
}

function makeConeAt(tip, direction, radius, height, color) {
  const geometry = new THREE.ConeGeometry(radius, height, 24, 1);
  const mesh = new THREE.Mesh(geometry, makeBasicMaterial(color, 1, { depthTest: false }));
  const dir = direction.clone().normalize();
  mesh.position.copy(tip).addScaledVector(dir, -height * 0.5);
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
  mesh.renderOrder = 21;
  setMaterialBase(mesh, 1);
  return mesh;
}

function createTextSprite(text, options = {}) {
  const size = options.size ?? 96;
  const italic = options.italic ?? true;
  const color = options.color ?? COLORS.white;
  const canvasText = document.createElement("canvas");
  const context = canvasText.getContext("2d");
  const font = `${italic ? "italic " : ""}${size}px "Times New Roman", "Songti SC", serif`;
  context.font = font;
  const metrics = context.measureText(text);
  const width = Math.ceil(metrics.width + size * 0.52);
  const height = Math.ceil(size * 1.42);
  canvasText.width = width;
  canvasText.height = height;
  context.font = font;
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.lineJoin = "round";
  context.strokeStyle = "rgba(0, 0, 0, 0.64)";
  context.lineWidth = Math.max(2, Math.round(size * 0.035));
  context.fillStyle = color;
  context.strokeText(text, width / 2, height / 2 + size * 0.02);
  context.fillText(text, width / 2, height / 2 + size * 0.02);

  const texture = new THREE.CanvasTexture(canvasText);
  texture.colorSpace = THREE.SRGBColorSpace;
  const material = new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    opacity: options.opacity ?? 1,
    depthTest: false,
    depthWrite: false,
    alphaTest: 0.01,
  });
  material.userData.baseOpacity = options.opacity ?? 1;
  const sprite = new THREE.Sprite(material);
  const worldHeight = options.height ?? 0.25;
  sprite.scale.set((worldHeight * width) / height, worldHeight, 1);
  sprite.renderOrder = options.renderOrder ?? 50;
  setMaterialBase(sprite, options.opacity ?? 1);
  return sprite;
}

function createRootFormulaSprite(options = {}) {
  return createTextSprite("y=√(R²−x²)", {
    size: options.size ?? 118,
    height: options.height ?? 0.34,
    color: options.color ?? COLORS.white,
    opacity: options.opacity ?? 1,
    renderOrder: options.renderOrder ?? 55,
  });
}

function addAxis(group, direction, label, labelPosition) {
  const dir = direction.clone().normalize();
  const end = dir.clone().multiplyScalar(AXIS_LENGTH);
  group.add(makeCylinderBetween(v(0, 0, 0), end.clone().addScaledVector(dir, -0.16), 0.009, COLORS.axis, 0.92));
  group.add(makeConeAt(end, dir, 0.052, 0.20, COLORS.axis));
  const sprite = createTextSprite(label, { size: LETTER_SIZE, height: LETTER_HEIGHT });
  sprite.position.copy(labelPosition);
  group.add(sprite);
}

function buildAxes() {
  addAxis(axisXGroup, v(1, 0, 0), "x", v(AXIS_LENGTH + 0.34, -0.12, -0.12));
  addAxis(axisYGroup, v(0, 1, 0), "y", v(0.18, AXIS_LENGTH - 0.36, -0.06));
  addAxis(axisZGroup, v(0, 0, 1), "z", v(0.18, -0.07, AXIS_LENGTH - 0.43));
}

function buildQuarterCylinders() {
  cylinderZGroup.add(makeMeshSurface(42, 10, (u, s) => {
    const theta = u * Math.PI * 0.5;
    const radius = s * R;
    return v(radius * Math.cos(theta), radius * Math.sin(theta), 0);
  }, COLORS.blue, 0.24, 1));
  cylinderZGroup.add(makeMeshSurface(42, 10, (u, s) => {
    const theta = u * Math.PI * 0.5;
    const radius = s * R;
    return v(radius * Math.cos(theta), radius * Math.sin(theta), CYLINDER_LENGTH);
  }, COLORS.blue, 0.20, 1));
  cylinderZGroup.add(makeMeshSurface(1, 1, (u, s) => v(u * R, 0, s * CYLINDER_LENGTH), "#2289ff", 0.18, 1));
  cylinderZGroup.add(makeMeshSurface(1, 1, (u, s) => v(0, u * R, s * CYLINDER_LENGTH), "#65e8ff", 0.18, 1));

  const zSurface = makeMeshSurface(
    64,
    18,
    (u, s) => {
      const theta = u * Math.PI * 0.5;
      return v(R * Math.cos(theta), R * Math.sin(theta), s * CYLINDER_LENGTH);
    },
    COLORS.blue,
    0.38,
    2,
  );
  cylinderZGroup.add(zSurface);
  for (const zVal of [0, CYLINDER_LENGTH]) {
    cylinderZGroup.add(makeTube(sampleCurve((u) => {
      const theta = u * Math.PI * 0.5;
      return v(R * Math.cos(theta), R * Math.sin(theta), zVal);
    }), COLORS.blueLine, 0.008, 0.86, 14));
    if (zVal === 0) {
      cylinderZGroup.add(makeTube([v(0, 0, zVal), v(R, 0, zVal)], COLORS.blueLine, 0.006, 0.70, 13));
      cylinderZGroup.add(makeTube([v(0, 0, zVal), v(0, R, zVal)], COLORS.blueLine, 0.006, 0.70, 13));
    } else {
      cylinderZGroup.add(makeDashedLine([v(0, 0, zVal), v(R, 0, zVal)], COLORS.blueLine, 0.64));
      cylinderZGroup.add(makeDashedLine([v(0, 0, zVal), v(0, R, zVal)], COLORS.blueLine, 0.64));
    }
  }
  cylinderZGroup.add(makeTube([v(0, 0, 0), v(0, 0, CYLINDER_LENGTH)], COLORS.blueLine, 0.006, 0.48, 13));
  for (const theta of [0, Math.PI / 2]) {
    cylinderZGroup.add(makeTube([v(R * Math.cos(theta), R * Math.sin(theta), 0), v(R * Math.cos(theta), R * Math.sin(theta), CYLINDER_LENGTH)], COLORS.blueLine, 0.006, 0.56, 13));
  }
  cylinderZGroup.add(makeDashedLine([v(R * Math.cos(Math.PI / 4), R * Math.sin(Math.PI / 4), 0), v(R * Math.cos(Math.PI / 4), R * Math.sin(Math.PI / 4), CYLINDER_LENGTH)], COLORS.blueLine, 0.58));
  cylinderZGroup.add(makeDashedLine([v(R, 0, 0), v(R, 0, CYLINDER_LENGTH)], COLORS.blueLine, 0.52));
  cylinderZGroup.add(makeDashedLine([v(0, R, 0), v(0, R, CYLINDER_LENGTH)], COLORS.blueLine, 0.52));

  cylinderYGroup.add(makeMeshSurface(42, 10, (u, s) => {
    const theta = u * Math.PI * 0.5;
    const radius = s * R;
    return v(radius * Math.cos(theta), 0, radius * Math.sin(theta));
  }, COLORS.pink, 0.23, 1));
  cylinderYGroup.add(makeMeshSurface(42, 10, (u, s) => {
    const theta = u * Math.PI * 0.5;
    const radius = s * R;
    return v(radius * Math.cos(theta), CYLINDER_LENGTH, radius * Math.sin(theta));
  }, COLORS.pink, 0.19, 1));
  cylinderYGroup.add(makeMeshSurface(1, 1, (u, s) => v(u * R, s * CYLINDER_LENGTH, 0), "#ff77cb", 0.18, 1));
  cylinderYGroup.add(makeMeshSurface(1, 1, (u, s) => v(0, s * CYLINDER_LENGTH, u * R), "#d59aff", 0.18, 1));

  const ySurface = makeMeshSurface(
    64,
    18,
    (u, s) => {
      const theta = u * Math.PI * 0.5;
      return v(R * Math.cos(theta), s * CYLINDER_LENGTH, R * Math.sin(theta));
    },
    COLORS.pink,
    0.36,
    3,
  );
  cylinderYGroup.add(ySurface);
  for (const yVal of [0, CYLINDER_LENGTH]) {
    cylinderYGroup.add(makeTube(sampleCurve((u) => {
      const theta = u * Math.PI * 0.5;
      return v(R * Math.cos(theta), yVal, R * Math.sin(theta));
    }), COLORS.pinkLine, 0.008, 0.84, 14));
    if (yVal === 0) {
      cylinderYGroup.add(makeTube([v(0, yVal, 0), v(R, yVal, 0)], COLORS.pinkLine, 0.006, 0.68, 13));
      cylinderYGroup.add(makeTube([v(0, yVal, 0), v(0, yVal, R)], COLORS.pinkLine, 0.006, 0.68, 13));
    } else {
      cylinderYGroup.add(makeDashedLine([v(0, yVal, 0), v(R, yVal, 0)], COLORS.pinkLine, 0.62));
      cylinderYGroup.add(makeDashedLine([v(0, yVal, 0), v(0, yVal, R)], COLORS.pinkLine, 0.62));
    }
  }
  cylinderYGroup.add(makeTube([v(0, 0, 0), v(0, CYLINDER_LENGTH, 0)], COLORS.pinkLine, 0.006, 0.46, 13));
  for (const theta of [0, Math.PI / 2]) {
    cylinderYGroup.add(makeTube([v(R * Math.cos(theta), 0, R * Math.sin(theta)), v(R * Math.cos(theta), CYLINDER_LENGTH, R * Math.sin(theta))], COLORS.pinkLine, 0.006, 0.54, 13));
  }
  cylinderYGroup.add(makeDashedLine([v(R * Math.cos(Math.PI / 4), 0, R * Math.sin(Math.PI / 4)), v(R * Math.cos(Math.PI / 4), CYLINDER_LENGTH, R * Math.sin(Math.PI / 4))], COLORS.pinkLine, 0.56));
  cylinderYGroup.add(makeDashedLine([v(R, 0, 0), v(R, CYLINDER_LENGTH, 0)], COLORS.pinkLine, 0.50));
  cylinderYGroup.add(makeDashedLine([v(0, 0, R), v(0, CYLINDER_LENGTH, R)], COLORS.pinkLine, 0.50));
}

function buildTent() {
  tentGroup.add(makeMeshSurface(90, 20, (u, s) => {
    const x = u * R;
    const h = radiusHeight(x);
    return v(x, s * h, h);
  }, COLORS.blue, 0.48, 5));

  tentGroup.add(makeMeshSurface(90, 20, (u, s) => {
    const x = u * R;
    const h = radiusHeight(x);
    return v(x, h, s * h);
  }, COLORS.pink, 0.43, 6));

  tentGroup.add(makeMeshSurface(72, 12, (u, s) => {
    const x = u * R;
    const h = radiusHeight(x);
    return v(x, s * h, 0);
  }, "#2478ff", 0.18, 4));

  tentGroup.add(makeMeshSurface(72, 12, (u, s) => {
    const x = u * R;
    const h = radiusHeight(x);
    return v(x, 0, s * h);
  }, "#ff91df", 0.16, 4));

  tentGroup.add(makeMeshSurface(1, 1, (u, s) => v(0, u * R, s * R), "#9bb3ff", 0.18, 4));

  const topEdge = sampleCurve((u) => {
    const x = u * R;
    const h = radiusHeight(x);
    return v(x, h, h);
  });
  const floorArc = sampleCurve((u) => {
    const x = u * R;
    return v(x, radiusHeight(x), 0);
  });
  const frontArc = sampleCurve((u) => {
    const x = u * R;
    return v(x, 0, radiusHeight(x));
  });
  tentGroup.add(makeTube(topEdge, COLORS.white, 0.012, 0.98, 18));
  tentGroup.add(makeTube(floorArc, "#bff5ff", 0.010, 0.92, 18));
  tentGroup.add(makeTube(frontArc, "#ffd1f2", 0.010, 0.88, 18));
  tentGroup.add(makeTube([v(0, 0, 0), v(R, 0, 0)], COLORS.white, 0.008, 0.78, 17));
  tentGroup.add(makeTube([v(0, 0, 0), v(0, R, 0)], "#bff5ff", 0.008, 0.88, 17));
  tentGroup.add(makeTube([v(0, 0, 0), v(0, 0, R)], "#ffd1f2", 0.008, 0.86, 17));
  tentGroup.add(makeTube([v(0, R, 0), v(0, R, R)], COLORS.white, 0.007, 0.82, 17));
  tentGroup.add(makeTube([v(0, 0, R), v(0, R, R)], COLORS.white, 0.007, 0.82, 17));

  for (const ratio of [0.28, 0.55, 0.80]) {
    surfaceGuideGroup.add(makeTube(sampleCurve((u) => {
      const x = u * R;
      const h = radiusHeight(x);
      return v(x, ratio * h, h);
    }), "#a4f1ff", 0.0045, 0.34, 16));
    surfaceGuideGroup.add(makeTube(sampleCurve((u) => {
      const x = u * R;
      const h = radiusHeight(x);
      return v(x, h, ratio * h);
    }), "#ffc2ee", 0.0045, 0.32, 16));
  }

  const h = radiusHeight(X_SLICE);
  projectionDetailGroup.add(makeTube([v(X_SLICE, 0, 0.012), v(X_SLICE, h, 0.012)], COLORS.white, 0.0055, 0.80, 25));
  const xLabel = createTextSprite("x", { size: LETTER_SIZE, height: LETTER_HEIGHT });
  xLabel.position.copy(v(X_SLICE, -0.17, 0.03));
  projectionDetailGroup.add(xLabel);
}

function buildFirstOctantMarker() {
  const red = "#ff3b30";
  firstOctantMarkerGroup.add(makeMeshSurface(72, 16, (u, s) => {
    const x = u * R;
    const h = radiusHeight(x);
    return v(x, s * h, h);
  }, red, 0.30, 58));

  firstOctantMarkerGroup.add(makeMeshSurface(72, 16, (u, s) => {
    const x = u * R;
    const h = radiusHeight(x);
    return v(x, h, s * h);
  }, red, 0.28, 59));

  firstOctantMarkerGroup.add(makeMeshSurface(1, 1, (u, s) => v(0, u * R, s * R), red, 0.20, 57));
  firstOctantMarkerGroup.add(makeMeshSurface(72, 10, (u, s) => {
    const x = u * R;
    return v(x, s * radiusHeight(x), 0);
  }, red, 0.18, 57));
  firstOctantMarkerGroup.add(makeMeshSurface(72, 10, (u, s) => {
    const x = u * R;
    return v(x, 0, s * radiusHeight(x));
  }, red, 0.18, 57));

  firstOctantMarkerGroup.add(makeTube(sampleCurve((u) => {
    const x = u * R;
    const h = radiusHeight(x);
    return v(x, h, h);
  }), "#ffb1aa", 0.011, 0.95, 76));
}

function buildRemnants() {
  remnantGroup.add(makeDashedLine(sampleCurve((u) => {
    const theta = u * Math.PI * 0.5;
    return v(R * Math.cos(theta), R * Math.sin(theta), CYLINDER_LENGTH);
  }), COLORS.blueLine, 0.58));
  remnantGroup.add(makeDashedLine([v(0, 0, CYLINDER_LENGTH), v(R, 0, CYLINDER_LENGTH)], COLORS.blueLine, 0.44));
  remnantGroup.add(makeDashedLine([v(0, 0, CYLINDER_LENGTH), v(0, R, CYLINDER_LENGTH)], COLORS.blueLine, 0.44));
  remnantGroup.add(makeDashedLine([v(0, 0, 0), v(0, 0, CYLINDER_LENGTH)], COLORS.blueLine, 0.34));
  remnantGroup.add(makeDashedLine([v(0, 0, 0), v(R, 0, 0)], COLORS.blueLine, 0.34));
  remnantGroup.add(makeDashedLine([v(0, 0, 0), v(0, R, 0)], COLORS.blueLine, 0.34));
  remnantGroup.add(makeDashedLine([v(R, 0, 0), v(R, 0, CYLINDER_LENGTH)], COLORS.blueLine, 0.48));
  remnantGroup.add(makeDashedLine([v(0, R, 0), v(0, R, CYLINDER_LENGTH)], COLORS.blueLine, 0.48));

  remnantGroup.add(makeDashedLine(sampleCurve((u) => {
    const theta = u * Math.PI * 0.5;
    return v(R * Math.cos(theta), CYLINDER_LENGTH, R * Math.sin(theta));
  }), COLORS.pinkLine, 0.56));
  remnantGroup.add(makeDashedLine([v(0, CYLINDER_LENGTH, 0), v(R, CYLINDER_LENGTH, 0)], COLORS.pinkLine, 0.43));
  remnantGroup.add(makeDashedLine([v(0, CYLINDER_LENGTH, 0), v(0, CYLINDER_LENGTH, R)], COLORS.pinkLine, 0.43));
  remnantGroup.add(makeDashedLine([v(0, 0, 0), v(0, CYLINDER_LENGTH, 0)], COLORS.pinkLine, 0.32));
  remnantGroup.add(makeDashedLine([v(0, 0, 0), v(R, 0, 0)], COLORS.pinkLine, 0.32));
  remnantGroup.add(makeDashedLine([v(0, 0, 0), v(0, 0, R)], COLORS.pinkLine, 0.32));
  remnantGroup.add(makeDashedLine([v(R, 0, 0), v(R, CYLINDER_LENGTH, 0)], COLORS.pinkLine, 0.46));
  remnantGroup.add(makeDashedLine([v(0, 0, R), v(0, CYLINDER_LENGTH, R)], COLORS.pinkLine, 0.46));
}

function buildAnnotations() {
  const entries = [
    ["O", v(-0.16, -0.14, 0.10)],
    ["D", v(0.58, 0.58, 0.07)],
    ["R", v(R + 0.18, -0.16, -0.07)],
    ["R", v(-0.20, R + 0.10, -0.06)],
  ];
  for (const [text, position] of entries) {
    const sprite = createTextSprite(text, { size: LETTER_SIZE, height: LETTER_HEIGHT });
    sprite.position.copy(position);
    annotationGroup.add(sprite);
  }

  const formula = createRootFormulaSprite({ size: 118, height: 0.34 });
  formula.position.copy(v(1.70, 1.56, 0.06));
  domainFormulaGroup.add(formula);
}

function addSymmetryAxis(direction, label, labelPosition) {
  const dir = direction.clone().normalize();
  const start = dir.clone().multiplyScalar(-FULL_AXIS_LENGTH);
  const end = dir.clone().multiplyScalar(FULL_AXIS_LENGTH);
  const shaft = makeCylinderBetween(start.clone().addScaledVector(dir, 0.18), end.clone().addScaledVector(dir, -0.18), 0.007, COLORS.axis, 0.78);
  const cone = makeConeAt(end, dir, 0.046, 0.18, COLORS.axis);
  shaft.renderOrder = 72;
  cone.renderOrder = 73;
  symmetryAxesGroup.add(shaft);
  symmetryAxesGroup.add(cone);
  const sprite = createTextSprite(label, { size: LETTER_SIZE, height: LETTER_HEIGHT });
  sprite.position.copy(labelPosition);
  sprite.renderOrder = 74;
  symmetryAxesGroup.add(sprite);
}

function buildSymmetryAxes() {
  addSymmetryAxis(v(1, 0, 0), "x", v(FULL_AXIS_LENGTH + 1.00, -0.28, -0.20));
  addSymmetryAxis(v(0, 1, 0), "y", v(0.18, FULL_AXIS_LENGTH + 0.46, -0.08));
  addSymmetryAxis(v(0, 0, 1), "z", v(0.22, -0.08, FULL_AXIS_LENGTH + 0.22));
}

function buildFullCylinders() {
  fullCylinderZGrowGroup.position.z = -CYLINDER_LENGTH;
  fullCylinderYGrowGroup.position.y = -CYLINDER_LENGTH;
  fullCylinderGroup.add(fullCylinderZGrowGroup, fullCylinderYGrowGroup);

  fullCylinderZGrowGroup.add(makeMeshSurface(120, 22, (u, s) => {
    const theta = u * Math.PI * 2;
    return v(R * Math.cos(theta), R * Math.sin(theta), s * 2 * CYLINDER_LENGTH);
  }, COLORS.blue, 0.18, 1));
  for (const zVal of [0, 2 * CYLINDER_LENGTH]) {
    fullCylinderZGrowGroup.add(makeMeshSurface(96, 10, (u, s) => {
      const theta = u * Math.PI * 2;
      return v(s * R * Math.cos(theta), s * R * Math.sin(theta), zVal);
    }, COLORS.blue, 0.075, 1));
  }

  fullCylinderYGrowGroup.add(makeMeshSurface(120, 22, (u, s) => {
    const theta = u * Math.PI * 2;
    return v(R * Math.cos(theta), s * 2 * CYLINDER_LENGTH, R * Math.sin(theta));
  }, COLORS.pink, 0.17, 1));
  for (const yVal of [0, 2 * CYLINDER_LENGTH]) {
    fullCylinderYGrowGroup.add(makeMeshSurface(96, 10, (u, s) => {
      const theta = u * Math.PI * 2;
      return v(s * R * Math.cos(theta), yVal, s * R * Math.sin(theta));
    }, COLORS.pink, 0.070, 1));
  }

  for (const zVal of [0, 2 * CYLINDER_LENGTH]) {
    fullCylinderZGrowGroup.add(makeTube(sampleCurve((u) => {
      const theta = u * Math.PI * 2;
      return v(R * Math.cos(theta), R * Math.sin(theta), zVal);
    }, 128), COLORS.blueLine, 0.006, 0.50, 10));
  }
  for (const yVal of [0, 2 * CYLINDER_LENGTH]) {
    fullCylinderYGrowGroup.add(makeTube(sampleCurve((u) => {
      const theta = u * Math.PI * 2;
      return v(R * Math.cos(theta), yVal, R * Math.sin(theta));
    }, 128), COLORS.pinkLine, 0.006, 0.48, 10));
  }
  for (const theta of [0, Math.PI / 2, Math.PI, Math.PI * 1.5]) {
    fullCylinderZGrowGroup.add(makeTube([v(R * Math.cos(theta), R * Math.sin(theta), 0), v(R * Math.cos(theta), R * Math.sin(theta), 2 * CYLINDER_LENGTH)], COLORS.blueLine, 0.0045, 0.28, 9));
    fullCylinderYGrowGroup.add(makeTube([v(R * Math.cos(theta), 0, R * Math.sin(theta)), v(R * Math.cos(theta), 2 * CYLINDER_LENGTH, R * Math.sin(theta))], COLORS.pinkLine, 0.0045, 0.26, 9));
  }
}

function buildOctantBlocks() {
  OCTANT_DEFINITIONS.forEach(({ label, sx, sy, sz, color, flash }, index) => {
    const block = new THREE.Group();
    const order = 34 + index;
    const pointX = (x) => sx * x;
    const pointY = (y) => sy * y;
    const pointZ = (z) => sz * z;
    const highlightGroup = new THREE.Group();

    block.add(makeMeshSurface(72, 16, (u, s) => {
      const x = u * R;
      const h = radiusHeight(x);
      return v(pointX(x), pointY(s * h), pointZ(h));
    }, color, 0.40, order));
    block.add(makeMeshSurface(72, 16, (u, s) => {
      const x = u * R;
      const h = radiusHeight(x);
      return v(pointX(x), pointY(h), pointZ(s * h));
    }, color, 0.37, order + 1));
    block.add(makeMeshSurface(1, 1, (u, s) => v(0, pointY(u * R), pointZ(s * R)), color, 0.26, order - 1));
    block.add(makeMeshSurface(72, 10, (u, s) => {
      const x = u * R;
      return v(pointX(x), pointY(s * radiusHeight(x)), 0);
    }, color, 0.24, order - 1));
    block.add(makeMeshSurface(72, 10, (u, s) => {
      const x = u * R;
      return v(pointX(x), 0, pointZ(s * radiusHeight(x)));
    }, color, 0.24, order - 1));

    block.add(makeTube(sampleCurve((u) => {
      const x = u * R;
      const h = radiusHeight(x);
      return v(pointX(x), pointY(h), pointZ(h));
    }), color, 0.007, 0.56, order + 10));
    block.add(makeTube(sampleCurve((u) => {
      const x = u * R;
      return v(pointX(x), pointY(radiusHeight(x)), 0);
    }), color, 0.006, 0.58, order + 9));
    block.add(makeTube(sampleCurve((u) => {
      const x = u * R;
      return v(pointX(x), 0, pointZ(radiusHeight(x)));
    }), color, 0.006, 0.58, order + 9));
    block.add(makeTube([v(0, 0, 0), v(pointX(R), 0, 0)], color, 0.005, 0.42, order + 8));
    block.add(makeTube([v(0, 0, 0), v(0, pointY(R), 0)], color, 0.005, 0.42, order + 8));
    block.add(makeTube([v(0, 0, 0), v(0, 0, pointZ(R))], color, 0.005, 0.42, order + 8));
    block.add(makeTube([v(0, pointY(R), 0), v(0, pointY(R), pointZ(R))], color, 0.0045, 0.52, order + 8));
    block.add(makeTube([v(0, 0, pointZ(R)), v(0, pointY(R), pointZ(R))], color, 0.0045, 0.52, order + 8));

    const highlightLines = [
      sampleCurve((u) => {
        const x = u * R;
        const h = radiusHeight(x);
        return v(pointX(x), pointY(h), pointZ(h));
      }),
      sampleCurve((u) => {
        const x = u * R;
        return v(pointX(x), pointY(radiusHeight(x)), 0);
      }),
      sampleCurve((u) => {
        const x = u * R;
        return v(pointX(x), 0, pointZ(radiusHeight(x)));
      }),
      [v(0, 0, 0), v(pointX(R), 0, 0)],
      [v(0, 0, 0), v(0, pointY(R), 0)],
      [v(0, 0, 0), v(0, 0, pointZ(R))],
      [v(0, pointY(R), 0), v(0, pointY(R), pointZ(R))],
      [v(0, 0, pointZ(R)), v(0, pointY(R), pointZ(R))],
    ];
    for (const points of highlightLines) {
      highlightGroup.add(makeTube(points, flash, 0.019, 1, 90 + index));
    }
    block.userData.label = label;
    block.userData.highlightGroup = highlightGroup;
    block.add(highlightGroup);
    octantBlocks.push(block);
    octantGroup.add(block);
  });
}

function updateFormulaPanel(t) {
  const values = {
    vertical: interval(t, 1.65, 2.45) * (1 - interval(t, 11.65, 12.35)),
    horizontal: interval(t, 3.75, 4.65) * (1 - interval(t, 11.65, 12.35)),
    domain: 0,
    symmetry: interval(t, 31.25, 32.00),
  };
  for (const [key, value] of Object.entries(values)) {
    const selector = key === "symmetry" ? "#symmetry-formula" : `.formula[data-key="${key}"]`;
    document.querySelector(selector)?.style.setProperty("--alpha", value.toFixed(3));
  }
}

let currentViewHeight = 6.05;
let currentViewOffsetX = 0.0;
let currentViewOffsetY = 0.0;
function updateProjection() {
  const width = window.innerWidth || 1920;
  const height = window.innerHeight || 1080;
  const aspect = width / height;
  const viewWidth = currentViewHeight * aspect;
  camera.left = -viewWidth / 2 + currentViewOffsetX;
  camera.right = viewWidth / 2 + currentViewOffsetX;
  camera.top = currentViewHeight / 2 + currentViewOffsetY;
  camera.bottom = -currentViewHeight / 2 + currentViewOffsetY;
  camera.updateProjectionMatrix();
}

function updateCamera(t) {
  const a = interval(t, 5.8, 9.5);
  const projection = interval(t, 11.45, 15.55);
  const symmetryReturn = interval(t, 18.3, 23.05);
  const earlyPos = v(5.15, 1.75, 2.35);
  const figureAPos = v(5.30, 1.55, 2.45);
  const figureBPos = v(0.94, 0.98, 8.0);
  const symmetryPos = v(5.30, 1.55, 2.45);
  const earlyTarget = v(0.52, 0.55, 0.46);
  const figureATarget = v(0.78, 0.76, 0.66);
  const figureBTarget = v(0.94, 0.98, 0.0);
  const symmetryTarget = v(0.78, 0.76, 0.66);
  const position = earlyPos.clone().lerp(figureAPos, a).lerp(figureBPos, projection).lerp(symmetryPos, symmetryReturn);
  const target = earlyTarget.clone().lerp(figureATarget, a).lerp(figureBTarget, projection).lerp(symmetryTarget, symmetryReturn);
  const up = v(0, 0, 1).lerp(v(0, 1, 0), projection).lerp(v(0, 0, 1), symmetryReturn).normalize();
  camera.position.copy(position);
  camera.up.copy(up);
  camera.lookAt(target);
  currentViewHeight = THREE.MathUtils.lerp(THREE.MathUtils.lerp(THREE.MathUtils.lerp(6.05, 5.28, a), 5.34, projection), 7.18, symmetryReturn);
  currentViewOffsetX = THREE.MathUtils.lerp(THREE.MathUtils.lerp(0.30, 0.26, projection), 0.22, symmetryReturn);
  currentViewOffsetY = THREE.MathUtils.lerp(THREE.MathUtils.lerp(0.36, 0.24, projection), 0.18, symmetryReturn);
  updateProjection();
}

function updateScene(t) {
  const time = Math.max(0, Math.min(DURATION, t));
  const axesAlpha = interval(time, 0, 0.75);
  const firstReveal = interval(time, 1.0, 3.0);
  const secondReveal = interval(time, 3.2, 5.25);
  const fadeCylinders = interval(time, 6.0, 7.85);
  const projection = interval(time, 11.45, 15.55);
  const symmetryReturn = interval(time, 18.3, 23.05);
  const topViewNotesOut = interval(time, 18.75, 20.45);
  const singleBlockOut = interval(time, 25.20, 26.00);
  const fullAxesAlpha = interval(time, 23.10, 24.05);
  const fullZGrow = interval(time, 23.20, 25.05);
  const fullYGrow = interval(time, 23.35, 25.20);
  const fullCylinderPresence = (fullZGrow > 0.002 || fullYGrow > 0.002 ? 1 : 0) * (1 - interval(time, 26.20, 28.20) * 0.61);
  const octantAlpha = interval(time, 25.20, 26.00);
  const remnantAlpha = interval(time, 6.95, 8.45) * (1 - interval(time, 9.8, 10.8));
  const overlapGhost = interval(time, 4.65, 5.75) * (1 - interval(time, 6.45, 7.1)) * 0.46;
  const tentAlpha = Math.max(overlapGhost, interval(time, 6.55, 8.0) * (1 - interval(time, 7.7, 8.9)) * 0.68, interval(time, 8.0, 9.18));
  const annotationAlpha = interval(time, 8.85, 9.7);
  const projectionAlpha = projection * (1 - topViewNotesOut);
  const firstOctantMarkerAlpha = interval(time, 18.30, 18.95);
  const oldAxesAlpha = axesAlpha * (1 - fullAxesAlpha);

  cylinderZGroup.scale.set(1, 1, Math.max(0.001, firstReveal));
  cylinderYGroup.scale.set(1, Math.max(0.001, secondReveal), 1);
  fullCylinderZGrowGroup.scale.set(1, 1, Math.max(0.001, fullZGrow));
  fullCylinderYGrowGroup.scale.set(1, Math.max(0.001, fullYGrow), 1);
  setGroupOpacity(axisXGroup, oldAxesAlpha);
  setGroupOpacity(axisYGroup, oldAxesAlpha);
  setGroupOpacity(axisZGroup, oldAxesAlpha * (1 - projection * (1 - symmetryReturn)));
  setGroupOpacity(cylinderZGroup, firstReveal * (1 - fadeCylinders));
  setGroupOpacity(cylinderYGroup, secondReveal * (1 - fadeCylinders));
  setGroupOpacity(remnantGroup, remnantAlpha);
  setGroupOpacity(tentGroup, tentAlpha * (1 - singleBlockOut));
  setGroupOpacity(firstOctantMarkerGroup, firstOctantMarkerAlpha);
  setGroupOpacity(surfaceGuideGroup, tentAlpha * (1 - projection) * (1 - singleBlockOut));
  setGroupOpacity(annotationGroup, annotationAlpha * (1 - topViewNotesOut));
  setGroupOpacity(projectionDetailGroup, projectionAlpha);
  setGroupOpacity(domainFormulaGroup, projectionAlpha);
  setGroupOpacity(symmetryAxesGroup, fullAxesAlpha);
  setGroupOpacity(fullCylinderGroup, fullCylinderPresence);
  const flashStart = 26.25;
  const flashDuration = 0.46;
  const flashStep = 0.58;
  const settleAlpha = interval(time, 31.25, 32.00);
  octantBlocks.forEach((block, index) => {
    const phase = time - flashStart - index * flashStep;
    const flash = phase >= 0 && phase <= flashDuration
      ? Math.sin((phase / flashDuration) * Math.PI)
      : 0;
    const blockAlpha = octantAlpha * (0.66 + settleAlpha * 0.18);
    setGroupOpacity(block, blockAlpha);
    setGroupOpacity(block.userData.highlightGroup, octantAlpha * flash);
  });
  updateFormulaPanel(time);
  updateCamera(time);
  renderer.render(scene, camera);
}

function resize() {
  const width = window.innerWidth || 1920;
  const height = window.innerHeight || 1080;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(width, height, false);
  updateProjection();
}

function canvasStats() {
  const source = renderer.domElement;
  const temp = document.createElement("canvas");
  const sampleWidth = 320;
  const sampleHeight = Math.round((source.height / source.width) * sampleWidth);
  temp.width = sampleWidth;
  temp.height = sampleHeight;
  const context = temp.getContext("2d", { willReadFrequently: true });
  context.drawImage(source, 0, 0, sampleWidth, sampleHeight);
  const data = context.getImageData(0, 0, sampleWidth, sampleHeight).data;
  let nonDark = 0;
  let saturated = 0;
  let minX = sampleWidth;
  let minY = sampleHeight;
  let maxX = 0;
  let maxY = 0;
  for (let y = 0; y < sampleHeight; y += 1) {
    for (let x = 0; x < sampleWidth; x += 1) {
      const index = (y * sampleWidth + x) * 4;
      const r = data[index];
      const g = data[index + 1];
      const b = data[index + 2];
      const max = Math.max(r, g, b);
      const min = Math.min(r, g, b);
      if (max > 24) {
        nonDark += 1;
        minX = Math.min(minX, x);
        minY = Math.min(minY, y);
        maxX = Math.max(maxX, x);
        maxY = Math.max(maxY, y);
      }
      if (max - min > 36 && max > 52) saturated += 1;
    }
  }
  return {
    width: source.width,
    height: source.height,
    nonDarkRatio: nonDark / (sampleWidth * sampleHeight),
    saturatedRatio: saturated / (sampleWidth * sampleHeight),
    bounds: nonDark > 0 ? { minX, minY, maxX, maxY } : null,
  };
}

buildAxes();
buildQuarterCylinders();
buildRemnants();
buildTent();
buildFirstOctantMarker();
buildAnnotations();
buildSymmetryAxes();
buildFullCylinders();
buildOctantBlocks();
resize();
window.addEventListener("resize", () => {
  resize();
  updateScene(window.__steinmetzTime ?? 0);
});

window.steinmetzSetTime = (time) => {
  window.__steinmetzTime = time;
  updateScene(time);
  return canvasStats();
};
window.steinmetzStats = canvasStats;

const query = new URLSearchParams(window.location.search);
const fixedTime = query.has("t") ? Number(query.get("t")) : null;
if (Number.isFinite(fixedTime)) {
  updateScene(fixedTime);
  window.__steinmetzReady = true;
} else {
  const start = performance.now();
  const animate = () => {
    const time = ((performance.now() - start) / 1000) % DURATION;
    window.__steinmetzTime = time;
    updateScene(time);
    requestAnimationFrame(animate);
  };
  animate();
  window.__steinmetzReady = true;
}
