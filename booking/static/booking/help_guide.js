document.addEventListener('DOMContentLoaded', function () {
    const accordionButtons = document.querySelectorAll('.accordion-button');

    accordionButtons.forEach(button => {
        button.addEventListener('click', function () {
            const content = this.nextElementSibling;
            const isActive = this.classList.contains('active');

            // Close all other accordions
            accordionButtons.forEach(btn => {
                if (btn !== this) {
                    btn.classList.remove('active');
                    btn.nextElementSibling.style.display = 'none';
                }
            });

            // Toggle current accordion
            if (isActive) {
                this.classList.remove('active');
                content.style.display = 'none';
            } else {
                this.classList.add('active');
                content.style.display = 'block';
            }
        });
    });
});
