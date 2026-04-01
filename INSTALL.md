# 安装指南 / Installation Guide

## 环境要求

- **Python 3.9+**（仅使用标准库，无需 pip install）
- **OpenCode** 或 **Claude Code**

---

## OpenCode

```bash
# 克隆到 skills 目录
git clone https://github.com/yourname/current-partner-skill.git \
  ~/.config/codewiz/skills/current-partner

# 验证
ls ~/.config/codewiz/skills/current-partner/SKILL.md
```

安装完成后，在 OpenCode 中输入 `/init-partner` 即可开始使用。

---

## Claude Code

```bash
# 方式一：克隆到全局 skills 目录
git clone https://github.com/yourname/current-partner-skill.git \
  ~/.claude/skills/current-partner

# 方式二：克隆到项目级 skills 目录
git clone https://github.com/yourname/current-partner-skill.git \
  .claude/skills/current-partner
```

安装完成后，在 Claude Code 中输入 `/init-partner` 即可开始使用。

---

## 手动安装

如果你不想用 git clone，也可以手动下载：

1. 从 [Releases](https://github.com/yourname/current-partner-skill/releases) 下载最新版本
2. 解压到对应的 skills 目录：
   - OpenCode: `~/.config/codewiz/skills/current-partner/`
   - Claude Code: `~/.claude/skills/current-partner/`
3. 确保目录结构正确（SKILL.md 在根目录）

---

## 验证安装

在你的 AI Agent 中输入：

```
/partner-status
```

如果看到知识库状态输出，说明安装成功。

首次使用需要先初始化：

```
/init-partner
```

---

## 数据目录

运行时数据存储在 `~/.local/share/current-partner/`，与 skill 代码分离。

此目录在首次 `/init-partner` 时自动创建，无需手动操作。

---

## 更新

```bash
# OpenCode
cd ~/.config/codewiz/skills/current-partner && git pull

# Claude Code
cd ~/.claude/skills/current-partner && git pull
```

更新不会影响你的数据（数据在 `~/.local/share/current-partner/`）。

---

## 卸载

```bash
# 删除 skill
rm -rf ~/.config/codewiz/skills/current-partner   # OpenCode
rm -rf ~/.claude/skills/current-partner            # Claude Code

# 删除数据（可选，谨慎操作）
rm -rf ~/.local/share/current-partner
```

---

## 常见问题

### Q: 需要安装额外的 Python 包吗？

不需要。所有工具仅使用 Python 3 标准库（json, re, os, datetime, math, collections, shutil, argparse, pathlib）。

### Q: 数据会上传到服务器吗？

不会。所有数据纯本地存储，代码中零网络请求。

### Q: 支持 Windows 吗？

Python 工具支持 Windows，但 skill 主要在 macOS/Linux 上测试。Windows 用户可能需要调整路径分隔符。

### Q: 可以同时在 OpenCode 和 Claude Code 中使用吗？

可以，但建议只安装在一个环境中，避免数据冲突。两个环境共享同一个数据目录 `~/.local/share/current-partner/`。
