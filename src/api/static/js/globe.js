/**
 * TerraTwin 3D Planetary Globe
 * Scientific rendering using NASA Blue Marble (Earth), LRO LOLA (Moon),
 * and USGS Viking (Mars) global mosaics.
 * Features realistic physical lighting, natural atmospheric scattering,
 * surface-locked coordinate marker, and precise spherical raycasting.
 */

class PlanetaryGlobe {
  constructor(containerId, options = {}) {
    this.container = typeof containerId === 'string' ? document.getElementById(containerId) : containerId;
    if (!this.container) {
      console.error('PlanetaryGlobe: Container element not found:', containerId);
      return;
    }

    this.options = Object.assign({
      initialBody: 'moon',
      initialLat: 0.67,
      initialLon: 23.47,
      radius: 2.0,
      autoRotate: true,
      autoRotateSpeed: 0.0008,
      interactive: true,
      onLocationSelect: null,
    }, options);

    this.currentBody = this.options.initialBody;
    this.targetLat = this.options.initialLat;
    this.targetLon = this.options.initialLon;
    this.radius = this.options.radius;
    this.animationId = null;

    // Texture cache & loaders
    this.textureLoader = new THREE.TextureLoader();
    this.textures = {};
    this.materials = {};

    this.init();
  }

  init() {
    // 1. Scene setup
    this.scene = new THREE.Scene();

    // 2. Camera setup
    const width = this.container.clientWidth || 800;
    const height = this.container.clientHeight || 600;
    const aspect = width / height;
    this.camera = new THREE.PerspectiveCamera(40, aspect, 0.1, 1000);
    this.camera.position.set(0, 0, 5.8);

    // 3. WebGL Renderer with calibrated ACES tone mapping & exposure
    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.35; // Enhanced exposure for crisp planetary surface details
    this.container.appendChild(this.renderer.domElement);

    // 4. OrbitControls
    if (this.options.interactive && typeof THREE.OrbitControls !== 'undefined') {
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.06;
      this.controls.rotateSpeed = 0.65;
      this.controls.minDistance = 2.4;
      this.controls.maxDistance = 10.0;
      this.controls.enablePan = false;
    }

    // 5. Scientific Multi-Light Architecture (Prevents Pitch-Black Regions)
    this.setupLighting();

    // 6. Globe Mesh
    this.globeGeometry = new THREE.SphereGeometry(this.radius, 64, 64);
    this.globeMesh = new THREE.Mesh(this.globeGeometry);
    this.scene.add(this.globeMesh);

    // 7. Earth Cloud Layer Mesh (Child of Globe for Synced Rotation)
    this.setupClouds();

    // 8. Atmospheric Scattering Rim Shader
    this.setupAtmosphere();

    // 9. Coordinate Marker Beacon (Attached directly to globeMesh)
    this.setupMarker();

    // 10. Raycasting for Accurate Lat/Lon Selection
    if (this.options.interactive) {
      this.setupRaycaster();
    }

    // 11. Resize handling
    window.addEventListener('resize', () => this.onResize());

    // 12. Set initial planet
    this.setBody(this.currentBody, false);
    this.setMarker(this.targetLat, this.targetLon);
    this.flyTo(this.targetLat, this.targetLon, 0);

    // 13. Start animation loop
    this.animate = this.animate.bind(this);
    this.animate();
  }

  setupLighting() {
    // 1. Hemisphere Light: provides soft cosmic diffuse fill on the unlit hemisphere
    // Sky color: soft starlight pale blue, Ground color: deep space navy
    this.hemiLight = new THREE.HemisphereLight(0xe2edf8, 0x141e30, 0.82);
    this.scene.add(this.hemiLight);

    // 2. Primary Solar Directional Key Light (realistic 5778 K solar daylight)
    this.sunLight = new THREE.DirectionalLight(0xfffdf6, 2.4);
    this.sunLight.position.set(6, 2.5, 5);
    this.scene.add(this.sunLight);

    // 3. Secondary Nightside Fill Light (prevents pitch-black voids, preserves maria & craters)
    this.fillLight = new THREE.DirectionalLight(0x7090b8, 0.55);
    this.fillLight.position.set(-6, -1.5, -4);
    this.scene.add(this.fillLight);

    // 4. Subtle limb rim light
    this.rimLight = new THREE.DirectionalLight(0x254b77, 0.35);
    this.rimLight.position.set(-5, 3, -5);
    this.scene.add(this.rimLight);
  }

