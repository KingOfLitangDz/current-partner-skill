---
name: "current-partner"
description: "现任.skill — 把现任蒸馏成本地知识库。导入 QQ/微信聊天记录、截图、人为描述，构建本地 RAG 库，记录关键时间节点、承诺事项、常用语句和期望回复方式，支持增量/全量更新。触发词：现任、对象、bae、另一半、partner"
---

> **Language / 语言**: 根据用户第一条消息的语言，全程使用同一语言回复。

# 现任.skill — 恋爱关系知识库

## 触发条件

当用户说以下任意内容时启动对应功能：

**初始化：**
* `/init-partner` 或 "初始化现任" / "新建对象档案" / "建一个现任skill"

**对话模式：**
* `/partner` 或 "问问ta会怎么说" / "ta怎么想" / "模拟现任"

**查询模式：**
* `/partner-lookup` 或 "查一下ta的xx" / "ta的生日" / "ta喜欢什么" / "纪念日是什么时候"
* `/partner-promises` 或 "ta承诺过什么" / "我答应过什么" / "我们说好的"
* `/partner-timeline` 或 "时间线" / "我们经历了什么"
* `/partner-reply` 或 "ta一般怎么回" / "怎么回复ta" / "ta期望我怎么说"

**更新模式：**
* `/partner-update` 或 "更新记录" / "追加记录" / "我想补充"
* `/partner-rebuild` 或 "全量重建" / "重新导入"

**管理命令：**
* `/partner-status` — 查看 RAG 库状态
* `/partner-export` — 导出知识库
* `/partner-backup` — 手动备份
* `/partner-ui` — 启动 Web 可视化管理界面

**回复顾问：**
* `/partner-advisor` 或 "帮我分析怎么回" / "ta这么说该怎么回" / "回复建议"

---

## 工具使用规则

本 Skill 运行在 OpenCode / Claude Code 环境，使用以下工具：

| 任务 | 使用工具 |
|------|----------|
| **解读图片/截图** | `look_at` 工具（首选）或 `Read` 工具 — 支持 JPG/PNG/WEBP/GIF，直接传文件路径 |
| 读取文本文件 | `Read` 工具 |
| 解析微信聊天记录 | `Bash` → `python3 ${SKILL_DIR}/tools/wechat_parser.py` |
| 解析 QQ 聊天记录 | `Bash` → `python3 ${SKILL_DIR}/tools/qq_parser.py` |
| 扫描图片目录 | `Bash` → `python3 ${SKILL_DIR}/tools/image_scanner.py` |
| RAG 知识库操作 | `Bash` → `python3 ${SKILL_DIR}/tools/rag_store.py` |
| 承诺追踪 | `Bash` → `python3 ${SKILL_DIR}/tools/promise_tracker.py` |
| 写入/更新文件 | `Write` / `Edit` 工具 |
| 备份与版本管理 | `Bash` → `python3 ${SKILL_DIR}/tools/version_manager.py` |
| **Web 可视化管理** | `Bash` → `python3 ${SKILL_DIR}/tools/web_server.py` — 启动本地 HTTP 服务，浏览器访问管理界面 |

**数据目录**：`~/.local/share/current-partner/`

### 图片解读能力（⭐ 核心能力）

本 Skill 通过 OpenCode/Claude Code **原生图片理解能力**解读截图，无需 OCR 库。

**支持的图片类型：**
- 聊天截图（微信/QQ/iMessage/其他 IM）
- 朋友圈/微博/小红书截图
- 备忘录/便签截图
- 合照/约会照片
- 转账/红包/订单截图

**解读流程：**

1. **单张图片** — 用 `look_at` 工具直接解读：
```
look_at(file_path="/path/to/screenshot.jpg", goal="从这张截图中提取以下信息：1.聊天内容和发送者 2.时间信息 3.情绪/语气 4.承诺或约定 5.口头禅或特殊用语 6.地点/事件相关信息")
```

2. **批量图片** — 先用 `image_scanner.py` 扫描目录获取文件列表，再逐张用 `look_at` 解读：
```bash
python3 ${SKILL_DIR}/tools/image_scanner.py \
  --dir /path/to/screenshots \
  --output /tmp/image_list.json
```
然后对每张图片调用 `look_at`，将提取的文本保存到 `raw_materials/`。

