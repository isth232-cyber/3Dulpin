// 3D ULPIN & Subsurface Utility Viewer - BK Pudur, Coimbatore
// Powered by Three.js & Leaflet

const isStatic = window.location.pathname.endsWith('.html') || window.location.protocol === 'file:' || window.location.hostname.includes('github.io') || window.location.port === '';
const basePath = isStatic ? './' : '/model/';
const staticPath = isStatic ? './web_viewer/static/' : '/static/';

let scene, camera, renderer, controls;
let houseModel = null;
let groundPlane = null;
let cadastralPrism = null;
let utilityPipes = [];
let raycaster, mouse;
let currentMode = "surface";
let miniMap = null;
const DESKTOP_BREAKPOINT = 1024;
const DEFAULT_CAMERA = { position: [22, 14, 28], target: [0, 2, 0] };

const COORDS = { lat: 10.953500, lng: 76.963400 };

// Utility pipe metadata registry
const UTILITY_DATA = {
  "water-main": {
    name: "Municipal Potable Water Main (Siruvani Grid)",
    type: "Potable Water Supply",
    badge: "WATER",
    depth: "-1.20 m below street grade",
    dia: "150 mm (6 inch) Nominal Bore",
    mat: "Ductile Iron (DI) Class K9 with cement mortar lining",
    operator: "Coimbatore City Municipal Corporation (CCMC) Water Works",
    color: "#00b4d8"
  },
  "water-branch": {
    name: "Domestic Potable Service Inflow & Water Meter",
    type: "Water Connection",
    badge: "WATER",
    depth: "-1.00 m to ground level (+0.2m)",
    dia: "50 mm (2 inch)",
    mat: "High-Density Polyethylene (HDPE) PN10",
    operator: "Private Household Metered Connection",
    color: "#48cae4"
  },
  "sewer-main": {
    name: "Municipal Sewer Trunk Line (UGD System)",
    type: "Underground Drainage",
    badge: "SEWER",
    depth: "-2.50 m below street grade",
    dia: "250 mm (10 inch)",
    mat: "Spun Reinforced Concrete Pipe (NP3 Class)",
    operator: "CCMC Underground Drainage (UGD) Division",
    color: "#e76f51"
  },
  "sewer-branch": {
    name: "House Lateral Sewer & Inspection Chamber (IC)",
    type: "Sanitary Drain",
    badge: "SEWER",
    depth: "-1.80 m (1:80 self-cleansing slope)",
    dia: "160 mm (6.3 inch)",
    mat: "uPVC SWR Ring-Fit Class B",
    operator: "Property Sanitary Connection",
    color: "#f4a261"
  },
  "storm-drain": {
    name: "Roadside Stormwater & Rainwater Recharge Drain",
    type: "Stormwater Drainage",
    badge: "STORM",
    depth: "-0.80 m below curb",
    dia: "300 mm (12 inch)",
    mat: "Precast Reinforced Concrete Box Culvert",
    operator: "CCMC Roads & Stormwater Infrastructure",
    color: "#2a9d8f"
  },
  "power-conduit": {
    name: "TANGEDCO Underground Power & Optical Fiber Duct",
    type: "Electrical / Telecom",
    badge: "POWER",
    depth: "-0.70 m",
    dia: "90 mm Double Wall Corrugated",
    mat: "DWC HDPE Duct with caution tape",
    operator: "TANGEDCO Coimbatore South Distribution",
    color: "#e9c46a"
  }
};

window.addEventListener("DOMContentLoaded", () => {
  initThree();
  initMiniMap();
  setupUIEvents();
  setupResponsiveShell();
  setupFloatingControls();
  loadCadastreAPI();
  loadHouseModel();
});