  setupAtmosphere() {
    const atmosGeo = new THREE.SphereGeometry(this.radius * 1.018, 48, 48);
    this.atmosMaterial = new THREE.ShaderMaterial({
      vertexShader: `
        varying vec3 vNormal;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        varying vec3 vNormal;
        uniform vec3 glowColor;
        uniform float intensity;
        void main() {
          float rim = 1.0 - max(0.0, dot(vNormal, vec3(0.0, 0.0, 1.0)));
          float alpha = pow(rim, 3.4) * intensity;
          gl_FragColor = vec4(glowColor, alpha);
        }
      `,
      uniforms: {
        glowColor: { value: new THREE.Color(0x38bdf8) },
        intensity: { value: 0.65 }
      },
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
      transparent: true,
      depthWrite: false
    });

    this.atmosMesh = new THREE.Mesh(atmosGeo, this.atmosMaterial);
    this.scene.add(this.atmosMesh);
  }

  setupClouds() {
    const cloudGeo = new THREE.SphereGeometry(this.radius * 1.008, 64, 64);
    
    // Load NASA Cloud Map with sRGB encoding
    const cloudTex = this.textureLoader.load('/static/textures/earth_clouds.png');
    cloudTex.wrapS = THREE.RepeatWrapping;
    cloudTex.encoding = THREE.sRGBEncoding;

    this.cloudMaterial = new THREE.MeshStandardMaterial({
      map: cloudTex,
      transparent: true,
      opacity: 0.65,
      blending: THREE.NormalBlending,
      roughness: 0.95,
      metalness: 0.0,
      depthWrite: false
    });

    this.cloudMesh = new THREE.Mesh(cloudGeo, this.cloudMaterial);
    this.cloudMesh.visible = false;
    this.globeMesh.add(this.cloudMesh); // Child of globeMesh for synced rotation
  }

