/* ==========================================================================
   Admin Product & Store Management JavaScript
   ========================================================================== */

function showAddProductModal() {
    const modal = document.getElementById('product-modal');
    const form = document.getElementById('product-form');
    const title = document.getElementById('modal-title');
    const imagePreview = document.getElementById('image-preview');

    title.textContent = 'Add New Snack Product';
    form.action = '/admin/products/add';
    form.method = 'POST';
    form.reset();
    if (imagePreview) imagePreview.innerHTML = '';

    modal.style.display = 'block';
}

function showEditProductModal(id, name, category, price, description, imageUrl) {
    const modal = document.getElementById('product-modal');
    const form = document.getElementById('product-form');
    const title = document.getElementById('modal-title');
    const imagePreview = document.getElementById('image-preview');

    title.textContent = 'Edit Product';
    form.action = `/admin/products/${id}/edit`;
    form.method = 'POST';

    document.getElementById('product-name').value = name || '';
    const categorySelect = document.getElementById('product-category');
    if (categorySelect) {
        let matched = false;
        for (const opt of categorySelect.options) {
            if (opt.value === category) {
                matched = true;
                break;
            }
        }
        if (!matched && category) {
            const newOpt = document.createElement('option');
            newOpt.value = category;
            newOpt.textContent = category.replace(/_/g, ' ');
            categorySelect.appendChild(newOpt);
        }
        categorySelect.value = category;
    }
    document.getElementById('product-price').value = price;
    document.getElementById('product-description').value = description || '';

    if (imagePreview) {
        if (imageUrl) {
            imagePreview.innerHTML = `
                <div style="display:flex;align-items:center;gap:12px;margin-top:8px;padding:8px;background:var(--bg-subtle);border-radius:8px;">
                    <img src="/static/images/products/${imageUrl}" alt="Current" style="width:64px;height:64px;object-fit:cover;border-radius:6px;" onerror="this.src='/uploads/${imageUrl}'">
                    <span style="font-size:0.82rem;color:var(--text-secondary);">Current image attached. Upload a new file to replace it.</span>
                </div>
            `;
        } else {
            imagePreview.innerHTML = '';
        }
    }

    modal.style.display = 'block';
}

function closeProductModal() {
    const modal = document.getElementById('product-modal');
    if (modal) modal.style.display = 'none';
}

function deleteProduct(productId, productName = 'this product') {
    showConfirmModal({
        title: 'Remove Product?',
        message: `Are you sure you want to remove "${productName}" from the active menu?`,
        confirmText: 'Remove Product',
        danger: true,
        onConfirm: () => {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `/admin/products/${productId}/delete`;
            document.body.appendChild(form);
            form.submit();
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const imageInput = document.getElementById('product-image');
    if (imageInput) {
        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            const imagePreview = document.getElementById('image-preview');
            if (!file) {
                if (imagePreview) imagePreview.innerHTML = '';
                return;
            }
            if (file.size > 5 * 1024 * 1024) {
                showNotification('Image size must be under 5MB.', 'error');
                e.target.value = '';
                if (imagePreview) imagePreview.innerHTML = '';
                return;
            }
            const reader = new FileReader();
            reader.onload = function(ev) {
                if (imagePreview) {
                    imagePreview.innerHTML = `
                        <div style="margin-top:8px;">
                            <img src="${ev.target.result}" alt="Preview" style="max-height:120px;border-radius:8px;border:1px solid var(--border-color);">
                        </div>
                    `;
                }
            };
            reader.readAsDataURL(file);
        });
    }

    window.addEventListener('click', function(event) {
        const productModal = document.getElementById('product-modal');
        if (productModal && event.target === productModal) {
            closeProductModal();
        }
    });
});