function initThree() {
  const container = document.getElementById("canvas-container");
  
  // Scene
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0c1322);
  scene.fog = new THREE.FogExp2(0x0c1322, 0.012);

  // Camera
  camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.set(22, 14, 28);

  // Renderer
  const isSmallScreen = window.innerWidth < DESKTOP_BREAKPOINT;
  const isLowEndDevice = (navigator.hardwareConcurrency || 4) <= 4;
  const pixelRatioCap = isSmallScreen || isLowEndDevice ? 1.5 : 2;
  renderer = new THREE.WebGLRenderer({ antialias: !isLowEndDevice, alpha: false });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, pixelRatioCap));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputEncoding = THREE.sRGBEncoding;
  container.appendChild(renderer.domElement);

  // Controls
  controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.maxPolarAngle = Math.PI / 2 + 0.35; // Allow looking slightly upward from underground!
  controls.target.set(0, 2, 0);

  // Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.65);
  scene.add(ambientLight);

  const sunLight = new THREE.DirectionalLight(0xfff3d6, 1.2);
  sunLight.position.set(35, 45, 25);
  sunLight.castShadow = true;
  sunLight.shadow.mapSize.width = 2048;
  sunLight.shadow.mapSize.height = 2048;
  sunLight.shadow.camera.near = 0.5;
  sunLight.shadow.camera.far = 150;
  sunLight.shadow.camera.left = -30;
  sunLight.shadow.camera.right = 30;
  sunLight.shadow.camera.top = 30;
  sunLight.shadow.camera.bottom = -30;
  sunLight.shadow.bias = -0.0005;
  scene.add(sunLight);

  // Soft blue sky fill light
  const skyLight = new THREE.DirectionalLight(0x70a6ff, 0.45);
  skyLight.position.set(-25, 20, -25);
  scene.add(skyLight);

  // Subsurface illumination (so underground pipes are luminous and visible in X-ray mode)
  const subLight = new THREE.PointLight(0x00f0ff, 0.8, 40);
  subLight.position.set(0, -2.5, 5);
  scene.add(subLight);

  const subLight2 = new THREE.PointLight(0xffaa55, 0.8, 40);
  subLight2.position.set(-5, -2.0, 10);
  scene.add(subLight2);

  // Build Scene Elements
  createGroundPlane();
  createCadastralPrism();
  createSubsurfaceUtilities();
  createSubsurfaceExcavationGrid();

  // Raycasting for clicking pipes
  raycaster = new THREE.Raycaster();
  mouse = new THREE.Vector2();
  renderer.domElement.addEventListener("pointerdown", onPointerDown);

  // Responsive resize: window resize, orientation change, and container size
  // changes (device rotation, browser chrome show/hide on mobile).
  window.addEventListener("resize", onWindowResize);
  window.addEventListener("orientationchange", () => setTimeout(onWindowResize, 200));
  if (window.ResizeObserver) {
    const resizeObserver = new ResizeObserver(() => onWindowResize());
    resizeObserver.observe(container);
  }

  // Animation Loop
  animate();
}

// 1. Ground Plane with Satellite Imagery of BK Pudur
function createGroundPlane() {
  const groundGeo = new THREE.PlaneGeometry(75, 75, 32, 32);
  groundGeo.rotateX(-Math.PI / 2);

  const textureLoader = new THREE.TextureLoader();
  const satTexture = textureLoader.load(staticPath + "satellite_ground.jpg", (tex) => {
    tex.wrapS = THREE.ClampToEdgeWrapping;
    tex.wrapT = THREE.ClampToEdgeWrapping;
    tex.encoding = THREE.sRGBEncoding;
  });

  const groundMat = new THREE.MeshStandardMaterial({
    map: satTexture,
    roughness: 0.85,
    metalness: 0.1,
    transparent: true,
    opacity: 1.0
  });

  groundPlane = new THREE.Mesh(groundGeo, groundMat);
  groundPlane.position.y = 0.0;
  groundPlane.receiveShadow = true;
  scene.add(groundPlane);

  // Road Asphalt in front of the house
  const roadGeo = new THREE.PlaneGeometry(75, 14);
  roadGeo.rotateX(-Math.PI / 2);
  const roadMat = new THREE.MeshStandardMaterial({
    color: 0x1e242f,
    roughness: 0.9,
    metalness: 0.1,
    transparent: true,
    opacity: 0.95
  });
  const road = new THREE.Mesh(roadGeo, roadMat);
  road.position.set(0, 0.02, 16);
  road.receiveShadow = true;
  scene.add(road);

  // Road white center stripe
  const stripeGeo = new THREE.PlaneGeometry(75, 0.25);
  stripeGeo.rotateX(-Math.PI / 2);
  const stripeMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.7 });
  const stripe = new THREE.Mesh(stripeGeo, stripeMat);
  stripe.position.set(0, 0.03, 16);
  scene.add(stripe);
}

// 2. 3D Cadastral Property Volume / Parcel Prism
function createCadastralPrism() {
  const parcelWidth = 18.0;
  const parcelLength = 22.0;
  const heightLimit = 12.0; // Air rights (+12m)
  const depthLimit = 4.0;   // Subsurface depth (-4m)
  const totalH = heightLimit + depthLimit;

  const prismGeo = new THREE.BoxGeometry(parcelWidth, totalH, parcelLength);
  const prismMat = new THREE.MeshStandardMaterial({
    color: 0xf59e0b,
    transparent: true,
    opacity: 0.12,
    roughness: 0.2,
    metalness: 0.1,
    side: THREE.DoubleSide
  });

  cadastralPrism = new THREE.Mesh(prismGeo, prismMat);
  cadastralPrism.position.set(0, (heightLimit - depthLimit) / 2, 0); // Center prism between -4m and +12m
  scene.add(cadastralPrism);

  // Add boundary line frame
  const edges = new THREE.EdgesGeometry(prismGeo);
  const lineMat = new THREE.LineBasicMaterial({ color: 0xf59e0b, transparent: true, opacity: 0.75, linewidth: 2 });
  const wireframe = new THREE.LineSegments(edges, lineMat);
  cadastralPrism.add(wireframe);

  // 4 Cadastral Boundary Stones (Jameen corner survey stones)
  const stoneGeo = new THREE.CylinderGeometry(0.3, 0.35, 0.8, 12);
  const stoneMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.9 });
  const corners = [
    [-parcelWidth/2, parcelLength/2],
    [parcelWidth/2, parcelLength/2],
    [parcelWidth/2, -parcelLength/2],
    [-parcelWidth/2, -parcelLength/2]
  ];
  corners.forEach(([x, z]) => {
    const stone = new THREE.Mesh(stoneGeo, stoneMat);
    stone.position.set(x, 0.4, z);
    stone.castShadow = true;
    scene.add(stone);

    // Red top survey dot
    const dotGeo = new THREE.CylinderGeometry(0.15, 0.15, 0.05, 12);
    const dotMat = new THREE.MeshBasicMaterial({ color: 0xef4444 });
    const dot = new THREE.Mesh(dotGeo, dotMat);
    dot.position.set(x, 0.82, z);
    scene.add(dot);
  });
}