  setupMarker() {
    this.markerGroup = new THREE.Group();

    // Central beacon dot (bright emissive cyan, visible in shadow and light)
    const coreGeo = new THREE.SphereGeometry(0.03, 16, 16);
    this.markerCoreMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      depthTest: true
    });
    const core = new THREE.Mesh(coreGeo, this.markerCoreMat);
    this.markerGroup.add(core);

    // Slim vertical pointer beam
    const beamGeo = new THREE.CylinderGeometry(0.005, 0.012, 0.32, 12);
    beamGeo.translate(0, 0.16, 0);
    this.markerBeamMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending
    });
    this.beam = new THREE.Mesh(beamGeo, this.markerBeamMat);
    this.markerGroup.add(this.beam);

    // Pulsing radar rings
    this.pulseRings = [];
    for (let i = 0; i < 2; i++) {
      const ringGeo = new THREE.RingGeometry(0.03, 0.055, 32);
      const ringMat = new THREE.MeshBasicMaterial({
        color: 0x38bdf8,
        transparent: true,
        opacity: 0.85,
        side: THREE.DoubleSide,
        depthWrite: false,
        blending: THREE.AdditiveBlending
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.rotation.x = Math.PI / 2; // Flat tangential to planet surface
      ring.userData = { phase: i * 0.5 };
      this.markerGroup.add(ring);
      this.pulseRings.push(ring);
    }

    // Attach marker directly to globeMesh so it remains surface-locked during rotation
    this.globeMesh.add(this.markerGroup);
  }

  setupRaycaster() {
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();
    let mouseDownPos = { x: 0, y: 0 };
    const dom = this.renderer.domElement;

    dom.addEventListener('mousedown', (e) => {
      mouseDownPos = { x: e.clientX, y: e.clientY };
    });

    dom.addEventListener('click', (e) => {
      const dist = Math.hypot(e.clientX - mouseDownPos.x, e.clientY - mouseDownPos.y);
      if (dist > 5) return; // User dragged to orbit

      const rect = dom.getBoundingClientRect();
      this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      this.raycaster.setFromCamera(this.mouse, this.camera);
      const intersects = this.raycaster.intersectObject(this.globeMesh, false);

      if (intersects.length > 0) {
        const hit = intersects[0];
        // Convert world intersection point to local coordinates inside globeMesh
        const localPoint = this.globeMesh.worldToLocal(hit.point.clone());
        const coords = this.vector3ToLatLon(localPoint);

        this.setMarker(coords.lat, coords.lon);

        if (typeof this.options.onLocationSelect === 'function') {
          this.options.onLocationSelect(coords.lat, coords.lon);
        }
      }
    });
  }

  // --------------------------------------------------------------------------
  // Spherical Coordinates & UV Mapping Synchronization
  // --------------------------------------------------------------------------
  latLonToVector3(lat, lon, r = this.radius) {
    const phi = (90.0 - lat) * (Math.PI / 180.0);
    const theta = (lon + 180.0) * (Math.PI / 180.0);

    const x = -r * Math.cos(theta) * Math.sin(phi);
    const y = r * Math.cos(phi);
    const z = r * Math.sin(theta) * Math.sin(phi);

    return new THREE.Vector3(x, y, z);
  }

  vector3ToLatLon(vec) {
    const v = vec.clone().normalize();
    const phi = Math.acos(Math.max(-1.0, Math.min(1.0, v.y)));
    const lat = 90.0 - phi * (180.0 / Math.PI);
    const theta = Math.atan2(v.z, -v.x);
    let lon = theta * (180.0 / Math.PI) - 180.0;

    while (lon > 180.0) lon -= 360.0;
    while (lon <= -180.0) lon += 360.0;

    return {
      lat: parseFloat(lat.toFixed(2)),
      lon: parseFloat(lon.toFixed(2))
    };
  }

  setMarker(lat, lon) {
    this.targetLat = lat;
    this.targetLon = lon;

    // Position in globeMesh's local coordinate space
    const localPos = this.latLonToVector3(lat, lon, this.radius);
    this.markerGroup.position.copy(localPos);

    // Orient marker normal perpendicular to sphere surface
    const normal = localPos.clone().normalize();
    this.markerGroup.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), normal);
  }

  flyTo(lat, lon, duration = 800) {
    const targetLocal = this.latLonToVector3(lat, lon, 1.0);
    if (!this.controls) return;

    const camDist = this.camera.position.length() || 5.8;
    const targetCamWorld = targetLocal.clone().multiplyScalar(camDist);

    if (duration === 0) {
      this.camera.position.copy(targetCamWorld);
      this.controls.target.set(0, 0, 0);
      this.controls.update();
      return;
    }

    const startPos = this.camera.position.clone();
    const startTime = performance.now();

    const animateFly = (time) => {
      const elapsed = time - startTime;
      const progress = Math.min(elapsed / duration, 1.0);
      const ease = 0.5 - Math.cos(progress * Math.PI) / 2;

      this.camera.position.lerpVectors(startPos, targetCamWorld, ease);
      this.controls.update();

      if (progress < 1.0) {
        requestAnimationFrame(animateFly);
      }
    };
    requestAnimationFrame(animateFly);
  }

  // --------------------------------------------------------------------------
  // Planet Switching & Calibrated Surface Materials
  // --------------------------------------------------------------------------
  setBody(body, flyToCoords = true) {
    const cleanBody = (body || 'moon').toLowerCase();
    this.currentBody = cleanBody;

    let mat = this.materials[cleanBody];
    if (!mat) {
      const texPath = cleanBody === 'earth' 
        ? '/static/textures/earth.jpg'
        : cleanBody === 'mars' 
          ? '/static/textures/mars.jpg' 
          : '/static/textures/moon.jpg';

      const tex = this.textureLoader.load(texPath);
      tex.wrapS = THREE.RepeatWrapping;
      tex.encoding = THREE.sRGBEncoding; // Calibrated sRGB texture color space

      if (cleanBody === 'earth') {
        mat = new THREE.MeshStandardMaterial({
          map: tex,
          color: 0xffffff,
          roughness: 0.52,
          metalness: 0.05
        });
      } else if (cleanBody === 'moon') {
        mat = new THREE.MeshStandardMaterial({
          map: tex,
          color: 0xf1f5f9, // Enhanced lunar albedo for maria & crater visibility
          roughness: 0.90,
          metalness: 0.0
        });
      } else { // Mars
        mat = new THREE.MeshStandardMaterial({
          map: tex,
          color: 0xffffff,
          roughness: 0.80,
          metalness: 0.04
        });
      }
      this.materials[cleanBody] = mat;
    }

    this.globeMesh.material = mat;

    // Update Atmosphere & Cloud visibility per scientific properties
    if (cleanBody === 'earth') {
      this.atmosMaterial.uniforms.glowColor.value.setHex(0x38bdf8);
      this.atmosMaterial.uniforms.intensity.value = 0.70;
      this.atmosMesh.visible = true;
      this.cloudMesh.visible = true;
      this.markerCoreMat.color.setHex(0x06b6d4);
      this.markerBeamMat.color.setHex(0x38bdf8);
      this.pulseRings.forEach(r => r.material.color.setHex(0x06b6d4));
    } else if (cleanBody === 'mars') {
      this.atmosMaterial.uniforms.glowColor.value.setHex(0xfba774);
      this.atmosMaterial.uniforms.intensity.value = 0.40;
      this.atmosMesh.visible = true;
      this.cloudMesh.visible = false;
      this.markerCoreMat.color.setHex(0xf97316);
      this.markerBeamMat.color.setHex(0xfb923c);
      this.pulseRings.forEach(r => r.material.color.setHex(0xf97316));
    } else { // Moon
      this.atmosMaterial.uniforms.glowColor.value.setHex(0x64748b);
      this.atmosMaterial.uniforms.intensity.value = 0.10;
      this.atmosMesh.visible = false;
      this.cloudMesh.visible = false;
      this.markerCoreMat.color.setHex(0x38bdf8);
      this.markerBeamMat.color.setHex(0x60a5fa);
      this.pulseRings.forEach(r => r.material.color.setHex(0x38bdf8));
    }

    if (flyToCoords) {
      this.flyTo(this.targetLat, this.targetLon, 700);
    }
  }

  // --------------------------------------------------------------------------
  // Animation Loop
  // --------------------------------------------------------------------------
  animate(time = 0) {
    this.animationId = requestAnimationFrame(this.animate);

    if (this.controls) {
      this.controls.update();
    }

    // Subtle Earth cloud layer differential drift
    if (this.cloudMesh && this.cloudMesh.visible) {
      this.cloudMesh.rotation.y += 0.0002;
    }

    // Animate radar pulse rings
    const sec = time * 0.001;
    this.pulseRings.forEach((ring) => {
      const t = (sec + ring.userData.phase) % 1.5;
      const scale = 1.0 + t * 2.2;
      const opacity = Math.max(0, 0.85 * (1.0 - t / 1.5));
      ring.scale.set(scale, scale, 1.0);
      ring.material.opacity = opacity;
    });

    this.renderer.render(this.scene, this.camera);
  }

  onResize() {
    if (!this.container || !this.renderer || !this.camera) return;
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    if (width === 0 || height === 0) return;

    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  destroy() {
    if (this.animationId) cancelAnimationFrame(this.animationId);
    if (this.renderer && this.renderer.domElement) {
      this.renderer.domElement.remove();
    }
  }
}

