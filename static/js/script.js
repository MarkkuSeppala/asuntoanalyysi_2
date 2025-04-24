document.addEventListener('DOMContentLoaded', function() {
    // URL-muodon validointi
    const urlInput = document.getElementById('url');
    if (urlInput) {
        urlInput.addEventListener('blur', function() {
            const url = this.value.trim();
            if (url && !url.includes('oikotie.fi') && !url.includes('etuovi.com')) {
                this.setCustomValidity('Syötä kelvollinen Oikotie- tai Etuovi-asuntolinkin URL');
            } else {
                this.setCustomValidity('');
            }
        });
    }

    // Lomakkeen lähetyksen käsittely
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            // Estetään lomakkeen lähetys, jos URL on tyhjä
            if (!urlInput.value.trim()) {
                e.preventDefault();
                urlInput.setCustomValidity('URL-osoite on pakollinen');
                urlInput.reportValidity();
                return false;
            }
            
            // Näytetään latausilmaisin
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerText = 'Analysoidaan...';
                submitBtn.classList.add('loading');
            }
            
            // Jatketaan normaalisti lomakkeen lähetystä
            return true;
        });
    }
    
    // URL-parametrien käsittely virheilmoituksia varten
    const queryParams = new URLSearchParams(window.location.search);
    const errorMsg = queryParams.get('error');
    if (errorMsg) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = decodeURIComponent(errorMsg);
        
        const formSection = document.querySelector('.form-section');
        if (formSection) {
            formSection.prepend(errorDiv);
        }
    }
}); 