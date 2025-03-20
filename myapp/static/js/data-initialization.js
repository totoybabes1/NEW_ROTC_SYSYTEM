// Create this file to initialize chart data that is passed from Django template
// Place this before the admin_charts.js script in your HTML

// Add this to your Django template where you load your JS files
// These variables need to be populated with Django template variables
document.addEventListener('DOMContentLoaded', function() {
    // Gender data
    window.genderMale = {{ stats.gender_male }};
    window.genderFemale = {{ stats.gender_female }};
    window.genderNonbinary = {{ stats.gender_nonbinary }};
    window.genderOther = {{ stats.gender_other }};

    // Group data
    window.groupNames = {{ group_names|safe }};
    window.groupMembers = {{ group_members }};
});

// Create global variables for chart data
window.initializeChartData = function(genderData, groupData) {
    // Gender data
    window.genderMale = genderData.male;
    window.genderFemale = genderData.female;
    window.genderNonbinary = genderData.nonbinary;
    window.genderOther = genderData.other;
    
    // Group data
    window.groupNames = groupData.names;
    window.groupMembers = groupData.members;
    
    // If charts are already initialized, update them
    if (window.updateCharts) {
        window.updateCharts();
    }
};