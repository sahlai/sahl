// وظيفة إرسال رسالة المحادثة
function sendMessage() {
    var userInput = document.getElementById('user-input').value;
    if (userInput.trim() === '') return;

    appendMessage('أنت', userInput);
    document.getElementById('user-input').value = '';

    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({message: userInput}),
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            appendMessage('النظام', data.error);
        } else {
            appendMessage('SAHL', data.response);
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        appendMessage('النظام', 'حدث خطأ في الاتصال. الرجاء المحاولة مرة أخرى.');
    });
}

// وظيفة لإضافة الرسائل في المحادثة
function appendMessage(sender, message) {
    var chatMessages = document.getElementById('chat-messages');
    var messageElement = document.createElement('div');
    messageElement.innerHTML = '<strong>' + sender + ':</strong> ' + message;
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// وظيفة لتحريك القائمة الجانبية
document.querySelector('.menu-toggle').addEventListener('click', function() {
    document.querySelector('.sidebar').classList.toggle('collapsed');
});

// تحديث الدولة
function updateCountry(countryId, newName) {
    $.ajax({
        url: "/admin/countries",
        method: 'POST',
        data: { action: 'update', country_id: countryId, country_name: newName },
        success: function(response) {
            alert('تم تحديث الدولة بنجاح');
        },
        error: function() {
            alert('حدث خطأ أثناء تحديث الدولة');
        }
    });
}

// تغيير حالة التفعيل
function toggleCountryStatus(countryId) {
    $.ajax({
        url: "/admin/countries",
        method: 'POST',
        data: { action: 'toggle_status', country_id: countryId },
        success: function(response) {
            alert('تم تغيير حالة الدولة بنجاح');
        },
        error: function() {
            alert('حدث خطأ أثناء تغيير حالة الدولة');
        }
    });
}

// إضافة مدينة جديدة
function addCity(countryId, cityName) {
    $.ajax({
        url: "/admin/cities",
        method: 'POST',
        data: { action: 'add', city_name: cityName, country_id: countryId },
        success: function(response) {
            if (response.success) {
                alert('تمت إضافة المدينة بنجاح');
                location.reload();
            } else {
                alert('فشل في إضافة المدينة');
            }
        },
        error: function() {
            alert('حدث خطأ أثناء إضافة المدينة');
        }
    });
}

// حذف مدينة
function deleteCity(cityId) {
    if (confirm('هل أنت متأكد من حذف هذه المدينة؟')) {
        $.ajax({
            url: "/admin/cities",
            method: 'POST',
            data: { action: 'delete', city_id: cityId },
            success: function(response) {
                if (response.success) {
                    alert('تم حذف المدينة بنجاح');
                    location.reload();
                } else {
                    alert('فشل في حذف المدينة');
                }
            },
            error: function() {
                alert('حدث خطأ أثناء حذف المدينة');
            }
        });
    }
}