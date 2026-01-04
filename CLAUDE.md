# Claude Code Rules for MV Internal

## Model

**Use Claude Opus 4.5** (`claude-opus-4-5-20251101`) for all tasks on this project.

---

## PROJECT CONSTANTS — SINGLE SOURCE OF TRUTH

### Server & Deployment

| Key | Value | Notes |
|-----|-------|-------|
| SSH_HOST | `mv-internal` | SSH config alias. Use this for all ssh/scp/rsync commands. |
| DOMAIN | `maurinventuresinternal.com` | NO subdomain. Not www. Not internal. Just this. |
| SERVER_IP | `54.198.253.138` | EC2 instance |
| SSH_USER | `ec2-user` | |
| SSH_KEY | `~/Documents/keys/per_aspera/per-aspera-key.pem` | |
| REMOTE_PATH | `/home/ec2-user/mv-internal` | Where the app lives on server. NOT /var/www/ |
| GIT_REPO_PATH | `/home/ec2-user/video-management` | Git repo on server (syncs to REMOTE_PATH) |
| SERVICE_NAME | `mv-internal` | systemd service name |

### Local Development

| Key | Value |
|-----|-------|
| LOCAL_WEB_PATH | `web/` |
| TEMPLATES | `web/templates/` |
| STATIC | `web/static/` |
| APP_ENTRY | `web/app.py` |

### URLs (Production)

| Route | URL |
|-------|-----|
| Home | `https://maurinventuresinternal.com/chat` |
| Recents | `https://maurinventuresinternal.com/chat/recents` |
| Projects list | `https://maurinventuresinternal.com/chat/projects` |
| Single project | `https://maurinventuresinternal.com/project/{id}` |
| Single chat | `https://maurinventuresinternal.com/chat/{id}` |

---

## RULES — DO NOT VIOLATE

### Rule 1: NEVER INVENT

Never invent, guess, or interpolate:
- Hostnames
- Subdomains
- File paths
- API endpoints
- SSH aliases

If a value is not in this file or in existing code, ASK.

**Wrong:** `internal.maurinventuresinternal.com` (invented subdomain)
**Wrong:** `/var/www/mv-internal/` (invented path)
**Right:** Check this file first, then ask if not found.

### Rule 2: VERIFY BEFORE EXECUTE

Before running any ssh/scp/rsync/curl command:
```bash
# Always echo first
echo "Will run: ssh $SSH_HOST ..."
# Then execute
```

### Rule 3: CANONICAL DEPLOY SEQUENCE
```bash
# 1. Push to git
git push origin main

# 2. Pull on server and sync
ssh mv-internal "cd ~/video-management && git pull && rsync -av ~/video-management/ ~/mv-internal/ --exclude='.git' --exclude='__pycache__' --exclude='*.pyc'"

# 3. Restart service
ssh mv-internal "sudo systemctl restart mv-internal"

# 4. Verify
ssh mv-internal "sudo systemctl status mv-internal --no-pager | head -5"
```

Do not use any other deployment method.

### Rule 4: ONE CHANGE AT A TIME

For any code change:
1. Describe the change
2. Show before/after
3. Make the change
4. Verify it works
5. Commit with descriptive message

Do not batch multiple unrelated changes.

### Rule 5: NO TECHNICAL DEBT

Before adding code, check if:
- Similar code already exists (reuse it)
- The code belongs in shared.js (put it there)
- The code duplicates an API call (consolidate)

Before deleting code:
- Grep to confirm it's unused
- Show the grep results

---

## SSH CONFIG REFERENCE

The local `~/.ssh/config` should contain:
```
Host mv-internal
    HostName 54.198.253.138
    User ec2-user
    IdentityFile ~/Documents/keys/per_aspera/per-aspera-key.pem
```

If it contains anything else for this project (like a different hostname), that is WRONG and should be fixed.

---

## DEBUGGING CHECKLIST

When something fails:

1. **SSH fails?** → Check `~/.ssh/config` matches above
2. **Path not found?** → Use `/home/ec2-user/mv-internal`, not `/var/www/`
3. **Service won't start?** → Check `sudo journalctl -u mv-internal -n 50`
4. **Changes not appearing?** → Did you restart? `sudo systemctl restart mv-internal`
5. **Git conflicts?** → Server repo is at `~/video-management`, app runs from `~/mv-internal`

---

## Secrets

Credentials are **encrypted** with OpenSSL AES-256-CBC and stored in `config/credentials.yaml.enc`.

- **Encrypted file**: `config/credentials.yaml.enc` (committed to git)
- **Template**: `config/credentials.yaml.template` (shows structure)
- **Decrypted file**: `config/credentials.yaml` (gitignored, never commit)

### What's encrypted
- AWS credentials (S3, RDS access)
- Database connection (PostgreSQL on RDS)
- API keys (OpenAI, Anthropic, Notion)
- EC2 instance details

### To decrypt
```bash
openssl aes-256-cbc -d -pbkdf2 -in config/credentials.yaml.enc -out config/credentials.yaml
# Password: Ask project owner or check 1Password
```

### To re-encrypt after changes
```bash
openssl aes-256-cbc -salt -pbkdf2 -in config/credentials.yaml -out config/credentials.yaml.enc
```

---

## Database

- **Type**: PostgreSQL on AWS RDS
- **Credentials**: In encrypted `config/credentials.yaml.enc`

---

## Code Style

- Use existing patterns from the codebase
- Keep UI consistent across all pages (sidebar, styling, interactions)
- Don't create unnecessary files or documentation unless asked

---

## Git

- Commit changes with clear messages
- Push to `main` branch
- Deploy after pushing using canonical sequence

---

## After Every Task

Append a summary to `/docs/CHANGELOG.md` with:
- What you changed and why
- Files modified
- Any issues encountered
- Current state of the feature
