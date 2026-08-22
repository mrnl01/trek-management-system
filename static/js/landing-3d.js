/**
 * TrekManager - Golden Sunrise 3D Mountain Environment & Scroll Experience
 * Uses Three.js for rendering procedural low-poly 3D mountain landscape with golden morning light & mist.
 */

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', initLanding);

    function initLanding() {
        initNavbarScroll();
        initScrollReveals();
        init3DHero();
    }

    function initNavbarScroll() {
        const navbar = document.querySelector('.lp-navbar');
        if (!navbar) return;

        window.addEventListener('scroll', () => {
            if (window.scrollY > 40) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }

    function initScrollReveals() {
        const reveals = document.querySelectorAll('.lp-reveal');
        if (!reveals.length) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                }
            });
        }, {
            threshold: 0.15
        });

        reveals.forEach(el => observer.observe(el));
    }

    function init3DHero() {
        const canvas = document.getElementById('hero-3d-canvas');
        const fallback = document.querySelector('.lp-hero-fallback');

        if (!canvas) return;

        if (typeof THREE === 'undefined' || !isWebGLAvailable()) {
            if (fallback) fallback.classList.add('active');
            return;
        }

        let scene, camera, renderer;
        let mountainLayers = [];
        let particlesMesh;
        let mouseX = 0, mouseY = 0;
        let targetMouseX = 0, targetMouseY = 0;
        let windowHalfX = window.innerWidth / 2;
        let windowHalfY = window.innerHeight / 2;
        let scrollY = 0;

        try {
            // 1. Scene & Powder Blue Sky Fog
            scene = new THREE.Scene();
            scene.fog = new THREE.FogExp2(0xddf4f7, 0.016);

            // 2. Camera setup
            camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 300);
            camera.position.set(0, 9, 36);

            // 3. WebGL Renderer
            renderer = new THREE.WebGLRenderer({
                canvas: canvas,
                alpha: true,
                antialias: true,
                powerPreference: 'high-performance'
            });
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

            // 4. Golden Morning Lighting
            const ambientLight = new THREE.AmbientLight(0xb9e7f5, 1.4);
            scene.add(ambientLight);

            const sunLight = new THREE.DirectionalLight(0xfffae8, 1.8);
            sunLight.position.set(30, 45, 20);
            scene.add(sunLight);

            const horizonLight = new THREE.DirectionalLight(0xffd1b8, 1.1);
            horizonLight.position.set(-30, 20, -10);
            scene.add(horizonLight);

            // 5. Create Mountain Ridges (Lavender distant, Peach midground, Sky foreground)
            createMountainTerrain(scene, mountainLayers);

            // 6. Create Soft Cream Floating Particles
            createParticleMist(scene);

            // 7. Events
            document.addEventListener('mousemove', onDocumentMouseMove);
            window.addEventListener('resize', onWindowResize);
            window.addEventListener('scroll', onWindowScroll);

            onWindowScroll();

            // 8. Render loop
            animate();

        } catch (err) {
            console.warn('Three.js golden sunrise scene failed, falling back to vector artwork.', err);
            if (fallback) fallback.classList.add('active');
        }

        function isWebGLAvailable() {
            try {
                const c = document.createElement('canvas');
                return !!(window.WebGLRenderingContext && (c.getContext('webgl') || c.getContext('experimental-webgl')));
            } catch (e) {
                return false;
            }
        }

        function createMountainTerrain(scene, layers) {
            const specs = [
                // Distant sharp lavender peaks
                { width: 150, height: 65, segsX: 45, segsY: 25, z: -35, y: -2, color: 0xc9c2f5, mult: 12 },
                // Midground warm peach mountain range
                { width: 115, height: 48, segsX: 35, segsY: 20, z: -15, y: -4, color: 0xffd1b8, mult: 8 },
                // Foreground sky-powder smooth ridge
                { width: 90, height: 36, segsX: 25, segsY: 15, z: 0, y: -7, color: 0xb9e7f5, mult: 5 }
            ];

            specs.forEach((spec, idx) => {
                const geometry = new THREE.PlaneGeometry(spec.width, spec.height, spec.segsX, spec.segsY);
                const pos = geometry.attributes.position;

                for (let i = 0; i < pos.count; i++) {
                    const vx = pos.getX(i);
                    const vy = pos.getY(i);
                    const peakFactor = Math.cos((vx / spec.width) * Math.PI);

                    let elevation = (Math.sin(vx * 0.09) * Math.cos(vy * 0.12) * 1.8 +
                                     Math.sin(vx * 0.2 + idx) * 0.8 +
                                     Math.cos(vx * 0.05) * 2.5) * peakFactor;

                    if (elevation < 0) elevation *= 0.25;

                    pos.setZ(i, elevation * (spec.mult / 3));
                }

                geometry.computeVertexNormals();

                const material = new THREE.MeshLambertMaterial({
                    color: spec.color,
                    flatShading: true
                });

                const mesh = new THREE.Mesh(geometry, material);
                mesh.rotation.x = -Math.PI / 2.3;
                mesh.position.set(0, spec.y, spec.z);

                scene.add(mesh);
                layers.push({ mesh: mesh, baseY: spec.y, speed: 0.1 * (idx + 1) });
            });
        }

        function createParticleMist(scene) {
            const count = 300;
            const geometry = new THREE.BufferGeometry();
            const positions = new Float32Array(count * 3);

            for (let i = 0; i < count; i++) {
                positions[i * 3] = (Math.random() - 0.5) * 100;
                positions[i * 3 + 1] = Math.random() * 30;
                positions[i * 3 + 2] = (Math.random() - 0.5) * 60;
            }

            geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

            const material = new THREE.PointsMaterial({
                color: 0xfff9f2,
                size: 0.45,
                transparent: true,
                opacity: 0.65,
                blending: THREE.AdditiveBlending
            });

            particlesMesh = new THREE.Points(geometry, material);
            scene.add(particlesMesh);
        }

        function onDocumentMouseMove(event) {
            targetMouseX = (event.clientX - windowHalfX) * 0.0008;
            targetMouseY = (event.clientY - windowHalfY) * 0.0008;
        }

        function onWindowScroll() {
            scrollY = window.scrollY || window.pageYOffset;
        }

        function onWindowResize() {
            windowHalfX = window.innerWidth / 2;
            windowHalfY = window.innerHeight / 2;

            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();

            renderer.setSize(window.innerWidth, window.innerHeight);
        }

        function animate() {
            requestAnimationFrame(animate);

            mouseX += (targetMouseX - mouseX) * 0.05;
            mouseY += (targetMouseY - mouseY) * 0.05;

            const scrollFactor = Math.min(scrollY / 1000, 1);
            
            camera.position.x = mouseX * 12;
            camera.position.y = 9 - mouseY * 8 - scrollFactor * 4;
            camera.position.z = 36 - scrollFactor * 10;
            camera.lookAt(0, 4 - scrollFactor * 3, 0);

            mountainLayers.forEach(layer => {
                layer.mesh.position.y = layer.baseY + scrollFactor * layer.speed * 8;
            });

            if (particlesMesh) {
                const pos = particlesMesh.geometry.attributes.position;
                for (let i = 0; i < pos.count; i++) {
                    let y = pos.getY(i);
                    y += 0.015;
                    if (y > 30) y = 0;
                    pos.setY(i, y);
                }
                particlesMesh.geometry.attributes.position.needsUpdate = true;
                particlesMesh.rotation.y += 0.0004;
            }

            renderer.render(scene, camera);
        }
    }
})();
