import os
import json
import base64
import pandas as pd
import streamlit.components.v1 as components
from typing import List, Dict, Any

AIRBUS_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "reference", "airbus_a320.glb")
RUNWAY_MODEL_PATHS = [
    os.path.join(os.path.dirname(__file__), "..", "data", "reference", "runway.glb"),
    "/Users/aakanshabasera/Downloads/ps3_cars_2_tvg_runway_tour.glb",
    "/Users/aakanshabasera/Downloads/runway.glb"
]

def load_file_base64(path: str) -> str:
    """Loads a binary GLB file and encodes to base64."""
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""

def get_runway_base64() -> str:
    for p in RUNWAY_MODEL_PATHS:
        if os.path.exists(p):
            return load_file_base64(p)
    return ""


def render_3d_airport_model(df: pd.DataFrame, alerts: List[Dict[str, Any]] = None, height: int = 600):
    """
    Renders an interactive WebGL scene featuring Airbus A320 aircraft telemetry
    and custom 3D runway infrastructure with smooth flight kinematics.
    """
    ref_lat = 28.5562
    ref_lon = 77.1000
    
    trajectory_points = []
    if df is not None and not df.empty:
        for _, row in df.iterrows():
            rel_x = (float(row["longitude"]) - ref_lon) * 10000.0
            rel_z = (ref_lat - float(row["latitude"])) * 10000.0
            alt_y = float(row.get("altitude_ft", 0.0)) / 10.0
            trajectory_points.append({
                "x": round(rel_x, 2),
                "y": round(alt_y, 2),
                "z": round(rel_z, 2),
                "timestamp": float(row["timestamp"]),
                "speed_kts": float(row.get("speed_kts", 0.0)),
                "heading_deg": float(row.get("heading_deg", 0.0)),
                "altitude_ft": float(row.get("altitude_ft", 0.0)),
                "is_spoofed": bool(row.get("is_spoofed", False))
            })

    alert_points = []
    if alerts:
        seen_categories = set()
        for a in alerts:
            cat = a["alert_type"]
            if cat not in seen_categories:
                seen_categories.add(cat)
                loc = a["location"]
                rel_x = (float(loc[1]) - ref_lon) * 10000.0
                rel_z = (ref_lat - float(loc[0])) * 10000.0
                alt_y = 15.0
                if df is not None and not df.empty:
                    match = df[df["timestamp"] == a["timestamp"]]
                    if not match.empty:
                        alt_y = float(match.iloc[0].get("altitude_ft", 0.0)) / 10.0
                
                alert_points.append({
                    "x": round(rel_x, 2),
                    "y": round(alt_y, 2),
                    "z": round(rel_z, 2),
                    "type": a["alert_type"],
                    "severity": a["severity"],
                    "score": a["risk_score"]
                })

    airbus_b64 = load_file_base64(AIRBUS_MODEL_PATH)
    runway_b64 = get_runway_base64()
    points_json = json.dumps(trajectory_points)
    alerts_json = json.dumps(alert_points)

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; background-color: #0b1329; font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
            #canvas-container {{ width: 100%; height: {height}px; position: relative; }}
            
            .hud-card {{
                position: absolute;
                background: rgba(15, 23, 42, 0.92);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.15);
                color: #f8fafc;
                padding: 12px 16px;
                border-radius: 8px;
                font-size: 12px;
                z-index: 100;
                box-shadow: 0 4px 14px rgba(0,0,0,0.35);
            }}

            #top-overlay {{ top: 12px; left: 12px; }}
            #telemetry-hud {{ top: 12px; right: 12px; width: 220px; }}
            #controls-hud {{ bottom: 12px; left: 12px; }}

            .hud-title {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; margin-bottom: 6px; font-weight: 600; }}
            .hud-value {{ font-size: 14px; font-weight: 700; color: #38bdf8; font-family: monospace; }}
            .status-normal {{ color: #34d399; font-weight: 700; }}
            .status-alert {{ color: #f87171; font-weight: 700; animation: blink 1s infinite; }}

            @keyframes blink {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} 100% {{ opacity: 1; }} }}

            .cam-btn {{
                background: #1e293b;
                border: 1px solid #475569;
                color: #f8fafc;
                padding: 6px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 11px;
                font-weight: 500;
                margin-right: 4px;
                transition: all 0.2s ease;
            }}
            .cam-btn:hover, .cam-btn.active {{
                background: #2563eb;
                border-color: #3b82f6;
            }}
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
    </head>
    <body>
        <div id="canvas-container">
            <div id="top-overlay" class="hud-card">
                <div class="hud-title">Spatial Flight Operations</div>
                <div style="margin-bottom: 8px;"><strong>Airbus A320-200</strong> (Tail: AI101)</div>
                <div>
                    <button class="cam-btn active" id="btn-orbit" onclick="setCamMode('orbit')">Free Orbit</button>
                    <button class="cam-btn" id="btn-chase" onclick="setCamMode('chase')">Follow Aircraft</button>
                    <button class="cam-btn" id="btn-cockpit" onclick="setCamMode('cockpit')">Cockpit View</button>
                </div>
            </div>

            <div id="telemetry-hud" class="hud-card">
                <div class="hud-title">Live Telemetry</div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>Altitude:</span> <span class="hud-value" id="hud-alt">0 ft</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>Airspeed:</span> <span class="hud-value" id="hud-spd">0 kts</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>Pitch / Bank:</span> <span class="hud-value" id="hud-att">0° / 0°</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 8px; border-top: 1px solid #334155; padding-top: 6px;">
                    <span>Status:</span> <span id="hud-status" class="status-normal">NORMAL</span>
                </div>
            </div>

            <div id="controls-hud" class="hud-card">
                <span style="color:#38bdf8;">Blue Ribbon</span>: Flight Path | 
                <span style="color:#ef4444;">Beacon</span>: Spoofing Anomaly Location
            </div>
        </div>

        <script>
            const container = document.getElementById('canvas-container');
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0b1329);
            scene.fog = new THREE.FogExp2(0x0b1329, 0.0005);

            // Set Camera zoomed directly onto the runway flight path
            const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 1, 10000);
            camera.position.set(200, 160, 320);

            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.setPixelRatio(window.devicePixelRatio);
            renderer.shadowMap.enabled = true;
            container.appendChild(renderer.domElement);

            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.target.set(0, 30, 0);

            // Lighting
            scene.add(new THREE.AmbientLight(0xffffff, 1.2));
            const sunLight = new THREE.DirectionalLight(0xffffff, 1.5);
            sunLight.position.set(400, 700, 300);
            scene.add(sunLight);

            // Ground Base Plane
            const groundGeo = new THREE.PlaneGeometry(8000, 8000);
            const groundMat = new THREE.MeshStandardMaterial({{ color: 0x070d19, roughness: 0.9 }});
            const ground = new THREE.Mesh(groundGeo, groundMat);
            ground.rotation.x = -Math.PI / 2;
            ground.position.y = -1.0;
            scene.add(ground);

            const gridHelper = new THREE.GridHelper(5000, 100, 0x1e293b, 0x0f172a);
            gridHelper.position.y = -0.5;
            scene.add(gridHelper);

            // Load Custom 3D Runway Model GLB & Filter Out Outer Dome/Sky Mesh
            const runwayB64 = "{runway_b64}";
            
            if (runwayB64.length > 100) {{
                const binaryString = window.atob(runwayB64);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {{
                    bytes[i] = binaryString.charCodeAt(i);
                }}

                const rwLoader = new THREE.GLTFLoader();
                rwLoader.parse(bytes.buffer, '', function(gltf) {{
                    const rwMesh = gltf.scene;
                    
                    // Traverse and hide outer skybox/dome meshes so we look directly inside at the runway
                    rwMesh.traverse((child) => {{
                        if (child.isMesh) {{
                            const name = (child.name || '').toLowerCase();
                            // Hide sky, dome, background, or giant outer sphere meshes
                            if (name.includes('sky') || name.includes('dome') || name.includes('background') || name.includes('bg') || name.includes('sphere')) {{
                                child.visible = false;
                            }}
                        }}
                    }});

                    const visibleBox = new THREE.Box3();
                    rwMesh.traverse((child) => {{
                        if (child.isMesh && child.visible) {{
                            visibleBox.expandByObject(child);
                        }}
                    }});

                    const size = visibleBox.getSize(new THREE.Vector3());
                    const center = visibleBox.getCenter(new THREE.Vector3());
                    
                    rwMesh.position.sub(center); // Center visible runway
                    
                    const maxDim = Math.max(size.x, size.z);
                    if (maxDim > 0) {{
                        const s = 1000.0 / maxDim;
                        rwMesh.scale.set(s, s * 0.5, s);
                    }}
                    
                    rwMesh.position.set(0, 0, 0);
                    scene.add(rwMesh);
                }});
            }} else {{
                // High Quality Fallback Runway
                const rwGroup = new THREE.Group();
                const asphalt = new THREE.Mesh(
                    new THREE.PlaneGeometry(1200, 60),
                    new THREE.MeshStandardMaterial({{ color: 0x1e293b, roughness: 0.7 }})
                );
                asphalt.rotation.x = -Math.PI / 2;
                rwGroup.add(asphalt);
                rwGroup.position.set(0, 0, 0);
                scene.add(rwGroup);
            }}

            // Control Tower
            const towerGeo = new THREE.CylinderGeometry(12, 18, 90, 16);
            const towerMat = new THREE.MeshStandardMaterial({{ color: 0x475569 }});
            const tower = new THREE.Mesh(towerGeo, towerMat);
            tower.position.set(-200, 45, 150);
            scene.add(tower);

            // Load Airbus A320-200 GLB Model with Auto-Scaling
            const airbusB64 = "{airbus_b64}";
            let airbusMesh = null;
            let auraMesh = null;

            if (airbusB64.length > 100) {{
                const binaryString = window.atob(airbusB64);
                const len = binaryString.length;
                const bytes = new Uint8Array(len);
                for (let i = 0; i < len; i++) {{
                    bytes[i] = binaryString.charCodeAt(i);
                }}

                const loader = new THREE.GLTFLoader();
                loader.parse(bytes.buffer, '', function(gltf) {{
                    airbusMesh = gltf.scene;
                    
                    const box = new THREE.Box3().setFromObject(airbusMesh);
                    const size = box.getSize(new THREE.Vector3());
                    const maxDim = Math.max(size.x, size.y, size.z);
                    if (maxDim > 0) {{
                        const targetScale = 75.0 / maxDim; // Prominent Airbus plane scale
                        airbusMesh.scale.set(targetScale, targetScale, targetScale);
                    }}

                    scene.add(airbusMesh);

                    // Add Threat Aura Around Airbus Model
                    const auraGeo = new THREE.SphereGeometry(45, 16, 16);
                    const auraMat = new THREE.MeshBasicMaterial({{ color: 0xef4444, transparent: true, opacity: 0.0, wireframe: true }});
                    auraMesh = new THREE.Mesh(auraGeo, auraMat);
                    airbusMesh.add(auraMesh);
                }});
            }} else {{
                const group = new THREE.Group();
                const fuselage = new THREE.Mesh(new THREE.CylinderGeometry(6, 6, 50, 16), new THREE.MeshStandardMaterial({{ color: 0xf8fafc }}));
                fuselage.rotation.x = Math.PI / 2;
                group.add(fuselage);
                const wings = new THREE.Mesh(new THREE.BoxGeometry(60, 1.5, 12), new THREE.MeshStandardMaterial({{ color: 0x94a3b8 }}));
                group.add(wings);
                airbusMesh = group;
                scene.add(airbusMesh);
            }}

            // Trajectory Ribbon & Altitude Drop Lines
            const pointsData = {points_json};
            const alertData = {alerts_json};
            let curve = null;

            if (pointsData.length > 1) {{
                const curvePoints = pointsData.map(p => new THREE.Vector3(p.x, p.y, p.z));
                curve = new THREE.CatmullRomCurve3(curvePoints);
                
                const tubeGeo = new THREE.TubeGeometry(curve, 160, 3.5, 8, false);
                const tubeMat = new THREE.MeshStandardMaterial({{ color: 0x38bdf8, emissive: 0x0284c7, roughness: 0.2 }});
                scene.add(new THREE.Mesh(tubeGeo, tubeMat));

                // Clean Altitude Drop Lines
                pointsData.forEach((p, idx) => {{
                    if (idx % 6 === 0) {{
                        const lineGeo = new THREE.BufferGeometry().setFromPoints([
                            new THREE.Vector3(p.x, p.y, p.z),
                            new THREE.Vector3(p.x, 0, p.z)
                        ]);
                        const line = new THREE.Line(lineGeo, new THREE.LineDashedMaterial({{ color: 0x334155, dashSize: 6, gapSize: 6 }}));
                        line.computeLineDistances();
                        scene.add(line);
                    }}
                }});
            }}

            // Clean Anomaly Beacons (One glowing beacon per alert event)
            const alertBeacons = [];
            alertData.forEach(a => {{
                const beaconGroup = new THREE.Group();
                
                // Vertical Light Beam
                const beamGeo = new THREE.CylinderGeometry(2, 6, 250, 16);
                const beamMat = new THREE.MeshBasicMaterial({{ color: 0xef4444, transparent: true, opacity: 0.55 }});
                const beam = new THREE.Mesh(beamGeo, beamMat);
                beam.position.set(a.x, a.y + 125, a.z);
                beaconGroup.add(beam);

                // Ground Warning Ring
                const ringGeo = new THREE.RingGeometry(15, 30, 32);
                const ringMat = new THREE.MeshBasicMaterial({{ color: 0xef4444, side: THREE.DoubleSide, transparent: true, opacity: 0.85 }});
                const ring = new THREE.Mesh(ringGeo, ringMat);
                ring.rotation.x = Math.PI / 2;
                ring.position.set(a.x, 0.5, a.z);
                beaconGroup.add(ring);

                scene.add(beaconGroup);
                alertBeacons.push({{ ring: ring, beam: beam }});
            }});

            // Camera View Modes
            let currentCamMode = 'orbit';
            window.setCamMode = function(mode) {{
                currentCamMode = mode;
                document.querySelectorAll('.cam-btn').forEach(btn => btn.classList.remove('active'));
                document.getElementById('btn-' + mode).classList.add('active');
                
                if (mode === 'orbit') {{
                    controls.enabled = true;
                    camera.position.set(200, 160, 320);
                    controls.target.set(0, 30, 0);
                }} else {{
                    controls.enabled = false;
                }}
            }};

            // Animation Loop & Silky-Smooth Lerp/Slerp Flight Kinematics
            let progress = 0;
            let pulseTime = 0;
            const dummyTarget = new THREE.Object3D();

            function animate() {{
                requestAnimationFrame(animate);
                
                if (curve && airbusMesh) {{
                    progress = (progress + 0.0008) % 1; // Smooth flight step
                    const pos = curve.getPointAt(progress);
                    const tangent = curve.getTangentAt(progress);
                    
                    dummyTarget.position.copy(pos);
                    dummyTarget.lookAt(pos.clone().add(tangent));

                    const pitchRad = Math.atan2(tangent.y, Math.sqrt(tangent.x * tangent.x + tangent.z * tangent.z));
                    dummyTarget.rotateX(-pitchRad * 0.6);

                    // Silky-Smooth Lerp Position & Slerp Quaternion Interpolation
                    airbusMesh.position.lerp(dummyTarget.position, 0.12);
                    airbusMesh.quaternion.slerp(dummyTarget.quaternion, 0.12);

                    const dataIdx = Math.floor(progress * (pointsData.length - 1));
                    const currentPoint = pointsData[dataIdx] || pointsData[0];

                    document.getElementById('hud-alt').innerText = Math.round(currentPoint.altitude_ft) + ' ft';
                    document.getElementById('hud-spd').innerText = Math.round(currentPoint.speed_kts) + ' kts';
                    document.getElementById('hud-att').innerText = Math.round(pitchRad * 180 / Math.PI) + '° / 0°';

                    const statusElem = document.getElementById('hud-status');
                    if (currentPoint.is_spoofed) {{
                        statusElem.innerText = 'SPOOFING ALERT';
                        statusElem.className = 'status-alert';
                        if (auraMesh) auraMesh.material.opacity = 0.6 + 0.3 * Math.sin(pulseTime * 10);
                    }} else {{
                        statusElem.innerText = 'NORMAL';
                        statusElem.className = 'status-normal';
                        if (auraMesh) auraMesh.material.opacity = 0.0;
                    }}

                    if (currentCamMode === 'chase') {{
                        const chaseOffset = tangent.clone().multiplyScalar(-110).add(new THREE.Vector3(0, 35, 0));
                        camera.position.lerp(airbusMesh.position.clone().add(chaseOffset), 0.12);
                        camera.lookAt(airbusMesh.position.clone().add(tangent.clone().multiplyScalar(100)));
                    }} else if (currentCamMode === 'cockpit') {{
                        const cockpitOffset = tangent.clone().multiplyScalar(20).add(new THREE.Vector3(0, 5, 0));
                        camera.position.copy(airbusMesh.position.clone().add(cockpitOffset));
                        camera.lookAt(airbusMesh.position.clone().add(tangent.clone().multiplyScalar(250)));
                    }} else {{
                        controls.update();
                    }}
                }} else if (currentCamMode === 'orbit') {{
                    controls.update();
                }}

                pulseTime += 0.05;
                alertBeacons.forEach(b => {{
                    const sc = 1 + 0.3 * Math.sin(pulseTime * 4);
                    b.ring.scale.set(sc, sc, sc);
                }});

                renderer.render(scene, camera);
            }}
            animate();

            window.addEventListener('resize', () => {{
                camera.aspect = container.clientWidth / container.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(container.clientWidth, container.clientHeight);
            }});
        </script>
    </body>
    </html>
    """
    
    components.html(html_code, height=height)
