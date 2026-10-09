/**
 * THE ULTIMATE SHOPPING — AI Shopping Assistant Engine
 * Powers Floating Assistant Widget and Dedicated AI Assistant Page
 */

document.addEventListener('DOMContentLoaded', () => {
    initFloatingAssistantWidget();
    initDedicatedAssistantPage();
});

function initFloatingAssistantWidget() {
    const launcherBtn = document.getElementById('ai-launcher-btn');
    const popover = document.getElementById('ai-chat-popover');
    const closeBtn = document.getElementById('ai-close-btn');
    const form = document.getElementById('ai-widget-form');
    const input = document.getElementById('ai-widget-input');
    const messagesContainer = document.getElementById('ai-widget-messages');

    if (!launcherBtn || !popover) return;

    launcherBtn.addEventListener('click', () => {
        popover.classList.toggle('open');
        if (popover.classList.contains('open') && input) {
            input.focus();
        }
    });

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            popover.classList.remove('open');
        });
    }

    if (form && input && messagesContainer) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const query = input.value.trim();
            if (!query) return;

            input.value = '';
            appendUserMessage(messagesContainer, query);
            fetchAssistantResponse(query, messagesContainer);
        });

        // Click on suggestion chip
        messagesContainer.addEventListener('click', (e) => {
            const chip = e.target.closest('.ai-suggestion-chip');
            if (chip) {
                const query = chip.getAttribute('data-query');
                appendUserMessage(messagesContainer, query);
                fetchAssistantResponse(query, messagesContainer);
            }
        });
    }
}

function initDedicatedAssistantPage() {
    const form = document.getElementById('ai-page-form');
    const input = document.getElementById('ai-page-input');
    const messagesContainer = document.getElementById('ai-page-messages');

    if (!form || !input || !messagesContainer) return;

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = input.value.trim();
        if (!query) return;

        input.value = '';
        appendUserMessage(messagesContainer, query);
        fetchAssistantResponse(query, messagesContainer);
    });

    messagesContainer.addEventListener('click', (e) => {
        const chip = e.target.closest('.ai-suggestion-chip');
        if (chip) {
            const query = chip.getAttribute('data-query');
            appendUserMessage(messagesContainer, query);
            fetchAssistantResponse(query, messagesContainer);
        }
    });
}

function appendUserMessage(container, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'ai-message ai-message-user';
    msgDiv.textContent = text;
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
}

function fetchAssistantResponse(query, container) {
    // Show typing placeholder
    const typingDiv = document.createElement('div');
    typingDiv.className = 'ai-message ai-message-bot ai-typing-indicator';
    typingDiv.innerHTML = `<span class="spinner-grow spinner-grow-sm text-warning me-1"></span> Searching our database catalog...`;
    container.appendChild(typingDiv);
    container.scrollTop = container.scrollHeight;

    fetch('/assistant/chat/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken') || '',
        },
        body: JSON.stringify({ query: query })
    })
    .then(res => res.json())
    .then(data => {
        typingDiv.remove();

        const botMsgDiv = document.createElement('div');
        botMsgDiv.className = 'ai-message ai-message-bot';

        let html = `<p class="mb-2"><strong><i class="bi bi-robot text-orange me-1"></i> Ultimate AI:</strong> ${escapeHtml(data.text || '')}</p>`;

        if (data.products && data.products.length > 0) {
            html += `<div class="ai-products-grid mt-2 d-flex flex-column gap-2">`;
            data.products.forEach(p => {
                html += `
                    <div class="card p-2 border shadow-sm" style="background: var(--bg-card); border-radius: 10px;">
                        <div class="d-flex gap-2 align-items-center">
                            <img src="${p.image}" alt="${escapeHtml(p.name)}" style="width: 55px; height: 55px; object-fit: cover; border-radius: 8px;">
                            <div class="flex-grow-1" style="min-width: 0;">
                                <div class="fw-bold text-truncate" style="font-size: 0.82rem; color: var(--text-primary);">${escapeHtml(p.name)}</div>
                                <div class="d-flex align-items-center gap-2 mt-1">
                                    <span class="fw-bold text-orange" style="font-size: 0.88rem;">₹${p.effective_price}</span>
                                    ${p.discount_percent > 0 ? `<span class="badge bg-danger" style="font-size: 0.65rem;">${p.discount_percent}% OFF</span>` : ''}
                                    <span class="text-warning small ms-auto"><i class="bi bi-star-fill"></i> ${p.rating}</span>
                                </div>
                            </div>
                        </div>
                        <div class="d-flex gap-2 mt-2 pt-1 border-top">
                            <a href="${p.detail_url}" class="btn btn-sm btn-outline-secondary flex-grow-1" style="font-size: 0.75rem;">View</a>
                            ${p.in_stock ? `
                                <a href="${p.add_cart_url}" class="btn btn-sm btn-dark ajax-add-cart flex-grow-1" data-url="${p.add_cart_url}" style="font-size: 0.75rem; background: var(--orange-primary); border: none;">Add to Cart</a>
                            ` : `<span class="badge bg-secondary flex-grow-1 py-1" style="font-size: 0.75rem;">Out of Stock</span>`}
                        </div>
                    </div>
                `;
            });
            html += `</div>`;
        }

        if (data.suggestions && data.suggestions.length > 0) {
            html += `<div class="mt-2 pt-2 border-top"><small class="text-muted d-block mb-1">Try asking:</small><div class="d-flex flex-wrap gap-1">`;
            data.suggestions.forEach(s => {
                html += `<button type="button" class="btn btn-sm btn-light border ai-suggestion-chip" data-query="${escapeHtml(s)}" style="font-size: 0.72rem; border-radius: 12px; padding: 2px 8px;">${escapeHtml(s)}</button>`;
            });
            html += `</div></div>`;
        }

        botMsgDiv.innerHTML = html;
        container.appendChild(botMsgDiv);
        container.scrollTop = container.scrollHeight;
    })
    .catch(() => {
        typingDiv.remove();
        const errDiv = document.createElement('div');
        errDiv.className = 'ai-message ai-message-bot text-danger';
        errDiv.textContent = "Sorry, I encountered an issue searching the catalog. Please try again.";
        container.appendChild(errDiv);
        container.scrollTop = container.scrollHeight;
    });
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, function(m) {
        return {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        }[m];
    });
}
