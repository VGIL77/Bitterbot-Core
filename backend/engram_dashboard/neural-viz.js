// Neural Network 3D Visualization for ENGRAM System

class NeuralNetworkViz {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.engrams = new Map(); // Store engram nodes
        this.connections = new Map(); // Store connections between engrams
        this.particles = [];
        this.autoRotate = true;
        this.clock = new THREE.Clock();
        
        this.init();
        this.animate();
    }
    
    init() {
        // Scene setup
        this.scene = new THREE.Scene();
        this.scene.fog = new THREE.FogExp2(0x000000, 0.0008);
        
        // Camera setup
        const aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000);
        this.camera.position.set(0, 0, 50);
        
        // Renderer setup
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true, 
            alpha: true 
        });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.container.appendChild(this.renderer.domElement);
        
        // Controls
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.rotateSpeed = 0.5;
        this.controls.autoRotate = this.autoRotate;
        this.controls.autoRotateSpeed = 0.5;
        
        // Lighting
        const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
        this.scene.add(ambientLight);
        
        const pointLight1 = new THREE.PointLight(0x00ffff, 1, 100);
        pointLight1.position.set(20, 20, 20);
        this.scene.add(pointLight1);
        
        const pointLight2 = new THREE.PointLight(0xff00ff, 1, 100);
        pointLight2.position.set(-20, -20, 20);
        this.scene.add(pointLight2);
        
        // Add particle field for background
        this.createParticleField();
        
        // Add grid for reference
        this.createGrid();
        
        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize(), false);
    }
    
    createParticleField() {
        const particleGeometry = new THREE.BufferGeometry();
        const particleCount = 1000;
        const positions = new Float32Array(particleCount * 3);
        
        for (let i = 0; i < particleCount * 3; i += 3) {
            positions[i] = (Math.random() - 0.5) * 200;
            positions[i + 1] = (Math.random() - 0.5) * 200;
            positions[i + 2] = (Math.random() - 0.5) * 200;
        }
        
        particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        
        const particleMaterial = new THREE.PointsMaterial({
            color: 0x00ffff,
            size: 0.5,
            transparent: true,
            opacity: 0.3,
            blending: THREE.AdditiveBlending
        });
        
        const particles = new THREE.Points(particleGeometry, particleMaterial);
        this.scene.add(particles);
        this.particles.push(particles);
    }
    
    createGrid() {
        const gridHelper = new THREE.GridHelper(100, 20, 0x00ffff, 0x003333);
        gridHelper.position.y = -20;
        gridHelper.material.opacity = 0.2;
        gridHelper.material.transparent = true;
        this.scene.add(gridHelper);
    }
    
    addEngram(engramData) {
        const { id, relevance, surprise, age, position } = engramData;
        
        // Create engram node
        const geometry = new THREE.SphereGeometry(
            Math.max(0.5, relevance * 2), // Size based on relevance
            32, 
            32
        );
        
        // Color based on age and type
        let color;
        if (surprise > 0.8) {
            color = new THREE.Color(0xffff00); // Yellow for surprise
        } else if (age < 60) { // Less than 1 minute old
            color = new THREE.Color(0x00ffff); // Cyan for recent
        } else if (relevance > 2) {
            color = new THREE.Color(0xff00ff); // Magenta for high relevance
        } else {
            color = new THREE.Color(0x00ff00); // Green for normal
        }
        
        const material = new THREE.MeshPhongMaterial({
            color: color,
            emissive: color,
            emissiveIntensity: 0.5,
            transparent: true,
            opacity: 0.8
        });
        
        const mesh = new THREE.Mesh(geometry, material);
        
        // Position in 3D space
        if (position) {
            mesh.position.set(position.x, position.y, position.z);
        } else {
            // Random position if not specified
            mesh.position.set(
                (Math.random() - 0.5) * 40,
                (Math.random() - 0.5) * 40,
                (Math.random() - 0.5) * 40
            );
        }
        
        // Add glow effect
        const glowGeometry = new THREE.SphereGeometry(
            Math.max(1, relevance * 3),
            16,
            16
        );
        const glowMaterial = new THREE.MeshBasicMaterial({
            color: color,
            transparent: true,
            opacity: 0.2,
            side: THREE.BackSide
        });
        const glow = new THREE.Mesh(glowGeometry, glowMaterial);
        mesh.add(glow);
        
        // Store engram data
        this.engrams.set(id, {
            mesh: mesh,
            data: engramData,
            connections: new Set(),
            pulsePhase: Math.random() * Math.PI * 2
        });
        
        this.scene.add(mesh);
        
        // Add entrance animation
        mesh.scale.set(0, 0, 0);
        this.animateScale(mesh, { x: 1, y: 1, z: 1 }, 1000);
    }
    
    addConnection(fromId, toId, strength) {
        const from = this.engrams.get(fromId);
        const to = this.engrams.get(toId);
        
        if (!from || !to) return;
        
        // Create connection line
        const points = [
            from.mesh.position,
            to.mesh.position
        ];
        
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        
        // Color and opacity based on strength
        const color = new THREE.Color().setHSL(0.5 + strength * 0.5, 1, 0.5);
        const material = new THREE.LineBasicMaterial({
            color: color,
            transparent: true,
            opacity: Math.min(0.8, strength),
            linewidth: Math.max(1, strength * 3)
        });
        
        const line = new THREE.Line(geometry, material);
        this.scene.add(line);
        
        // Store connection
        const connectionId = `${fromId}-${toId}`;
        this.connections.set(connectionId, {
            line: line,
            strength: strength,
            particles: []
        });
        
        // Add particles flowing along connection
        this.createConnectionParticles(connectionId, points);
        
        // Update engram connections
        from.connections.add(toId);
        to.connections.add(fromId);
    }
    
    createConnectionParticles(connectionId, points) {
        const connection = this.connections.get(connectionId);
        if (!connection) return;
        
        // Create particles that flow along the connection
        const particleCount = 5;
        const particles = [];
        
        for (let i = 0; i < particleCount; i++) {
            const particleGeometry = new THREE.SphereGeometry(0.2, 8, 8);
            const particleMaterial = new THREE.MeshBasicMaterial({
                color: 0x00ffff,
                transparent: true,
                opacity: 0.8
            });
            
            const particle = new THREE.Mesh(particleGeometry, particleMaterial);
            particle.position.copy(points[0]);
            
            particles.push({
                mesh: particle,
                progress: i / particleCount,
                speed: 0.5 + Math.random() * 0.5
            });
            
            this.scene.add(particle);
        }
        
        connection.particles = particles;
    }
    
    updateConnectionParticles() {
        const deltaTime = this.clock.getDelta();
        
        this.connections.forEach((connection, connectionId) => {
            const [fromId, toId] = connectionId.split('-');
            const from = this.engrams.get(fromId);
            const to = this.engrams.get(toId);
            
            if (!from || !to) return;
            
            connection.particles.forEach(particle => {
                particle.progress += particle.speed * deltaTime * 0.1;
                
                if (particle.progress > 1) {
                    particle.progress = 0;
                }
                
                // Interpolate position along the line
                particle.mesh.position.lerpVectors(
                    from.mesh.position,
                    to.mesh.position,
                    particle.progress
                );
                
                // Pulse opacity
                particle.mesh.material.opacity = 0.3 + 0.5 * Math.sin(particle.progress * Math.PI);
            });
            
            // Update line position if engrams moved
            const positions = connection.line.geometry.attributes.position.array;
            positions[0] = from.mesh.position.x;
            positions[1] = from.mesh.position.y;
            positions[2] = from.mesh.position.z;
            positions[3] = to.mesh.position.x;
            positions[4] = to.mesh.position.y;
            positions[5] = to.mesh.position.z;
            connection.line.geometry.attributes.position.needsUpdate = true;
        });
    }
    
    pulseEngrams() {
        const time = this.clock.getElapsedTime();
        
        this.engrams.forEach(engram => {
            // Pulse effect
            const scale = 1 + 0.1 * Math.sin(time * 2 + engram.pulsePhase);
            engram.mesh.scale.set(scale, scale, scale);
            
            // Rotate slowly
            engram.mesh.rotation.y += 0.01;
            
            // Update glow intensity based on relevance
            if (engram.mesh.children[0]) {
                engram.mesh.children[0].material.opacity = 
                    0.1 + 0.1 * Math.sin(time * 3 + engram.pulsePhase);
            }
        });
    }
    
    neuralPulse() {
        // Create a wave effect through all engrams
        const center = new THREE.Vector3(0, 0, 0);
        const time = this.clock.getElapsedTime();
        
        this.engrams.forEach((engram, id) => {
            const distance = engram.mesh.position.distanceTo(center);
            const delay = distance * 0.05;
            const wave = Math.sin(time * 5 - delay);
            
            // Temporary scale boost
            const scaleBoost = 1 + wave * 0.3;
            this.animateScale(engram.mesh, 
                { x: scaleBoost, y: scaleBoost, z: scaleBoost }, 
                200
            );
            
            // Temporary brightness boost
            engram.mesh.material.emissiveIntensity = 0.5 + wave * 0.5;
        });
        
        // Flash all connections
        this.connections.forEach(connection => {
            this.animateOpacity(connection.line.material, 1, 500);
            setTimeout(() => {
                this.animateOpacity(connection.line.material, connection.strength, 500);
            }, 500);
        });
    }
    
    animateScale(object, target, duration) {
        const start = {
            x: object.scale.x,
            y: object.scale.y,
            z: object.scale.z
        };
        const startTime = Date.now();
        
        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeProgress = this.easeOutElastic(progress);
            
            object.scale.x = start.x + (target.x - start.x) * easeProgress;
            object.scale.y = start.y + (target.y - start.y) * easeProgress;
            object.scale.z = start.z + (target.z - start.z) * easeProgress;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        animate();
    }
    
    animateOpacity(material, target, duration) {
        const start = material.opacity;
        const startTime = Date.now();
        
        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            material.opacity = start + (target - start) * progress;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        animate();
    }
    
    easeOutElastic(x) {
        const c4 = (2 * Math.PI) / 3;
        return x === 0 ? 0 : x === 1 ? 1 : 
            Math.pow(2, -10 * x) * Math.sin((x * 10 - 0.75) * c4) + 1;
    }
    
    removeEngram(id) {
        const engram = this.engrams.get(id);
        if (!engram) return;
        
        // Remove connections
        engram.connections.forEach(connectedId => {
            const connectionId = `${id}-${connectedId}`;
            const reverseConnectionId = `${connectedId}-${id}`;
            
            this.removeConnection(connectionId);
            this.removeConnection(reverseConnectionId);
        });
        
        // Animate removal
        this.animateScale(engram.mesh, { x: 0, y: 0, z: 0 }, 500);
        setTimeout(() => {
            this.scene.remove(engram.mesh);
            this.engrams.delete(id);
        }, 500);
    }
    
    removeConnection(connectionId) {
        const connection = this.connections.get(connectionId);
        if (!connection) return;
        
        // Remove particles
        connection.particles.forEach(particle => {
            this.scene.remove(particle.mesh);
        });
        
        // Remove line
        this.scene.remove(connection.line);
        this.connections.delete(connectionId);
    }
    
    updateEngramPosition(id, newPosition) {
        const engram = this.engrams.get(id);
        if (!engram) return;
        
        // Animate to new position
        const duration = 1000;
        const start = {
            x: engram.mesh.position.x,
            y: engram.mesh.position.y,
            z: engram.mesh.position.z
        };
        const startTime = Date.now();
        
        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeProgress = this.easeInOutQuad(progress);
            
            engram.mesh.position.x = start.x + (newPosition.x - start.x) * easeProgress;
            engram.mesh.position.y = start.y + (newPosition.y - start.y) * easeProgress;
            engram.mesh.position.z = start.z + (newPosition.z - start.z) * easeProgress;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        animate();
    }
    
    easeInOutQuad(x) {
        return x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2;
    }
    
    setAutoRotate(enabled) {
        this.autoRotate = enabled;
        this.controls.autoRotate = enabled;
    }
    
    setViewMode(mode) {
        const duration = 1000;
        let targetPosition;
        
        switch(mode) {
            case 'top':
                targetPosition = { x: 0, y: 80, z: 0 };
                break;
            case 'side':
                targetPosition = { x: 80, y: 0, z: 0 };
                break;
            case '3d':
            default:
                targetPosition = { x: 30, y: 30, z: 50 };
        }
        
        this.animateCameraPosition(targetPosition, duration);
    }
    
    animateCameraPosition(target, duration) {
        const start = {
            x: this.camera.position.x,
            y: this.camera.position.y,
            z: this.camera.position.z
        };
        const startTime = Date.now();
        
        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeProgress = this.easeInOutQuad(progress);
            
            this.camera.position.x = start.x + (target.x - start.x) * easeProgress;
            this.camera.position.y = start.y + (target.y - start.y) * easeProgress;
            this.camera.position.z = start.z + (target.z - start.z) * easeProgress;
            
            this.camera.lookAt(0, 0, 0);
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        animate();
    }
    
    onWindowResize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }
    
    animate() {
        requestAnimationFrame(() => this.animate());
        
        // Update controls
        this.controls.update();
        
        // Update particles
        this.particles.forEach(particleSystem => {
            particleSystem.rotation.y += 0.0002;
        });
        
        // Update engrams
        this.pulseEngrams();
        
        // Update connection particles
        this.updateConnectionParticles();
        
        // Render
        this.renderer.render(this.scene, this.camera);
    }
    
    // Test data generation
    generateTestData() {
        // Add some test engrams
        for (let i = 0; i < 20; i++) {
            this.addEngram({
                id: `test-${i}`,
                relevance: Math.random() * 3 + 0.5,
                surprise: Math.random(),
                age: Math.random() * 3600, // Random age in seconds
                position: {
                    x: (Math.random() - 0.5) * 50,
                    y: (Math.random() - 0.5) * 50,
                    z: (Math.random() - 0.5) * 50
                }
            });
        }
        
        // Add some test connections
        for (let i = 0; i < 30; i++) {
            const from = Math.floor(Math.random() * 20);
            const to = Math.floor(Math.random() * 20);
            if (from !== to) {
                this.addConnection(
                    `test-${from}`,
                    `test-${to}`,
                    Math.random() * 0.8 + 0.2
                );
            }
        }
    }
}

// Initialize visualization when DOM is ready
let neuralViz = null;

document.addEventListener('DOMContentLoaded', () => {
    neuralViz = new NeuralNetworkViz('neural-3d-viz');
    
    // Bind control buttons
    document.getElementById('rotate-toggle').addEventListener('click', () => {
        neuralViz.setAutoRotate(!neuralViz.autoRotate);
    });
    
    document.getElementById('view-mode').addEventListener('click', (e) => {
        const modes = ['3d', 'top', 'side'];
        const currentMode = e.target.textContent.toLowerCase().replace(' view', '');
        const currentIndex = modes.indexOf(currentMode);
        const nextIndex = (currentIndex + 1) % modes.length;
        const nextMode = modes[nextIndex];
        
        neuralViz.setViewMode(nextMode);
        e.target.textContent = `${nextMode.toUpperCase()} VIEW`;
    });
    
    document.getElementById('neural-pulse').addEventListener('click', () => {
        neuralViz.neuralPulse();
    });
    
    // Generate test data for demo
    setTimeout(() => {
        neuralViz.generateTestData();
    }, 1000);
});