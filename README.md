# 现任.skill

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)](#)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-compatible-orange.svg)](#)
[![OpenCode](https://img.shields.io/badge/OpenCode-supported-purple.svg)](#)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-supported-blueviolet.svg)](#)

> 把现任蒸馏成本地知识库，不再忘记那些重要的小事。

Inspired by [前任.skill](https://github.com/therealXiaomanChu/ex-skill) — 从「回忆过去」变成「经营当下」。

**语言 / Language：** [中文](#这是什么) · [English](./README_EN.md)

📖 [安装指南](./INSTALL.md)
---

## 这是什么

一个 AI Agent Skill（兼容 OpenCode / Claude Code），帮你把对象的信息整理成**本地 RAG 知识库**：

- **QQ/微信聊天记录** → 自动提取口头禅、说话风格、承诺语句
- **截图/图片** → AI 视觉直接「看图」提取内容（聊天截图、朋友圈、合照、转账记录等）
- **你的描述** → 记录性格、喜好、雷区、应对方式

建好之后可以：

- 查 ta 的生日、纪念日、喜好
- 追踪双方的承诺（到期提醒）
- 查 ta 说某句话时期望你怎么回
- 模拟 ta 的说话方式（对话模式）
- 随时追加新信息（增量更新）


> *人事音书，漫寄此生。*
> *趁 ta 还在身边，把每一句话都好好收着。*
> *记住 ta 爱吃什么，记住 ta 几点会困，记住那些说过就忘的小事。*
> *世间最奢侈的浪漫，不过是「你随口说的，我都记得」。*

---

## 效果展示

### 初始化

```
> /init-partner

🎯 你好，我是现任.skill 知识库创建器。

你平时怎么叫 ta？

> 宝宝

一句话介绍一下你们的情况？

> 北京 金融 认识一年了

✅ 知识库初始化完成！
```

### 日常查询

```
> ta的生日是什么时候

🔍 从知识库中找到：
  ta 的生日是 3月20日（双鱼座）

💡 提醒：距离下次生日还有 127 天
```

### 回复建议

```
> ta说"我好累"，我该怎么回

🎯 场景：ta说"我好累"

💡 建议这样回：
  "辛苦了宝宝，想吃什么我给你点"

❌ 不要这样回：
  "我也累"

📝 原因：ta需要被关心而不是比惨
```

### 承诺追踪

```
> /partner-promises

🤝 承诺追踪
==================================================

⏳ PENDING (2)
------------------------------
  [p001] ta承诺：说好今年带我去日本
         📅 日期：2024-08-01
         ⏰ 截止：2024-12-31

  [p002] 我承诺：每周至少做一次饭
         📅 日期：2024-09-01
```

### 图片解读

```
> 帮我看看这张聊天截图 ~/screenshots/chat_01.jpg

📸 正在解读截图...

✅ 从截图中提取到：
  - 3条对话消息
  - ta的口头禅："你说呢"
  - 发现一条承诺："下周带你去吃那家日料"

已存入知识库 ✅
```

---

## 快速开始

### 安装

**OpenCode：**
```bash
git clone https://github.com/yourname/current-partner-skill.git \
  ~/.config/opencode/skills/current-partner
```

**Claude Code：**
```bash
git clone https://github.com/yourname/current-partner-skill.git \
  ~/.claude/skills/current-partner
```

> 详细安装指南见 [INSTALL.md](./INSTALL.md)

### 使用

| 命令 | 功能 |
|------|------|
| `/init-partner` | 初始化知识库 |
| `/partner-lookup {关键词}` | 通用查询（生日、喜好、习惯等） |
| `/partner-promises` | 查看所有承诺及状态 |
| `/partner-timeline` | 展示关系时间线 |
| `/partner-reply {场景}` | 查 ta 在该场景下期望的回复方式 |
| `/partner` | 对话模拟（模拟 ta 说话） |
| `/partner-update` | 增量追加新信息 |
| `/partner-rebuild` | 全量重建（⚠️ 会清空重来） |
| `/partner-status` | 查看知识库状态 |
| `/partner-backup` | 手动备份 |
| `/partner-export` | 导出知识库 |
| `/partner-ui` | 🆕 启动 Web 可视化管理界面 |
| `/partner-advisor` | 🆕 回复顾问（分析对话，推荐回复） |

---

## 知识库维度

| 维度 | 内容 | 示例 |
|------|------|------|
| **基础档案** | 称呼、生日、星座、MBTI、职业、喜好 | INFJ 天蝎座 前端工程师 |
| **时间线** | 关键事件和日期 | 2024-06-15 正式在一起 |
| **承诺追踪** | ta的承诺 + 我的承诺 + 状态 | ta说今年带我去日本（pending） |
| **语言模式** | 口头禅 + 说话风格 + 期望回复 | ta说"好累" → 应该关心不要比惨 |
| **情感模式** | 情绪触发器 + 表现 + 应对方式 | 生气时已读不回 → 先认错别讲道理 |

---

## 项目结构

```
current-partner-skill/
├── SKILL.md                 # Skill 入口定义
├── README.md                # 本文件
├── README_EN.md             # English version
├── INSTALL.md               # 安装指南
├── LICENSE                  # MIT License
├── .gitignore
├── prompts/                 # 提示词模板
│   ├── intake.md            #   信息录入引导
│   ├── analysis_guide.md    #   原材料分析指南
│   └── reply_advisor.md     #   回复建议模板
└── tools/                   # Python 工具（零依赖）
    ├── rag_store.py          #   RAG 知识库（TF-IDF 检索）
    ├── promise_tracker.py    #   承诺追踪器
    ├── image_scanner.py      #   图片目录扫描
    ├── wechat_parser.py      #   微信聊天记录解析
    ├── qq_parser.py          #   QQ 聊天记录解析
    ├── version_manager.py    #   版本备份与回滚
    ├── web_server.py         #   🆕 Web UI 服务器
    └── static/               #   🆕 Web UI 静态文件
        └── index.html        #     甜蜜风格管理界面
```

运行时数据存储：
```
~/.local/share/current-partner/
├── profile.json              # 基础档案
├── timeline.jsonl            # 时间线事件
├── promises.jsonl            # 承诺追踪
├── language_patterns.jsonl   # 语言模式
├── emotional_patterns.jsonl  # 情感模式
├── index.json                # TF-IDF 索引
├── meta.json                 # 元数据
├── raw_materials/            # 原始素材文本
└── backups/                  # 版本备份
```

---

## 🆕 Web 可视化管理界面

启动本地 Web 服务，在浏览器中可视化管理知识库：

```bash
python3 tools/web_server.py --data-dir ~/.local/share/current-partner
```

浏览器自动打开 `http://127.0.0.1:8765`

### 功能一览

| Tab | 功能 |
|-----|------|
| 💕 档案 | 编辑基础档案（称呼、生日、MBTI、爱好、标签等） |
| 📅 时间线 | 可视化时间轴，添加/编辑/删除事件 |
| 🤝 承诺 | 按状态分组展示承诺，支持状态切换 |
| 🗣️ 语言 | 口头禅、期望回复方式、发消息风格管理 |
| 💡 情感 | 情感模式管理（触发因素、表现特征、应对方式） |
| 💬 回复顾问 | 粘贴对话内容，AI 分析推荐回复 + 避雷回复 |

### 回复顾问功能

粘贴聊天记录或描述场景，AI 基于知识库分析：

```
输入：
  ta: 我今天好累啊
  我: 怎么了？
  ta: 就是很烦，不想说话

输出：
  ✅ 推荐回复：先表示关心，问问发生了什么，不要急着给建议
  ❌ 避雷回复：说"我也累"、"你想多了"
  💡 原因：当对方表达负面情绪时，需要的是共情和关心
```

分析结果可一键存入知识库。

### 界面风格

- 🎨 甜蜜粉色主题，温暖美观
- 📱 响应式设计，支持移动端
- ⚡ 实时同步，操作直接写入文件

---

## 技术特点

- **零外部依赖** — 仅使用 Python 3 标准库（json, re, os, datetime, math, collections）
- **纯本地存储** — 所有数据存在 `~/.local/share/current-partner/`，零网络请求
- **TF-IDF 检索** — 轻量级文本检索，无需向量数据库
- **AI 视觉解读** — 通过 `look_at` 工具直接「看」截图，提取文本信息
- **隐私优先** — 截图仅提取文字后保存为文本，不存储原始图片
- **增量更新** — 每次更新自动备份，支持回滚
- **🆕 Web 可视化** — 本地 HTTP 服务 + 甜蜜风格管理界面，支持增删改查

---

## 隐私说明

- 所有数据**纯本地存储**，零网络请求
- 截图仅提取文字，不保存原始图片
- 支持随时导出、备份、删除全部数据
- 你的数据只属于你

---

## 贡献

欢迎贡献！请参考以下方式：

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: 添加某某功能'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 贡献方向

- 支持更多聊天记录格式（Telegram、iMessage、LINE 等）
- 优化 TF-IDF 检索效果
- 添加纪念日自动提醒
- 支持多对象管理（如果你有这个需求的话...）
- 国际化（i18n）

---

## 致敬

架构灵感来自 [前任.skill](https://github.com/therealXiaomanChu/ex-skill)（by therealXiaomanChu），从「回忆过去的人」变成「更好地对待眼前的人」。

---

## License

[MIT](./LICENSE) - 随便用，开心就好。

---

> 最好的关系不是记住 ta 说过什么，而是记住 ta 需要什么。

---

## 写在最后

满目山河空念远，不如怜取眼前人。

---

> 愿每一对恋人，都能被温柔以待。
