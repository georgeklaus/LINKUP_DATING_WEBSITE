// Main JavaScript for LoveConnect

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
});

// Auto-hide alerts after 5 seconds
setTimeout(function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
    });
}, 5000);

// Image preview for file inputs
function previewImage(input, previewId) {
    const preview = document.getElementById(previewId);
    const file = input.files[0];
    const reader = new FileReader();

    reader.onloadend = function () {
        preview.src = reader.result;
    }

    if (file) {
        reader.readAsDataURL(file);
    } else {
        preview.src = "";
    }
}

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    let isValid = true;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });

    return isValid;
}

// AJAX helper function
function ajaxRequest(url, method, data, successCallback, errorCallback) {
    const xhr = new XMLHttpRequest();
    xhr.open(method, url);
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    
    xhr.onload = function() {
        if (xhr.status === 200) {
            successCallback(JSON.parse(xhr.responseText));
        } else {
            errorCallback(xhr.status, xhr.responseText);
        }
    };
    
    xhr.onerror = function() {
        errorCallback(0, 'Network error');
    };
    
    const formData = new URLSearchParams();
    for (const key in data) {
        formData.append(key, data[key]);
    }
    
    xhr.send(formData);
}

// Coin balance update
function updateCoinBalance(newBalance) {
    const coinElements = document.querySelectorAll('.coin-balance');
    coinElements.forEach(element => {
        element.textContent = newBalance + ' coins';
    });
}

// Online status indicator
function updateOnlineStatus() {
    // This would typically ping the server to update last activity
    fetch('/users/update-online-status/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        }
    });
}

// Get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Typing indicator for chat
let typingTimer;
const doneTypingInterval = 1000;

function typingStarted(roomName) {
    // Send typing started event to server
    // This would be implemented with WebSockets
}

function typingStopped(roomName) {
    // Send typing stopped event to server
    // This would be implemented with WebSockets
}

// Debounced typing detection
function onTyping(inputElement, roomName) {
    clearTimeout(typingTimer);
    typingStarted(roomName);
    typingTimer = setTimeout(() => typingStopped(roomName), doneTypingInterval);
}

// Image lazy loading
function lazyLoadImages() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    lazyLoadImages();
    
    // Update online status every minute
    setInterval(updateOnlineStatus, 60000);
    
    // Add smooth scrolling to all links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
});

// Export functions for use in other modules
window.LoveConnect = {
    validateForm,
    ajaxRequest,
    updateCoinBalance,
    getCookie,
    previewImage
};