// ----------------------------------------------------------------------------
// Showcase Mini-Globe Factory for Landing Page (Calibrated High Visibility)
// ----------------------------------------------------------------------------
function createShowcaseGlobe(canvasId, body) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || typeof THREE === 'undefined') return null;

  const width = canvas.clientWidth || 140;
  const height = canvas.clientHeight || 140;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
  camera.position.set(0, 0, 3.2);

  const renderer = new THREE.WebGLRenderer({
    canvas: canvas,
    antialias: true,
    alpha: true
  });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.45; // Generous exposure for bright showcase card previews

  // Balanced Lighting for Showcase Globes
  // 1. Hemisphere light: guarantees nightside and shadows have clear visibility
  const hemi = new THREE.HemisphereLight(0xffffff, 0x223348, 0.95);
  scene.add(hemi);

  // 2. Solar key directional light
  const sun = new THREE.DirectionalLight(0xfffdf6, 2.5);
  sun.position.set(4, 2, 4);
  scene.add(sun);

  // 3. Fill directional light from rear-left
  const fill = new THREE.DirectionalLight(0x7292b8, 0.65);
  fill.position.set(-4, -1, -3);
  scene.add(fill);

  // Mesh & Texture with sRGB encoding
  const texPath = body === 'earth' 
    ? '/static/textures/earth.jpg'
    : body === 'mars' 
      ? '/static/textures/mars.jpg' 
      : '/static/textures/moon.jpg';

  const loader = new THREE.TextureLoader();
  const tex = loader.load(texPath);
  tex.wrapS = THREE.RepeatWrapping;
  tex.encoding = THREE.sRGBEncoding;

  const geo = new THREE.SphereGeometry(1.0, 48, 48);
  const mat = new THREE.MeshStandardMaterial({
    map: tex,
    color: body === 'moon' ? 0xf1f5f9 : 0xffffff,
    roughness: body === 'moon' ? 0.90 : 0.65,
    metalness: 0.04
  });
  const sphere = new THREE.Mesh(geo, mat);
  scene.add(sphere);

  // Cloud layer for Earth
  let clouds = null;
  if (body === 'earth') {
    const cloudTex = loader.load('/static/textures/earth_clouds.png');
    cloudTex.wrapS = THREE.RepeatWrapping;
    cloudTex.encoding = THREE.sRGBEncoding;
    const cloudMat = new THREE.MeshStandardMaterial({
      map: cloudTex,
      transparent: true,
      opacity: 0.6,
      roughness: 0.95,
      depthWrite: false
    });
    clouds = new THREE.Mesh(new THREE.SphereGeometry(1.012, 48, 48), cloudMat);
    scene.add(clouds);
  }

  // Atmospheric halo
  if (body !== 'moon') {
    const atmosGeo = new THREE.SphereGeometry(1.025, 32, 32);
    const atmosMat = new THREE.ShaderMaterial({
      vertexShader: `
        varying vec3 vNormal;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        varying vec3 vNormal;
        uniform vec3 glowColor;
        void main() {
          float rim = 1.0 - max(0.0, dot(vNormal, vec3(0.0, 0.0, 1.0)));
          gl_FragColor = vec4(glowColor, pow(rim, 3.4) * 0.75);
        }
      `,
      uniforms: {
        glowColor: { value: new THREE.Color(body === 'earth' ? 0x38bdf8 : 0xfba774) }
      },
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
      transparent: true,
      depthWrite: false
    });
    scene.add(new THREE.Mesh(atmosGeo, atmosMat));
  }

  let animId;
  function animate() {
    animId = requestAnimationFrame(animate);
    sphere.rotation.y += 0.003;
    if (clouds) clouds.rotation.y += 0.0038;
    renderer.render(scene, camera);
  }
  animate();

  return {
    destroy: () => {
      if (animId) cancelAnimationFrame(animId);
    }
  };
}

