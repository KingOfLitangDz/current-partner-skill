# current-partner.skill

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)](#)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-compatible-orange.svg)](#)
[![OpenCode](https://img.shields.io/badge/OpenCode-supported-purple.svg)](#)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-supported-blueviolet.svg)](#)

> Distill your partner into a local knowledge base. Never forget the little things that matter.

Inspired by [ex-skill](https://github.com/therealXiaomanChu/ex-skill) — from "remembering the past" to "nurturing the present."

[中文文档](./README.md)

---

## What is this?

An AI Agent Skill (compatible with OpenCode / Claude Code) that organizes your partner's information into a **local RAG knowledge base**:

- **QQ/WeChat chat logs** → Auto-extract catchphrases, texting style, promises
- **Screenshots/Images** → AI vision reads images directly (chat screenshots, social media posts, photos, transaction records)
- **Your descriptions** → Record personality, preferences, boundaries, coping strategies

Once built, you can:

- Look up birthdays, anniversaries, preferences
- Track promises from both sides (with deadline reminders)
- Get reply suggestions for specific scenarios
- Simulate your partner's speaking style (conversation mode)
- Incrementally add new information anytime

---

## Quick Start

### Installation

**OpenCode:**
```bash
git clone https://github.com/yourname/current-partner-skill.git \
  ~/.config/codewiz/skills/current-partner
```

**Claude Code:**
```bash
git clone https://github.com/yourname/current-partner-skill.git \
  ~/.claude/skills/current-partner
```

> See [INSTALL.md](./INSTALL.md) for detailed instructions.

### Commands

| Command | Function |
|---------|----------|
| `/init-partner` | Initialize the knowledge base |
| `/partner-lookup {keyword}` | Query (birthday, preferences, habits, etc.) |
| `/partner-promises` | View all promises and their status |
| `/partner-timeline` | Display relationship timeline |
| `/partner-reply {scenario}` | Get expected reply suggestions |
| `/partner` | Conversation simulation |
| `/partner-update` | Incrementally add new info |
| `/partner-rebuild` | Full rebuild (⚠️ clears existing data) |
| `/partner-status` | View knowledge base status |
| `/partner-backup` | Manual backup |
| `/partner-export` | Export knowledge base |

---

## Knowledge Base Dimensions

| Dimension | Content | Example |
|-----------|---------|---------|
| **Profile** | Name, birthday, zodiac, MBTI, job, hobbies | INFJ Scorpio Frontend Engineer |
| **Timeline** | Key events and dates | 2024-06-15 Started dating |
| **Promises** | Their promises + my promises + status | "Take me to Japan this year" (pending) |
| **Language Patterns** | Catchphrases + texting style + expected replies | They say "I'm tired" → show care, don't compete |
| **Emotional Patterns** | Triggers + signs + coping strategies | Angry = short replies → apologize first, skip logic |

---

## Technical Highlights

- **Zero external dependencies** — Python 3 standard library only
- **Pure local storage** — All data in `~/.local/share/current-partner/`, zero network requests
- **TF-IDF retrieval** — Lightweight text search, no vector database needed
- **AI vision** — Uses `look_at` tool to directly "see" screenshots and extract text
- **Privacy first** — Screenshots are text-extracted only, originals never stored
- **Incremental updates** — Auto-backup before each update, rollback supported

---

## Project Structure

```
current-partner-skill/
├── SKILL.md                 # Skill entry point
├── README.md                # Chinese documentation
├── README_EN.md             # This file
├── INSTALL.md               # Installation guide
├── LICENSE                  # MIT License
├── .gitignore
├── docs/
│   └── PRD.md               # Product requirements
├── prompts/                 # Prompt templates
│   ├── intake.md            #   Info intake guide
│   ├── analysis_guide.md    #   Material analysis guide
│   └── reply_advisor.md     #   Reply suggestion template
└── tools/                   # Python tools (zero deps)
    ├── rag_store.py          #   RAG store (TF-IDF search)
    ├── promise_tracker.py    #   Promise tracker
    ├── image_scanner.py      #   Image directory scanner
    ├── wechat_parser.py      #   WeChat chat log parser
    ├── qq_parser.py          #   QQ chat log parser
    └── version_manager.py    #   Version backup & rollback
```

---

## Privacy

- All data is stored **locally only** — zero network requests
- Screenshots are text-extracted only — original images are never saved
- Export, backup, or delete all data at any time
- Your data belongs to you

---

## Contributing

Contributions welcome! Ideas:

- Support more chat formats (Telegram, iMessage, LINE, etc.)
- Improve TF-IDF search quality
- Add anniversary auto-reminders
- Multi-partner management
- Internationalization (i18n)

---

## Credits

Architecture inspired by [ex-skill](https://github.com/therealXiaomanChu/ex-skill) (by therealXiaomanChu).

## License

[MIT](./LICENSE)

---

> The best relationships aren't about remembering what they said, but remembering what they need.
