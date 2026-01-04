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
 * Toggle Projects section in sidebar
 */
function toggleProjectsSection() {
    const headers = document.querySelectorAll('.sidebar-section-header');
    const header = headers[0]; // First header is Projects
    const section = document.getElementById('projectsSection');
    if (!header || !section) return;
    header.classList.toggle('expanded');
    section.classList.toggle('expanded');
    localStorage.setItem('projectsExpanded', section.classList.contains('expanded'));
}

/**
 * Toggle Library section in sidebar
 */
function toggleLibrarySection() {
    const headers = document.querySelectorAll('.sidebar-section-header');
    const header = headers[1]; // Second header is Library
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

    // Restore Projects section state
    if (localStorage.getItem('projectsExpanded') === 'false') {
        const headers = document.querySelectorAll('.sidebar-section-header');
        const projectsSection = document.getElementById('projectsSection');
        if (headers[0]) headers[0].classList.remove('expanded');
        if (projectsSection) projectsSection.classList.remove('expanded');
    }

    // Restore Library section state
    if (localStorage.getItem('libraryExpanded') === 'false') {
        const headers = document.querySelectorAll('.sidebar-section-header');
        const librarySection = document.getElementById('librarySection');
        if (headers[1]) headers[1].classList.remove('expanded');
        if (librarySection) librarySection.classList.remove('expanded');
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
// Recents Section (Project-Grouped Conversations)
// ============================================

/**
 * Inject CSS for recents project grouping if not already present
 */
function injectRecentsStyles() {
    if (document.getElementById('recents-styles')) return;

    const style = document.createElement('style');
    style.id = 'recents-styles';
    style.textContent = `
        .recents-project-group {
            margin-bottom: 0.25rem;
        }
        .recents-project-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.375rem 0.75rem;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.15s;
        }
        .recents-project-header:hover {
            background: #f0efea;
        }
        .recents-project-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            flex-shrink: 0;
        }
        .recents-project-name {
            font-size: 0.8125rem;
            font-weight: 500;
            color: #1a1a1a;
            flex: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .recents-project-chevron {
            width: 14px;
            height: 14px;
            color: #888;
            transition: transform 0.2s;
            flex-shrink: 0;
        }
        .recents-project-header.expanded .recents-project-chevron {
            transform: rotate(180deg);
        }
        .recents-project-items {
            display: none;
            padding-left: 0.5rem;
        }
        .recents-project-items.expanded {
            display: block;
        }
        .conversation-item.nested {
            padding-left: 1.25rem;
        }
    `;
    document.head.appendChild(style);
}

/**
 * Toggle a project folder in the recents section
 * @param {string} projectId - Project ID
 */
function toggleRecentsProject(projectId) {
    const items = document.getElementById(`recents-project-${projectId}`);
    if (!items) return;
    const header = items.previousElementSibling;
    const isExpanded = items.classList.toggle('expanded');
    if (header) header.classList.toggle('expanded', isExpanded);
    localStorage.setItem(`recents_project_${projectId}`, isExpanded);
}

/**
 * Render conversations list grouped by project
 * @param {Array} conversations - Array of conversation objects
 * @param {string} containerId - ID of the container element (default: 'conversationsList')
 */
function renderConversationsGrouped(conversations, containerId = 'conversationsList') {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Inject styles if needed
    injectRecentsStyles();

    // Filter out empty chats and group by project
    const projectGroups = {};
    const ungrouped = [];

    (conversations || []).filter(c => c.message_count > 0).forEach(conv => {
        if (conv.project) {
            if (!projectGroups[conv.project.id]) {
                projectGroups[conv.project.id] = {
                    project: conv.project,
                    conversations: []
                };
            }
            projectGroups[conv.project.id].conversations.push(conv);
        } else {
            ungrouped.push(conv);
        }
    });

    let html = '';

    // Render project groups
    Object.values(projectGroups).forEach(group => {
        const isExpanded = localStorage.getItem(`recents_project_${group.project.id}`) !== 'false';
        html += `
            <div class="recents-project-group">
                <div class="recents-project-header ${isExpanded ? 'expanded' : ''}" onclick="toggleRecentsProject('${group.project.id}')">
                    <span class="recents-project-dot" style="background: ${group.project.color || '#d97757'}"></span>
                    <span class="recents-project-name">${escapeHtml(group.project.name)}</span>
                    <svg class="recents-project-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
                </div>
                <div class="recents-project-items ${isExpanded ? 'expanded' : ''}" id="recents-project-${group.project.id}">
                    ${group.conversations.map(conv => `
                        <a href="/chat?conversation=${conv.id}" class="conversation-item nested">
                            <span class="conversation-title">${escapeHtml(conv.title)}</span>
                        </a>
                    `).join('')}
                </div>
            </div>
        `;
    });

    // Render ungrouped conversations
    ungrouped.forEach(conv => {
        html += `
            <a href="/chat?conversation=${conv.id}" class="conversation-item">
                <span class="conversation-title">${escapeHtml(conv.title)}</span>
            </a>
        `;
    });

    container.innerHTML = html || '<div style="padding: 0.5rem 1rem; font-size: 0.8125rem; color: #888;">No recent chats</div>';
}

// ============================================
// Auto-initialize on DOM ready
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    restoreSidebarState();
    injectRecentsStyles();
});
