class ActivityManager {
    constructor() {
        this.initializeElements();
        this.initializeEventListeners();
        this.setupInitialDisplay();
    }

    initializeElements() {
        this.searchInput = document.getElementById('activitySearch');
        this.activityItems = document.querySelectorAll('.activity-item');
        this.activityTimeline = document.querySelector('.activity-timeline');
    }

    initializeEventListeners() {
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => this.handleSearch(e));
        }
    }

    setupInitialDisplay() {
        // Ensure all activities are visible initially
        this.activityItems.forEach(item => {
            item.style.display = 'flex';
            // Add animation delay for staggered appearance
            const index = Array.from(this.activityItems).indexOf(item);
            item.style.animationDelay = `${index * 0.1}s`;
        });
    }

    handleSearch(e) {
        const searchTerm = e.target.value.toLowerCase();

        this.activityItems.forEach(item => {
            const description = item.querySelector('.activity-description').textContent.toLowerCase();
            const user = item.querySelector('.activity-user').textContent.toLowerCase();
            const matches = description.includes(searchTerm) || user.includes(searchTerm);

            // Use animation for hiding/showing
            if (matches) {
                item.style.display = 'flex';
                item.style.animation = 'fadeInUp 0.3s ease-out forwards';
            } else {
                item.style.display = 'none';
            }
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing ActivityManager');
    const activityManager = new ActivityManager();
}); 