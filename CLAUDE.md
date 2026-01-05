# Claude Code Rules for MV Internal

**Last Updated:** 2026-01-04 21:30 EST

---

## MODEL REQUIREMENT

**Use Claude Sonnet 4** (`claude-sonnet-4-20250514`) for all tasks.

**Opus 4.5 is too expensive.** Only use if explicitly requested.

---

## SESSION START — REQUIRED CONFIRMATION

At the START of every session, Claude Code must:

### 1. Confirm Model

```
✅ Model: Claude Sonnet 4 (claude-sonnet-4-20250514)
```

If using Opus, STOP and switch to Sonnet unless user explicitly approved Opus.

### 2. Confirm Task Understanding

Before writing ANY code or running ANY command:

```
📋 TASK CONFIRMATION

I will:
1. [First thing I will do]
2. [Second thing I will do]
3. [Third thing I will do]

Files I will modify:
- path/to/file1.html
- path/to/file2.py

I will NOT:
- [Anything out of scope]

Proceed? (yes/no)
```

Wait for user confirmation before proceeding.

### 3. Read CLAUDE.md

```
✅ Read CLAUDE.md
✅ SSH_HOST: mv-internal
✅ DOMAIN: maurinventuresinternal.com
✅ Will follow one-change-at-a-time rule
```

---

## SESSION LOGGING — REQUIRED

At the END of every session, create a detailed log:

```bash
# Create session log with timestamp
SESSION_LOG="session_$(date +%Y%m%d_%H%M%S).md"
cat > "$SESSION_LOG" << 'EOF'
# Session Log: [DATE]

## Summary
[One paragraph summary of what was accomplished]

## Changes Made
| File | Change | Lines |
|------|--------|-------|
| path/to/file | Description | 10-25 |

## Commands Executed
```bash
[All significant commands run]
```

## Issues Encountered
- [Issue 1 and resolution]

## Current State
[What works, what doesn't, what's next]

## Verification Results
- [ ] Tested X — PASS/FAIL
- [ ] Tested Y — PASS/FAIL
EOF

# Show location
echo "Session log saved to: $SESSION_LOG"
```

Save to project root. User will send to auditor.

---

## PROJECT CONSTANTS — SINGLE SOURCE OF TRUTH

### Server & Deployment

| Key | Value | Notes |
|-----|-------|-------|
| SSH_HOST | `mv-internal` | SSH config alias. Use for all ssh/scp/rsync. |
| DOMAIN | `maurinventuresinternal.com` | NO subdomain. Not www. Not internal. |
| SERVER_IP | `54.198.253.138` | EC2 instance |
| SSH_USER | `ec2-user` | |
| SSH_KEY | `~/Documents/keys/per_aspera/per-aspera-key.pem` | |
| REMOTE_PATH | `/home/ec2-user/mv-internal` | App location. NOT /var/www/ |
| GIT_REPO_PATH | `/home/ec2-user/video-management` | Git repo (syncs to REMOTE_PATH) |
| SERVICE_NAME | `mv-internal` | systemd service name |

### Local Development

| Key | Value |
|-----|-------|
| LOCAL_WEB_PATH | `web/` |
| TEMPLATES | `web/templates/` |
| STATIC | `web/static/` |
| SHARED_JS | `web/static/js/shared.js` |
| APP_ENTRY | `web/app.py` |

### URLs (Production)

| Route | URL |
|-------|-----|
| Home | `https://maurinventuresinternal.com/chat` |
| Chats List | `https://maurinventuresinternal.com/chat/recents` |
| Projects List | `https://maurinventuresinternal.com/projects` |
| Single Project | `https://maurinventuresinternal.com/project/{id}` |
| Single Chat | `https://maurinventuresinternal.com/chat/{id}` |

---

## RULES — DO NOT VIOLATE

### Rule 1: NEVER INVENT

Never invent, guess, or interpolate:
- Hostnames or subdomains
- File paths
- API endpoints
- SSH aliases
- CSS class names

If a value is not in this file or in existing code, **ASK**.