// 3. Procedural Underground Utilities Network (Water, Sewer, Storm, Power)
function createSubsurfaceUtilities() {
  const pipeGroup = new THREE.Group();
  pipeGroup.name = "subsurface-utilities";

  // Helper function to create cylinder pipes
  function createPipe(points, radius, colorHex, id, name) {
    const curve = new THREE.CatmullRomCurve3(points, false, "catmullrom", 0.1);
    const geometry = new THREE.TubeGeometry(curve, 64, radius, 16, false);
    const material = new THREE.MeshStandardMaterial({
      color: colorHex,
      roughness: 0.3,
      metalness: 0.5,
      emissive: colorHex,
      emissiveIntensity: 0.25,
      transparent: true,
      opacity: 0.95
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.castShadow = true;
    mesh.userData = { utilityId: id, name: name };
    pipeGroup.add(mesh);
    utilityPipes.push(mesh);
    return mesh;
  }

  // A. POTABLE WATER PIPELINE (Blue)
  // Street Water Main (running along road at y = -1.2m)
  createPipe([
    new THREE.Vector3(-36, -1.2, 13),
    new THREE.Vector3(0, -1.2, 13),
    new THREE.Vector3(36, -1.2, 13)
  ], 0.18, 0x00b4d8, "water-main", "Water Main");

  // Domestic Water Branch (connecting street main into the front porch / sump)
  createPipe([
    new THREE.Vector3(3.5, -1.2, 13),
    new THREE.Vector3(3.5, -1.0, 9.0),
    new THREE.Vector3(3.5, -1.0, 4.0),
    new THREE.Vector3(3.5, -0.2, 1.0),
    new THREE.Vector3(3.5, 0.3, 1.0) // Riser at water meter
  ], 0.08, 0x48cae4, "water-branch", "Domestic Water Inflow");

  // Water Meter Box at surface
  const meterGeo = new THREE.BoxGeometry(0.5, 0.4, 0.4);
  const meterMat = new THREE.MeshStandardMaterial({ color: 0x0077b6, roughness: 0.4 });
  const meterBox = new THREE.Mesh(meterGeo, meterMat);
  meterBox.position.set(3.5, 0.2, 1.0);
  pipeGroup.add(meterBox);

  // B. SANITARY SEWER PIPELINE (Terracotta Orange)
  // Municipal Street Sewer Trunk Line (deeper, at y = -2.5m)
  createPipe([
    new THREE.Vector3(-36, -2.5, 18),
    new THREE.Vector3(0, -2.5, 18),
    new THREE.Vector3(36, -2.5, 18)
  ], 0.24, 0xe76f51, "sewer-main", "Sewer Trunk Main");

  // Household Lateral Sewer Line (from house bathroom out through driveway to street)
  createPipe([
    new THREE.Vector3(-5.0, -1.5, -6.0), // Under house bathroom
    new THREE.Vector3(-4.0, -1.8, 0.0),
    new THREE.Vector3(-4.0, -2.1, 7.5),  // Under front gate / driveway IC
    new THREE.Vector3(-4.0, -2.5, 18.0)  // Drops into municipal trunk
  ], 0.14, 0xf4a261, "sewer-branch", "Household Lateral Sewer");

  // Inspection Chamber (IC) / Concrete Manhole near front gate
  const icGeo = new THREE.CylinderGeometry(0.7, 0.8, 2.2, 16);
  const icMat = new THREE.MeshStandardMaterial({ color: 0x7f8c8d, roughness: 0.9, transparent: true, opacity: 0.75 });
  const ic = new THREE.Mesh(icGeo, icMat);
  ic.position.set(-4.0, -1.1, 7.5);
  pipeGroup.add(ic);

  // Cast Iron Manhole Cover at driveway surface
  const lidGeo = new THREE.CylinderGeometry(0.5, 0.5, 0.06, 24);
  const lidMat = new THREE.MeshStandardMaterial({ color: 0x2c3e50, roughness: 0.5, metalness: 0.8 });
  const lid = new THREE.Mesh(lidGeo, lidMat);
  lid.position.set(-4.0, 0.03, 7.5);
  pipeGroup.add(lid);

  // Street Manhole on main road
  const streetManhole = new THREE.Mesh(icGeo, icMat);
  streetManhole.position.set(0, -1.3, 18);
  pipeGroup.add(streetManhole);
  const streetLid = new THREE.Mesh(lidGeo, lidMat);
  streetLid.position.set(0, 0.03, 18);
  pipeGroup.add(streetLid);

  // C. STORMWATER CONDUIT (Teal)
  // Roadside drain channel
  createPipe([
    new THREE.Vector3(-36, -0.7, 9.5),
    new THREE.Vector3(0, -0.7, 9.5),
    new THREE.Vector3(36, -0.7, 9.5)
  ], 0.22, 0x2a9d8f, "storm-drain", "Stormwater Drain");

  // Roof Rainwater harvesting pipe discharge
  createPipe([
    new THREE.Vector3(-7.5, 0.0, 7.0),
    new THREE.Vector3(-7.5, -0.7, 9.5)
  ], 0.09, 0x2a9d8f, "storm-drain", "Rainwater Harvesting Feeder");

  // D. ELECTRICAL & FIBER OPTIC DUCT (Yellow)
  createPipe([
    new THREE.Vector3(8.0, -0.7, 14.0), // Utility Pole drop
    new THREE.Vector3(6.5, -0.7, 8.5),  // Under front gate
    new THREE.Vector3(6.5, -0.5, 2.0),
    new THREE.Vector3(6.5, 0.6, 2.0)   // Riser to electric meter
  ], 0.07, 0xe9c46a, "power-conduit", "Electrical Duct");

  // Utility pole next to road (seen in the photos!)
  const poleGeo = new THREE.CylinderGeometry(0.18, 0.22, 9.5, 12);
  const poleMat = new THREE.MeshStandardMaterial({ color: 0x95a5a6, roughness: 0.7 });
  const pole = new THREE.Mesh(poleGeo, poleMat);
  pole.position.set(8.0, 4.75, 14.0);
  pole.castShadow = true;
  pipeGroup.add(pole);

  scene.add(pipeGroup);
}

// 4. Subsurface Depth Reference Grid (-1m, -2m, -3m depth markers)
function createSubsurfaceExcavationGrid() {
  const depthGroup = new THREE.Group();
  depthGroup.name = "subsurface-grid";

  const depths = [-1.0, -2.0, -3.0];
  depths.forEach((d) => {
    const grid = new THREE.GridHelper(50, 25, 0x00f0ff, 0x1e3a8a);
    grid.position.y = d;
    grid.material.transparent = true;
    grid.material.opacity = 0.18;
    depthGroup.add(grid);
  });

  scene.add(depthGroup);
}

// 5. Load the 3D Textured House Model (final.obj & final.mtl)
function loadHouseModel() {
  const loaderBanner = document.getElementById("loader-banner");
  const loaderText = document.getElementById("loader-text");
  const errorBanner = document.getElementById("error-banner");
  errorBanner.classList.add("hidden");
  loaderBanner.classList.remove("hidden");
  loaderText.textContent = "Loading 3D house model & subsurface utility network...";
  document.getElementById("loader-progress").style.width = "0%";

  const mtlLoader = new THREE.MTLLoader();
  mtlLoader.setPath(basePath);
  
  mtlLoader.load("final.mtl", (materials) => {
    materials.preload();

    // Ensure all materials are double-sided and well-lit
    for (let key in materials.materials) {
      const mat = materials.materials[key];
      mat.side = THREE.DoubleSide;
      mat.transparent = true;
      mat.opacity = 1.0;
      mat.roughness = 0.65;
    }

    const objLoader = new THREE.OBJLoader();
    objLoader.setMaterials(materials);
    objLoader.setPath(basePath);

    objLoader.load(
      "final.obj",
      (object) => {
        houseModel = object;

        // Compute Bounding Box to center and place at ground level
        const box = new THREE.Box3().setFromObject(object);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());

        console.log("Loaded final.obj size:", size);

        // Scale factor to map Blender export into ~18m x 15m real-world footprint
        const targetWidth = 16.5;
        const scaleFactor = targetWidth / Math.max(size.x, size.z);
        object.scale.set(scaleFactor, scaleFactor, scaleFactor);

        // Recompute scaled box
        const scaledBox = new THREE.Box3().setFromObject(object);
        const scaledCenter = scaledBox.getCenter(new THREE.Vector3());

        // Center on parcel and place on ground y = 0.0
        object.position.x = -scaledCenter.x;
        object.position.y = -scaledBox.min.y; // Sits flush on ground!
        object.position.z = -scaledCenter.z - 2.0; // Setback from front road

        // Enable shadows on all meshes
        object.traverse((child) => {
          if (child.isMesh) {
            child.castShadow = true;
            child.receiveShadow = true;
          }
        });

        scene.add(object);

        // Hide loader
        loaderBanner.classList.add("hidden");
      },
      (xhr) => {
        const pct = Math.min(100, Math.round((xhr.loaded / (xhr.total || 10500000)) * 100));
        loaderText.textContent = `Streaming 3D house geometry: ${pct}%...`;
        document.getElementById("loader-progress").style.width = `${pct}%`;
      },
      (error) => {
        console.warn("Error loading final.obj with MTL, attempting fallback OBJ load:", error);
        fallbackObjLoad();
      }
    );
  }, (err) => {
    console.warn("MTL load failed, loading OBJ with standard material fallback:", err);
    fallbackObjLoad();
  });
}

// Fallback OBJ loader in case texture path is altered
function fallbackObjLoad() {
  const objLoader = new THREE.OBJLoader();
  objLoader.load(basePath + "final.obj", (object) => {
    houseModel = object;
    const box = new THREE.Box3().setFromObject(object);
    const size = box.getSize(new THREE.Vector3());
    const scaleFactor = 16.5 / Math.max(size.x, size.z);
    object.scale.set(scaleFactor, scaleFactor, scaleFactor);

    const fallbackMat = new THREE.MeshStandardMaterial({
      color: 0xfacc15, // Characteristic Yellow Plaster
      roughness: 0.7,
      metalness: 0.1,
      side: THREE.DoubleSide
    });

    object.traverse((child) => {
      if (child.isMesh) {
        child.material = fallbackMat;
        child.castShadow = true;
        child.receiveShadow = true;
      }
    });

    const scaledBox = new THREE.Box3().setFromObject(object);
    object.position.x = -scaledBox.getCenter(new THREE.Vector3()).x;
    object.position.y = -scaledBox.min.y;
    object.position.z = -scaledBox.getCenter(new THREE.Vector3()).z - 2.0;

    scene.add(object);
    document.getElementById("loader-banner").classList.add("hidden");
  }, undefined, (error) => {
    console.error("Fallback OBJ load also failed:", error);
    showModelLoadError();
  });
}

function showModelLoadError() {
  document.getElementById("loader-banner").classList.add("hidden");
  const errorBanner = document.getElementById("error-banner");
  document.getElementById("error-text").textContent =
    "The 3D house model could not be loaded. Check your connection and try again.";
  errorBanner.classList.remove("hidden");
}

// 6. Interactive Raycasting: Click on any pipe to inspect
function onPointerDown(event) {
  // The canvas only receives this event when the click didn't land on an
  // overlay panel (those sit above it in z-order and stop the event there),
  // so no manual pixel-region guessing is needed here.
  const container = document.getElementById("canvas-container");
  const rect = container.getBoundingClientRect();
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

  raycaster.setFromCamera(mouse, camera);
  const intersects = raycaster.intersectObjects(utilityPipes, true);

  if (intersects.length > 0) {
    const hitObj = intersects[0].object;
    const utilId = hitObj.userData.utilityId;
    if (utilId && UTILITY_DATA[utilId]) {
      displayUtilityInfo(UTILITY_DATA[utilId]);

      // Flash glow on selected pipe
      hitObj.material.emissiveIntensity = 0.8;
      setTimeout(() => {
        hitObj.material.emissiveIntensity = 0.25;
      }, 700);
    }
  }
}

function displayUtilityInfo(info) {
  document.getElementById("pipe-name").textContent = info.name;
  document.getElementById("pipe-badge").textContent = info.badge;
  document.getElementById("pipe-badge").style.backgroundColor = info.color;
  document.getElementById("pipe-depth").textContent = info.depth;
  document.getElementById("pipe-dia").textContent = info.dia;
  document.getElementById("pipe-mat").textContent = info.mat;
  document.getElementById("pipe-op").textContent = info.operator;

  document.getElementById("pipe-empty-state").classList.add("hidden");
  document.getElementById("pipe-details-box").classList.remove("hidden");

  // On phones/tablets, surface the newly selected utility by expanding the sheet.
  if (window.innerWidth < DESKTOP_BREAKPOINT) {
    setSheetExpanded(true);
  }
}

// 7. Mini 2D Leaflet Map showing BK Pudur
function initMiniMap() {
  miniMap = L.map("mini-map", {
    center: [COORDS.lat, COORDS.lng],
    zoom: 16,
    zoomControl: false,
    attributionControl: false
  });

  // High-res OpenStreetMap / CartoDB tile
  L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png", {
    maxZoom: 19
  }).addTo(miniMap);

  // Red cadastral parcel marker
  const marker = L.circleMarker([COORDS.lat, COORDS.lng], {
    color: "#e11d48",
    fillColor: "#f43f5e",
    fillOpacity: 0.9,
    radius: 7
  }).addTo(miniMap);

  marker.bindPopup("<b>BK Pudur</b><br>SF No. 142/3B");

  // Parcel polygon box
  const bounds = [
    [COORDS.lat - 0.00015, COORDS.lng - 0.00012],
    [COORDS.lat + 0.00015, COORDS.lng + 0.00012]
  ];
  L.rectangle(bounds, { color: "#f59e0b", weight: 2, fillOpacity: 0.25 }).addTo(miniMap);
}

