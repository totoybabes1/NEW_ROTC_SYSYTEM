document.addEventListener('DOMContentLoaded', function() {
    // Initialize all modals
    var modals = document.querySelectorAll('.modal');
    modals.forEach(function(modal) {
        new bootstrap.Modal(modal);
        
        // Add event listener for when modal is hidden
        modal.addEventListener('hidden.bs.modal', function () {
            // Remove modal backdrop
            const modalBackdrops = document.getElementsByClassName('modal-backdrop');
            while(modalBackdrops.length > 0) {
                modalBackdrops[0].remove();
            }
            // Re-enable scrolling on body
            document.body.classList.remove('modal-open');
        });
    });

    // Add click handlers for edit buttons
    var editButtons = document.querySelectorAll('[data-bs-toggle="modal"]');
    editButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            // Remove any existing backdrops first
            const existingBackdrops = document.getElementsByClassName('modal-backdrop');
            while(existingBackdrops.length > 0) {
                existingBackdrops[0].remove();
            }
            
            var targetModal = document.querySelector(button.getAttribute('data-bs-target'));
            var modal = new bootstrap.Modal(targetModal);
            modal.show();
        });
    });

    // Handle form submissions
    var forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            // Add any form validation here if needed
        });
    });

    // Add click handlers for modal close buttons
    var closeButtons = document.querySelectorAll('[data-bs-dismiss="modal"]');
    closeButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            // Remove modal backdrop
            const modalBackdrops = document.getElementsByClassName('modal-backdrop');
            while(modalBackdrops.length > 0) {
                modalBackdrops[0].remove();
            }
            // Re-enable scrolling on body
            document.body.classList.remove('modal-open');
        });
    });

    const searchInput = document.getElementById('searchInput');
    const sortSelect = document.getElementById('sortSelect');
    const table = document.getElementById('personnelTable');
    const tbody = table.getElementsByTagName('tbody')[0];
    const rows = Array.from(tbody.getElementsByTagName('tr'));
    
    // Search function with count update
    function searchTable() {
        const searchTerm = searchInput.value.toLowerCase();
        let visibleCount = 0;
        
        rows.forEach(row => {
            const name = row.querySelector('.fw-bold').textContent.toLowerCase();
            const position = row.cells[2].textContent.toLowerCase();
            const status = row.cells[3].textContent.toLowerCase();
            const flightGroup = row.cells[4].textContent.toLowerCase();
            
            if (name.includes(searchTerm) || 
                position.includes(searchTerm) || 
                status.includes(searchTerm) ||
                flightGroup.includes(searchTerm)) {
                row.style.display = '';
                visibleCount++;
                highlightText(row, searchTerm);
            } else {
                row.style.display = 'none';
            }
        });
        
        // Update total count with animation
        updateTotalCount(visibleCount);
    }

    // Highlight matching text
    function highlightText(row, searchTerm) {
        if (searchTerm === '') {
            // Reset highlights if search is empty
            row.querySelectorAll('.highlight').forEach(el => {
                el.outerHTML = el.textContent;
            });
            return;
        }

        const elements = [
            row.querySelector('.fw-bold'),
            row.cells[2],
            row.cells[3],
            row.cells[4]
        ];

        elements.forEach(element => {
            if (!element) return;
            
            const text = element.textContent;
            const regex = new RegExp(searchTerm, 'gi');
            
            if (text.toLowerCase().includes(searchTerm)) {
                element.innerHTML = text.replace(
                    regex, 
                    match => `<span class="highlight">${match}</span>`
                );
            }
        });
    }

    // Update total count with animation
    function updateTotalCount(newCount) {
        const totalElement = document.getElementById('totalPersonnel');
        const currentCount = parseInt(totalElement.textContent);
        
        if (currentCount !== newCount) {
            animateCount(currentCount, newCount, totalElement);
        }
    }

    // Animate count function
    function animateCount(start, end, element) {
        let current = start;
        const duration = 300; // Animation duration in milliseconds
        const stepTime = 20; // Time between steps in milliseconds
        const steps = duration / stepTime;
        const increment = (end - start) / steps;

        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                clearInterval(timer);
                element.textContent = end;
            } else {
                element.textContent = Math.round(current);
            }
        }, stepTime);
    }

    // Sort function with count update
    function sortTable(sortValue) {
        rows.sort((a, b) => {
            let aValue, bValue;
            
            switch(sortValue) {
                case 'name_asc':
                case 'name_desc':
                    aValue = a.querySelector('.fw-bold').textContent.toLowerCase();
                    bValue = b.querySelector('.fw-bold').textContent.toLowerCase();
                    break;
                case 'position_asc':
                case 'position_desc':
                    aValue = a.cells[2].textContent.toLowerCase();
                    bValue = b.cells[2].textContent.toLowerCase();
                    break;
                default:
                    return 0;
            }
            
            const comparison = aValue.localeCompare(bValue);
            return sortValue.endsWith('desc') ? -comparison : comparison;
        });

        // Clear and re-append sorted rows
        tbody.innerHTML = '';
        rows.forEach(row => tbody.appendChild(row));
        
        // Update count after sorting
        const visibleCount = rows.filter(row => row.style.display !== 'none').length;
        updateTotalCount(visibleCount);
    }

    // Event listeners
    searchInput.addEventListener('input', searchTable);
    sortSelect.addEventListener('change', (e) => sortTable(e.target.value));

    // Add these styles for search highlighting
    const style = document.createElement('style');
    style.textContent = `
        .highlight {
            background-color: #fff3cd;
            padding: 0.1em 0.2em;
            border-radius: 3px;
            font-weight: bold;
        }

        #searchInput:focus {
            box-shadow: 0 0 0 0.2rem rgba(78, 115, 223, 0.25);
            border-color: #4e73df;
        }

        .input-group-text {
            background-color: #f8f9fa;
            border-right: none;
        }

        #searchInput {
            border-left: none;
        }

        #searchInput::placeholder {
            color: #6c757d;
            font-size: 0.875rem;
        }

        @keyframes highlightFade {
            from { background-color: #fff3cd; }
            to { background-color: transparent; }
        }

        .highlight {
            animation: highlightFade 2s ease-in-out;
        }
    `;
    document.head.appendChild(style);

    // Handle image loading
    const profileImages = document.querySelectorAll('.profile-preview');
    profileImages.forEach(img => {
        img.addEventListener('load', function() {
            this.style.opacity = '1';
        });
    });

    // Add keyboard navigation for modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal && modal.classList.contains('show')) {
                    bsModal.hide();
                }
            });
        }
    });
}); 