**Wrong:** `internal.maurinventuresinternal.com` (invented subdomain)
**Wrong:** `/var/www/mv-internal/` (invented path)
**Wrong:** `class="project-dot"` when CSS defines `.project-color-dot`
**Right:** Check this file first, grep existing code, then ask if not found.

### Rule 2: VERIFY BEFORE EXECUTE

Before running any destructive or remote command:
```bash
# Echo first
echo "Will run: ssh $SSH_HOST ..."
# Then execute
```

### Rule 3: CANONICAL DEPLOY SEQUENCE

```bash
# 1. Commit and push
git add -A && git commit -m "Description of change"
git push origin main

# 2. Pull on server and sync
ssh mv-internal "cd ~/video-management && git pull && rsync -av ~/video-management/ ~/mv-internal/ --exclude='.git' --exclude='__pycache__' --exclude='*.pyc'"

# 3. Restart service
ssh mv-internal "sudo systemctl restart mv-internal"

# 4. Verify running
ssh mv-internal "sudo systemctl status mv-internal --no-pager | head -5"
```

**Do not use any other deployment method.**

### Rule 4: ONE CHANGE AT A TIME

For any code change:
1. State what you will change and why
2. Show the exact before/after
3. Make the change
4. Verify it works (provide test steps)
5. Commit with descriptive message
6. Provide rollback command

**Never batch multiple unrelated changes.**

### Rule 5: NO TECHNICAL DEBT

Before adding code:
- [ ] Grep for similar code — reuse it
- [ ] Check if it belongs in `shared.js` — put it there
- [ ] Check for duplicate API calls — consolidate

Before deleting code:
- [ ] Grep to confirm unused
- [ ] Show grep results proving it's safe

### Rule 6: CSS/HTML CONSISTENCY

Before using a CSS class:
```bash
# Verify the class exists
grep -n "\.classname" web/templates/*.html web/static/css/*.css
```

Before creating a CSS class:
```bash
# Check no similar class exists
grep -n "similar-name" web/templates/*.html
```

**Class naming conventions:**
- Use existing class names exactly as defined
- Sidebar items: `.project-item`, `.project-color-dot`, `.project-name`, `.project-count`
- Do not create variants like `.project-dot` when `.project-color-dot` exists

### Rule 7: SERVER-SIDE RENDERING FOR SIDEBAR

Sidebar content (projects list, recents list) must be **server-rendered via Jinja**, not loaded via JavaScript fetch.

**Why:** JavaScript-loaded content causes layout jitter on page load.

**Pattern:**
```python
# In Flask route
@app.route('/page')
def page():
    projects = get_projects()
    return render_template('page.html', projects=projects)
```

```html
<!-- In Jinja template -->
{% for project in projects %}
<a href="/project/{{ project.id }}" class="project-item">
    <span class="project-color-dot" style="background: {{ project.color }}"></span>
    <span class="project-name">{{ project.name }}</span>
</a>
{% endfor %}
```

**Keep JavaScript only for:** Refreshing after user actions (create, delete, rename).

---

## TESTING CHECKLIST

After ANY frontend change, verify:

- [ ] Hard refresh `/chat` — no console errors
- [ ] Sidebar renders immediately — no jitter, no flash
- [ ] Click sidebar items — navigation works, no jitter
- [ ] Collapse/expand sections — state persists on reload
- [ ] Mobile width — sidebar collapses appropriately

After ANY backend change, verify:

- [ ] Service restarts without error
- [ ] `curl https://maurinventuresinternal.com/chat` returns 200
- [ ] API endpoints return expected data

---

## AUTOMATED SITE AUDIT

Run the full site audit after any significant UI changes or before major releases.

### Setup (one-time)

```bash
cd ~/video-management
npm install playwright
npx playwright install chromium
mkdir -p tests test-results
```

### Get Session Cookie

1. Open https://maurinventuresinternal.com in browser
2. DevTools (F12) → Application → Cookies
3. Copy `session` cookie value
4. Update `AUTH_COOKIE.value` in `tests/full-site-audit.js`

