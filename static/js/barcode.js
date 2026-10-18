/* ==========================================================================
   Keyboard-Wedge USB Barcode Scanner Integration — Trio Snacks POS
   ========================================================================== */

let barcodeBuffer = '';
let barcodeTimeout = null;

function initBarcodeScanner() {
    const searchInput = document.getElementById('product-search');
    if (!searchInput) return;

    searchInput.addEventListener('keydown', function(e) {
        if (barcodeTimeout) {
            clearTimeout(barcodeTimeout);
        }

        if (e.key === 'Enter' && barcodeBuffer.length >= 5 && !barcodeBuffer.includes(' ')) {
            e.preventDefault();
            const code = barcodeBuffer.trim();
            barcodeBuffer = '';
            searchByBarcode(code);
            return;
        }

        if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
            barcodeBuffer += e.key;
            barcodeTimeout = setTimeout(() => {
                barcodeBuffer = '';
            }, 120);
        } else if (e.key === 'Enter') {
            barcodeBuffer = '';
        }
    });
}

async function searchByBarcode(barcode) {
    try {
        const response = await fetch(`/api/products?barcode=${encodeURIComponent(barcode)}`);
        const products = await response.json();

        if (Array.isArray(products) && products.length > 0) {
            const product = products[0];
            addToCart(product.id);
            showNotification(`Scanned: ${product.name}`, 'success');
            const searchInput = document.getElementById('product-search');
            if (searchInput) searchInput.value = '';
        } else {
            showNotification(`No item matched barcode: ${barcode}`, 'error');
        }
    } catch (error) {
        console.error('Barcode lookup error:', error);
    }
}

document.addEventListener('DOMContentLoaded', initBarcodeScanner);
