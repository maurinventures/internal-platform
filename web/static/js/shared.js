/**
 * MV Internal - Shared Utility Functions
 * This file contains common functions used across multiple templates.
 * Include this file before template-specific JavaScript.
 */

// ============================================
// Text Utilities
// ============================================

/**
 * Escape HTML special characters to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped HTML string
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format a date string as relative time (e.g., "5m ago", "2h ago")
 * @param {string} dateStr - ISO date string
 * @returns {string} Formatted relative time
 */
function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;

    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    if (diff < 604800000) return `${Math.floor(diff / 86400000)}d ago`;
    return date.toLocaleDateString();
}

// ============================================
// Sidebar Functions
// ============================================

/**
 * Toggle sidebar collapsed state
 */
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    sidebar.classList.toggle('collapsed');
    localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
}

/**
 * Toggle Library section in sidebar
 */
function toggleLibrarySection() {
    const header = document.getElementById('libraryHeader');
    const section = document.getElementById('librarySection');
    if (!header || !section) return;
    header.classList.toggle('expanded');
    section.classList.toggle('expanded');
    localStorage.setItem('libraryExpanded', section.classList.contains('expanded'));
}

/**
 * Restore sidebar state from localStorage
 * Call this on DOMContentLoaded
 */
function restoreSidebarState() {
    // Restore collapsed state
    if (localStorage.getItem('sidebarCollapsed') === 'true') {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) sidebar.classList.add('collapsed');
    }

    // Restore Library section state (use IDs for reliability)
    const libraryHeader = document.getElementById('libraryHeader');
    const librarySection = document.getElementById('librarySection');
    const libraryExpanded = localStorage.getItem('libraryExpanded');

    if (libraryExpanded === 'false') {
        if (libraryHeader) libraryHeader.classList.remove('expanded');
        if (librarySection) librarySection.classList.remove('expanded');
    } else if (libraryExpanded === 'true') {
        if (libraryHeader) libraryHeader.classList.add('expanded');
        if (librarySection) librarySection.classList.add('expanded');
    }

    // Remove the blocking style override now that classes are properly set
    const overrideStyle = document.getElementById('sidebar-state-override');
    if (overrideStyle) {
        overrideStyle.remove();
    }
}

// ============================================
// Toast Notifications
// ============================================

/**
 * Show a toast notification
 * @param {string} message - Message to display
 * @param {string} type - Type: 'success', 'error', or 'info'
 */
