function showAddDistrictForm() {
    document.getElementById('add-district-form').style.display = 'block';
}

function addDistrict() {
    var districtName = document.getElementById('new-district-name').value;
    var cityId = {{ city.id }};  // تأكد من أن هذه القيمة تم تمريرها بشكل صحيح من الباكيند

    if (districtName) {
        $.ajax({
            url: "/admin/districts",
            method: 'POST',
            data: {
                action: 'add',
                district_name: districtName,
                city_id: cityId
            },
            success: function(response) {
                if (response.success) {
                    alert('تمت إضافة الحي بنجاح');
                    location.reload();  // إعادة تحميل الصفحة لتحديث قائمة الأحياء
                } else {
                    alert('فشل في إضافة الحي');
                }
            },
            error: function(xhr, status, error) {
                alert('حدث خطأ أثناء إضافة الحي');
            }
        });
    } else {
        alert('الرجاء إدخال اسم الحي');
    }

    return false;  // منع إعادة تحميل الصفحة
}

function toggleDistrictStatus(id, currentStatus) {
    $.ajax({
        url: "/admin/districts",
        method: 'POST',
        data: {
            action: 'toggle_status',
            district_id: id,
        },
        success: function(response) {
            if (response.success) {
                var newStatus = response.new_status ? "مفعلة" : "معطلة";
                document.getElementById('status-' + id).textContent = newStatus;
                var toggleButton = document.getElementById('toggle-' + id);
                toggleButton.textContent = response.new_status ? "تعطيل" : "تفعيل";
                alert('تم تغيير حالة الحي بنجاح');
            } else {
                alert('فشل في تغيير حالة الحي');
            }
        },
        error: function(xhr, status, error) {
            alert('حدث خطأ أثناء تغيير حالة الحي');
        }
    });
}
