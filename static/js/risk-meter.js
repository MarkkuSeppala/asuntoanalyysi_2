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
        
        // Luodaan asteikkomerkinnät 0-10
        const riskMeterContainer = document.querySelector('.risk-meter-container');
        if (riskMeterContainer) {
            // Lisätään asteikkomerkinnät
            const scaleMarks = document.createElement('div');
            scaleMarks.className = 'risk-scale-marks';
            
            // Luodaan 11 merkintää (0-10)
            for (let i = 0; i <= 10; i++) {
                const mark = document.createElement('div');
                mark.className = 'risk-scale-mark';
                mark.setAttribute('data-value', i);
                mark.style.left = (i * 10) + '%';
                scaleMarks.appendChild(mark);
            }
            
            // Lisätään merkinnät riskimittarin alle, mutta ennen selitettä
            const riskMeter = riskMeterContainer.querySelector('.risk-meter');
            riskMeterContainer.insertBefore(scaleMarks, riskMeter.nextSibling);
        }
    }
}); 