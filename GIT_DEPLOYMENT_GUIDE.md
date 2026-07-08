# Git Deployment Guide

How to get code from this local project onto GitHub — and why it feels different
from Replit.

---

## Replit vs. local VS Code + terminal

| | Replit (cloud GUI) | Local VS Code + terminal (this project) |
|---|---|---|
| Where the code lives | On Replit's servers, in your browser | On your Mac's disk (`~/Desktop/Claude/Clinical-AI-Eval-Designer`) |
| Sync to GitHub | A "Version control" side-panel button; Replit does the git plumbing invisibly | **You** run the git commands (or click VS Code's Source Control panel) |
| Secrets | Replit "Secrets" tab | `.streamlit/secrets.toml`, kept out of git by `.gitignore` |
| Mental model | Auto-magic sync | Explicit: **stage → commit → push** |

The trade-off: local gives you full control and no vendor lock-in, but nothing
syncs until *you* tell it to. That's what the three commands below do.

---

## The 3-step Git workflow (the loop you'll repeat forever)

```bash
git add -A                       # 1. STAGE   — mark which changes to save
git commit -m "what I changed"   # 2. COMMIT  — save a snapshot locally
git push                         # 3. PUSH    — upload snapshots to GitHub
```

- **`git add`** picks *what* goes into the next snapshot. `-A` = all changes.
- **`git commit`** writes the snapshot to your local history with a message.
  Nothing has left your machine yet.
- **`git push`** sends your local commits up to GitHub. This is the only step
  that touches the internet.

Check state any time with `git status` (what's changed) and `git log --oneline`
(history).

---

## Selective staging — commit only some files

Instead of `git add -A`, name specific files to stage just those:

```bash
git add DEMO_PLAN.md ARCHITECTURE.md      # stage only these two
git commit -m "Update demo plan and architecture"
git push
```

Everything you *didn't* add stays as uncommitted working changes — useful when
you've edited five files but only want to ship two. `git status` shows staged
(green) vs unstaged (red) so you can see exactly what the next commit will
include.

---

## First push & the `--force` flag (online starter files)

When you create a repo on GitHub, if you tick **"Add a README"** (or add a
`.gitignore`/license), GitHub makes a first commit *on the server* that your
local repo doesn't have. Your first `git push` is then **rejected** — git won't
let you overwrite server history it doesn't recognize.

**Safe fix (recommended): merge the server's starter commit into yours.**
```bash
git pull --rebase origin main   # replay your commits on top of GitHub's starter
git push -u origin main
```

**`--force` (only when you're sure):**
```bash
git push -u origin main --force
```
`--force` tells GitHub "discard whatever is up there and make it match my local
history." That **permanently deletes** the server-side starter README/commit.
Fine for a brand-new repo you just made (there's nothing valuable to lose);
**dangerous** on a shared repo with collaborators' work, because it erases their
commits too. Rule of thumb: `--force` only on a repo that is yours alone and
freshly created. Otherwise use `git pull --rebase` first.

If you created the repo **empty** (no README), none of this applies — your first
`git push -u origin main` just works.

---

## VS Code Source Control panel (terminal alternative)

You don't have to use the terminal for the daily loop. In VS Code:

1. Click the **Source Control** icon in the left sidebar (branch-looking icon,
   or `Ctrl/Cmd+Shift+G`).
2. Changed files appear under "Changes." Hover a file and click **+** to stage
   it (equivalent to `git add <file>`); the **+** at the group header stages all.
3. Type a message in the box at the top and click **✓ Commit** (equivalent to
   `git commit -m`).
4. Click **Sync Changes** / the **⋯ → Push** menu (equivalent to `git push`).

It's the same three steps — stage, commit, push — with buttons instead of
commands. The terminal and the panel are interchangeable; use whichever you
prefer.

---

## This project's remote

```
origin  https://github.com/victoriaxxwang/clinical-ai-eval-designer.git
```

Authentication (since `gh` isn't installed): either install the GitHub CLI
(`brew install gh` → `gh auth login`) for browser-based login, or push over
HTTPS and paste a **Personal Access Token** (GitHub → Settings → Developer
settings → Personal access tokens → classic, `repo` scope) when prompted for a
password.
