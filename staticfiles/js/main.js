/**
 * THE ULTIMATE SHOPPING — Core Interactive Engine
 * Handles Theme Toggling, AJAX Cart/Wishlist/Compare, Toasts, PIN Estimator, & Modals
 */

document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initAjaxCart();
    initAjaxWishlist();
    initAjaxCompare();
    initPinEstimator();
    initImageGallery();
    initCountdownTimers();
    initNewsletterForm();
});

// 1. Dark Mode / Light Mode
function initThemeToggle() {
    const toggleBtn = document.getElementById('theme-toggle-btn');
    const htmlEl = document.documentElement;
    const currentTheme = localStorage.getItem('theme') || 'light';

    htmlEl.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme);

    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const activeTheme = htmlEl.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            htmlEl.setAttribute('data-theme', activeTheme);
            localStorage.setItem('theme', activeTheme);
            updateThemeIcon(activeTheme);
            showToast(`Switched to ${activeTheme === 'dark' ? 'Dark' : 'Light'} Mode`, 'info');
        });
    }
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('theme-icon');
    if (icon) {
        if (theme === 'dark') {
            icon.className = 'bi bi-sun-fill text-warning';
        } else {
            icon.className = 'bi bi-moon-stars-fill';
        }
    }
}

// 2. Global Toast Notification System
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'custom-toast';

    let iconClass = 'bi-info-circle-fill text-info';
    if (type === 'success') iconClass = 'bi-check-circle-fill text-success';
    if (type === 'warning') iconClass = 'bi-exclamation-triangle-fill text-warning';
    if (type === 'error') iconClass = 'bi-x-circle-fill text-danger';

    toast.innerHTML = `
        <i class="bi ${iconClass} fs-5"></i>
        <div class="flex-grow-1">${message}</div>
        <button type="button" class="btn-close btn-close-white ms-2" style="font-size: 0.75rem;"></button>
    `;

    container.appendChild(toast);

    toast.querySelector('.btn-close').addEventListener('click', () => {
        toast.remove();
    });

    setTimeout(() => {
        toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(50px)';
        setTimeout(() => toast.remove(), 400);
    }, 4000);
}

// 3. AJAX Cart Handler
function initAjaxCart() {
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.ajax-add-cart');
        if (!btn) return;

        e.preventDefault();
        const url = btn.getAttribute('data-url') || btn.getAttribute('href');
        if (!url) return;

        const originalHtml = btn.innerHTML;
        btn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status"></span> Adding...`;
        btn.disabled = true;

        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(res => res.json())
        .then(data => {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
            if (data.success) {
                showToast(data.message, 'success');
                // Update badge
                const cartBadge = document.getElementById('nav-cart-badge');
                if (cartBadge) {
                    cartBadge.textContent = data.cart_items_count;
                    cartBadge.classList.remove('d-none');
                }
            } else {
                showToast(data.message, 'warning');
            }
        })
        .catch(err => {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
            // Fallback to normal navigation
            window.location.href = url;
        });
    });
}

// 4. AJAX Wishlist Toggle
function initAjaxWishlist() {
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.ajax-toggle-wishlist');
        if (!btn) return;

        e.preventDefault();
        const url = btn.getAttribute('data-url') || btn.getAttribute('href');
        if (!url) return;

        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast(data.message, data.in_wishlist ? 'success' : 'info');
                
                // Toggle active style
                if (data.in_wishlist) {
                    btn.classList.add('active');
                    btn.querySelector('i')?.classList.replace('bi-heart', 'bi-heart-fill');
                    btn.querySelector('i')?.classList.add('text-danger');
                } else {
                    btn.classList.remove('active');
                    btn.querySelector('i')?.classList.replace('bi-heart-fill', 'bi-heart');
                    btn.querySelector('i')?.classList.remove('text-danger');
                }

                // Update badge
                const badge = document.getElementById('nav-wishlist-badge');
                if (badge) {
                    badge.textContent = data.count;
                    badge.style.display = data.count > 0 ? 'flex' : 'none';
                }
            }
        })
        .catch(() => {
            window.location.href = url;
        });
    });
}

// 5. AJAX Compare Toggle
function initAjaxCompare() {
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.ajax-toggle-compare');
        if (!btn) return;

        e.preventDefault();
        const url = btn.getAttribute('data-url') || btn.getAttribute('href');
        if (!url) return;

        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast(data.message, data.in_compare ? 'success' : 'info');
                const badge = document.getElementById('nav-compare-badge');
                if (badge) {
                    badge.textContent = data.count;
                    badge.style.display = data.count > 0 ? 'flex' : 'none';
                }
                if (data.in_compare) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            } else {
                showToast(data.message, 'warning');
            }
        })
        .catch(() => {
            window.location.href = url;
        });
    });
}