/**
 * Realistic 3D Curved Earth Horizon for Opening Intro Screen
 * Renders an orbital viewpoint of Earth's curved limb with atmospheric glow
 * and slow cinematic drift against deep space.
 */
function createIntroEarthHorizon(canvasId) {
  const canvas = typeof canvasId === 'string' ? document.getElementById(canvasId) : canvasId;
  if (!canvas || typeof THREE === 'undefined') return null;

  const width = canvas.clientWidth || window.innerWidth;
  const height = canvas.clientHeight || window.innerHeight;

  const scene = new THREE.Scene();

  const camera = new THREE.PerspectiveCamera(35, width / height, 0.1, 100);
  camera.position.set(0, 0, 4.5);

  const renderer = new THREE.WebGLRenderer({
    canvas: canvas,
    antialias: true,
    alpha: true,
    powerPreference: 'high-performance'
  });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.35;

  // Illumination
  const hemi = new THREE.HemisphereLight(0x7292b8, 0x050b14, 0.55);
  scene.add(hemi);

  const sun = new THREE.DirectionalLight(0xfffef5, 2.8);
  sun.position.set(6, 4, 3);
  scene.add(sun);

  const fill = new THREE.DirectionalLight(0x38bdf8, 0.45);
  fill.position.set(-5, -2, -2);
  scene.add(fill);

  // Large Earth Sphere positioned below camera so top curved horizon fills lower half
  const earthRadius = 14.0;
  const earthCenterY = -13.2;

  const loader = new THREE.TextureLoader();
  const earthTex = loader.load('/static/textures/earth.jpg');
  earthTex.wrapS = THREE.RepeatWrapping;
  earthTex.encoding = THREE.sRGBEncoding;

  const earthGeo = new THREE.SphereGeometry(earthRadius, 96, 96);
  const earthMat = new THREE.MeshStandardMaterial({
    map: earthTex,
    roughness: 0.70,
    metalness: 0.05
  });
  const earthMesh = new THREE.Mesh(earthGeo, earthMat);
  earthMesh.position.set(0, earthCenterY, 0);
  earthMesh.rotation.x = 0.22; // slight orbital inclination tilt
  scene.add(earthMesh);

  // Earth Clouds Layer
  const cloudTex = loader.load('/static/textures/earth_clouds.png');
  cloudTex.wrapS = THREE.RepeatWrapping;
  cloudTex.encoding = THREE.sRGBEncoding;

  const cloudGeo = new THREE.SphereGeometry(earthRadius + 0.04, 96, 96);
  const cloudMat = new THREE.MeshStandardMaterial({
    map: cloudTex,
    transparent: true,
    opacity: 0.65,
    roughness: 0.95,
    depthWrite: false
  });
  const cloudMesh = new THREE.Mesh(cloudGeo, cloudMat);
  cloudMesh.position.set(0, earthCenterY, 0);
  cloudMesh.rotation.x = 0.22;
  scene.add(cloudMesh);

  // Atmospheric Rim Glow Shader on the Horizon
  const atmosGeo = new THREE.SphereGeometry(earthRadius + 0.12, 64, 64);
  const atmosMat = new THREE.ShaderMaterial({
    vertexShader: `
      varying vec3 vNormal;
      varying vec3 vPosition;
      void main() {
        vNormal = normalize(normalMatrix * normal);
        vPosition = (modelViewMatrix * vec4(position, 1.0)).xyz;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      varying vec3 vNormal;
      varying vec3 vPosition;
      void main() {
        vec3 viewDir = normalize(-vPosition);
        float rim = 1.0 - max(0.0, dot(vNormal, viewDir));
        float intensity = pow(rim, 3.2) * 1.1;
        vec3 glowColor = vec3(0.22, 0.74, 0.97); // Pale cyan atmospheric ozone glow
        gl_FragColor = vec4(glowColor, intensity * 0.85);
      }
    `,
    blending: THREE.AdditiveBlending,
    side: THREE.BackSide,
    transparent: true,
    depthWrite: false
  });
  const atmosMesh = new THREE.Mesh(atmosGeo, atmosMat);
  atmosMesh.position.set(0, earthCenterY, 0);
  atmosMesh.rotation.x = 0.22;
  scene.add(atmosMesh);

  // Handle Resize
  function onResize() {
    if (!canvas) return;
    const w = canvas.clientWidth || window.innerWidth;
    const h = canvas.clientHeight || window.innerHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  }
  window.addEventListener('resize', onResize);

  let animId;
  function animate() {
    animId = requestAnimationFrame(animate);
    earthMesh.rotation.y += 0.00045;
    cloudMesh.rotation.y += 0.00062;
    renderer.render(scene, camera);
  }
  animate();

  return {
    destroy: () => {
      if (animId) cancelAnimationFrame(animId);
      window.removeEventListener('resize', onResize);
      renderer.dispose();
    },
    onResize
  };
}

window.PlanetaryGlobe = PlanetaryGlobe;
window.createShowcaseGlobe = createShowcaseGlobe;
window.createIntroEarthHorizon = createIntroEarthHorizon;
