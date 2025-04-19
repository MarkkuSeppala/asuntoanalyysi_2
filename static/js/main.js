// Pääkäyttäjän JavaScript-tiedosto

document.addEventListener('DOMContentLoaded', function() {
    // Bootstrap dropdown-valikoiden alustus
    var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    var dropdownList = dropdownElementList.map(function(dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl);
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