3. **解读后处理** — 将 `look_at` 返回的文本内容按 6 个维度分析（参考 `prompts/analysis_guide.md`），存入 RAG 库对应分类。

**从图片中提取的信息类型：**

| 图片类型 | 提取内容 | 存入分类 |
|----------|----------|----------|
| 聊天截图 | 对话内容、语气、口头禅、承诺 | language_patterns + promises |
| 朋友圈截图 | 文案风格、兴趣爱好、心情状态 | profile + emotional_patterns |
| 合照/约会照 | 地点、时间、事件 | timeline |
| 转账/红包截图 | 金额、备注、纪念日线索 | timeline + promises |
| 备忘录截图 | 计划、愿望清单、承诺 | promises + timeline |

---

## 安全边界（⚠️ 重要）

1. **仅用于经营现有关系**，帮助你更了解对方、记住承诺、改善沟通
2. **隐私保护**：所有数据仅本地存储，绝不上传任何服务器
3. **不替代真实沟通**：这是辅助工具，不是替代品
4. **尊重对方**：不用于监控、控制或操纵对方
5. **图片处理**：截图仅提取文字信息后保存为文本，不存储原始图片

---

## 主流程一：初始化（`/init-partner`）

### Step 1：基础信息录入

参考 `${SKILL_DIR}/prompts/intake.md` 的问题序列，问以下问题：

1. **称呼/昵称**（必填）
   * 你平时怎么叫ta？
   * 示例：`宝宝` / `小猪` / `老公` / `亲爱的` / `某某某`

2. **基本信息**（一句话概括）
   * 示例：`在一起一年了 互联网前端 上海 大学同学`
   * 示例：`谈了三个月 老师 北京 朋友介绍的`

3. **性格画像**（一句话描述）
   * 示例：`INFJ 天蝎座 外冷内热 嘴硬心软 生气不说话但会给我买吃的`
   * 示例：`ENFP 狮子座 话痨 社牛 占有欲强 但很会照顾人`

4. **关键纪念日**（可跳过）
   * 在一起的日期、生日、第一次见面等
   * 示例：`在一起 2024-06-15 生日 1999-03-20 第一次见面 2024-05-01`

除称呼外均可跳过。收集完后汇总确认再进入下一步。

### Step 2：原材料导入

```
你有哪些素材可以提供？素材越多，知识库越完善。

  [A] 微信聊天记录导出
      支持 WeChatMsg、留痕、PyWxDump 导出格式（txt/html/json）

  [B] QQ 聊天记录导出
      支持 QQ 导出的 txt/mht 格式

  [C] 截图/图片（⭐ 支持 AI 视觉解读）
      聊天截图、朋友圈截图、合照、转账截图、备忘录截图
      → AI 直接"看"图片，提取文字、情绪、地点等信息
      → 支持单张或整个文件夹批量导入
      → 不保存原图，仅保留提取的文本

  [D] 直接口述/粘贴
      把你记得的事情告诉我，比如：
      🗓️ 关键的事件和日期
      🤝 ta/你承诺过的事情
      🗣️ ta的口头禅和常用语
      💬 ta喜欢你怎么回复
      😤 ta生气时你应该怎么做
      💕 你们的 inside jokes

可以混用，随时追加。也可以先跳过，之后用 /partner-update 补充。
```

#### 方式 C 详细流程：截图/图片解读

**场景 1：用户提供单张图片路径**

直接用 `look_at` 工具解读，goal 参数根据图片类型调整：

```
# 聊天截图
look_at(file_path="{用户提供的路径}", goal="这是一张聊天截图。请提取：1.每条消息的发送者和内容 2.时间信息 3.对话中体现的语气和情绪 4.任何承诺、约定或计划 5.口头禅或反复出现的表达方式 6.称呼方式")

# 朋友圈/社交媒体截图
look_at(file_path="{用户提供的路径}", goal="这是一张社交媒体截图。请提取：1.发布的文案内容 2.发布时间 3.体现的心情/状态 4.兴趣爱好线索 5.地点信息 6.评论互动内容")

# 合照/约会照片
look_at(file_path="{用户提供的路径}", goal="这是一张照片。请描述：1.场景和地点 2.活动内容 3.可辨认的时间线索（季节、节日等）4.照片中的物品或食物 5.整体氛围")

# 转账/红包截图
look_at(file_path="{用户提供的路径}", goal="这是一张转账/红包截图。请提取：1.金额 2.转账备注/留言 3.时间 4.发送方和接收方")

# 备忘录/便签截图
look_at(file_path="{用户提供的路径}", goal="这是一张备忘录/便签截图。请提取：1.完整文字内容 2.是否包含计划/愿望/承诺 3.时间相关信息")
```

