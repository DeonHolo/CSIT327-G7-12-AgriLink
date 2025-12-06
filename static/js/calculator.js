/**
 * Fair Price Calculator - Feature 6.2
 * Standalone calculator for determining fair selling prices.
 * 
 * Market Split Model Formula:
 *   Fair Price = (Farmgate Price + Market Price) / 2
 *   Fallback: Farmgate Price * 1.35 (35% markup) if no market price
 * 
 * Savings: ((Market Price - Fair Price) / Market Price) * 100
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const productNameInput = document.getElementById('product-name');
    const categoryInput = document.getElementById('category-select');
    const farmgatePriceInput = document.getElementById('farmgate-price');
    const marketPriceInput = document.getElementById('market-price');
    const fairPriceDisplay = document.getElementById('fair-price-result');
    const savingsBadge = document.getElementById('savings-badge');
    const savingsPercent = document.getElementById('savings-percent');
    const saveBtn = document.getElementById('save-btn');
    const errorDiv = document.getElementById('calc-error');
    const errorText = document.getElementById('calc-error-text');
    const deleteModal = document.getElementById('calc-delete-modal');
    const deleteModalConfirm = document.getElementById('confirm-delete-btn');
    const deleteModalCancel = document.getElementById('cancel-delete-btn');
    const deleteModalClose = document.getElementById('close-delete-btn');
    
    // Constants
    const FALLBACK_MARKUP = 0.35; // 35% markup when no market price
    let pendingDelete = { url: null, button: null };
    
    /**
     * Calculate fair price based on inputs
     * Returns null if farmgate price is invalid
     */
    function calculateFairPrice() {
        const farmgatePrice = parseFloat(farmgatePriceInput.value) || 0;
        const marketPrice = parseFloat(marketPriceInput.value) || 0;
        
        if (farmgatePrice <= 0) {
            return null;
        }
        
        let fairPrice;
        if (marketPrice > 0) {
            // Market Split Model: average of farmgate and market price
            fairPrice = (farmgatePrice + marketPrice) / 2;
        } else {
            // Fallback: 35% markup on farmgate price
            fairPrice = farmgatePrice * (1 + FALLBACK_MARKUP);
        }
        
        return Math.round(fairPrice * 100) / 100; // Round to 2 decimal places
    }
    
    /**
     * Calculate buyer savings percentage
     * Returns 0 if market price is not provided or invalid
     */
    function calculateSavings() {
        const marketPrice = parseFloat(marketPriceInput.value) || 0;
        const fairPrice = calculateFairPrice();
        
        if (marketPrice <= 0 || fairPrice === null || fairPrice >= marketPrice) {
            return 0;
        }
        
        return Math.round(((marketPrice - fairPrice) / marketPrice) * 100);
    }
    
    const formatPeso = (value) => {
        if (value === null || value === undefined || Number.isNaN(value)) return '0.00';
        return new Intl.NumberFormat('en-PH', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    };

    /**
     * Update the fair price display in real-time
     */
    function updateDisplay() {
        const fairPrice = calculateFairPrice();
        const savings = calculateSavings();
        const marketPrice = parseFloat(marketPriceInput.value) || 0;
        
        if (fairPrice !== null) {
            fairPriceDisplay.textContent = formatPeso(fairPrice);
            fairPriceDisplay.classList.add('has-value');
        } else {
            fairPriceDisplay.textContent = '0.00';
            fairPriceDisplay.classList.remove('has-value');
        }
        
        // Show/hide savings badge
        if (savingsBadge && savingsPercent) {
            if (savings > 0 && marketPrice > 0) {
                savingsPercent.textContent = savings;
                savingsBadge.style.display = 'block';
            } else {
                savingsBadge.style.display = 'none';
            }
        }
    }
    
    /**
     * Show error message
     */
    function showError(message) {
        errorText.textContent = message;
        errorDiv.style.display = 'flex';
    }
    
    /**
     * Hide error message
     */
    function hideError() {
        errorDiv.style.display = 'none';
    }
    
    /**
     * Get CSRF token from cookie
     */
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
    
    /**
     * Save calculation to database via AJAX
     */
    async function saveCalculation() {
        hideError();
        
        const productName = productNameInput.value.trim();
        const category = categoryInput.value.trim();
        const farmgatePrice = parseFloat(farmgatePriceInput.value) || 0;
        const marketPrice = parseFloat(marketPriceInput.value) || null;
        const fairPrice = calculateFairPrice();
        
        // Validate product name
        if (!productName) {
            showError('Please enter a product name.');
            productNameInput.focus();
            return;
        }

        // Validate category
        if (!category) {
            showError('Please enter a category.');
            categoryInput.focus();
            return;
        }
        
        // Validate fair price calculation
        if (fairPrice === null) {
            showError('Please enter a valid farmgate price.');
            return;
        }
        
        // Disable button during request
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Saving...';
        
        try {
            const response = await fetch(window.location.href, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    // Keep crop_name key for backend compatibility
                    crop_name: productName,
                    product_name: productName,
                    category: category,
                    farmgate_price: farmgatePrice,
                    market_price: marketPrice,
                    fair_price: fairPrice
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Reload page to show updated history
                window.location.reload();
            } else {
                showError(data.error || 'Failed to save calculation.');
            }
        } catch (err) {
            console.error('Save error:', err);
            showError('Network error. Please try again.');
        } finally {
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="bi bi-save"></i> Save Calculation';
        }
    }
    
    // Event listeners for real-time updates
    farmgatePriceInput.addEventListener('input', updateDisplay);
    marketPriceInput.addEventListener('input', updateDisplay);
    
    // Save button click
    saveBtn.addEventListener('click', saveCalculation);
    
    function openDeleteModal(url, button) {
        if (!deleteModal) return;
        pendingDelete = { url, button };
        deleteModal.classList.add('show');
        deleteModal.setAttribute('aria-hidden', 'false');
        deleteModalConfirm?.focus();
    }
    
    function closeDeleteModal() {
        if (!deleteModal) return;
        deleteModal.classList.remove('show');
        deleteModal.setAttribute('aria-hidden', 'true');
        pendingDelete = { url: null, button: null };
    }
    
    /**
     * Delete a saved calculation
     */
    async function deleteCalculation(deleteUrl, button) {
        if (!deleteUrl) return;
        if (button) button.disabled = true;
        try {
            const response = await fetch(deleteUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
            
            const data = await response.json();
            if (data.success) {
                // Remove row from table without full reload
                const row = button.closest('tr');
                row?.remove();
                closeDeleteModal();
            } else {
                showError(data.error || 'Failed to delete calculation.');
            }
        } catch (err) {
            console.error('Delete error:', err);
            showError('Network error. Please try again.');
        } finally {
            if (button) button.disabled = false;
        }
    }
    
    // Bind delete buttons
    document.querySelectorAll('.calc-delete-btn').forEach(btn => {
        btn.addEventListener('click', () => openDeleteModal(btn.dataset.deleteUrl, btn));
    });
    
    // Modal actions
    deleteModalConfirm?.addEventListener('click', () => {
        if (pendingDelete.url) {
            deleteCalculation(pendingDelete.url, pendingDelete.button);
        }
    });
    deleteModalCancel?.addEventListener('click', closeDeleteModal);
    deleteModalClose?.addEventListener('click', closeDeleteModal);
    deleteModal?.addEventListener('click', (e) => {
        if (e.target === deleteModal) closeDeleteModal();
    });
    
    // Initial display update
    updateDisplay();
});
