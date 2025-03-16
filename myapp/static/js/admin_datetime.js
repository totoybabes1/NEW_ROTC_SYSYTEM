document.addEventListener('DOMContentLoaded', function() {
    function updateDateTime() {
        const now = new Date();

        // Update date
        const options = {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        };
        const dateElement = document.getElementById('currentDate');
        if (dateElement) {
            dateElement.textContent = now.toLocaleDateString('en-US', options);
        }

        // Update time
        const timeElement = document.getElementById('currentTime');
        if (timeElement) {
            timeElement.textContent = now.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }
    }

    // Update immediately and then every second
    updateDateTime();
    setInterval(updateDateTime, 1000);
});