**场景 2：用户提供图片目录（批量导入）**

```bash
# Step 1: 扫描目录，获取所有图片文件列表
python3 ${SKILL_DIR}/tools/image_scanner.py \
  --dir "{用户提供的目录}" \
  --output /tmp/partner_images.json
```

```
# Step 2: 对扫描结果中的每张图片，调用 look_at 解读
# （并行处理多张，每张用合适的 goal）
look_at(file_path="{image_path}", goal="分析这张图片，提取所有与恋爱关系相关的信息：对话内容、情绪、承诺、地点、时间、口头禅、喜好等")
```

```bash
# Step 3: 将提取的文本保存到 raw_materials/
# 用 Write 工具写入 ~/.local/share/current-partner/raw_materials/screenshot_{序号}.txt
```

**场景 3：用户直接粘贴/拖入图片**

如果用户在对话中直接发送图片，用 `look_at` 的 `image_data` 参数（base64）或 `Read` 工具直接处理。

**图片解读后的处理流程：**

1. `look_at` 返回图片描述文本
2. 将描述文本保存到 `~/.local/share/current-partner/raw_materials/screenshot_{序号}.txt`
3. 按 `prompts/analysis_guide.md` 的 6 个维度分析文本内容
4. 将结构化信息存入 RAG 库对应分类（调用 `rag_store.py --action add`）
5. 展示提取摘要，让用户确认或补充

### Step 3：解析原材料 → 构建 RAG 知识库

将所有原材料按以下维度分析并存入本地 RAG 库：

**A. 关系档案（Profile）**
```bash
python3 ${SKILL_DIR}/tools/rag_store.py \
  --action init \
  --data-dir ~/.local/share/current-partner
```

**B. 时间线事件（Timeline）** — 关键时间节点
```bash
python3 ${SKILL_DIR}/tools/rag_store.py \
  --action add \
  --category timeline \
  --data '{"date": "2024-06-15", "event": "在一起", "detail": "..."}' \
  --data-dir ~/.local/share/current-partner
```

**C. 承诺追踪（Promises）** — ta的承诺 + 我的承诺
```bash
python3 ${SKILL_DIR}/tools/promise_tracker.py \
  --action add \
  --who "ta" \
  --content "说好今年带我去日本" \
  --date "2024-08-01" \
  --status pending \
  --data-dir ~/.local/share/current-partner
```

**D. 语言模式（Language Patterns）** — 常用语句 + 期望回复
```bash
python3 ${SKILL_DIR}/tools/rag_store.py \
  --action add \
  --category language_patterns \
  --data '{"type": "catchphrase", "text": "你说呢", "context": "反问时常用"}' \
  --data-dir ~/.local/share/current-partner
```

**E. 情感模式（Emotional Patterns）** — 生气/开心/难过时的表现和应对
```bash
python3 ${SKILL_DIR}/tools/rag_store.py \
  --action add \
  --category emotional_patterns \
  --data '{"emotion": "angry", "signs": ["已读不回", "说话变简短"], "best_response": "先给空间，过一会儿买杯奶茶"}' \
  --data-dir ~/.local/share/current-partner
```

### Step 4：预览 & 确认

向用户展示 RAG 库摘要：

```
📊 知识库初始化完成！

关系档案：
  - 称呼：{name}
  - 在一起：{duration}
  - MBTI/星座：{mbti} {zodiac}

已录入：
  - 📅 时间线事件：{N} 条
  - 🤝 承诺追踪：{N} 条（ta承诺 {X} / 我承诺 {Y}）
  - 🗣️ 语言模式：{N} 条（口头禅 {X} / 期望回复 {Y}）
  - 💡 情感模式：{N} 条

状态：就绪 ✅
用 /partner-lookup 查询，/partner-update 追加。
```

---

## 主流程二：查询（`/partner-lookup`）

### 工作原理

1. 用户输入查询（如"ta的生日是什么时候"、"ta喜欢什么花"）
2. 对 RAG 库进行检索：

```bash
python3 ${SKILL_DIR}/tools/rag_store.py \
  --action search \
  --query "生日" \
  --data-dir ~/.local/share/current-partner
```

