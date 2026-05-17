document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // === Cart Functions using Fetch API ===

    /**
     * Update the cart badge with the current count from the server.
     * @returns {Promise<void>}
     */
    async function updateCartBadge() {
        const badge = document.getElementById('cart-count');
        if (!badge) return;

        try {
            const response = await fetch('/cart_count');
            if (!response.ok) throw new Error('Failed to fetch cart count');
            const data = await response.json();
            const count = data.count || 0;
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline' : 'none';
        } catch (error) {
            console.error('Error updating cart badge:', error);
        }
    }

    /**
     * Add a product to the cart.
     * @param {number} productId - The product ID.
     * @param {number} [quantity=1] - Quantity to add.
     * @returns {Promise<void>}
     */
    async function addToCart(productId, quantity = 1) {
        try {
            const response = await fetch('/add_to_cart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ product_id: productId, quantity: quantity })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || 'Failed to add to cart');
            }

            await updateCartBadge();
            showFeedback('Item added to cart!', 'success');
        } catch (error) {
            console.error('Error adding to cart:', error);
            showFeedback(error.message || 'Could not add item to cart.', 'error');
        }
    }

    /**
     * Remove an item from the cart.
     * @param {number} cartItemId - The cart item ID.
     * @returns {Promise<void>}
     */
    async function removeFromCart(cartItemId) {
        try {
            const response = await fetch('/remove_from_cart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ cart_item_id: cartItemId })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || 'Failed to remove item');
            }

            // Remove the row from the table if on cart page
            const row = document.querySelector(`tr[data-cart-item-id="${cartItemId}"]`);
            if (row) row.remove();

            await updateCartBadge();
            showFeedback('Item removed from cart.', 'success');

            // Update total if on cart page
            updateCartTotal();
        } catch (error) {
            console.error('Error removing from cart:', error);
            showFeedback(error.message || 'Could not remove item.', 'error');
        }
    }

    /**
     * Update the quantity of a cart item.
     * @param {number} cartItemId - The cart item ID.
     * @param {number} newQuantity - New quantity.
     * @returns {Promise<void>}
     */
    async function updateCartQuantity(cartItemId, newQuantity) {
        if (newQuantity < 1) {
            await removeFromCart(cartItemId);
            return;
        }

        try {
            const response = await fetch('/update_cart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ cart_item_id: cartItemId, quantity: newQuantity })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || 'Failed to update quantity');
            }

            // Update the displayed quantity and price in the cart table
            const row = document.querySelector(`tr[data-cart-item-id="${cartItemId}"]`);
            if (row) {
                const quantitySpan = row.querySelector('.item-quantity');
                if (quantitySpan) quantitySpan.textContent = newQuantity;

                const priceCell = row.querySelector('.item-total');
                if (priceCell) {
                    const unitPrice = parseFloat(row.dataset.unitPrice);
                    if (!isNaN(unitPrice)) {
                        priceCell.textContent = (unitPrice * newQuantity).toFixed(2);
                    }
                }
            }

            await updateCartBadge();
            updateCartTotal();
        } catch (error) {
            console.error('Error updating cart quantity:', error);
            showFeedback(error.message || 'Could not update quantity.', 'error');
        }
    }

    /**
     * Update the total price displayed on the cart page.
     */
    function updateCartTotal() {
        const totalElement = document.getElementById('cart-total');
        if (!totalElement) return;

        let total = 0;
        document.querySelectorAll('.item-total').forEach(function(cell) {
            const value = parseFloat(cell.textContent);
            if (!isNaN(value)) total += value;
        });
        totalElement.textContent = total.toFixed(2);
    }

    /**
     * Get CSRF token from the meta tag or cookie.
     * @returns {string}
     */
    function getCSRFToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta) return meta.getAttribute('content');

        // Fallback: try to read from cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrf_token') return value;
        }
        return '';
    }

    /**
     * Show a feedback message to the user.
     * @param {string} message - The message.
     * @param {string} type - 'success' or 'error'.
     */
    function showFeedback(message, type) {
        // Create or use existing feedback container
        let container = document.getElementById('feedback-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'feedback-container';
            container.style.position = 'fixed';
            container.style.top = '20px';
            container.style.right = '20px';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        const feedback = document.createElement('div');
        feedback.className = `feedback feedback-${type}`;
        feedback.textContent = message;
        feedback.style.padding = '10px 20px';
        feedback.style.marginBottom = '10px';
        feedback.style.borderRadius = '4px';
        feedback.style.color = '#fff';
        feedback.style.backgroundColor = type === 'success' ? '#28a745' : '#dc3545';
        feedback.style.boxShadow = '0 2px 8px rgba(0,0,0,0.2)';
        feedback.style.transition = 'opacity 0.3s';

        container.appendChild(feedback);

        // Auto remove after 3 seconds
        setTimeout(() => {
            feedback.style.opacity = '0';
            setTimeout(() => feedback.remove(), 300);
        }, 3000);
    }

    // === Event Delegation for Cart Actions ===

    document.addEventListener('click', function(event) {
        // Add to cart button
        const addBtn = event.target.closest('.add-to-cart');
        if (addBtn) {
            event.preventDefault();
            const productId = addBtn.dataset.productId;
            const quantityInput = addBtn.closest('.product-actions')?.querySelector('.quantity-input');
            const quantity = quantityInput ? parseInt(quantityInput.value, 10) : 1;
            if (productId) addToCart(parseInt(productId, 10), quantity || 1);
            return;
        }

        // Remove from cart button
        const removeBtn = event.target.closest('.remove-from-cart');
        if (removeBtn) {
            event.preventDefault();
            const cartItemId = removeBtn.dataset.cartItemId;
            if (cartItemId) removeFromCart(parseInt(cartItemId, 10));
            return;
        }

        // Quantity increment/decrement buttons (if needed)
        const qtyInc = event.target.closest('.qty-inc');
        if (qtyInc) {
            const input = qtyInc.parentElement.querySelector('.cart-quantity');
            if (input) {
                const cartItemId = input.dataset.cartItemId;
                const newQty = parseInt(input.value, 10) + 1;
                if (cartItemId) updateCartQuantity(parseInt(cartItemId, 10), newQty);
            }
            return;
        }

        const qtyDec = event.target.closest('.qty-dec');
        if (qtyDec) {
            const input = qtyDec.parentElement.querySelector('.cart-quantity');
            if (input) {
                const cartItemId = input.dataset.cartItemId;
                const currentQty = parseInt(input.value, 10);
                const newQty = Math.max(1, currentQty - 1);
                if (cartItemId) updateCartQuantity(parseInt(cartItemId, 10), newQty);
            }
            return;
        }
    });

    // Handle direct changes to quantity input (e.g., typing)
    document.addEventListener('change', function(event) {
        const qtyInput = event.target.closest('.cart-quantity');
        if (qtyInput) {
            const cartItemId = qtyInput.dataset.cartItemId;
            let newQty = parseInt(qtyInput.value, 10);
            if (isNaN(newQty) || newQty < 1) {
                qtyInput.value = 1;
                newQty = 1;
            }
            if (cartItemId) updateCartQuantity(parseInt(cartItemId, 10), newQty);
        }
    });

    // === Client-Side Filtering for Shop Page ===

    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        const categorySelect = document.getElementById('category-filter');
        const priceMinInput = document.getElementById('price-min');
        const priceMaxInput = document.getElementById('price-max');
        const searchInput = document.getElementById('search-query');
        const productGrid = document.getElementById('product-grid');
        const productCards = productGrid ? productGrid.querySelectorAll('.product-card') : [];

        /**
         * Filter products based on current filter values.
         */
        function filterProducts() {
            const category = categorySelect ? categorySelect.value.toLowerCase() : '';
            const priceMin = priceMinInput ? parseFloat(priceMinInput.value) : NaN;
            const priceMax = priceMaxInput ? parseFloat(priceMaxInput.value) : NaN;
            const search = searchInput ? searchInput.value.toLowerCase().trim() : '';

            productCards.forEach(function(card) {
                const name = (card.dataset.name || '').toLowerCase();
                const price = parseFloat(card.dataset.price);
                const cat = (card.dataset.category || '').toLowerCase();

                let visible = true;

                // Category filter
                if (category && cat !== category) {
                    visible = false;
                }

                // Price filter
                if (!isNaN(priceMin) && price < priceMin) {
                    visible = false;
                }
                if (!isNaN(priceMax) && price > priceMax) {
                    visible = false;
                }

                // Search filter
                if (search && !name.includes(search)) {
                    visible = false;
                }

                card.style.display = visible ? '' : 'none';
            });
        }

        // Add event listeners for live filtering
        const filterInputs = [categorySelect, priceMinInput, priceMaxInput, searchInput];
        filterInputs.forEach(function(input) {
            if (input) {
                input.addEventListener('input', filterProducts);
                input.addEventListener('change', filterProducts);
            }
        });

        // Initial filter call
        filterProducts();
    }

    // === Initialize: update cart badge on page load ===
    updateCartBadge();
});