// 8. Fetch and populate live Cadastre API (falls back to the static markup
// already in the HTML if the request fails, so the panel is never blank).
function loadCadastreAPI() {
  const targetUrl = isStatic ? (staticPath + "cadastre.json") : "/api/cadastre";
  fetch(targetUrl)
    .then((r) => r.json())
    .then((data) => {
      console.log("Cadastre API data loaded:", data);
      applyCadastreData(data);
    })
    .catch((err) => console.log("Local cadastre fallback active (using static markup):", err));
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el && value !== undefined && value !== null) el.textContent = value;
}

function applyCadastreData(data) {
  const parcel = data.parcel || {};
  const envelope = parcel.vertical_envelope || {};

  setText("stat-ulpin", (data.ulpin || "").replace(/-\d{4}$/, ""));
  setText("stat-survey", parcel.survey_number);
  setText("ulpin-value", data.ulpin);
  setText("meta-survey", parcel.survey_number);
  setText("meta-patta", parcel.patta_number);
  setText("meta-ward", parcel.ward_number);
  setText("meta-classification", parcel.classification);

  if (parcel.area_sqft !== undefined && parcel.area_sqm !== undefined) {
    setText("meta-area", `${parcel.area_sqft.toLocaleString()} sq.ft (${parcel.area_sqm} m²)`);
  }
  if (envelope.subsurface_limit_m !== undefined && envelope.air_rights_limit_m !== undefined) {
    setText("meta-envelope", `${envelope.subsurface_limit_m.toFixed(1)} m to +${envelope.air_rights_limit_m.toFixed(1)} m`);
    setText("stat-depth", `${envelope.subsurface_limit_m.toFixed(1)} m Clear`);
  }
}