3. 返回相关记录，整理后回复用户

### 快捷查询

| 命令 | 功能 |
|------|------|
| `/partner-lookup {关键词}` | 通用查询 |
| `/partner-promises` | 列出所有承诺及状态 |
| `/partner-timeline` | 展示完整时间线 |
| `/partner-reply {场景}` | 查询ta在该场景下的期望回复方式 |

---

## 主流程三：增量更新（`/partner-update`）

1. 用户提供新素材（聊天记录/截图/口述）
2. 解析新内容
3. **增量合并**到现有 RAG 库（不覆盖旧数据）：

```bash
python3 ${SKILL_DIR}/tools/rag_store.py \
  --action merge \
  --input /tmp/new_data.json \
  --mode incremental \
  --data-dir ~/.local/share/current-partner
```

4. 自动备份当前版本后合并
5. 展示新增内容摘要

---

## 主流程四：全量重建（`/partner-rebuild`）

⚠️ 高危操作，需二次确认。

1. 备份现有数据
2. 清空 RAG 库
3. 重新走一遍初始化流程
4. 重新导入所有素材

```bash
# 自动备份
python3 ${SKILL_DIR}/tools/version_manager.py \
  --action backup --data-dir ~/.local/share/current-partner

# 全量重建
python3 ${SKILL_DIR}/tools/rag_store.py \
  --action rebuild \
  --data-dir ~/.local/share/current-partner
```

---

## 主流程五：对话模拟（`/partner`）

加载 RAG 库中的 persona + language patterns + emotional patterns，模拟对象的说话方式。

### 运行规则

1. 从 RAG 库加载对象的语言模式、性格画像、情感模式
2. 按 Layer 结构处理：

```
Layer 0：硬规则
  - 你是{name}，不是 AI
  - 基于 RAG 库中的真实记录回复
  - 不说 ta 从未说过的话（除非有素材支持）
  - 保持 ta 的真实性格，包括缺点

Layer 1：身份锚定
  - 从 RAG 库 profile 分类加载

Layer 2：说话风格
  - 从 RAG 库 language_patterns 分类加载

Layer 3：情感模式
  - 从 RAG 库 emotional_patterns 分类加载

Layer 4：关系行为
  - 从 RAG 库 timeline + promises 分类加载上下文
```

### 加载数据

```bash
python3 ${SKILL_DIR}/tools/rag_store.py \
  --action export \
  --category profile,language_patterns,emotional_patterns \
  --data-dir ~/.local/share/current-partner
```

---

## 管理命令

### `/partner-status` — 查看知识库状态

```bash
python3 ${SKILL_DIR}/tools/rag_store.py \
  --action status \
  --data-dir ~/.local/share/current-partner
```

### `/partner-backup` — 手动备份

```bash
python3 ${SKILL_DIR}/tools/version_manager.py \
  --action backup --data-dir ~/.local/share/current-partner
```

### `/partner-export` — 导出知识库

```bash
python3 ${SKILL_DIR}/tools/rag_store.py \
  --action export --all \
  --output ~/Desktop/partner_export.json \
  --data-dir ~/.local/share/current-partner
```

---

## 主流程六：Web 可视化管理（`/partner-ui`）

启动本地 HTTP 服务，在浏览器中可视化管理知识库。

### 启动服务

```bash
python3 ${SKILL_DIR}/tools/web_server.py \
  --data-dir ~/.local/share/current-partner \
  --port 8765
```

服务启动后自动打开浏览器访问 `http://127.0.0.1:8765`。

### Web UI 功能

| Tab | 功能 |
|-----|------|
| 💕 档案 | 编辑基础档案（称呼、生日、MBTI、爱好、标签等） |
| 📅 时间线 | 可视化时间轴，添加/编辑/删除事件 |
| 🤝 承诺 | 按状态分组展示承诺，支持状态切换 |
| 🗣️ 语言 | 口头禅、期望回复方式、发消息风格管理 |
| 💡 情感 | 情感模式管理（触发因素、表现特征、应对方式） |
| 💬 回复顾问 | 粘贴对话内容，AI 分析推荐回复 + 避雷回复 |

### 回复顾问功能

1. 粘贴聊天记录或描述场景
2. AI 基于知识库分析：
   - ✅ 推荐回复方式
   - ❌ 避雷回复方式
   - 💡 原因分析
