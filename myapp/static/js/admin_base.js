// Apply sidebar state immediately - BEFORE DOMContentLoaded
// This code runs as soon as the script is loaded
(function() {
    if (window.innerWidth > 991) { // Not mobile
        const sidebarMinimized = localStorage.getItem('sidebarMinimized') === 'true';
        if (sidebarMinimized) {
            document.documentElement.classList.add('sidebar-starts-minimized');
            document.body.classList.add('sidebar-minimized-body');
        }
    }
})();

document.addEventListener('DOMContentLoaded', () => {
    // Enable transitions after page load
    setTimeout(() => {
        document.body.classList.add('transitions-enabled');
    }, 300);
    
    // Initialize all dropdowns
    var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    var dropdownList = dropdownElementList.map((dropdownToggleEl) => new bootstrap.Dropdown(dropdownToggleEl));

    const sidebar = document.getElementById('sidebar');
    const content = document.getElementById('content');
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    const overlay = document.getElementById('sidebarOverlay');
    
    // Function to check if we're on mobile
    const isMobile = () => window.innerWidth <= 991;

    // Apply sidebar state as soon as DOM is ready
    if (!isMobile() && sidebar) {
        const sidebarMinimized = localStorage.getItem('sidebarMinimized') === 'true';
        if (sidebarMinimized) {
            sidebar.classList.add('minimized');
            content.classList.add('expanded');
        }
    }

    // Function to toggle sidebar
    function toggleSidebar() {
        if (isMobile()) {
            sidebar.classList.toggle('active');
            overlay.classList.toggle('active');
        } else {
            sidebar.classList.toggle('minimized');
            content.classList.toggle('expanded');
            document.body.classList.toggle('sidebar-minimized-body');
            
            // Save sidebar state to localStorage
            localStorage.setItem('sidebarMinimized', sidebar.classList.contains('minimized'));
        }
    }

    // Add click event to sidebar toggle button
    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', (e) => {
            e.preventDefault();
            toggleSidebar();
        });
    }

    // Add click event to overlay
    if (overlay) {
        overlay.addEventListener('click', () => {
            if (isMobile() && sidebar.classList.contains('active')) {
                toggleSidebar();
            }
        });
    }

    // Close sidebar when clicking a link (for mobile only)
    if (sidebar) {
        const sidebarLinks = sidebar.querySelectorAll('a');
        sidebarLinks.forEach(link => {
            link.addEventListener('click', () => {
                // Only toggle for mobile
                if (isMobile() && sidebar.classList.contains('active')) {
                    toggleSidebar();
                }
                // For desktop, just make sure we save the current state
                if (!isMobile()) {
                    localStorage.setItem('sidebarMinimized', sidebar.classList.contains('minimized'));
                    console.log('Sidebar state saved on link click:', sidebar.classList.contains('minimized'));
                }
            });
        });
    }

    // Check localStorage for saved sidebar state on page load
    if (!isMobile() && sidebar) {
        const sidebarMinimized = localStorage.getItem('sidebarMinimized') === 'true';
        console.log('Loading sidebar state:', sidebarMinimized);
        
        if (sidebarMinimized) {
            sidebar.classList.add('minimized');
            content.classList.add('expanded');
        } else {
            sidebar.classList.remove('minimized');
            content.classList.remove('expanded');
        }
    }

    // Handle window resize
    window.addEventListener('resize', () => {
        if (window.innerWidth > 991) {
            // On desktop
            if (sidebar) {
                sidebar.classList.remove('active');
                overlay.classList.remove('active');
                
                // Apply minimized state from localStorage when returning to desktop
                const sidebarMinimized = localStorage.getItem('sidebarMinimized') === 'true';
                if (sidebarMinimized) {
                    sidebar.classList.add('minimized');
                    content.classList.add('expanded');
                }
            }
        } else {
            // On mobile
            if (sidebar && sidebar.classList.contains('minimized')) {
                sidebar.classList.remove('minimized');
                content.classList.remove('expanded');
            }
        }
    });

    // Add animation classes to dropdown menu when shown
    const dropdowns = document.querySelectorAll('.dropdown');
    dropdowns.forEach(dropdown => {
        dropdown.addEventListener('shown.bs.dropdown', function() {
            const menu = this.querySelector('.dropdown-menu');
            menu.classList.add('animate-dropdown');
        });
        
        dropdown.addEventListener('hide.bs.dropdown', function() {
            const menu = this.querySelector('.dropdown-menu');
            menu.classList.remove('animate-dropdown');
        });
    });

    // Add hover effect to sidebar items
    const sidebarItems = document.querySelectorAll('.components a');
    sidebarItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            const icon = this.querySelector('i');
            if (icon) {
                icon.classList.add('fa-beat-fade');
            }
        });
        
        item.addEventListener('mouseleave', function() {
            const icon = this.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-beat-fade');
            }
        });
    });

    // Add ripple effect to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const x = e.clientX - e.target.getBoundingClientRect().left;
            const y = e.clientY - e.target.getBoundingClientRect().top;
            
            const ripple = document.createElement('span');
            ripple.classList.add('ripple-effect');
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
});

