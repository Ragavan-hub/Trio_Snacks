/* ==========================================================================
   Billing / Cloud POS Terminal Logic — Trio Snacks
   ========================================================================== */

let cart = {};
let taxRate = typeof window.taxRate !== 'undefined' ? parseFloat(window.taxRate) : 5.0;
let currentCategory = 'all';

async function loadCart() {
    try {
        const response = await fetch('/api/cart');
        const data = await response.json();
        cart = data.cart || {};
        if (typeof data.tax_rate !== 'undefined') {
            taxRate = parseFloat(data.tax_rate) || 0;
        }
        renderCart();
        calculateTotal();
    } catch (error) {
        console.error('Error loading cart:', error);
    }
}

async function addToCart(productId) {
    try {
        const response = await fetch('/api/cart/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: productId, quantity: 1 })
        });
        const data = await response.json();
        if (data.error) {
            showNotification(data.error, 'error');
            return;
        }
        cart = data.cart;
        renderCart();
        calculateTotal();
        showNotification('Added to bill', 'success');
    } catch (error) {
        console.error('Error adding to cart:', error);
        showNotification('Could not add item to bill', 'error');
    }
}

async function updateCartItem(productId, quantity) {
    if (isNaN(quantity) || quantity <= 0) {
        removeFromCart(productId);
        return;
    }
    try {
        const response = await fetch('/api/cart/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: productId, quantity: quantity })
        });
        const data = await response.json();
        if (data.error) {
            showNotification(data.error, 'error');
            return;
        }
        cart = data.cart;
        renderCart();
        calculateTotal();
    } catch (error) {
        console.error('Error updating cart:', error);
        showNotification('Error updating item quantity', 'error');
    }
}

async function removeFromCart(productId) {
    try {
        const response = await fetch('/api/cart/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: productId })
        });
        const data = await response.json();
        if (data.error) {
            showNotification(data.error, 'error');
            return;
        }
        cart = data.cart;
        renderCart();
        calculateTotal();
    } catch (error) {
        console.error('Error removing item:', error);
    }
}

function clearCart() {
    if (Object.keys(cart).length === 0) return;

    showConfirmModal({
        title: 'Clear Current Bill?',
        message: 'All items currently in the cart will be removed.',
        confirmText: 'Clear Cart',
        danger: true,
        onConfirm: async () => {
            try {
                const response = await fetch('/api/cart/clear', { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    cart = {};
                    renderCart();
                    calculateTotal();
                    showNotification('Cart cleared', 'info');
                }
            } catch (error) {
                console.error('Error clearing cart:', error);
            }
        }
    });
}

function renderCart() {
    const cartItems = document.getElementById('cart-items');
    const countBadge = document.getElementById('cart-count-badge');

    const totalQty = Object.values(cart).reduce((acc, item) => acc + (parseInt(item.quantity) || 0), 0);
    if (countBadge) {
        countBadge.textContent = `${totalQty} ${totalQty === 1 ? 'item' : 'items'}`;
    }

    if (Object.keys(cart).length === 0) {
        cartItems.innerHTML = '<p class="empty-cart" data-i18n="cart_empty">Cart is empty. Tap any snack on the left to add it.</p>';
        if (typeof updateI18n === 'function') updateI18n();
        return;
    }

    let html = '';
    for (const [productId, item] of Object.entries(cart)) {
        const itemTotal = item.price * item.quantity;
        html += `
            <div class="cart-item">
                <div class="cart-item-info">
                    <h4>${escapeHtml(item.name)}</h4>
                    <p class="item-price">${formatCurrency(item.price)} each</p>
                </div>
                <div class="cart-item-controls">
                    <div class="quantity-control">
                        <button type="button" onclick="updateCartItem(${productId}, ${item.quantity - 1})" aria-label="Decrease quantity">−</button>
                        <input type="number" value="${item.quantity}" min="1" max="999"
                               onchange="updateCartItem(${productId}, parseInt(this.value, 10))" aria-label="Quantity">
                        <button type="button" onclick="updateCartItem(${productId}, ${item.quantity + 1})" aria-label="Increase quantity">+</button>
                    </div>
                    <span class="cart-item-total">${formatCurrency(itemTotal)}</span>
                    <button type="button" class="cart-item-remove" onclick="removeFromCart(${productId})" title="Remove item">&times;</button>
                </div>
            </div>
        `;
    }

    cartItems.innerHTML = html;
}

function calculateTotal() {
    let subtotal = 0;
    for (const item of Object.values(cart)) {
        subtotal += (parseFloat(item.price) || 0) * (parseInt(item.quantity, 10) || 0);
    }

    const discountInput = document.getElementById('discount-input');
    const rawDiscount = discountInput ? (parseFloat(discountInput.value) || 0) : 0;
    const discountAmount = Math.min(Math.max(0, rawDiscount), subtotal);
    const taxableAmount = Math.max(0, subtotal - discountAmount);
    const taxAmount = Math.round(((taxableAmount * taxRate) / 100) * 100) / 100;
    const total = Math.round((taxableAmount + taxAmount) * 100) / 100;

    const subEl = document.getElementById('subtotal');
    const taxEl = document.getElementById('tax-amount');
    const totalEl = document.getElementById('total-amount');

    if (subEl) subEl.textContent = formatCurrency(subtotal);
    if (taxEl) taxEl.textContent = formatCurrency(taxAmount);
    if (totalEl) totalEl.textContent = formatCurrency(total);
}

async function processOrder() {
    if (Object.keys(cart).length === 0) {
        showNotification('Please add at least one snack to process an order.', 'error');
        return;
    }

    const discountInput = document.getElementById('discount-input');
    const customerNameInput = document.getElementById('customer-name-input');
    const customerPhoneInput = document.getElementById('customer-phone-input');
    const processBtn = document.getElementById('process-order-btn');

    const discount = discountInput ? (parseFloat(discountInput.value) || 0) : 0;
    const customerName = customerNameInput ? customerNameInput.value.trim() : '';
    const customerPhone = customerPhoneInput ? customerPhoneInput.value.trim() : '';

    if (processBtn) {
        processBtn.disabled = true;
        processBtn.textContent = 'Processing...';
    }

    try {
        const response = await fetch('/api/order/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                discount: discount,
                customer_name: customerName,
                customer_phone: customerPhone
            })
        });

        const data = await response.json();

        if (data.error) {
            showNotification(data.error, 'error');
            return;
        }

        if (data.success) {
            if (discountInput) discountInput.value = 0;
            if (customerNameInput) customerNameInput.value = '';
            if (customerPhoneInput) customerPhoneInput.value = '';

            cart = {};
            renderCart();
            calculateTotal();

            showOrderSuccessModal(data);
        }
    } catch (error) {
        console.error('Error processing order:', error);
        showNotification('Error processing order. Please try again.', 'error');
    } finally {
        if (processBtn) {
            processBtn.disabled = false;
            processBtn.textContent = typeof t === 'function' ? t('process_order') : 'Complete Order';
        }
    }
}

