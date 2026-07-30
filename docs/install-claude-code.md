# Installing Claude Code

中文版：[install-claude-code_zh.md](./install-claude-code_zh.md)

This page is the verbatim Claude Code install guide that used to live at the top of `README.md`. If you already have `claude` on your `PATH`, skip this and go back to the repo root.

## Comparison of Usage Methods

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| Web | Complete beginners | No installation required | Limited features |
| CLI (command line) | Developers | Full-featured, highly integrated | Requires command-line familiarity |
| Editor integration (VS Code / Cursor, etc.) | Daily development | Seamless workflow | Depends on plugins and environment setup |

**Recommendation:**
- Complete beginner → Try the web at [https://claude.ai/](https://claude.ai/) first
- Want to use it for development → Go straight to CLI
- Already familiar → Consider editor integration

This guide focuses on the **CLI**.

---

## Installing Claude Code CLI

### 1. Prerequisites

- A Claude account — register at [claude.ai](https://claude.ai) (skip if using a third-party compatible provider)
- A command-line tool:
  - Mac / Linux: open Terminal
  - Windows: open PowerShell or install WSL

### 2. Install via Official Script (Recommended)

**macOS / Linux / WSL:**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows PowerShell:**
```powershell
irm https://claude.ai/install.ps1 | iex
```

**Windows CMD:**
```cmd
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

Verify the installation:
```bash
claude --version
```
A version number means it installed successfully.

### 3. Install via npm

Prerequisite: Node.js must be installed (verify: `node --version`; if missing, download from [nodejs.org](https://nodejs.org))

```bash
npm install -g @anthropic-ai/claude-code
```

If the download is slow, use a mirror:
```bash
npm install -g @anthropic-ai/claude-code --registry=https://registry.npmmirror.com
```

### 4. Updating

Update manually:
```bash
claude update
```

Claude Code checks for updates at launch and installs them in the background; the new version takes effect on the next launch. Configure update behavior in `settings.json`:

```json
{
  "autoUpdatesChannel": "stable"
}
```

Disable automatic updates:
```json
{
  "env": {
    "DISABLE_AUTOUPDATER": "1"
  }
}
```

> **Note:** Homebrew and WinGet installations do not support automatic updates. Update manually:
> ```bash
> brew upgrade claude-code           # macOS
> winget upgrade Anthropic.ClaudeCode  # Windows
> ```

### 5. Common Installation Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| `npm command not found` | Node.js not installed | Download from [nodejs.org](https://nodejs.org) |
| `permission denied` | Insufficient permissions | Mac/Linux: prefix with `sudo`; Windows: run PowerShell as Administrator |
| Slow or stalled installation | Network issues | Use a mirror: `--registry=https://registry.npmmirror.com` |

### Terminal Recommendations

- [WezTerm](https://wezterm.org/) (cross-platform)
- [Alacritty](https://alacritty.org/) (cross-platform)
- [Ghostty](https://ghostty.org/) (Linux / macOS)
- [Kitty](https://github.com/kovidgoyal/kitty) (Linux / macOS)
