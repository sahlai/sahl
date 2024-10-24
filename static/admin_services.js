function editService(id) {
    const newName = prompt("أدخل الاسم الجديد للخدمة:");
    if (newName) {
        fetch(`/admin/services/${id}/edit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: newName }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('فشل تحديث الخدمة');
            }
        });
    }
}

function deleteService(id) {
    if (confirm('هل أنت متأكد من حذف هذه الخدمة؟')) {
        fetch(`/admin/services/${id}/delete`, {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('فشل حذف الخدمة');
            }
        });
    }
}

function toggleService(id) {
    fetch(`/admin/services/${id}/toggle`, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            alert('فشل تغيير حالة الخدمة');
            location.reload();
        }
    });
}
