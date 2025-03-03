document.addEventListener('DOMContentLoaded', function() {
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');

    togglePassword.addEventListener('click', function() {
        // Toggle the password visibility
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        
        // Toggle the eye icon
        this.classList.toggle('fa-eye');
        this.classList.toggle('fa-eye-slash');
        
        // Add a small animation
        this.style.transform = 'translateY(-50%) scale(0.8)';
        setTimeout(() => {
            this.style.transform = 'translateY(-50%) scale(1)';
        }, 100);
    });

    // Reset icon state when input is cleared
    passwordInput.addEventListener('input', function() {
        if (this.value === '') {
            this.setAttribute('type', 'password');
            togglePassword.classList.remove('fa-eye-slash');
            togglePassword.classList.add('fa-eye');
        }
    });
}); 