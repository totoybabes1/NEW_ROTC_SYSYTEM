document.addEventListener('DOMContentLoaded', function() {
    const calendarDays = document.getElementById('calendarDays');
    const currentMonthElement = document.getElementById('currentMonth');
    const selectedDateElement = document.getElementById('selectedDate');
    const eventListElement = document.getElementById('eventList');
    const prevMonthButton = document.getElementById('prevMonth');
    const nextMonthButton = document.getElementById('nextMonth');
    
    let currentDate = new Date();
    let selectedDate = new Date();
    
    // Sample events data - in a real app, this would come from your backend
    const events = {
        // Format: 'YYYY-MM-DD': [{time: 'HH:MM', title: 'Event Title'}]
        [formatDateKey(new Date())]: [
            {time: '09:00 AM', title: 'Morning Briefing'},
            {time: '02:30 PM', title: 'Team Meeting'}
        ],
        [formatDateKey(new Date(new Date().setDate(new Date().getDate() + 2)))]: [
            {time: '11:00 AM', title: 'Project Review'},
            {time: '04:00 PM', title: 'Client Call'}
        ]
    };
    
    // Initialize calendar
    generateCalendar(currentDate);
    updateSelectedDateDisplay(selectedDate);
    loadEvents(selectedDate);
    
    // Event listeners for month navigation
    prevMonthButton.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        generateCalendar(currentDate);
    });
    
    nextMonthButton.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        generateCalendar(currentDate);
    });
    
    // Generate calendar for given date
    function generateCalendar(date) {
        // Clear previous calendar
        calendarDays.innerHTML = '';
        
        // Set current month display
        const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 
                           'July', 'August', 'September', 'October', 'November', 'December'];
        currentMonthElement.textContent = `${monthNames[date.getMonth()]} ${date.getFullYear()}`;
        
        // Get first day of month and total days
        const firstDay = new Date(date.getFullYear(), date.getMonth(), 1);
        const lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0);
        const totalDays = lastDay.getDate();
        const startingDay = firstDay.getDay(); // 0 = Sunday, 1 = Monday, etc.
        
        // Create empty cells for days before the first day of month
        for (let i = 0; i < startingDay; i++) {
            const prevMonthLastDay = new Date(date.getFullYear(), date.getMonth(), 0).getDate();
            const dayElement = document.createElement('div');
            dayElement.textContent = prevMonthLastDay - (startingDay - i - 1);
            dayElement.classList.add('other-month');
            calendarDays.appendChild(dayElement);
        }
        
        // Create cells for each day of the month
        const today = new Date();
        for (let day = 1; day <= totalDays; day++) {
            const dayElement = document.createElement('div');
            dayElement.textContent = day;
            
            // Check if this day is today
            if (date.getFullYear() === today.getFullYear() && 
                date.getMonth() === today.getMonth() && 
                day === today.getDate()) {
                dayElement.classList.add('today');
            }
            
            // Check if this day is selected
            if (selectedDate && 
                date.getFullYear() === selectedDate.getFullYear() && 
                date.getMonth() === selectedDate.getMonth() && 
                day === selectedDate.getDate()) {
                dayElement.classList.add('selected');
            }
            
            // Check if this day has events
            const dateKey = formatDateKey(new Date(date.getFullYear(), date.getMonth(), day));
            if (events[dateKey] && events[dateKey].length > 0) {
                dayElement.classList.add('has-events');
            }
            
            // Add click event to select a day
            dayElement.addEventListener('click', () => {
                // Remove selected class from previously selected day
                const previouslySelected = document.querySelector('.calendar-days .selected');
                if (previouslySelected) {
                    previouslySelected.classList.remove('selected');
                }
                
                // Add selected class to clicked day
                dayElement.classList.add('selected');
                
                // Update selected date
                selectedDate = new Date(date.getFullYear(), date.getMonth(), day);
                updateSelectedDateDisplay(selectedDate);
                loadEvents(selectedDate);
            });
            
            calendarDays.appendChild(dayElement);
        }
        
        // Fill in remaining days from next month if needed
        const totalCells = calendarDays.childElementCount;
        const remainingCells = 42 - totalCells; // 6 rows of 7 days
        
        for (let i = 1; i <= remainingCells; i++) {
            const dayElement = document.createElement('div');
            dayElement.textContent = i;
            dayElement.classList.add('other-month');
            calendarDays.appendChild(dayElement);
        }
    }
    
    // Update the selected date display
    function updateSelectedDateDisplay(date) {
        const options = { weekday: 'long', month: 'long', day: 'numeric' };
        selectedDateElement.textContent = date.toLocaleDateString('en-US', options);
    }
    
    // Load events for the selected date
    function loadEvents(date) {
        const dateKey = formatDateKey(date);
        eventListElement.innerHTML = '';
        
        if (events[dateKey] && events[dateKey].length > 0) {
            events[dateKey].forEach(event => {
                const eventItem = document.createElement('div');
                eventItem.classList.add('event-item');
                eventItem.innerHTML = `
                    <div class="event-time">${event.time}</div>
                    <div class="event-title">${event.title}</div>
                `;
                eventListElement.appendChild(eventItem);
            });
        } else {
            eventListElement.innerHTML = '<div class="no-events">No events scheduled for this day</div>';
        }
    }
    
    // Helper function to format date as YYYY-MM-DD for event lookup
    function formatDateKey(date) {
        return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`;
    }
}); 