// 9. UI Events & Controls
function setupUIEvents() {
  // Mode Buttons
  const btnSurface = document.getElementById("btn-surface-mode");
  const btnXray = document.getElementById("btn-xray-mode");
  const btnCadastre = document.getElementById("btn-cadastre-mode");
  const btnTop = document.getElementById("btn-top-mode");

  btnSurface.addEventListener("click", () => setViewMode("surface"));
  btnXray.addEventListener("click", () => setViewMode("xray"));
  btnCadastre.addEventListener("click", () => setViewMode("cadastre"));
  btnTop.addEventListener("click", () => setViewMode("top"));

  // Camera preset buttons (desktop sidebar + mobile "More" popover) now use
  // data attributes instead of inline onclick handlers.
  document.querySelectorAll("[data-camera-view]").forEach((btn) => {
    btn.addEventListener("click", () => setCameraView(btn.dataset.cameraView));
  });
  document.querySelectorAll("[data-mode-view]").forEach((btn) => {
    btn.addEventListener("click", () => setViewMode(btn.dataset.modeView));
  });

  // Layer Toggles
  setupLayerToggle("layer-water", "water");
  setupLayerToggle("layer-sewer", "sewer");
  setupLayerToggle("layer-storm", "storm");
  setupLayerToggle("layer-power", "power");

  // Sliders
  const groundSlider = document.getElementById("slider-ground-opacity");
  groundSlider.addEventListener("input", (e) => {
    const val = e.target.value / 100;
    document.getElementById("val-ground-opacity").textContent = `${e.target.value}%`;
    if (groundPlane) groundPlane.material.opacity = val;
  });

  const houseSlider = document.getElementById("slider-house-opacity");
  houseSlider.addEventListener("input", (e) => {
    const val = e.target.value / 100;
    document.getElementById("val-house-opacity").textContent = `${e.target.value}%`;
    if (houseModel) {
      houseModel.traverse((child) => {
        if (child.isMesh && child.material) {
          child.material.transparent = true;
          child.material.opacity = val;
        }
      });
    }
  });

  const depthSlider = document.getElementById("slider-depth-cutoff");
  depthSlider.addEventListener("input", (e) => {
    const val = (e.target.value / 10).toFixed(1);
    document.getElementById("val-depth-cutoff").textContent = `${val} m`;
    // Filter utility visibility based on depth
    utilityPipes.forEach((pipe) => {
      const uId = pipe.userData.utilityId;
      if (uId && UTILITY_DATA[uId]) {
        const depthVal = parseFloat(UTILITY_DATA[uId].depth);
        pipe.visible = depthVal >= parseFloat(val);
      }
    });
  });
}

