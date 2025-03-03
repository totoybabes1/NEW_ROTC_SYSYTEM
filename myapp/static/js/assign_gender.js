function toggleSelectAll(source) {
    const checkboxes = document.querySelectorAll('.select-person');
    checkboxes.forEach(checkbox => {
        checkbox.checked = source.checked;
    });
}

function submitBulkAssign(gender) {
    const selectedCheckboxes = document.querySelectorAll('.select-person:checked');
    
    if (selectedCheckboxes.length === 0) {
        alert('Please select at least one person.');
        return;
    }

    if (confirm(`Are you sure you want to assign ${gender} to the selected personnel?`)) {
        const form = document.getElementById('bulkAssignForm');
        const genderInput = document.getElementById('gender_to_assign');
        
        // Remove any existing personnel inputs
        const existingInputs = form.querySelectorAll('input[name="selected_personnel"]');
        existingInputs.forEach(input => input.remove());

        // Add selected personnel to the form
        selectedCheckboxes.forEach(checkbox => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'selected_personnel';
            input.value = checkbox.value;
            form.appendChild(input);
        });
        
        // Set the gender and submit
        genderInput.value = gender;
        form.submit();
        showFeedbackMessage();
    }
}

function toggleSelectAllCheckboxes() {
    const selectAllCheckbox = document.getElementById('select_all');
    selectAllCheckbox.checked = !selectAllCheckbox.checked;
    toggleSelectAll(selectAllCheckbox);
}

function filterPersonnel() {
    const input = document.getElementById('searchInput');
    const filter = input.value.toLowerCase();
    const table = document.getElementById('personnelTable');
    const rows = table.getElementsByTagName('tr');

    for (let i = 0; i < rows.length; i++) {
        const nameCell = rows[i].getElementsByTagName('td')[1];
        if (nameCell) {
            const name = nameCell.textContent || nameCell.innerText;
            rows[i].style.display = name.toLowerCase().indexOf(filter) > -1 ? '' : 'none';
        }
    }
}

function showFeedbackMessage() {
    const feedbackMessage = document.getElementById('feedbackMessage');
    feedbackMessage.classList.remove('d-none');
    setTimeout(() => {
        feedbackMessage.classList.add('d-none');
    }, 3000);
}

function renderGenderChart() {
    const ctx = document.getElementById('genderChart').getContext('2d');
    const maleCount = document.querySelectorAll('select.gender-select option[value="Male"]:checked').length;
    const femaleCount = document.querySelectorAll('select.gender-select option[value="Female"]:checked').length;
    const nonBinaryCount = document.querySelectorAll('select.gender-select option[value="Non-binary"]:checked').length;
    const otherCount = document.querySelectorAll('select.gender-select option[value="Other"]:checked').length;

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    boxWidth: 10,
                    padding: 5
                }
            }
        }
    };

    const genderChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Male', 'Female', 'Non-binary', 'Other'],
            datasets: [{
                data: [maleCount, femaleCount, nonBinaryCount, otherCount],
                backgroundColor: [
                    '#4e73df',
                    '#e74a3b',
                    '#f6c23e',
                    '#36b9cc'
                ],
                borderWidth: 0
            }]
        },
        options: chartOptions
    });
}

document.addEventListener('DOMContentLoaded', renderGenderChart); 