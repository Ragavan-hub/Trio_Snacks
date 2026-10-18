/* ==========================================================================
   Multi-Language Support (English & Tamil) — Trio Snacks POS
   ========================================================================== */

const translations = {
    en: {
        products: 'Menu Catalog',
        cart: 'Current Bill',
        clear: 'Clear',
        cart_empty: 'Cart is empty. Tap any snack on the left to add it.',
        subtotal: 'Subtotal:',
        tax: 'Tax / GST:',
        discount: 'Discount (₹):',
        total: 'Grand Total:',
        customer_details: 'Customer Info (Optional)',
        customer_name: 'Customer Name',
        customer_phone: 'Phone Number',
        process_order: 'Complete Order & Generate Bill'
    },
    ta: {
        products: 'தயாரிப்புகள் பட்டியல்',
        cart: 'தற்போதைய பில்',
        clear: 'அழிக்க',
        cart_empty: 'கார்ட் காலியாக உள்ளது. பொருட்களைச் சேர்க்கவும்.',
        subtotal: 'உப தொகை:',
        tax: 'வரி / GST:',
        discount: 'தள்ளுபடி (₹):',
        total: 'மொத்த தொகை:',
        customer_details: 'வாடிக்கையாளர் விவரம்',
        customer_name: 'வாடிக்கையாளர் பெயர்',
        customer_phone: 'தொலைபேசி எண்',
        process_order: 'ஆர்டர் முடித்து பில் உருவாக்கு'
    }
};

let currentLanguage = 'en';

function initI18n() {
    try {
        currentLanguage = localStorage.getItem('language') || 'en';
    } catch (e) {
        currentLanguage = 'en';
    }
    updateI18n();

    const languageToggle = document.getElementById('language-toggle');
    if (languageToggle && !languageToggle.dataset.boundLang) {
        languageToggle.dataset.boundLang = '1';
        languageToggle.addEventListener('click', toggleLanguage);
    }
}

function toggleLanguage() {
    currentLanguage = currentLanguage === 'en' ? 'ta' : 'en';
    try {
        localStorage.setItem('language', currentLanguage);
    } catch (e) {}
    updateI18n();
}

function updateI18n() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[currentLanguage] && translations[currentLanguage][key]) {
            el.textContent = translations[currentLanguage][key];
        }
    });

    const toggle = document.getElementById('language-toggle');
    if (toggle) {
        toggle.textContent = currentLanguage === 'en' ? '🌐 தமிழ்' : '🌐 EN';
    }
}

function t(key) {
    return (translations[currentLanguage] && translations[currentLanguage][key]) || translations.en[key] || key;
}
