# 安装 Claude Code

English version: [install-claude-code.md](./install-claude-code.md)

本页是从 `README_zh.md` 顶部移过来的 Claude Code 安装指南原文。如果 `claude` 已在你的 `PATH` 中，可跳过本页直接回到仓库根目录。

## 三种使用方式对比

| 方式 | 适合人群 | 优点 | 缺点 |
|------|----------|------|------|
| Web 端 | 完全新手 | 无需安装，打开就用 | 功能相对有限 |
| CLI（命令行） | 有一定基础的开发者 | 功能完整，集成度高 | 需要熟悉命令行 |
| 编辑器集成（VS Code / Cursor 等） | 日常开发 | 无缝融入工作流 | 依赖插件和环境配置 |

**建议：**
- 完全新手 → 先用 Web 端 [https://claude.ai/](https://claude.ai/) 试试手感
- 想用于开发 → 直接学 CLI（命令行）
- 已经熟练使用 → 考虑编辑器集成

本教程以 **CLI** 为主。

---

## 安装 Claude Code CLI

### 1. 前置准备

- 需要一个 Claude 账号，访问 [claude.ai](https://claude.ai) 注册（如使用国内大模型可跳过）
- 确保电脑有命令行工具：
  - Mac / Linux：打开 Terminal（终端）
  - Windows：打开 PowerShell 或安装 WSL

### 2. 使用官方脚本安装（推荐）

**macOS / Linux / WSL：**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows PowerShell：**
```powershell
irm https://claude.ai/install.ps1 | iex
```

**Windows CMD：**
```cmd
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

安装完成后验证：
```bash
claude --version
```
显示版本号即安装成功。

### 3. 使用 npm 安装

前置条件：已安装 Node.js（验证：`node --version`，若未安装请至 [nodejs.org](https://nodejs.org) 下载）

```bash
npm install -g @anthropic-ai/claude-code
```

网络较慢时可使用国内镜像：
```bash
npm install -g @anthropic-ai/claude-code --registry=https://registry.npmmirror.com
```

### 4. 更新

手动更新：
```bash
claude update
```

Claude Code 启动时会自动检查更新，后台下载后下次启动生效。可在 `settings.json` 中配置更新行为：

```json
{
  "autoUpdatesChannel": "stable"
}
```

禁用自动更新：
```json
{
  "env": {
    "DISABLE_AUTOUPDATER": "1"
  }
}
```

> **注意：** 通过 Homebrew 或 WinGet 安装时不支持自动更新，需手动执行：
> ```bash
> brew upgrade claude-code      # macOS
> winget upgrade Anthropic.ClaudeCode  # Windows
> ```

### 5. 常见安装问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `npm command not found` | 未安装 Node.js | 至 [nodejs.org](https://nodejs.org) 下载安装 |
| `permission denied` | 无管理员权限 | Mac/Linux：命令前加 `sudo`；Windows：以管理员身份运行 PowerShell |
| 安装缓慢或卡住 | 网络问题 | 使用国内镜像：`--registry=https://registry.npmmirror.com` |

### 终端推荐

- [WezTerm](https://wezterm.org/)（跨平台）
- [Alacritty](https://alacritty.org/)（跨平台）
- [Ghostty](https://ghostty.org/)（Linux / macOS）
- [Kitty](https://github.com/kovidgoyal/kitty)（Linux / macOS）