function showToast(message, type = 'info') {
    // Remove existing toasts
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    // Add styles if not already in document
    if (!document.getElementById('toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            .toast {
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                padding: 12px 24px;
                border-radius: 8px;
                color: white;
                font-size: 14px;
                z-index: 10000;
                animation: toastIn 0.3s ease;
            }
            .toast-success { background: #10b981; }
            .toast-error { background: #ef4444; }
            .toast-info { background: #3b82f6; }
            @keyframes toastIn {
                from { opacity: 0; transform: translateX(-50%) translateY(20px); }
                to { opacity: 1; transform: translateX(-50%) translateY(0); }
            }
        `;
        document.head.appendChild(style);
    }

    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// ============================================
// Recents Section
// ============================================

/**
 * Toggle expand/collapse state of a recents project folder
 * @param {string} projectId - UUID of the project
 */
function toggleRecentsProject(projectId) {
    const header = document.querySelector(`.recents-project-header[onclick*="${projectId}"]`);
    const items = document.getElementById(`recents-project-${projectId}`);

    if (!header || !items) return;

    // Toggle expanded class
    header.classList.toggle('expanded');
    items.classList.toggle('expanded');

    // Save state to localStorage
    const isExpanded = items.classList.contains('expanded');
    localStorage.setItem(`recents_project_${projectId}`, isExpanded);
}

/**
 * Render conversations list (flat list, no project grouping)
 * @param {Array} conversations - Array of conversation objects
 * @param {string} containerId - ID of the container element (default: 'conversationsList')
 */
function renderConversationsGrouped(conversations, containerId = 'conversationsList') {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Filter out empty chats
    const nonEmpty = (conversations || []).filter(c => c.message_count > 0);

    if (nonEmpty.length === 0) {
        container.innerHTML = '<div style="padding: 0.5rem 1rem; font-size: 0.8125rem; color: #888;">No recent chats</div>';
        return;
    }

    container.innerHTML = nonEmpty.map(conv => `
        <a href="/chat?conversation=${conv.id}" class="conversation-item">
            <span class="conversation-title">${escapeHtml(conv.title)}</span>
        </a>
    `).join('');
}

// ============================================
// Chat Interface (Claude.ai style)
// ============================================

const Chat = {
    conversationId: null,
    selectedModel: 'sonnet-4',
    isLoading: false,

    elements: {},

    init() {
        // Cache DOM elements
        this.elements = {
            welcome: document.getElementById('chatWelcome'),
            greeting: document.getElementById('welcomeGreeting'),
            messages: document.getElementById('chatMessages'),
            input: document.getElementById('chatInput'),
            inputBox: document.getElementById('chatInputBox'),
            sendBtn: document.getElementById('sendBtn'),
            attachBtn: document.getElementById('attachBtn'),
            attachDropdown: document.getElementById('attachDropdown'),
            modelSelectorBtn: document.getElementById('modelSelectorBtn'),
            modelDropdown: document.getElementById('modelDropdown'),
            modelName: document.querySelector('.model-name'),
            quickActions: document.getElementById('quickActions'),
            page: document.querySelector('.chat-page')
        };

        if (!this.elements.input) return;

        this.setGreeting();
        this.bindEvents();
        this.checkExistingChat();

        console.log('Chat initialized');
    },

    setGreeting() {
        const hour = new Date().getHours();
        let greeting;

        if (hour < 12) {
            greeting = 'Good morning, Joy';
        } else if (hour < 17) {
            greeting = 'Good afternoon, Joy';
        } else if (hour < 21) {
            greeting = 'Good evening, Joy';
        } else {
            greeting = 'Coffee and Claude time?';
        }

        if (this.elements.greeting) {
            this.elements.greeting.textContent = greeting;
        }
    },

    bindEvents() {
        // Send button
        this.elements.sendBtn.addEventListener('click', () => this.send());

        // Enter to send (Shift+Enter for newline)
        this.elements.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.send();
            }
        });

        // Input changes
        this.elements.input.addEventListener('input', () => {
            this.autoResize();
            this.elements.sendBtn.disabled = !this.elements.input.value.trim();
        });

        // Attachment menu
        this.elements.attachBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDropdown('attachDropdown');
        });

        // Model selector
        this.elements.modelSelectorBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDropdown('modelDropdown');
        });

        // Model options
        document.querySelectorAll('.model-option[data-model]').forEach(btn => {
            btn.addEventListener('click', () => this.selectModel(btn.dataset.model));
        });

        // Quick action chips
        document.querySelectorAll('.quick-action-chip').forEach(btn => {
            btn.addEventListener('click', () => this.handleQuickAction(btn.dataset.action));
        });

        // Attach options
        document.querySelectorAll('.attach-option').forEach(btn => {
            btn.addEventListener('click', () => this.handleAttachOption(btn.dataset.action));
        });

        // Close dropdowns when clicking outside
        document.addEventListener('click', () => {
            this.closeAllDropdowns();
        });
    },

    autoResize() {
        const input = this.elements.input;
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 200) + 'px';
    },

    toggleDropdown(id) {
        const dropdown = document.getElementById(id);
        const isOpen = dropdown.classList.contains('open');

        this.closeAllDropdowns();

        if (!isOpen) {
            dropdown.classList.add('open');
        }
    },

    closeAllDropdowns() {
        document.querySelectorAll('.model-dropdown, .attach-dropdown').forEach(d => {
            d.classList.remove('open');
        });
    },

    selectModel(model) {
        this.selectedModel = model;

        // Update button text
        const names = {
            'opus-4.5': 'Opus 4.5',
            'sonnet-4': 'Sonnet 4',
            'haiku-4.5': 'Haiku 4.5'
        };
        this.elements.modelName.textContent = names[model] || model;

        // Update selected state
        document.querySelectorAll('.model-option').forEach(btn => {
            btn.classList.toggle('selected', btn.dataset.model === model);
        });

        this.closeAllDropdowns();
    },

    handleQuickAction(action) {
        const prompts = {
            'write': 'Help me write ',
            'learn': 'Explain ',
            'code': 'Write code to ',
            'life-stuff': 'Help me with ',
            'claude-choice': ''
        };

        if (prompts[action] !== undefined) {
            this.elements.input.value = prompts[action];
            this.elements.input.focus();
            this.autoResize();
            this.elements.sendBtn.disabled = !this.elements.input.value.trim();
        }
    },

    handleAttachOption(action) {
        this.closeAllDropdowns();

        switch (action) {
            case 'add-files':
                this.openFilePicker();
                break;
            case 'screenshot':
                showToast('Screenshot feature coming soon', 'info');
                break;
            case 'research':
                this.elements.input.value = '/research ';
                this.elements.input.focus();
                break;
            case 'web-search':
                // Toggle web search
                break;
            default:
                console.log('Action:', action);
        }
    },

    openFilePicker() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*,.pdf,.doc,.docx,.txt,.csv';
        input.multiple = true;
        input.onchange = (e) => {
            const files = Array.from(e.target.files);
            console.log('Files selected:', files.map(f => f.name));
            // TODO: Handle file upload
        };
        input.click();
    },

    async send() {
        const message = this.elements.input.value.trim();
        if (!message || this.isLoading) return;

        this.isLoading = true;
        this.elements.sendBtn.disabled = true;

        // Switch to chat mode
        this.elements.page.classList.add('has-messages');

        // Add user message
        this.addMessage('user', message);

        // Clear input
        this.elements.input.value = '';
        this.autoResize();

        // Add loading message
        const loadingId = this.addMessage('assistant', '', true);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message,
                    conversation_id: this.conversationId,
                    model: this.selectedModel
                })
            });

            if (!response.ok) throw new Error('Failed to send');

            const data = await response.json();

            // Remove loading, add response
            this.removeMessage(loadingId);
            this.addMessage('assistant', data.response);

            // Update conversation ID
            if (data.conversation_id && !this.conversationId) {
                this.conversationId = data.conversation_id;
                history.pushState({}, '', `/chat/${data.conversation_id}`);
            }

        } catch (error) {
            console.error('Chat error:', error);
            this.removeMessage(loadingId);
            this.addMessage('error', 'Failed to send message. Please try again.');
        } finally {
            this.isLoading = false;
            this.elements.sendBtn.disabled = !this.elements.input.value.trim();
        }
    },

    addMessage(role, content, isLoading = false) {
        const id = 'msg-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = `message message-${role}${isLoading ? ' loading' : ''}`;

        div.innerHTML = `
            <div class="message-content">
                ${isLoading ? '<div class="typing-dots"><span></span><span></span><span></span></div>' : this.formatContent(content)}
            </div>
        `;

        this.elements.messages.appendChild(div);
        this.elements.messages.scrollTop = this.elements.messages.scrollHeight;

        return id;
    },

    removeMessage(id) {
        document.getElementById(id)?.remove();
    },

    formatContent(content) {
        // Basic formatting - escape HTML and convert newlines
        return content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\n/g, '<br>');
    },

    checkExistingChat() {
        const match = window.location.pathname.match(/\/chat\/([a-f0-9-]+)/);
        if (match) {
            this.conversationId = match[1];
            this.loadChat();
        }
    },

    async loadChat() {
        try {
            const response = await fetch(`/api/chat/${this.conversationId}`);
            if (!response.ok) return;

            const data = await response.json();

            this.elements.page.classList.add('has-messages');

            data.messages.forEach(msg => {
                this.addMessage(msg.role, msg.content);
            });
        } catch (error) {
            console.error('Failed to load chat:', error);
        }
    }
};

// ============================================
// Auto-initialize on DOM ready
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    restoreSidebarState();

    // Initialize Chat interface if on chat page
    if (document.querySelector('.chat-page')) {
        Chat.init();
    }
});
