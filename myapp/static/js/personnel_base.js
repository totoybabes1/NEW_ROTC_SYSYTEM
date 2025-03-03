document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const content = document.getElementById('content');
    const sidebarCollapse = document.getElementById('sidebarCollapse');

    // Toggle sidebar with transition
    sidebarCollapse.addEventListener('click', function() {
        sidebar.classList.toggle('collapsed');
        content.classList.toggle('expanded');
        
        // Store the collapsed state in localStorage
        localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    });

    // Restore sidebar state from localStorage
    const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (sidebarCollapsed) {
        sidebar.classList.add('collapsed');
        content.classList.add('expanded');
    }

    // Handle responsive behavior
    function handleResize() {
        if (window.innerWidth <= 768) {
            sidebar.classList.add('collapsed');
            content.classList.add('expanded');
        } else {
            // Restore the saved state when returning to desktop view
            const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
            if (!sidebarCollapsed) {
                sidebar.classList.remove('collapsed');
                content.classList.remove('expanded');
            }
        }
    }

    // Initial check and event listener for window resize
    handleResize();
    window.addEventListener('resize', handleResize);
}); 