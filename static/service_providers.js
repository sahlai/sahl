document.addEventListener('DOMContentLoaded', function () {
    // Function to handle form submission
    const providerForm = document.querySelector('#providerForm');
    if (providerForm) {
        providerForm.addEventListener('submit', function (event) {
            event.preventDefault();
            const formData = new FormData(providerForm);
            const formAction = providerForm.getAttribute('action');

            fetch(formAction, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('تم إضافة مقدم الخدمة بنجاح');
                    window.location.href = '/admin/service_providers';
                } else {
                    alert('حدث خطأ أثناء إضافة مقدم الخدمة: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('حدث خطأ غير متوقع');
            });
        });
    }
});
