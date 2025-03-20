document.addEventListener('DOMContentLoaded', function() {
    // Initialize AOS
    AOS.init({
        duration: 800,
        once: true,
        easing: 'ease-out-cubic'
    });

    // Update the chart options
    const chartDefaults = {
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    font: {
                        family: "'Poppins', sans-serif",
                        size: 11
                    },
                    padding: 10
                }
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                padding: 8,
                titleFont: {
                    size: 12
                },
                bodyFont: {
                    size: 11
                },
                cornerRadius: 4
            }
        },
        maintainAspectRatio: false,
        responsive: true
    };

    // Gender Distribution Chart
    let genderChart;
    let groupChart;

    // Chart.js global defaults to match the design
    Chart.defaults.font.family = "'Segoe UI', 'Roboto', sans-serif";
    Chart.defaults.color = '#666';
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(50, 50, 50, 0.8)';
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 6;
    Chart.defaults.plugins.tooltip.titleFont = {size: 14, weight: 'bold'};
    Chart.defaults.plugins.tooltip.bodyFont = {size: 13};
    Chart.defaults.plugins.legend.labels.padding = 15;
    Chart.defaults.elements.bar.borderRadius = 8;
    Chart.defaults.elements.line.borderCapStyle = 'round';
    Chart.defaults.elements.point.radius = 41;
    Chart.defaults.elements.point.hoverRadius = 61;

    function createGenderChart(type = 'pie') {
        const genderCtx = document.getElementById('genderChart')?.getContext('2d');
        if (!genderCtx) {
            console.error('Gender chart context not found');
            return;
        }
        
        // Modern color palette
        const colors = ['#6c5ce7', '#e84393', '#00b894', '#fdcb6e'];
        
        // Use the global variables set by data-initialization.js
        const data = {
            labels: ['Male', 'Female', 'Non-binary', 'Other'],
            datasets: [{
                data: [
                    window.genderMale || 0,
                    window.genderFemale || 0, 
                    window.genderNonbinary || 0,
                    window.genderOther || 0
                ],
                backgroundColor: colors,
                borderWidth: 0,
                hoverOffset: 15
            }]
        };
        
        // Chart configuration
        const chartConfig = {
            type: type,
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: type === 'doughnut' ? '70%' : undefined
            }
        };
        
        // Destroy existing chart if it exists
        if (genderChart) {
            genderChart.destroy();
        }
        
        genderChart = new Chart(genderCtx, chartConfig);
    }

    // Flight Group Members Chart
    function createGroupChart(type = 'bar') {
        const groupCtx = document.getElementById('groupChart')?.getContext('2d');
        if (!groupCtx) {
            console.error('Group chart context not found');
            return;
        }
        
        // Modern gradient for bar chart
        let gradient;
        if (groupCtx && type === 'bar') {
            gradient = groupCtx.createLinearGradient(0, 0, 0, 400);
            gradient.addColorStop(0, '#6c5ce7');
            gradient.addColorStop(1, 'rgba(108, 92, 231, 0.2)');
        }
        
        // Line chart gradient
        let lineGradient;
        if (groupCtx && type === 'line') {
            lineGradient = groupCtx.createLinearGradient(0, 0, 0, 400);
            lineGradient.addColorStop(0, 'rgba(108, 92, 231, 0.8)');
            lineGradient.addColorStop(1, 'rgba(108, 92, 231, 0)');
        }
        
        const data = {
            labels: window.groupNames || [],
            datasets: [{
                label: 'Members',
                data: window.groupMembers || [],
                backgroundColor: type === 'bar' ? gradient : 
                                 type === 'radar' ? 'rgba(108, 92, 231, 0.5)' : 
                                 '#6c5ce7',
                borderColor: '#6c5ce7',
                borderWidth: type === 'line' ? 3 : 0,
                pointBackgroundColor: '#fff',
                pointBorderColor: '#6c5ce7',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6,
                fill: type === 'line' ? {
                    target: 'origin',
                    above: lineGradient
                } : false,
                tension: 0.4
            }]
        };
        
        const chartConfig = {
            type: type,
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            title: function(tooltipItems) {
                                return tooltipItems[0].label;
                            },
                            label: function(context) {
                                return `Members: ${context.raw}`;
                            }
                        }
                    }
                },
                scales: type !== 'radar' ? {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            padding: 10
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            padding: 10,
                            callback: function(value) {
                                return value;
                            }
                        }
                    }
                } : {},
                elements: {
                    bar: {
                        borderRadius: 8,
                        borderSkipped: false
                    },
                    line: {
                        tension: 0.4
                    },
                    point: {
                        radius: 4,
                        hoverRadius: 6
                    }
                }
            }
        };
        
        // Destroy existing chart if it exists
        if (groupChart) {
            groupChart.destroy();
        }
        
        groupChart = new Chart(groupCtx, chartConfig);
    }

    // Function to update charts when data changes
    window.updateCharts = function() {
        createGenderChart('pie');
        createGroupChart('bar');
    };

    // Initialize charts when DOM is loaded
    if (window.groupNames && window.groupMembers) {
        createGenderChart('pie');
        createGroupChart('bar');
    }

    // Event listeners for chart controls
    document.querySelectorAll('.chart-toggle').forEach(button => {
        button.addEventListener('click', (e) => {
            const chartType = e.target.closest('button').dataset.chart;
            createGenderChart(chartType);
        });
    });

    document.getElementById('groupChartView')?.addEventListener('change', (e) => {
        createGroupChart(e.target.value);
    });
});