function setupLayerToggle(elementId, typeKey) {
  document.getElementById(elementId).addEventListener("change", (e) => {
    const checked = e.target.checked;
    utilityPipes.forEach((p) => {
      const uId = p.userData.utilityId;
      if (uId && uId.includes(typeKey)) {
        p.visible = checked;
      }
    });
  });
}

// 10. Responsive shell: left drawer, right bottom sheet, and the mobile
// mini-map popover. On desktop (>=1024px) CSS repositions these same
// elements into persistent overlay panels, so only mobile/tablet needs the
// open/close state managed here.
function setupResponsiveShell() {
  const drawer = document.getElementById("left-drawer");
  const backdrop = document.getElementById("drawer-backdrop");
  const btnMenu = document.getElementById("btn-menu");
  const btnDrawerClose = document.getElementById("btn-drawer-close");

  function openDrawer() {
    drawer.classList.add("is-open");
    backdrop.classList.add("is-visible");
    btnMenu.setAttribute("aria-expanded", "true");
  }
  function closeDrawer() {
    drawer.classList.remove("is-open");
    backdrop.classList.remove("is-visible");
    btnMenu.setAttribute("aria-expanded", "false");
  }
  btnMenu.addEventListener("click", () => {
    drawer.classList.contains("is-open") ? closeDrawer() : openDrawer();
  });
  btnDrawerClose.addEventListener("click", closeDrawer);
  backdrop.addEventListener("click", closeDrawer);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeDrawer();
  });

  // Right bottom sheet (property / utility inspector)
  const sheet = document.getElementById("right-sheet");
  const sheetHandle = document.getElementById("sheet-handle");
  const sheetChevron = document.getElementById("sheet-chevron");
  const btnInfo = document.getElementById("btn-info");

  function toggleSheet() {
    setSheetExpanded(!sheet.classList.contains("is-expanded"));
  }
  sheetHandle.addEventListener("click", toggleSheet);
  sheetHandle.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggleSheet(); }
  });
  btnInfo.addEventListener("click", toggleSheet);
  window.setSheetExpandedRef = (expanded) => {
    sheet.classList.toggle("is-expanded", expanded);
    sheetHandle.setAttribute("aria-expanded", expanded ? "true" : "false");
    btnInfo.setAttribute("aria-expanded", expanded ? "true" : "false");
    if (sheetChevron) sheetChevron.classList.toggle("fa-chevron-down", expanded);
    if (sheetChevron) sheetChevron.classList.toggle("fa-chevron-up", !expanded);
  };

  // Mini-map: a single Leaflet instance is reused, its container element is
  // relocated between the desktop widget and the mobile popover so we never
  // spin up two map instances for the same data.
  const mapEl = document.getElementById("mini-map");
  const desktopWidget = document.getElementById("mini-map-widget");
  const mobilePopover = document.getElementById("mini-map-popover");
  const mapToggle = document.getElementById("mini-map-toggle");
  const mapPopoverClose = document.getElementById("mini-map-popover-close");

  function openMiniMapPopover() {
    mobilePopover.appendChild(mapEl);
    mobilePopover.classList.add("is-open");
    mapToggle.setAttribute("aria-expanded", "true");
    setTimeout(() => miniMap && miniMap.invalidateSize(), 50);
  }
  function closeMiniMapPopover() {
    mobilePopover.classList.remove("is-open");
    mapToggle.setAttribute("aria-expanded", "false");
    desktopWidget.appendChild(mapEl);
  }
  mapToggle.addEventListener("click", openMiniMapPopover);
  mapPopoverClose.addEventListener("click", closeMiniMapPopover);

  // Keep the map anchored in the correct container when the viewport crosses
  // the desktop breakpoint (e.g. tablet rotated to a wide landscape).
  window.addEventListener("resize", () => {
    if (window.innerWidth >= DESKTOP_BREAKPOINT) {
      closeMiniMapPopover();
      if (mapEl.parentElement !== desktopWidget) desktopWidget.appendChild(mapEl);
      if (miniMap) setTimeout(() => miniMap.invalidateSize(), 50);
    }
  });
}