// 6. Delivery Pincode Estimator
function initPinEstimator() {
    const pinBtn = document.getElementById('btn-check-pin');
    const pinInput = document.getElementById('input-pincode');
    const resultBox = document.getElementById('pin-check-result');

    if (pinBtn && pinInput && resultBox) {
        pinBtn.addEventListener('click', () => {
            const pin = pinInput.value.trim();
            if (pin.length !== 6 || isNaN(pin)) {
                resultBox.innerHTML = `<div class="text-danger small mt-2"><i class="bi bi-x-circle me-1"></i>Please enter a valid 6-digit PIN code.</div>`;
                return;
            }

            resultBox.innerHTML = `<div class="text-muted small mt-2"><span class="spinner-border spinner-border-sm me-1"></span>Checking serviceable area...</div>`;

            fetch(`/api/check-pincode/?pincode=${pin}`)
            .then(res => res.json())
            .then(data => {
                if (data.serviceable) {
                    resultBox.innerHTML = `
                        <div class="alert alert-success py-2 px-3 mt-2 small mb-0">
                            <strong><i class="bi bi-truck me-1"></i> Delivery in ${data.days} Business Days</strong>
                            <div class="text-muted mt-1">${data.city ? data.city + ', ' + data.state : 'Serviceable Destination'} • ${data.cod ? 'Cash on Delivery Available' : 'Prepaid Only'}</div>
                        </div>
                    `;
                } else {
                    resultBox.innerHTML = `
                        <div class="alert alert-warning py-2 px-3 mt-2 small mb-0">
                            <i class="bi bi-exclamation-triangle me-1"></i> ${data.message}
                        </div>
                    `;
                }
            })
            .catch(() => {
                resultBox.innerHTML = `<div class="text-danger small mt-2">Could not verify PIN code. Please try again.</div>`;
            });
        });
    }
}

// 7. Product Detail Image Gallery
function initImageGallery() {
    const mainImg = document.getElementById('main-product-image');
    const thumbs = document.querySelectorAll('.gallery-thumb');

    if (mainImg && thumbs.length > 0) {
        thumbs.forEach(thumb => {
            thumb.addEventListener('click', () => {
                thumbs.forEach(t => t.classList.remove('border-primary', 'active-thumb'));
                thumb.classList.add('border-primary', 'active-thumb');
                mainImg.src = thumb.getAttribute('data-full-img');
            });
        });
    }
}

// 8. Flash Deals Live Countdown
function initCountdownTimers() {
    const timers = document.querySelectorAll('.deal-countdown');
    timers.forEach(timer => {
        const endTime = new Date(timer.getAttribute('data-end')).getTime();
        if (isNaN(endTime)) return;

        const interval = setInterval(() => {
            const now = new Date().getTime();
            const distance = endTime - now;

            if (distance < 0) {
                clearInterval(interval);
                timer.innerHTML = "<span class='badge bg-secondary'>Deal Ended</span>";
                return;
            }

            const days = Math.floor(distance / (1000 * 60 * 60 * 24));
            const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((distance % (1000 * 60)) / 1000);

            const daysEl = timer.querySelector('.cd-days');
            const hoursEl = timer.querySelector('.cd-hours');
            const minsEl = timer.querySelector('.cd-mins');
            const secsEl = timer.querySelector('.cd-secs');

            if (daysEl) daysEl.textContent = String(days).padStart(2, '0');
            if (hoursEl) hoursEl.textContent = String(hours).padStart(2, '0');
            if (minsEl) minsEl.textContent = String(minutes).padStart(2, '0');
            if (secsEl) secsEl.textContent = String(seconds).padStart(2, '0');
        }, 1000);
    });
}

// 9. Newsletter Subscription
function initNewsletterForm() {
    const form = document.getElementById('newsletter-form');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const emailInput = form.querySelector('input[type="email"]');
            if (!emailInput) return;

            const formData = new FormData();
            formData.append('email', emailInput.value);

            fetch('/api/newsletter/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                showToast(data.message, data.success ? 'success' : 'warning');
                if (data.success) emailInput.value = '';
            })
            .catch(() => {
                showToast("Subscription received. Thank you!", 'success');
                emailInput.value = '';
            });
        });
    }
}

// Helper: Get CSRF Cookie
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