function showOrderSuccessModal(orderData) {
    let modal = document.getElementById('order-success-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'order-success-modal';
        modal.className = 'modal';
        document.body.appendChild(modal);
    }

    modal.innerHTML = `
        <div class="modal-content" style="max-width: 440px; text-align: center;">
            <button type="button" class="close" onclick="document.getElementById('order-success-modal').style.display='none'">&times;</button>
            <div style="width: 56px; height: 56px; border-radius: 50%; background: var(--success-bg); color: var(--success-color); display: flex; align-items: center; justify-content: center; font-size: 1.75rem; margin: 0 auto 1rem;">✓</div>
            <h2 style="margin-bottom: 0.35rem;">Order Completed!</h2>
            <p style="color: var(--text-secondary); font-size: 0.92rem; margin-bottom: 1.25rem;">
                Invoice <strong>${escapeHtml(orderData.invoice_number)}</strong> has been recorded.
            </p>
            <div style="background: var(--bg-subtle); padding: 1rem; border-radius: var(--radius-md); margin-bottom: 1.5rem;">
                <span style="font-size: 0.82rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700;">Total Paid</span>
                <div style="font-size: 1.8rem; font-weight: 800; color: var(--text-primary); font-family: 'Outfit', sans-serif;">
                    ${formatCurrency(orderData.total_amount || 0)}
                </div>
            </div>
            <div style="display: flex; gap: 0.65rem; justify-content: center; flex-wrap: wrap;">
                <a href="/invoice/${orderData.order_id}/pdf" class="btn btn-primary">Download PDF Invoice</a>
                <a href="/orders/${orderData.order_id}" class="btn btn-secondary">View Receipt</a>
                <button type="button" class="btn btn-secondary" onclick="document.getElementById('order-success-modal').style.display='none'">Next Bill</button>
            </div>
        </div>
    `;
    modal.style.display = 'block';
}

function searchProducts() {
    const searchInput = document.getElementById('product-search');
    const search = searchInput ? searchInput.value.trim() : '';
    const category = currentCategory || 'all';

    fetch(`/api/products?category=${encodeURIComponent(category)}&search=${encodeURIComponent(search)}`)
        .then(res => res.json())
        .then(products => renderProducts(products))
        .catch(err => console.error('Error searching products:', err));
}

function filterByCategory(category) {
    currentCategory = category;
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-category') === category);
    });
    searchProducts();
}

function renderProducts(products) {
    const productsList = document.getElementById('products-list');
    if (!productsList) return;

    if (!products || products.length === 0) {
        productsList.innerHTML = '<p class="empty-cart" style="grid-column: 1 / -1;">No matching snacks found.</p>';
        return;
    }

    let html = '';
    products.forEach(product => {
        const imageUrl = product.image_url ? `/static/images/products/${product.image_url}` : '';
        const catDisplay = product.category_display || product.category;
        const initial = (product.name || 'S').charAt(0).toUpperCase();

        html += `
            <div class="product-item" data-product-id="${product.id}" data-category="${escapeHtml(product.category)}" onclick="addToCart(${product.id})">
                <div class="product-item-top">
                    <div class="product-item-image">
                        ${imageUrl
                            ? `<img src="${imageUrl}" alt="${escapeHtml(product.name)}" onerror="this.parentElement.innerHTML='<div class=\\'product-image-placeholder-small\\'>${initial}</div>'">`
                            : `<div class="product-image-placeholder-small">${initial}</div>`
                        }
                    </div>
                    <div class="product-item-info">
                        <h4>${escapeHtml(product.name)}</h4>
                        <p class="product-category">${escapeHtml(catDisplay)}</p>
                    </div>
                </div>
                <div class="product-item-actions">
                    <span class="product-price">${formatCurrency(product.price)}</span>
                    <button type="button" class="btn btn-sm btn-primary" onclick="event.stopPropagation(); addToCart(${product.id})">+ Add</button>
                </div>
            </div>
        `;
    });

    productsList.innerHTML = html;
}

function escapeHtml(str) {
    return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function initBilling() {
    if (typeof window.taxRate !== 'undefined') {
        taxRate = parseFloat(window.taxRate) || 0;
    }

    const discountInput = document.getElementById('discount-input');
    if (discountInput) {
        discountInput.addEventListener('input', calculateTotal);
    }

    const productSearch = document.getElementById('product-search');
    if (productSearch) {
        productSearch.addEventListener('input', () => {
            searchProducts();
        });
        productSearch.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchProducts();
            }
        });
    }
}