function setSheetExpanded(expanded) {
  if (window.setSheetExpandedRef) window.setSheetExpandedRef(expanded);
}

// 11. Floating 3D viewer controls: zoom, reset, top view, fullscreen, and a
// compact "More" menu holding the remaining camera presets / view modes so
// the on-screen control cluster stays small on phones.
function setupFloatingControls() {
  document.getElementById("fab-zoom-in").addEventListener("click", () => dollyCamera(0.8));
  document.getElementById("fab-zoom-out").addEventListener("click", () => dollyCamera(1.25));
  document.getElementById("fab-reset").addEventListener("click", () => setCameraView("reset"));
  document.getElementById("fab-top").addEventListener("click", () => setCameraView("top"));

  const btnFullscreen = document.getElementById("fab-fullscreen");
  btnFullscreen.addEventListener("click", () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  });
  document.addEventListener("fullscreenchange", () => {
    const icon = btnFullscreen.querySelector("i");
    icon.classList.toggle("fa-expand", !document.fullscreenElement);
    icon.classList.toggle("fa-compress", !!document.fullscreenElement);
  });

  const btnMore = document.getElementById("fab-more");
  const morePopover = document.getElementById("more-popover");
  btnMore.addEventListener("click", () => {
    const open = morePopover.classList.toggle("is-open");
    btnMore.setAttribute("aria-expanded", open ? "true" : "false");
  });
  document.addEventListener("click", (e) => {
    if (!morePopover.contains(e.target) && e.target !== btnMore && !btnMore.contains(e.target)) {
      morePopover.classList.remove("is-open");
      btnMore.setAttribute("aria-expanded", "false");
    }
  });

  const btnRetry = document.getElementById("btn-retry");
  if (btnRetry) {
    btnRetry.addEventListener("click", () => {
      document.getElementById("error-banner").classList.add("hidden");
      loadHouseModel();
    });
  }
}

