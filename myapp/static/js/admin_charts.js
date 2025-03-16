document.addEventListener('DOMContentLoaded', function() {
    // Initialize AOS
    AOS.init({
        duration: 800,
        once: true
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
    const genderColors = {
        Male: '#4a90e2',
        Female: '#e25c5c',
        'Non-binary': '#50c878',
        Other: '#ffd700'
    };

    function createGenderChart(type = 'pie') {
        const genderCtx = document.getElementById('genderChart')?.getContext('2d');
        if (!genderCtx) {
            console.error('Gender chart context not found');
            return;
        }

        if (genderChart) {
            genderChart.destroy();
        }

        genderChart = new Chart(genderCtx, {
            type: type,
            data: {
                labels: ['Male', 'Female', 'Non-binary', 'Other'],
                datasets: [{
                    data: [
                        genderMale,
                        genderFemale,
                        genderNonbinary,
                        genderOther
                    ],
                    backgroundColor: Object.values(genderColors),
                    borderWidth: 1,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                ...chartDefaults,
                plugins: {
                    ...chartDefaults.plugins,
                    title: {
                        display: true,
                        text: 'Personnel Gender Distribution',
                        padding: {
                            top: 10,
                            bottom: 10
                        },
                        font: {
                            size: 14
                        }
                    }
                }
            }
        });
    }

    // Flight Group Members Chart
    let groupChart;
    function createGroupChart(type = 'bar') {
        const groupCtx = document.getElementById('groupChart')?.getContext('2d');
        if (!groupCtx) {
            console.error('Group chart context not found');
            return;
        }

        if (groupChart) {
            groupChart.destroy();
        }

        const chartConfig = {
            type: type,
            data: {
                labels: groupNames,
                datasets: [{
                    label: 'Members',
                    data: groupMembers,
                    backgroundColor: 'rgba(74, 144, 226, 0.7)',
                    borderColor: '#4a90e2',
                    borderWidth: 1
                }]
            },
            options: {
                ...chartDefaults,
                scales: type !== 'radar' ? {
                    y: {
                        beginAtZero: true,
                        grid: {
                            display: true,
                            drawBorder: false
                        },
                        ticks: {
                            font: {
                                size: 11
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                size: 11
                            }
                        }
                    }
                } : {},
                plugins: {
                    ...chartDefaults.plugins,
                    title: {
                        display: true,
                        text: 'Flight Group Distribution',
                        padding: {
                            top: 10,
                            bottom: 10
                        },
                        font: {
                            size: 14
                        }
                    }
                }
            }
        };

        groupChart = new Chart(groupCtx, chartConfig);
    }

    // Initialize charts
    createGenderChart('pie');
    createGroupChart('bar');

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