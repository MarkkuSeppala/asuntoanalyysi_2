// Pääkäyttäjän JavaScript-tiedosto

document.addEventListener('DOMContentLoaded', function() {
    // Bootstrap dropdown-valikoiden alustus
    var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    var dropdownList = dropdownElementList.map(function(dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl);
    });

    // Poistetaan navigaatiopalkin scroll-efekti, koska se aiheuttaa ongelmia logon koon kanssa
    // const navbar = document.querySelector('.navbar');
    // if (navbar) {
    //     window.addEventListener('scroll', function() {
    //         if (window.scrollY > 50) {
    //             navbar.classList.add('navbar-scrolled');
    //         } else {
    //             navbar.classList.remove('navbar-scrolled');
    //         }
    //     });
    // }

    // Aktiivisen sivun merkintä
    const currentPath = window.location.pathname;
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Mobile menu sulkeutuminen klikatessa linkkiä
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    const menuToggle = document.getElementById('navbarNav');
    const bsCollapse = menuToggle ? new bootstrap.Collapse(menuToggle, {toggle: false}) : null;
    
    navLinks.forEach(function(link) {
        link.addEventListener('click', function() {
            if (window.innerWidth < 992 && bsCollapse && menuToggle.classList.contains('show')) {
                bsCollapse.hide();
            }
        });
    });

    // Lomakkeiden validointi
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Salasanan vahvuuden tarkistaja
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        const passwordStrength = document.createElement('div');
        passwordStrength.classList.add('password-strength', 'mt-1');
        passwordInput.parentNode.appendChild(passwordStrength);

        passwordInput.addEventListener('input', function() {
            const password = this.value;
            let strength = 0;
            let message = '';

            if (password.length >= 8) strength += 1;
            if (password.match(/[a-z]+/)) strength += 1;
            if (password.match(/[A-Z]+/)) strength += 1;
            if (password.match(/[0-9]+/)) strength += 1;
            if (password.match(/[^a-zA-Z0-9]+/)) strength += 1;

            switch (strength) {
                case 0:
                case 1:
                    message = 'Heikko';
                    passwordStrength.style.color = 'red';
                    break;
                case 2:
                case 3:
                    message = 'Keskivahva';
                    passwordStrength.style.color = 'orange';
                    break;
                case 4:
                case 5:
                    message = 'Vahva';
                    passwordStrength.style.color = 'green';
                    break;
            }

            passwordStrength.textContent = `Salasanan vahvuus: ${message}`;
        });
    }

    // Flash-viestien automaattinen sulkeminen
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000); // Sulkeutuu 5 sekunnin kuluttua
    });
}); 