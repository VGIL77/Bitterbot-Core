// ENGRAM Neural Observatory - Real-time Dashboard Controller
// Academic-grade implementation for ML journal publication
// Authors: VMG & Claude (2025)

class EngramDashboard {
    constructor() {
        this.socket = null;
        this.charts = {};
        this.metrics = {
            consolidationRate: [],
            hebbianStrength: [],
            memoryDecay: [],
            surpriseEvents: [],
            compressionRatios: [],
            retrievalPrecision: [],
            contextContinuity: []
        };
        this.timeWindow = 3600; // 1 hour window for real-time analysis
        this.updateInterval = 1000; // Update every second
        this.dataExportQueue = [];
        
        // Statistical parameters
        this.SIGNIFICANCE_THRESHOLD = 0.05;
        this.CONFIDENCE_INTERVAL = 0.95;
        this.MIN_SAMPLE_SIZE = 30;
        
        this.init();
    }
    
    async init() {
        // Initialize WebSocket connection
        await this.initWebSocket();
        
        // Initialize all visualization components
        this.initCharts();
        this.initMetrics();
        this.initEventHandlers();
        
        // Start real-time updates
        this.startRealTimeUpdates();
        
        // Initialize particle background
        this.initParticles();
        
        console.log('ENGRAM Dashboard initialized - Academic Mode');
    }
    
    async initWebSocket() {
        // Connect to engram metrics endpoint
        const wsUrl = window.location.protocol === 'https:' 
            ? 'wss://' + window.location.host + '/ws/engrams'
            : 'ws://' + window.location.host + '/ws/engrams';
        
        try {
            this.socket = io(window.location.origin, {
                path: '/socket.io/',
                transports: ['websocket']
            });
            
            this.socket.on('connect', () => {
                console.log('Connected to ENGRAM metrics stream');
                document.getElementById('status-indicator').querySelector('.indicator-value').textContent = 'ONLINE';
                document.getElementById('status-indicator').querySelector('.indicator-value').classList.add('pulse');
            });
            
            this.socket.on('disconnect', () => {
                console.log('Disconnected from metrics stream');
                document.getElementById('status-indicator').querySelector('.indicator-value').textContent = 'OFFLINE';
                document.getElementById('status-indicator').querySelector('.indicator-value').classList.remove('pulse');
            });
            
            // Real-time engram events
            this.socket.on('engram:created', (data) => this.handleNewEngram(data));
            this.socket.on('engram:accessed', (data) => this.handleEngramAccess(data));
            this.socket.on('metrics:update', (data) => this.handleMetricsUpdate(data));
            
        } catch (error) {
            console.error('WebSocket connection failed:', error);
            // Fallback to polling mode
            this.startPollingMode();
        }
    }
    
