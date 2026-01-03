// Dashboard JavaScript
class NetworkDashboard {
    constructor() {
        this.charts = {};
        this.refreshInterval = null;
        this.currentAlert = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        // Chart modal functionality
        this.modalChart = null;
        this.setupChartModal();
        this.startAutoRefresh();
    }

    setupEventListeners() {
        // Refresh button
        document.getElementById('refreshAlerts').addEventListener('click', () => {
            this.loadAlerts();
        });

        // Filter changes
        document.getElementById('severityFilter').addEventListener('change', () => {
            this.loadAlerts();
        });

        document.getElementById('statusFilter').addEventListener('change', () => {
            this.loadAlerts();
        });

        // Traffic time range change
        document.getElementById('trafficTimeRange').addEventListener('change', (e) => {
            this.loadTrafficData(e.target.value);
        });

        // Chart control buttons
        document.querySelectorAll('.chart-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.chart-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.updateAlertsChart(e.target.dataset.chart);
            });
        });

        // Modal controls
        document.getElementById('closeModal').addEventListener('click', () => {
            this.closeModal();
        });

        document.getElementById('closeModalBtn').addEventListener('click', () => {
            this.closeModal();
        });

        document.getElementById('acknowledgeBtn').addEventListener('click', () => {
            this.acknowledgeAlert();
        });

        // Close modal on outside click
        document.getElementById('alertModal').addEventListener('click', (e) => {
            if (e.target.id === 'alertModal') {
                this.closeModal();
            }
        });
    }

    async loadInitialData() {
        this.showLoading(true);
        try {
            await Promise.all([
                this.loadOverviewData(),
                this.loadAlerts(),
                this.loadTrafficData(24),
                this.loadSystemStatus(),
                this.loadSystemLogs()
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load dashboard data');
        } finally {
            this.showLoading(false);
        }
    }

    async loadOverviewData() {
        try {
            const [alertStats, networkStats, anomalies, systemHealth] = await Promise.all([
                this.fetchAPI('/api/alerts/stats'),
                this.fetchAPI('/api/network/stats?hours=24'),
                this.fetchAPI('/api/network/anomalies?hours=24'),
                this.fetchAPI('/api/status/health')
            ]);

            // Update metric cards
            document.getElementById('activeAlerts').textContent = alertStats.stats.by_status.active;
            document.getElementById('networkTraffic').textContent = 
                this.formatBytes(networkStats.stats.total_bytes);
            document.getElementById('detectedAnomalies').textContent = anomalies.count;
            document.getElementById('systemHealth').textContent = 
                systemHealth.health.status.charAt(0).toUpperCase() + systemHealth.health.status.slice(1);

            // Update status indicator
            this.updateSystemStatus(systemHealth.health.status);

            // Update change indicators (simulated for demo)
            this.updateChangeIndicator('alertsChange', '+2', 'positive');
            this.updateChangeIndicator('trafficChange', '+15%', 'positive');
            this.updateChangeIndicator('anomaliesChange', '-5', 'negative');
            this.updateChangeIndicator('healthChange', 'Stable', 'neutral');

        } catch (error) {
            console.error('Error loading overview data:', error);
        }
    }

    async loadAlerts() {
        try {
            const severityFilter = document.getElementById('severityFilter').value;
            const statusFilter = document.getElementById('statusFilter').value;
            
            let url = '/api/alerts?limit=50';
            if (severityFilter) url += `&severity=${severityFilter}`;
            if (statusFilter) url += `&status=${statusFilter}`;

            const response = await this.fetchAPI(url);
            this.renderAlertsTable(response.alerts);
            this.updateAlertsChart('severity');
        } catch (error) {
            console.error('Error loading alerts:', error);
        }
    }

    async loadTrafficData(hours = 24) {
        try {
            const response = await this.fetchAPI(`/api/network/traffic?hours=${hours}`);
            this.updateTrafficChart(response.traffic_data);
        } catch (error) {
            console.error('Error loading traffic data:', error);
        }
    }

    async loadSystemStatus() {
        try {
            const response = await this.fetchAPI('/api/status/components');
            this.renderSystemComponents(response.components);
            
            const healthResponse = await this.fetchAPI('/api/status/health');
            this.renderSystemMetrics(healthResponse.health.system_metrics);
        } catch (error) {
            console.error('Error loading system status:', error);
        }
    }

    async loadSystemLogs() {
        try {
            const response = await this.fetchAPI('/api/status/logs?limit=20');
            this.renderSystemLogs(response.logs);
        } catch (error) {
            console.error('Error loading system logs:', error);
        }
    }

    initializeCharts() {
        // Traffic Chart
        const trafficCtx = document.getElementById('trafficChart').getContext('2d');
        this.charts.traffic = new Chart(trafficCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Total Traffic (MB)',
                    data: [],
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                }
            }
        });

        // Alerts Chart
        const alertsCtx = document.getElementById('alertsChart').getContext('2d');
        this.charts.alerts = new Chart(alertsCtx, {
            type: 'doughnut',
            data: {
                labels: ['Critical', 'High', 'Medium', 'Low'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        '#f56565',
                        '#ed8936',
                        '#ecc94b',
                        '#48bb78'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    }

    updateTrafficChart(data) {
        if (!data || data.length === 0) return;

        const labels = data.map(item => {
            const date = new Date(item.timestamp);
            return date.toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        });

        const values = data.map(item => (item.total_bytes / (1024 * 1024)).toFixed(2));

        this.charts.traffic.data.labels = labels;
        this.charts.traffic.data.datasets[0].data = values;
        this.charts.traffic.update();
    }

    async updateAlertsChart(type) {
        try {
            const response = await this.fetchAPI('/api/alerts/stats');
            const stats = response.stats;

            if (type === 'severity') {
                this.charts.alerts.data.labels = ['Critical', 'High', 'Medium', 'Low'];
                this.charts.alerts.data.datasets[0].data = [
                    stats.by_severity.critical,
                    stats.by_severity.high,
                    stats.by_severity.medium,
                    stats.by_severity.low
                ];
                this.charts.alerts.data.datasets[0].backgroundColor = [
                    '#f56565', '#ed8936', '#ecc94b', '#48bb78'
                ];
            } else if (type === 'type') {
                // Get alert types from recent alerts
                const alertsResponse = await this.fetchAPI('/api/alerts?limit=100');
                const typeCounts = {};
                alertsResponse.alerts.forEach(alert => {
                    typeCounts[alert.type] = (typeCounts[alert.type] || 0) + 1;
                });

                const types = Object.keys(typeCounts);
                const counts = Object.values(typeCounts);
                const colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe'];

                this.charts.alerts.data.labels = types;
                this.charts.alerts.data.datasets[0].data = counts;
                this.charts.alerts.data.datasets[0].backgroundColor = colors.slice(0, types.length);
            }

            this.charts.alerts.update();
        } catch (error) {
            console.error('Error updating alerts chart:', error);
        }
    }

    renderAlertsTable(alerts) {
        const tbody = document.getElementById('alertsTableBody');
        tbody.innerHTML = '';

        if (!alerts || alerts.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 2rem; color: #718096;">No alerts found</td></tr>';
            return;
        }

        alerts.forEach(alert => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${this.formatDateTime(alert.timestamp)}</td>
                <td>${alert.type}</td>
                <td>${alert.source_ip}</td>
                <td>${alert.destination_ip}</td>
                <td><span class="severity-badge severity-${alert.severity.toLowerCase()}">${alert.severity}</span></td>
                <td><span class="status-badge status-${alert.status.toLowerCase()}">${alert.status}</span></td>
                <td>${alert.description.substring(0, 50)}${alert.description.length > 50 ? '...' : ''}</td>
                <td>
                    <button class="action-btn view-btn" onclick="dashboard.viewAlert(${alert.id})">View</button>
                    ${alert.status === 'Active' ? `<button class="action-btn ack-btn" onclick="dashboard.acknowledgeAlertFromTable(${alert.id})">Ack</button>` : ''}
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    renderSystemComponents(components) {
        const container = document.getElementById('componentsList');
        container.innerHTML = '';

        Object.entries(components).forEach(([name, component]) => {
            const item = document.createElement('div');
            item.className = 'component-item';
            item.innerHTML = `
                <span class="component-name">${this.formatComponentName(name)}</span>
                <div class="component-status status-${component.status}">
                    <span class="status-dot"></span>
                    <span>${component.status}</span>
                </div>
            `;
            container.appendChild(item);
        });
    }

    renderSystemMetrics(metrics) {
        const container = document.getElementById('systemMetrics');
        container.innerHTML = '';

        const metricItems = [
            { name: 'CPU Usage', value: `${metrics.cpu_percent.toFixed(1)}%` },
            { name: 'Memory Usage', value: `${metrics.memory_percent.toFixed(1)}%` },
            { name: 'Disk Usage', value: `${metrics.disk_percent.toFixed(1)}%` },
            { name: 'Memory Available', value: `${metrics.memory_available_gb} GB` },
            { name: 'Disk Free', value: `${metrics.disk_free_gb} GB` }
        ];

        metricItems.forEach(metric => {
            const item = document.createElement('div');
            item.className = 'metric-item';
            item.innerHTML = `
                <span class="metric-name">${metric.name}</span>
                <span class="metric-value-small">${metric.value}</span>
            `;
            container.appendChild(item);
        });
    }

    renderSystemLogs(logs) {
        const container = document.getElementById('logsContainer');
        container.innerHTML = '';

        if (!logs || logs.length === 0) {
            container.innerHTML = '<div style="text-align: center; padding: 1rem; color: #718096;">No logs available</div>';
            return;
        }

        logs.forEach(log => {
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.innerHTML = `
                <div class="log-time">${this.formatDateTime(log.timestamp)}</div>
                <span class="log-level log-${log.level.toLowerCase()}">${log.level}</span>
                <span class="log-message">${log.message}</span>
            `;
            container.appendChild(entry);
        });
    }

    async viewAlert(alertId) {
        try {
            const response = await this.fetchAPI(`/api/alerts/${alertId}`);
            this.currentAlert = response.alert;
            this.showAlertModal(response.alert);
        } catch (error) {
            console.error('Error loading alert details:', error);
            this.showError('Failed to load alert details');
        }
    }

    showAlertModal(alert) {
        const modalBody = document.getElementById('alertModalBody');
        modalBody.innerHTML = `
            <div style="display: grid; gap: 1rem;">
                <div><strong>Alert ID:</strong> ${alert.id}</div>
                <div><strong>Type:</strong> ${alert.type}</div>
                <div><strong>Timestamp:</strong> ${this.formatDateTime(alert.timestamp)}</div>
                <div><strong>Source IP:</strong> ${alert.source_ip}</div>
                <div><strong>Destination IP:</strong> ${alert.destination_ip}</div>
                <div><strong>Port:</strong> ${alert.port || 'N/A'}</div>
                <div><strong>Protocol:</strong> ${alert.protocol || 'N/A'}</div>
                <div><strong>Severity:</strong> <span class="severity-badge severity-${alert.severity.toLowerCase()}">${alert.severity}</span></div>
                <div><strong>Status:</strong> <span class="status-badge status-${alert.status.toLowerCase()}">${alert.status}</span></div>
                <div><strong>Description:</strong> ${alert.description}</div>
                ${alert.details && Object.keys(alert.details).length > 0 ? `
                    <div><strong>Additional Details:</strong>
                        <pre style="background: #f7fafc; padding: 1rem; border-radius: 8px; margin-top: 0.5rem; overflow-x: auto;">${JSON.stringify(alert.details, null, 2)}</pre>
                    </div>
                ` : ''}
            </div>
        `;

        const acknowledgeBtn = document.getElementById('acknowledgeBtn');
        acknowledgeBtn.style.display = alert.status === 'Active' ? 'block' : 'none';

        document.getElementById('alertModal').classList.add('show');
    }

    closeModal() {
        document.getElementById('alertModal').classList.remove('show');
        this.currentAlert = null;
    }

    async acknowledgeAlert() {
        if (!this.currentAlert) return;

        try {
            await this.fetchAPI(`/api/alerts/${this.currentAlert.id}/acknowledge`, 'PUT');
            this.closeModal();
            this.loadAlerts();
            this.loadOverviewData();
            this.showSuccess('Alert acknowledged successfully');
        } catch (error) {
            console.error('Error acknowledging alert:', error);
            this.showError('Failed to acknowledge alert');
        }
    }

    async acknowledgeAlertFromTable(alertId) {
        try {
            await this.fetchAPI(`/api/alerts/${alertId}/acknowledge`, 'PUT');
            this.loadAlerts();
            this.loadOverviewData();
            this.showSuccess('Alert acknowledged successfully');
        } catch (error) {
            console.error('Error acknowledging alert:', error);
            this.showError('Failed to acknowledge alert');
        }
    }

    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            this.loadOverviewData();
            this.loadAlerts();
            this.loadSystemStatus();
            this.updateLastUpdateTime();
        }, 30000); // Refresh every 30 seconds
    }

    updateLastUpdateTime() {
        const now = new Date();
        document.getElementById('lastUpdate').textContent = now.toLocaleTimeString();
    }

    updateSystemStatus(status) {
        const statusElement = document.getElementById('systemStatus');
        statusElement.className = `status-indicator ${status}`;
        statusElement.querySelector('span').textContent = `System ${status.charAt(0).toUpperCase() + status.slice(1)}`;
    }

    updateChangeIndicator(elementId, value, type) {
        const element = document.getElementById(elementId);
        element.textContent = value;
        element.className = `metric-change ${type}`;
    }

    async fetchAPI(endpoint, method = 'GET', body = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            }
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        const response = await fetch(endpoint, options);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (show) {
            overlay.classList.add('show');
        } else {
            overlay.classList.remove('show');
        }
    }

    showError(message) {
        // Simple error notification (could be enhanced with a proper notification system)
        console.error(message);
        alert(`Error: ${message}`);
    }

    showSuccess(message) {
        // Simple success notification (could be enhanced with a proper notification system)
        console.log(message);
        // You could implement a toast notification here
    }

    formatDateTime(timestamp) {
        if (!timestamp) return 'N/A';
        const date = new Date(timestamp);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    setupChartModal() {
        // Setup modal close functionality
        const modal = document.getElementById('chartModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeChartModal();
                }
            });
        }
    }

    showChartModal(chartType) {
        const modal = document.getElementById('chartModal');
        const modalTitle = document.getElementById('chartModalTitle');
        const modalCanvas = document.getElementById('modalChart');
        
        if (!modal || !modalTitle || !modalCanvas) return;
        
        // Set modal title
        if (chartType === 'traffic') {
            modalTitle.textContent = 'Network Traffic Overview';
        } else if (chartType === 'alerts') {
            modalTitle.textContent = 'Alert Distribution';
        }
        
        // Show modal
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        
        // Create chart in modal
        setTimeout(() => {
            this.createModalChart(chartType, modalCanvas);
        }, 100);
    }

    closeChartModal() {
        const modal = document.getElementById('chartModal');
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
            
            // Destroy existing chart
            if (this.modalChart) {
                this.modalChart.destroy();
                this.modalChart = null;
            }
        }
    }

    async createModalChart(chartType, canvas) {
        if (this.modalChart) {
            this.modalChart.destroy();
        }
        
        const ctx = canvas.getContext('2d');
        
        if (chartType === 'traffic') {
            await this.createTrafficChart(ctx);
        } else if (chartType === 'alerts') {
            await this.createAlertChart(ctx);
        }
    }

    async createTrafficChart(ctx) {
        try {
            const response = await this.fetchAPI('/api/network/traffic?hours=24');
            const data = response.data || [];
            
            // Process data for chart
            const labels = [];
            const values = [];
            
            // Generate hourly data points for the last 24 hours
            const now = new Date();
            for (let i = 23; i >= 0; i--) {
                const time = new Date(now.getTime() - i * 60 * 60 * 1000);
                labels.push(time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }));
                
                // Simulate traffic data (in real implementation, this would come from API)
                const baseTraffic = Math.random() * 1000 + 500;
                const variation = Math.sin(i * 0.5) * 200;
                values.push(Math.max(0, baseTraffic + variation));
            }
            
            this.modalChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Network Traffic (MB)',
                        data: values,
                        borderColor: 'rgb(102, 126, 234)',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Traffic (MB)'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Time'
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error creating traffic chart:', error);
        }
    }

    async createAlertChart(ctx) {
        try {
            const response = await this.fetchAPI('/api/alerts/stats');
            const stats = response.stats || {};
            
            // Get current chart type (severity or type)
            const activeToggle = document.querySelector('.chart-toggle.active');
            const chartType = activeToggle ? activeToggle.dataset.type : 'severity';
            
            let labels, data, colors;
            
            if (chartType === 'severity') {
                labels = ['Critical', 'High', 'Medium', 'Low'];
                data = [
                    stats.by_severity?.critical || 0,
                    stats.by_severity?.high || 0,
                    stats.by_severity?.medium || 0,
                    stats.by_severity?.low || 0
                ];
                colors = ['#f56565', '#ed8936', '#ecc94b', '#48bb78'];
            } else {
                // For alert types, we'll use some sample data
                labels = ['DDoS', 'Port Scan', 'Brute Force', 'Unusual Traffic'];
                data = [2, 1, 1, 2]; // Sample data
                colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c'];
            }
            
            this.modalChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: colors,
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 20,
                                usePointStyle: true
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error creating alert chart:', error);
        }
    }

    formatComponentName(name) {
        return name.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new NetworkDashboard();
});

// Handle page visibility changes to pause/resume auto-refresh
document.addEventListener('visibilitychange', () => {
    if (window.dashboard) {
        if (document.hidden) {
            if (window.dashboard.refreshInterval) {
                clearInterval(window.dashboard.refreshInterval);
            }
        } else {
            window.dashboard.startAutoRefresh();
            window.dashboard.loadInitialData();
        }
    }
});

