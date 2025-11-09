
document.addEventListener('DOMContentLoaded', function() {
    const dateElements = document.querySelectorAll('.jalali-date');
    dateElements.forEach(function(element) {
        const jalaliDateStr = element.getAttribute('data-date');
        if (jalaliDateStr) {
            const parts = jalaliDateStr.split('/');
            if (parts.length === 3) {
                const jYear = parseInt(parts[0], 10);
                const jMonth = parseInt(parts[1], 10);
                const jDay = parseInt(parts[2], 10);

                try {
                    const gregorian = jalaali.toGregorian(jYear, jMonth, jDay);
                    const dateObj = new Date(gregorian.gy, gregorian.gm - 1, gregorian.gd);

                    const formattedDate = dateObj.toLocaleDateString('fa-IR', {
                        month: 'long',
                        day: 'numeric'
                    });
                    element.textContent = formattedDate;
                } catch (e) {
                    console.error('Could not convert date:', jalaliDateStr, e);
                }
            }
        }
    });
});