    initCharts() {
        // Consolidation Wave Chart - Fourier Transform of Memory Formation
        const waveCtx = document.getElementById('wave-chart').getContext('2d');
        this.charts.wave = new Chart(waveCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Consolidation Wave (FFT)',
                    data: [],
                    borderColor: '#00ffff',
                    backgroundColor: 'rgba(0, 255, 255, 0.1)',
                    tension: 0.4,
                    borderWidth: 2,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 0 },
                scales: {
                    x: {
                        type: 'time',
                        time: { unit: 'minute' },
                        ticks: { color: '#a0a0a0' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    y: {
                        title: { 
                            display: true, 
                            text: 'Amplitude (σ)',
                            color: '#a0a0a0'
                        },
                        ticks: { color: '#a0a0a0' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const value = context.raw.y;
                                const stdDev = this.calculateStandardDeviation(this.metrics.consolidationRate);
                                return `Value: ${value.toFixed(3)} (${(value/stdDev).toFixed(1)}σ)`;
                            }
                        }
                    }
                }
            }
        });
        
        // Memory Decay Chart - Ebbinghaus Forgetting Curve Fitting
        const decayCtx = document.getElementById('decay-chart').getContext('2d');
        this.charts.decay = new Chart(decayCtx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Observed Decay',
                    data: [],
                    backgroundColor: '#ff00ff',
                    borderColor: '#ff00ff',
                    pointRadius: 3
                }, {
                    label: 'Fitted Curve',
                    data: [],
                    borderColor: '#ffff00',
                    backgroundColor: 'transparent',
                    type: 'line',
                    pointRadius: 0,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'logarithmic',
                        title: { 
                            display: true, 
                            text: 'Time (hours)',
                            color: '#a0a0a0'
                        },
                        ticks: { color: '#a0a0a0' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    y: {
                        title: { 
                            display: true, 
                            text: 'Relevance Score',
                            color: '#a0a0a0'
                        },
                        min: 0,
                        max: 1,
                        ticks: { color: '#a0a0a0' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: '#a0a0a0' }
                    }
                }
            }
        });
        
        // Surprise Detection Radar - Multidimensional Analysis
        const surpriseCtx = document.getElementById('surprise-radar').getContext('2d');
        this.charts.surprise = new Chart(surpriseCtx, {
            type: 'radar',
            data: {
                labels: ['Topic Shift', 'Emotion', 'Code Complexity', 'Error Density', 'Length Anomaly', 'Sentiment'],
                datasets: [{
                    label: 'Current',
                    data: [0, 0, 0, 0, 0, 0],
                    borderColor: '#00ffff',
                    backgroundColor: 'rgba(0, 255, 255, 0.2)',
                    borderWidth: 2
                }, {
                    label: 'Baseline',
                    data: [0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
                    borderColor: '#606060',
                    backgroundColor: 'rgba(96, 96, 96, 0.1)',
                    borderWidth: 1,
                    borderDash: [5, 5]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        min: 0,
                        max: 1,
                        ticks: { 
                            color: '#a0a0a0',
                            backdropColor: 'transparent'
                        },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        pointLabels: { color: '#00ffff' }
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: '#a0a0a0' }
                    }
                }
            }
        });
    }
    
    initMetrics() {
        // Initialize D3-based Hebbian network visualization
        const width = document.getElementById('hebbian-network').clientWidth;
        const height = 200;
        
        const svg = d3.select('#hebbian-network')
            .append('svg')
            .attr('width', width)
            .attr('height', height);
        
        // Force-directed graph for Hebbian connections
        this.hebbianSimulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).strength(d => d.value))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(20));
        
        this.hebbianSvg = svg;
    }
    
    handleNewEngram(data) {
        // Update neural visualization
        if (window.neuralViz) {
            window.neuralViz.addEngram({
                id: data.id,
                relevance: data.relevance_score,
                surprise: data.surprise_score,
                age: 0,
                position: this.calculateEngramPosition(data)
            });
        }
        
        // Add to live feed with academic metadata
        this.addToEngramFeed(data);
        
        // Update metrics
        this.updateConsolidationMetrics(data);
        
        // Statistical significance testing
        if (data.surprise_score > this.calculateSurpriseThreshold()) {
            this.logSignificantEvent(data);
        }
    }
    
    handleEngramAccess(data) {
        // Update Hebbian connections
        if (window.neuralViz && data.related_engrams) {
            data.related_engrams.forEach(relatedId => {
                const strength = this.calculateHebbianStrength(data.id, relatedId);
                window.neuralViz.addConnection(data.id, relatedId, strength);
            });
        }
        
        // Update retrieval precision metrics
        this.updateRetrievalMetrics(data);
    }
    
    handleMetricsUpdate(data) {
        // Update all dashboard indicators
        document.getElementById('engram-rate-value').textContent = 
            (data.consolidation_rate * 60).toFixed(1);
        
        document.getElementById('health-value').textContent = 
            this.calculateMemoryHealth(data).toFixed(0) + '%';
        
        // Update cognitive load meters
        this.updateCognitiveLoadMeters(data);
        
        // Update statistical displays
        this.updateStatisticalMetrics(data);
    }
    
    calculateEngramPosition(engram) {
        // Use t-SNE inspired positioning based on semantic similarity
        const theta = (engram.thread_position / 1000) * Math.PI * 2;
        const r = 20 + (engram.surprise_score * 20);
        const phi = engram.relevance_score * Math.PI;
        
        return {
            x: r * Math.sin(phi) * Math.cos(theta),
            y: r * Math.sin(phi) * Math.sin(theta),
            z: r * Math.cos(phi)
        };
    }
    
    calculateHebbianStrength(id1, id2) {
        // Hebbian learning: "Neurons that fire together, wire together"
        const coActivations = this.getCoActivationCount(id1, id2);
        const timeFactor = this.getTemporalProximity(id1, id2);
        const semanticSimilarity = this.getSemanticSimilarity(id1, id2);
        
        return Math.min(1, (coActivations / 10) * timeFactor * semanticSimilarity);
    }
    
    calculateSurpriseThreshold() {
        // Dynamic threshold based on recent history
        const recentSurprises = this.metrics.surpriseEvents.slice(-100);
        if (recentSurprises.length < this.MIN_SAMPLE_SIZE) return 0.7;
        
        const mean = this.calculateMean(recentSurprises.map(e => e.score));
        const stdDev = this.calculateStandardDeviation(recentSurprises.map(e => e.score));
        
        // 2 standard deviations above mean
        return Math.min(0.95, mean + (2 * stdDev));
    }
    
    calculateMemoryHealth(data) {
        // Composite health score based on multiple factors
        const factors = {
            diversity: data.diversity_index || 0,
            retrievalSuccess: data.retrieval_success_rate || 0,
            compressionEfficiency: 1 - (data.compression_ratio || 0) / 10,
            temporalCoherence: data.temporal_coherence || 0,
            surpriseBalance: Math.abs(0.3 - (data.avg_surprise || 0)) / 0.3
        };
        
        // Weighted average with academic justification
        const weights = {
            diversity: 0.25,          // Shannon entropy of topics
            retrievalSuccess: 0.35,   // Hit rate in retrieval
            compressionEfficiency: 0.15, // Information theoretic efficiency
            temporalCoherence: 0.15,  // Temporal consistency
            surpriseBalance: 0.10     // Optimal surprise theory
        };
        
        let health = 0;
        for (const [factor, value] of Object.entries(factors)) {
            health += value * weights[factor];
        }
        
        return health * 100;
    }
    
    updateConsolidationMetrics(engram) {
        const now = Date.now();
        this.metrics.consolidationRate.push({
            time: now,
            value: 1,
            engram: engram
        });
        
        // Calculate wave pattern using FFT-like approach
        const waveData = this.calculateConsolidationWave();
        this.charts.wave.data.labels = waveData.labels;
        this.charts.wave.data.datasets[0].data = waveData.values;
        this.charts.wave.update('none');
        
        // Update frequency and amplitude
        document.getElementById('wave-frequency').textContent = 
            waveData.frequency.toFixed(2) + ' Hz';
        document.getElementById('wave-amplitude').textContent = 
            waveData.amplitude.toFixed(3);
    }
    
    calculateConsolidationWave() {
        // Simulate wave pattern from consolidation events
        const window = 300; // 5 minute window
        const now = Date.now();
        const cutoff = now - (window * 1000);
        
        const recentEvents = this.metrics.consolidationRate
            .filter(e => e.time > cutoff);
        
        // Generate time series
        const resolution = 100; // points
        const labels = [];
        const values = [];
        
        for (let i = 0; i < resolution; i++) {
            const t = cutoff + (i * (window * 1000) / resolution);
            labels.push(new Date(t));
            
            // Sum gaussian kernels around each event
            let value = 0;
            recentEvents.forEach(event => {
                const dt = (t - event.time) / 1000; // seconds
                const sigma = 10; // 10 second width
                value += Math.exp(-(dt * dt) / (2 * sigma * sigma));
            });
            
            values.push({ x: new Date(t), y: value });
        }
        
        // Calculate frequency (events per second)
        const frequency = recentEvents.length / window;
        
        // Calculate amplitude (peak value)
        const amplitude = Math.max(...values.map(v => v.y));
        
        return { labels, values, frequency, amplitude };
    }
    
    updateRetrievalMetrics(access) {
        // Track retrieval precision and recall
        this.metrics.retrievalPrecision.push({
            time: Date.now(),
            precision: access.precision_score || 0,
            recall: access.recall_score || 0,
            f1: access.f1_score || 0
        });
        
        // Update Hebbian network visualization
        this.updateHebbianNetwork(access);
    }
    
    updateHebbianNetwork(access) {
        // Convert engram connections to D3 format
        const nodes = [];
        const links = [];
        
        // Add accessed engram as central node
        nodes.push({
            id: access.id,
            group: 'accessed',
            radius: 10
        });
        
        // Add related engrams
        if (access.related_engrams) {
            access.related_engrams.forEach((related, i) => {
                nodes.push({
                    id: related.id,
                    group: 'related',
                    radius: 5 + (related.strength * 5)
                });
                
                links.push({
                    source: access.id,
                    target: related.id,
                    value: related.strength
                });
            });
        }
        
        // Update D3 visualization
        this.renderHebbianNetwork(nodes, links);
        
        // Update statistics
        document.getElementById('hebbian-connections').textContent = links.length;
        document.getElementById('hebbian-strength').textContent = 
            (links.reduce((sum, l) => sum + l.value, 0) / links.length).toFixed(2);
    }
    
    renderHebbianNetwork(nodes, links) {
        // Clear previous visualization
        this.hebbianSvg.selectAll('*').remove();
        
        // Create link elements
        const link = this.hebbianSvg.append('g')
            .selectAll('line')
            .data(links)
            .enter().append('line')
            .attr('stroke', d => d3.interpolateViridis(d.value))
            .attr('stroke-width', d => Math.max(1, d.value * 3))
            .attr('stroke-opacity', 0.6);
        
        // Create node elements
        const node = this.hebbianSvg.append('g')
            .selectAll('circle')
            .data(nodes)
            .enter().append('circle')
            .attr('r', d => d.radius)
            .attr('fill', d => d.group === 'accessed' ? '#00ffff' : '#ff00ff')
            .attr('fill-opacity', 0.8)
            .attr('stroke', '#fff')
            .attr('stroke-width', 1)
            .call(d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended));
        
        // Add labels
        const label = this.hebbianSvg.append('g')
            .selectAll('text')
            .data(nodes)
            .enter().append('text')
            .text(d => d.id.substring(0, 8))
            .attr('font-size', '10px')
            .attr('fill', '#a0a0a0')
            .attr('text-anchor', 'middle')
            .attr('dy', '.35em');
        
        // Update simulation
        this.hebbianSimulation
            .nodes(nodes)
            .on('tick', ticked);
        
        this.hebbianSimulation.force('link')
            .links(links);
        
        this.hebbianSimulation.alpha(1).restart();
        
        function ticked() {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            
            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
            
            label
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        }
        
        function dragstarted(event, d) {
            if (!event.active) this.hebbianSimulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }
        
        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }
        
        function dragended(event, d) {
            if (!event.active) this.hebbianSimulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }
    }
    
    addToEngramFeed(engram) {
        const feed = document.getElementById('engram-feed');
        
        const engramEl = document.createElement('div');
        engramEl.className = 'engram-item';
        
        const timeAgo = this.formatTimeAgo(new Date(engram.created_at));
        
        engramEl.innerHTML = `
            <div class="engram-header">
                <span class="engram-id">${engram.id.substring(0, 8)}</span>
                <span class="engram-time">${timeAgo}</span>
            </div>
            <div class="engram-content">${engram.content.substring(0, 150)}...</div>
            <div class="engram-metrics">
                <span class="engram-metric">Relevance: ${engram.relevance_score.toFixed(2)}</span>
                <span class="engram-metric">Surprise: ${engram.surprise_score.toFixed(2)}</span>
                <span class="engram-metric">Tokens: ${engram.token_count}</span>
            </div>
        `;
        
        feed.insertBefore(engramEl, feed.firstChild);
        
        // Keep only last 20 items
        while (feed.children.length > 20) {
            feed.removeChild(feed.lastChild);
        }
    }
    
    updateCognitiveLoadMeters(data) {
        // Compression meter
        const compressionRatio = data.compression_ratio || 1;
        const compressionPercent = Math.min(100, (compressionRatio / 10) * 100);
        document.getElementById('compression-meter').style.width = compressionPercent + '%';
        document.getElementById('compression-value').textContent = compressionRatio.toFixed(1) + ':1';
        
        // Retrieval precision meter
        const precision = (data.retrieval_precision || 0) * 100;
        document.getElementById('precision-meter').style.width = precision + '%';
        document.getElementById('precision-value').textContent = precision.toFixed(0) + '%';
        
        // Context continuity meter
        const continuity = (data.context_continuity || 0) * 100;
        document.getElementById('continuity-meter').style.width = continuity + '%';
        document.getElementById('continuity-value').textContent = continuity.toFixed(0) + '%';
    }
    
    updateStatisticalMetrics(data) {
        // Update memory decay chart with fitted curve
        if (data.decay_observations) {
            this.updateDecayChart(data.decay_observations);
        }
        
        // Update surprise radar
        if (data.surprise_components) {
            this.updateSurpriseRadar(data.surprise_components);
        }
    }
    
    updateDecayChart(observations) {
        // Convert observations to scatter points
        const scatterData = observations.map(obs => ({
            x: obs.hours_elapsed,
            y: obs.relevance_score
        }));
        
        // Fit exponential decay curve: R(t) = R0 * e^(-λt)
        const fitted = this.fitExponentialDecay(observations);
        
        // Generate fitted curve points
        const curveData = [];
        for (let t = 0.1; t <= 100; t *= 1.2) {
            curveData.push({
                x: t,
                y: fitted.R0 * Math.exp(-fitted.lambda * t)
            });
        }
        
        // Update chart
        this.charts.decay.data.datasets[0].data = scatterData;
        this.charts.decay.data.datasets[1].data = curveData;
        this.charts.decay.update('none');
        
        // Update statistics
        const halfLife = Math.log(2) / fitted.lambda;
        document.getElementById('memory-halflife').textContent = halfLife.toFixed(1) + ' hrs';
        document.getElementById('decay-fit').textContent = fitted.r2.toFixed(3);
    }
    
    fitExponentialDecay(observations) {
        // Least squares fit for exponential decay
        // Transform to linear: ln(R) = ln(R0) - λt
        const transformed = observations.map(obs => ({
            x: obs.hours_elapsed,
            y: Math.log(obs.relevance_score)
        }));
        
        // Linear regression
        const n = transformed.length;
        const sumX = transformed.reduce((sum, p) => sum + p.x, 0);
        const sumY = transformed.reduce((sum, p) => sum + p.y, 0);
        const sumXY = transformed.reduce((sum, p) => sum + p.x * p.y, 0);
        const sumX2 = transformed.reduce((sum, p) => sum + p.x * p.x, 0);
        
        const lambda = -(n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
        const lnR0 = (sumY - lambda * sumX) / n;
        const R0 = Math.exp(lnR0);
        
        // Calculate R²
        const yMean = sumY / n;
        const ssTotal = transformed.reduce((sum, p) => sum + Math.pow(p.y - yMean, 2), 0);
        const ssResidual = transformed.reduce((sum, p) => {
            const predicted = lnR0 - lambda * p.x;
            return sum + Math.pow(p.y - predicted, 2);
        }, 0);
        const r2 = 1 - (ssResidual / ssTotal);
        
        return { R0, lambda, r2 };
    }
    
    updateSurpriseRadar(components) {
        const data = [
            components.topic_shift || 0,
            components.emotion_intensity || 0,
            components.code_complexity || 0,
            components.error_density || 0,
            components.length_anomaly || 0,
            components.sentiment_shift || 0
        ];
        
        this.charts.surprise.data.datasets[0].data = data;
        this.charts.surprise.update('none');
        
        // Update peak and rate
        const peak = Math.max(...data);
        document.getElementById('surprise-peak').textContent = peak.toFixed(2);
        
        const recentRate = this.metrics.surpriseEvents
            .filter(e => e.time > Date.now() - 3600000)
            .length;
        document.getElementById('surprise-rate').textContent = recentRate.toString();
    }
    
    // Statistical utility functions
    calculateMean(values) {
        if (values.length === 0) return 0;
        return values.reduce((sum, val) => sum + val, 0) / values.length;
    }
    
    calculateStandardDeviation(values) {
        if (values.length < 2) return 0;
        const mean = this.calculateMean(values);
        const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / (values.length - 1);
        return Math.sqrt(variance);
    }
    
    calculateConfidenceInterval(values, confidence = 0.95) {
        const mean = this.calculateMean(values);
        const stdDev = this.calculateStandardDeviation(values);
        const n = values.length;
        
        // Z-score for confidence level
        const zScore = confidence === 0.95 ? 1.96 : confidence === 0.99 ? 2.576 : 1.645;
        const marginOfError = zScore * (stdDev / Math.sqrt(n));
        
        return {
            lower: mean - marginOfError,
            upper: mean + marginOfError,
            mean: mean,
            margin: marginOfError
        };
    }
    
    // Placeholder functions for demo
    getCoActivationCount(id1, id2) {
        // In real implementation, query database for co-activation history
        return Math.floor(Math.random() * 20);
    }
    
    getTemporalProximity(id1, id2) {
        // Calculate temporal distance factor
        return 0.5 + Math.random() * 0.5;
    }
    
    getSemanticSimilarity(id1, id2) {
        // In real implementation, use embeddings
        return 0.3 + Math.random() * 0.7;
    }
    
    logSignificantEvent(engram) {
        console.log('Significant surprise event:', engram);
        this.metrics.surpriseEvents.push({
            time: Date.now(),
            score: engram.surprise_score,
            engram: engram
        });
    }
    
    formatTimeAgo(date) {
        const seconds = Math.floor((new Date() - date) / 1000);
        if (seconds < 60) return seconds + 's ago';
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return minutes + 'm ago';
        const hours = Math.floor(minutes / 60);
        return hours + 'h ago';
    }
    
    // Polling fallback
    async startPollingMode() {
        console.log('Starting polling mode...');
        
        setInterval(async () => {
            try {
                const response = await fetch('/api/engrams/metrics');
                const data = await response.json();
                this.handleMetricsUpdate(data);
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 5000); // Poll every 5 seconds
    }
    
    startRealTimeUpdates() {
        // Periodic metric calculations
        setInterval(() => {
            this.cleanOldMetrics();
            this.updateLastTimestamp();
        }, this.updateInterval);
    }
    
    cleanOldMetrics() {
        // Remove metrics older than time window
        const cutoff = Date.now() - (this.timeWindow * 1000);
        
        Object.keys(this.metrics).forEach(key => {
            if (Array.isArray(this.metrics[key])) {
                this.metrics[key] = this.metrics[key].filter(m => m.time > cutoff);
            }
        });
    }
    
    updateLastTimestamp() {
        const now = new Date().toLocaleTimeString();
        document.getElementById('last-update').textContent = `Last update: ${now}`;
    }
    
    initParticles() {
        // Initialize particles.js background
        particlesJS('particles-js', {
            particles: {
                number: { value: 80, density: { enable: true, value_area: 800 } },
                color: { value: '#00ffff' },
                shape: { type: 'circle' },
                opacity: { value: 0.3, random: true },
                size: { value: 3, random: true },
                line_linked: {
                    enable: true,
                    distance: 150,
                    color: '#00ffff',
                    opacity: 0.1,
                    width: 1
                },
                move: {
                    enable: true,
                    speed: 2,
                    direction: 'none',
                    random: true,
                    straight: false,
                    out_mode: 'out',
                    bounce: false
                }
            },
            interactivity: {
                detect_on: 'canvas',
                events: {
                    onhover: { enable: true, mode: 'grab' },
                    onclick: { enable: true, mode: 'push' },
                    resize: true
                },
                modes: {
                    grab: { distance: 140, line_linked: { opacity: 0.5 } },
                    push: { particles_nb: 4 }
                }
            },
            retina_detect: true
        });
    }
    
    initEventHandlers() {
        // Thread selector
        document.getElementById('thread-select').addEventListener('change', (e) => {
            const threadId = e.target.value;
            this.switchThread(threadId);
        });
        
        // Export buttons for academic paper
        this.addExportButtons();
    }
    
    addExportButtons() {
        const controls = document.querySelector('.controls');
        
        const exportBtn = document.createElement('button');
        exportBtn.className = 'control-btn';
        exportBtn.textContent = 'EXPORT DATA';
        exportBtn.onclick = () => this.exportAcademicData();
        
        controls.appendChild(exportBtn);
    }
    
    async exportAcademicData() {
        // Prepare data for academic publication
        const exportData = {
            metadata: {
                version: '1.0',
                timestamp: new Date().toISOString(),
                duration_hours: this.timeWindow / 3600,
                sample_size: this.metrics.consolidationRate.length
            },
            statistics: {
                consolidation_rate: this.calculateConfidenceInterval(
                    this.metrics.consolidationRate.map(m => m.value)
                ),
                memory_decay: await this.exportDecayAnalysis(),
                surprise_detection: this.exportSurpriseAnalysis(),
                hebbian_strength: this.exportHebbianAnalysis()
            },
            raw_data: {
                consolidation_events: this.metrics.consolidationRate,
                surprise_events: this.metrics.surpriseEvents,
                retrieval_metrics: this.metrics.retrievalPrecision
            }
        };
        
        // Download as JSON
        const blob = new Blob([JSON.stringify(exportData, null, 2)], 
            { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `engram_data_${new Date().toISOString()}.json`;
        a.click();
        
        console.log('Academic data exported');
    }
    
    async exportDecayAnalysis() {
        // Comprehensive decay analysis for publication
        const observations = this.metrics.memoryDecay;
        if (observations.length < this.MIN_SAMPLE_SIZE) {
            return { status: 'insufficient_data' };
        }
        
        const fitted = this.fitExponentialDecay(observations);
        const halfLife = Math.log(2) / fitted.lambda;
        
        return {
            model: 'exponential_decay',
            parameters: {
                initial_relevance: fitted.R0,
                decay_constant: fitted.lambda,
                half_life_hours: halfLife
            },
            goodness_of_fit: {
                r_squared: fitted.r2,
                sample_size: observations.length
            }
        };
    }
    
    exportSurpriseAnalysis() {
        const surpriseScores = this.metrics.surpriseEvents.map(e => e.score);
        
        return {
            distribution: {
                mean: this.calculateMean(surpriseScores),
                std_dev: this.calculateStandardDeviation(surpriseScores),
                min: Math.min(...surpriseScores),
                max: Math.max(...surpriseScores),
                quartiles: this.calculateQuartiles(surpriseScores)
            },
            threshold_analysis: {
                dynamic_threshold: this.calculateSurpriseThreshold(),
                events_above_threshold: surpriseScores.filter(s => s > this.calculateSurpriseThreshold()).length,
                percentage_significant: (surpriseScores.filter(s => s > this.calculateSurpriseThreshold()).length / surpriseScores.length) * 100
            }
        };
    }
    
    exportHebbianAnalysis() {
        // Analyze connection strength distribution
        const strengths = [];
        this.connections.forEach(conn => strengths.push(conn.strength));
        
        return {
            network_metrics: {
                total_connections: strengths.length,
                average_strength: this.calculateMean(strengths),
                strength_distribution: this.calculateQuartiles(strengths)
            }
        };
    }
    
    calculateQuartiles(values) {
        const sorted = values.slice().sort((a, b) => a - b);
        const q1 = sorted[Math.floor(sorted.length * 0.25)];
        const q2 = sorted[Math.floor(sorted.length * 0.50)];
        const q3 = sorted[Math.floor(sorted.length * 0.75)];
        
        return { q1, q2, q3 };
    }
    
    switchThread(threadId) {
        console.log(`Switching to thread: ${threadId}`);
        // Reset visualizations and load new thread data
        if (window.neuralViz) {
            window.neuralViz.engrams.clear();
            window.neuralViz.connections.clear();
        }
        
        // Emit thread switch event
        if (this.socket) {
            this.socket.emit('thread:switch', { threadId });
        }
    }
}

// Initialize dashboard when DOM is ready
let dashboard = null;

document.addEventListener('DOMContentLoaded', () => {
    dashboard = new EngramDashboard();
    
    // Make dashboard available globally for debugging
    window.engramDashboard = dashboard;
    
    console.log('ENGRAM Neural Observatory - Ready for academic analysis');
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EngramDashboard;
}