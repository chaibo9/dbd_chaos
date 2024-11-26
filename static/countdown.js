document.addEventListener('DOMContentLoaded', function () {
    function getNextTuesday3PM() {
        const now = new Date();
        const dayOfWeek = now.getUTCDay();
        const hourOfDay = now.getUTCHours();
        const minuteOfHour = now.getUTCMinutes();

        // Calculate the number of days until next Tuesday
        let daysUntilTuesday = (9 - dayOfWeek) % 7; // 0 if today is Tuesday
        const isTodayTuesday = dayOfWeek === 2;

        // If today is Tuesday but it's past 15:01 UTC, target next Tuesday
        if (isTodayTuesday && (hourOfDay > 15 || (hourOfDay === 15 && minuteOfHour >= 1))) {
            daysUntilTuesday = 7; // Move to the next Tuesday
        }

        const nextTuesday = new Date(now);
        nextTuesday.setUTCDate(now.getUTCDate() + daysUntilTuesday);
        nextTuesday.setUTCHours(15, 1, 0, 0); // 15:01 UTC
        return nextTuesday;
    }

    function updateCountdown() {
        const now = new Date();
        const nextTuesday = getNextTuesday3PM();
        const timeRemaining = nextTuesday - now;

        // Calculate days, hours, minutes, and seconds
        const days = Math.floor(timeRemaining / (1000 * 60 * 60 * 24));
        const hours = Math.floor((timeRemaining % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((timeRemaining % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((timeRemaining % (1000 * 60)) / 1000);

        // Update the countdown element
        document.getElementById('countdown').innerHTML =
            `${days}d ${hours}h ${minutes}m ${seconds}s`;

        // Handle expiration and reset
        if (timeRemaining <= 0) {
            clearInterval(countdownInterval);
            document.getElementById('countdown').innerHTML = "RESETTING...";
            setTimeout(() => {
                // Restart countdown after a small delay
                updateCountdown();
                countdownInterval = setInterval(updateCountdown, 1000); // Reinitialize
            }, 1000);
        }
    }

    // Initialize the countdown
    let countdownInterval = setInterval(updateCountdown, 1000); // Update every second
    updateCountdown(); // Initial call to display the countdown immediately
});