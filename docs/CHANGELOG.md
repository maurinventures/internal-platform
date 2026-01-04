# Changelog

## 2026-01-04: Implement route-based view architecture

### What Changed
Completely rewrote the view system from state-based toggling to route-based navigation. Each view now has its own URL:
- `/chat` → New chat (welcome screen)
- `/chat/recents` → Chat list
- `/chat/projects` → Projects list
- `/chat/<conversation_id>` → Specific conversation

### Why
The previous state-based architecture had race conditions where async operations (like `loadConversations()`) would modify view state after the intended view was already shown. Adding guards wasn't sufficient because multiple code paths could show views.

### Root Cause
State-based view toggling is fundamentally prone to race conditions. Multiple functions (`clearChat`, `showChatView`, `createNewConversation`) all manipulated display state, and async operations competed with synchronous view initialization.

### Solution
**Architecture change**: One route = one view. No state toggles.
- Views are now rendered server-side via Jinja2 conditionals based on `{{ view }}` variable
- Sidebar items are `<a href>` links that navigate (not onclick handlers that toggle state)
- Removed: `hideAllViews()`, `showChatsListView()`, `showProjectsListView()`, `showLibraryListView()`, `showNewChatView()`
- Removed: `isChatsListViewActive`, `isProjectsListViewActive`, `isLibraryListViewActive` state variables
- Added: `loadConversationData()` for loading conversation on conversation view
- Added: `sessionStorage` for pending messages when creating new conversation from welcome screen

### Files Modified
- `web/app.py` - Added routes: `/chat/recents`, `/chat/projects`, `/chat/<id>`; updated `/chat` route
- `web/templates/chat.html` - Conditional view rendering, navigation links, removed state toggling

### Issues Encountered
- None - clean implementation

### Current State
- Deployed to production
- Service running
- Ready for testing

---

## 2026-01-04: Fix race condition causing multiple views to display (superseded)

### What Changed
Fixed a race condition in `loadConversations()` that caused BOTH a list view (Chats/Projects) AND the welcome screen to display simultaneously.

### Why
When navigating to Chats or Projects, the async `loadConversations()` function would complete after the view was already shown, then unconditionally call `createNewConversation()` which displayed the welcome screen on top of the list view.

### Root Cause
The default else block in `loadConversations()` always called `createNewConversation()` without checking if a list view was already intentionally displayed.

### Fix
Added condition check before calling `createNewConversation()`:
```javascript
// Before:
} else {
    await createNewConversation();
}

// After:
} else if (!isChatsListViewActive && !isProjectsListViewActive && !isLibraryListViewActive) {
    await createNewConversation();
}
```

### Files Modified
- `web/templates/chat.html` (lines 4266-4268)

### Issues Encountered
- SSH deployment initially failed due to wrong username (`ubuntu` vs `ec2-user`)
- Server doesn't use git for deployment; used `scp` to copy file directly

### Current State
- Fix deployed to production
- Service restarted and running
- Awaiting user verification of the fix
