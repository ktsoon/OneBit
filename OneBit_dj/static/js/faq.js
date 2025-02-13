$(document).ready(function() {
    $('#question-form').on('submit', function(event) {
        event.preventDefault();  // Prevent form submission for validation
        
        var email = $('#email').val().trim();
        var theme = $('#theme').val().trim();
        var message = $('#message').val().trim();
        var isValid = true;

        // Email validation
        if (!email || !validateEmail(email)) {
            $('#email').addClassAndRemove('danger-bord',0,500);
            isValid = false;
        }

        // Theme validation
        if (!theme) {
            $('#theme').addClassAndRemove('danger-bord',0,500);
            isValid = false;
        }

        // Message validation
        if (!message) {
            $('#message').addClassAndRemove('danger-bord',0,500);
            isValid = false;
        }

        // If all fields are valid, submit the form
        if (isValid) {
            // Here you can proceed to submit the form, e.g., via AJAX or regular submission
            this.submit();  // Un-comment this line if you want to submit the form
        }
    });

    // Email format validation function
    function validateEmail(email) {
        var regex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
        return regex.test(email);
    }
});