const MODE_BUTTON_IDS = {
  surface: "btn-surface-mode",
  xray: "btn-xray-mode",
  cadastre: "btn-cadastre-mode",
  top: "btn-top-mode"
};

function updateModeButtonStates(mode) {
  Object.entries(MODE_BUTTON_IDS).forEach(([key, id]) => {
    const btn = document.getElementById(id);
    if (!btn) return;
    const active = key === mode;
    btn.classList.toggle("is-active", active);
    btn.setAttribute("aria-pressed", active ? "true" : "false");
  });
}

function setViewMode(mode) {
  currentMode = mode;
  updateModeButtonStates(mode);
  const groundSlider = document.getElementById("slider-ground-opacity");
  const houseSlider = document.getElementById("slider-house-opacity");

  if (mode === "surface") {
    if (groundPlane) groundPlane.material.opacity = 1.0;
    if (cadastralPrism) cadastralPrism.visible = false;
    groundSlider.value = 100;
    document.getElementById("val-ground-opacity").textContent = "100%";
    if (houseModel) setHouseOpacity(1.0);
    houseSlider.value = 100;
    document.getElementById("val-house-opacity").textContent = "100%";
  } else if (mode === "xray") {
    // Make ground translucent glass to reveal underground pipes!
    if (groundPlane) groundPlane.material.opacity = 0.22;
    if (cadastralPrism) cadastralPrism.visible = true;
    groundSlider.value = 22;
    document.getElementById("val-ground-opacity").textContent = "22%";
    if (houseModel) setHouseOpacity(0.55);
    houseSlider.value = 55;
    document.getElementById("val-house-opacity").textContent = "55%";
  } else if (mode === "cadastre") {
    if (cadastralPrism) cadastralPrism.visible = true;
    if (groundPlane) groundPlane.material.opacity = 0.75;
    if (houseModel) setHouseOpacity(0.85);
  } else if (mode === "top") {
    setCameraView("top");
  }
}

function setHouseOpacity(val) {
  if (!houseModel) return;
  houseModel.traverse((child) => {
    if (child.isMesh && child.material) {
      child.material.transparent = true;
      child.material.opacity = val;
    }
  });
}

function setCameraView(preset) {
  if (preset === "front") {
    camera.position.set(0, 5, 24);
    controls.target.set(0, 3, 0);
  } else if (preset === "underground") {
    setViewMode("xray");
    camera.position.set(8, -4, 18);
    controls.target.set(0, -1.5, 4);
  } else if (preset === "street") {
    camera.position.set(-20, 7, 24);
    controls.target.set(0, 3, 5);
  } else if (preset === "drone") {
    camera.position.set(0, 42, 28);
    controls.target.set(0, 2, 0);
  } else if (preset === "top") {
    camera.position.set(0, 55, 0.1);
    controls.target.set(0, 0, 0);
  } else if (preset === "reset") {
    setViewMode("surface");
    camera.position.set(...DEFAULT_CAMERA.position);
    controls.target.set(...DEFAULT_CAMERA.target);
  }
}

function dollyCamera(factor) {
  const direction = new THREE.Vector3().subVectors(camera.position, controls.target);
  direction.multiplyScalar(factor);
  camera.position.copy(controls.target).add(direction);
}

function onWindowResize() {
  const container = document.getElementById("canvas-container");
  const width = container.clientWidth || window.innerWidth;
  const height = container.clientHeight || window.innerHeight;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
}

function animate() {
  requestAnimationFrame(animate);
  controls.update();

  // Subtle pulsing animation on water & power emissive highlights
  const t = Date.now() * 0.002;
  utilityPipes.forEach((p, idx) => {
    if (p.material && p.material.emissive) {
      p.material.emissiveIntensity = 0.22 + Math.sin(t + idx) * 0.08;
    }
  });

  renderer.render(scene, camera);
}