3. 可一键存入知识库

### 技术特点

- **零外部依赖**：仅使用 Python 3 标准库
- **纯本地运行**：数据不上传，隐私安全
- **实时同步**：Web 操作直接写入 JSONL 文件
- **甜蜜风格**：粉色主题，温暖美观

---

## RAG 知识库结构

```
~/.local/share/current-partner/
├── profile.json            # 基础档案
├── timeline.jsonl           # 时间线事件（按时间排序）
├── promises.jsonl           # 承诺追踪
├── language_patterns.jsonl  # 语言模式（口头禅、期望回复）
├── emotional_patterns.jsonl # 情感模式
├── raw_materials/           # 原始素材的文本提取结果
│   ├── wechat_001.txt
│   ├── qq_001.txt
│   └── screenshot_001.txt
├── index.json               # 全文索引（TF-IDF 权重）
├── meta.json                # 元数据
└── backups/                 # 版本备份
    ├── v1_20240615_120000/
    └── v2_20240801_153000/
```

---

## 数据分类说明

### profile — 基础档案
```json
{
  "name": "宝宝",
  "real_name": "",
  "gender": "",
  "birthday": "1999-03-20",
  "zodiac": "双鱼座",
  "mbti": "INFJ",
  "occupation": "前端工程师",
  "city": "上海",
  "together_since": "2024-06-15",
  "how_met": "大学同学",
  "hobbies": ["看电影", "烘焙", "撸猫"],
  "food_preferences": {"loves": ["火锅", "奶茶"], "hates": ["香菜"]},
  "tags": ["外冷内热", "嘴硬心软", "猫奴"]
}
```

### timeline — 时间线事件
```jsonl
{"id": "t001", "date": "2024-05-01", "event": "第一次见面", "detail": "在学校图书馆偶遇", "emotion": "positive", "tags": ["first_meet"]}
{"id": "t002", "date": "2024-06-15", "event": "正式在一起", "detail": "在外滩表白", "emotion": "positive", "tags": ["anniversary"]}
```

### promises — 承诺追踪
```jsonl
{"id": "p001", "who": "ta", "content": "说好今年带我去日本", "date": "2024-08-01", "deadline": "2024-12-31", "status": "pending", "context": "吃日料时说的"}
{"id": "p002", "who": "me", "content": "学会做红烧肉", "date": "2024-07-15", "deadline": "", "status": "completed", "context": "ta生日时答应的"}
```

### language_patterns — 语言模式
```jsonl
{"id": "l001", "type": "catchphrase", "text": "你说呢", "context": "反问时常用", "frequency": "high"}
{"id": "l002", "type": "catchphrase", "text": "随便吧", "context": "生气时挂嘴边", "frequency": "high"}
{"id": "l003", "type": "expected_reply", "scenario": "ta说'我今天好累'", "good_reply": "辛苦了宝宝，想吃什么我给你点", "bad_reply": "我也累", "note": "ta需要被关心而不是比惨"}
{"id": "l004", "type": "expected_reply", "scenario": "ta发了自拍", "good_reply": "好好看！！！这个角度绝了", "bad_reply": "嗯/还行", "note": "必须夸，而且要具体"}
{"id": "l005", "type": "texting_style", "text": "消息短句连发，不打句号，爱用省略号", "example": "嗯...\n好吧\n那你忙吧"}
```

### emotional_patterns — 情感模式
```jsonl
{"id": "e001", "emotion": "angry", "triggers": ["已读不回超过1小时", "和异性走太近"], "signs": ["说话变短", "用'哦'和'好的'", "不发表情"], "best_response": "先认错，不要讲道理，买杯奶茶", "worst_response": "讲道理/冷处理/说'你无理取闹'", "cool_down_time": "2-3小时"}
{"id": "e002", "emotion": "sad", "triggers": ["工作不顺", "和家人吵架"], "signs": ["突然安静", "发'没事'但明显有事"], "best_response": "不追问，陪在身边，点ta爱吃的外卖", "worst_response": "追问到底/说'想开点'"}
```

---

## 注意事项

- 所有脚本仅依赖 Python 3 标准库（json, re, os, datetime, math, collections）
- 数据纯本地存储，零网络请求
- 图片/截图仅提取文字描述后保存为文本，不存储原始图片文件
- 支持多次增量更新，每次自动备份
- 全量重建前会自动备份历史版本
