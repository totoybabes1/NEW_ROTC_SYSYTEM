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