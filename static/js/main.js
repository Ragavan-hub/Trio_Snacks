/* ==========================================================================
   Main JavaScript Utilities — Trio Snacks
   ========================================================================== */

function formatCurrency(amount) {
    const num = parseFloat(amount) || 0;
    return '₹' + num.toFixed(2);
}

function getStorageItem(key, fallback = null) {
    try {
        const val = localStorage.getItem(key);
        return val !== null ? val : fallback;
    } catch (e) {
        return fallback;
    }
}

function setStorageItem(key, value) {
    try {
        localStorage.setItem(key, value);
    } catch (e) {
        // Ignore storage errors in restricted environments
    }
}

function showNotification(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position:fixed;top:76px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:10px;max-width:360px;';
        document.body.appendChild(container);
    }

    const bgMap = {
        success: '#059669',
        error: '#DC2626',
        info: '#1F2937'
    };

    const toast = document.createElement('div');
    toast.className = `notification notification-${type}`;
    toast.style.cssText = `
        padding: 0.85rem 1.15rem;
        background-color: ${bgMap[type] || bgMap.info};
        color: #FFFFFF;
        border-radius: 10px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        font-size: 0.9rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        animation: slideInToast 0.22s ease-out;
    `;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(20px)';
        toast.style.transition = 'all 0.2s ease';
        setTimeout(() => toast.remove(), 220);
    }, 2800);
}

if (!document.getElementById('toast-keyframes')) {
    const style = document.createElement('style');
    style.id = 'toast-keyframes';
    style.textContent = `
        @keyframes slideInToast {
            from { transform: translateX(40px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);
}

/**
 * Accessible In-Page Confirmation Modal
 */
function showConfirmModal({ title = 'Confirm Action', message = 'Are you sure?', confirmText = 'Confirm', danger = false, onConfirm }) {
    let modal = document.getElementById('global-confirm-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'global-confirm-modal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 420px;">
                <button type="button" class="close" id="confirm-modal-close">&times;</button>
                <h2 id="confirm-modal-title" style="margin-bottom: 0.6rem; font-size: 1.3rem;"></h2>
                <p id="confirm-modal-message" style="color: var(--text-secondary); margin-bottom: 1.5rem; font-size: 0.95rem;"></p>
                <div class="form-actions" style="margin-top: 1rem;">
                    <button type="button" class="btn btn-secondary" id="confirm-modal-cancel">Cancel</button>
                    <button type="button" class="btn" id="confirm-modal-accept"></button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    document.getElementById('confirm-modal-title').textContent = title;
    document.getElementById('confirm-modal-message').textContent = message;
    const acceptBtn = document.getElementById('confirm-modal-accept');
    acceptBtn.textContent = confirmText;
    acceptBtn.className = danger ? 'btn btn-danger' : 'btn btn-primary';

    const closeModal = () => { modal.style.display = 'none'; };
    document.getElementById('confirm-modal-close').onclick = closeModal;
    document.getElementById('confirm-modal-cancel').onclick = closeModal;
    acceptBtn.onclick = () => {
        closeModal();
        if (typeof onConfirm === 'function') onConfirm();
    };

    modal.style.display = 'block';
}

/* Dark Mode Controller */
function initDarkMode() {
    const isDark = getStorageItem('darkMode') === 'true';
    if (isDark) {
        document.body.classList.add('dark-mode');
    }
    updateDarkModeIcons(isDark);

    document.querySelectorAll('[data-theme-toggle], #dark-mode-toggle').forEach(btn => {
        if (!btn.dataset.boundTheme) {
            btn.dataset.boundTheme = '1';
            btn.addEventListener('click', toggleDarkMode);
        }
    });
}

function toggleDarkMode() {
    const isDark = document.body.classList.toggle('dark-mode');
    setStorageItem('darkMode', isDark ? 'true' : 'false');
    updateDarkModeIcons(isDark);
}

function updateDarkModeIcons(isDark) {
    document.querySelectorAll('[data-theme-toggle], #dark-mode-toggle').forEach(btn => {
        btn.textContent = isDark ? '☀️' : '🌙';
        btn.title = isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode';
    });
}

/* Mobile Navigation Drawer */
function initMobileNav() {
    const toggleBtn = document.getElementById('mobile-nav-toggle');
    const navMenu = document.getElementById('main-nav-menu');
    if (toggleBtn && navMenu) {
        toggleBtn.addEventListener('click', () => {
            navMenu.classList.toggle('open');
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initDarkMode();
    initMobileNav();
});