### Run Audit

```bash
node tests/full-site-audit.js
```

### Review Results

```bash
# Summary in terminal
# Detailed results:
cat test-results/audit-results.json

# Screenshots of failures:
ls test-results/*.png
```

### When to Run

| Situation | Run Audit? |
|-----------|------------|
| After fixing navigation bugs | ✅ Yes |
| After changing sidebar | ✅ Yes |
| After adding new routes | ✅ Yes |
| After CSS-only changes | ⚠️ Optional |
| Before marking feature complete | ✅ Yes |
| After deployment to verify | ✅ Yes |

### What It Tests

- Sidebar navigation (all links go to correct URLs)
- Chats page (lists chats, count accurate)
- Projects page (loads, lists projects)
- Chat functionality (header, share, dropdown)
- Sidebar hover menus (••• button, menu opens)
- All internal links (no 404s)

### Fixing Failures

After audit, failures are listed with details. Fix ONE at a time:

1. Read the failure message
2. Find the relevant code (`grep`)
3. Fix it
4. Deploy
5. Re-run audit to confirm

---

## ROLLBACK PROCEDURE

If deployment breaks something:

```bash
# 1. Check what broke
ssh mv-internal "sudo journalctl -u mv-internal -n 50 --no-pager"

# 2. Find last working commit
git log --oneline -10

# 3. Revert to specific commit
git revert HEAD --no-edit  # Revert last commit
# OR
git reset --hard <commit-hash>  # Nuclear option

# 4. Force push and redeploy
git push origin main --force
ssh mv-internal "cd ~/video-management && git pull && rsync -av ~/video-management/ ~/mv-internal/ --exclude='.git' --exclude='__pycache__' --exclude='*.pyc'"
ssh mv-internal "sudo systemctl restart mv-internal"
```

---

## SSH CONFIG REFERENCE

Local `~/.ssh/config` must contain:
```
Host mv-internal
    HostName 54.198.253.138
    User ec2-user
    IdentityFile ~/Documents/keys/per_aspera/per-aspera-key.pem
```

Any other hostname for this project is **WRONG**.

---

## DEBUGGING CHECKLIST

| Symptom | Check |
|---------|-------|
| SSH fails | `~/.ssh/config` matches above |
| Path not found | Use `/home/ec2-user/mv-internal`, not `/var/www/` |
| Service won't start | `sudo journalctl -u mv-internal -n 50` |
| Changes not appearing | Did you `systemctl restart mv-internal`? |
| Git conflicts | Server repo at `~/video-management`, app at `~/mv-internal` |
| CSS class not working | Grep to verify class name matches exactly |
| Sidebar jitters | Content must be server-rendered, not JS-fetched |

---

## SECRETS

Credentials are **encrypted** with OpenSSL AES-256-CBC.

| File | Purpose |
|------|---------|
| `config/credentials.yaml.enc` | Encrypted (committed) |
| `config/credentials.yaml.template` | Structure reference |
| `config/credentials.yaml` | Decrypted (gitignored, never commit) |

```bash
# Decrypt
openssl aes-256-cbc -d -pbkdf2 -in config/credentials.yaml.enc -out config/credentials.yaml

# Re-encrypt after changes
openssl aes-256-cbc -salt -pbkdf2 -in config/credentials.yaml -out config/credentials.yaml.enc
```

---

## DATABASE

- **Type:** PostgreSQL on AWS RDS
- **Credentials:** In `config/credentials.yaml.enc`

---

## GIT WORKFLOW

1. Commit with clear, specific messages
2. Push to `main` branch
3. Deploy using canonical sequence
4. Verify deployment succeeded
5. Update `/docs/CHANGELOG.md`

---

## AFTER EVERY SESSION

1. **Create session log** (see SESSION LOGGING section)
2. **Update CHANGELOG.md** with:
   - What changed and why
   - Files modified
   - Issues encountered
   - Current state
3. **Inform user** of log location for audit
