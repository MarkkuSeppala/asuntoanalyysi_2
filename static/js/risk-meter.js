document.addEventListener('DOMContentLoaded', function() {
    // Tarkistetaan onko riski-data saatavilla
    const riskElements = document.querySelectorAll('.risk-area');
    
    if (riskElements.length > 0) {
        // Lisätään tooltip-toiminnallisuus kaikille riskialueille
        riskElements.forEach(element => {
            // Tooltip näytetään kun hiiri on elementin päällä
            element.addEventListener('mouseenter', function() {
                const tooltipId = this.getAttribute('data-tooltip-id');
                const tooltip = document.getElementById(tooltipId);
                if (tooltip) {
                    // Asetetaan tooltip näkyviin ja positioidaan se
                    tooltip.style.display = 'block';
                    
                    // Lasketaan tooltip-position
                    const rect = this.getBoundingClientRect();
                    const tooltipRect = tooltip.getBoundingClientRect();
                    
                    // Tooltip keskitettynä elementin yläpuolelle
                    const top = rect.top - tooltipRect.height - 10;
                    const left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
                    
                    tooltip.style.top = `${top}px`;
                    tooltip.style.left = `${left}px`;
                }
            });
            
            // Tooltip piilotetaan kun hiiri poistuu elementin päältä
            element.addEventListener('mouseleave', function() {
                const tooltipId = this.getAttribute('data-tooltip-id');
                const tooltip = document.getElementById(tooltipId);
                if (tooltip) {
                    tooltip.style.display = 'none';
                }
            });
        });
    }
}); 