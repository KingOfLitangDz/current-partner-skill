#!/usr/bin/env python3
"""现任.skill 本地 RAG 知识库

纯 Python 标准库实现，零外部依赖。
基于 TF-IDF 的文本检索 + JSONL 存储。

支持操作：
  init     — 初始化知识库
  add      — 添加记录
  search   — 搜索记录
  merge    — 增量合并
  rebuild  — 全量重建
  export   — 导出数据
  status   — 查看状态
  delete   — 删除记录

Usage:
    python3 rag_store.py --action init --data-dir <path>
    python3 rag_store.py --action add --category <cat> --data '<json>' --data-dir <path>
    python3 rag_store.py --action search --query <text> [--category <cat>] --data-dir <path>
    python3 rag_store.py --action merge --input <file> --mode incremental --data-dir <path>
    python3 rag_store.py --action rebuild --data-dir <path>
    python3 rag_store.py --action export [--category <cats>] [--all] [--output <file>] --data-dir <path>
    python3 rag_store.py --action status --data-dir <path>
    python3 rag_store.py --action delete --category <cat> --id <record_id> --data-dir <path>
"""

import argparse
import json
import os
import sys
import re
import math
from datetime import datetime
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

# ── 常量 ──────────────────────────────────────────────

CATEGORIES = [
    "profile",
    "timeline",
    "promises",
    "language_patterns",
    "emotional_patterns",
]

STOP_WORDS = set(
    "的 了 是 在 我 有 和 就 不 人 都 一 一个 上 也 很 到 说 要 去 你 会 着 没有 看 好 "
    "自己 这 他 她 它 们 那 里 后 吗 被 从 把 什么 时候 没 还 又 为 可以 做 让 用 吧 呢 "
    "嗯 哦 哈 啊 呀 噢 嘿 唉 嘛 么 了 啦 呗 哇".split()
)


# ── 工具函数 ──────────────────────────────────────────

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def load_jsonl(filepath: str) -> list:
    """加载 JSONL 文件"""
    if not os.path.exists(filepath):
        return []
    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def save_jsonl(filepath: str, records: list):
    """保存为 JSONL 文件"""
    ensure_dir(os.path.dirname(filepath) or ".")
    with open(filepath, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def load_json(filepath: str) -> dict:
    """加载 JSON 文件"""
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath: str, data: dict):
    """保存 JSON 文件"""
    ensure_dir(os.path.dirname(filepath) or ".")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def gen_id(prefix: str, existing_ids: set) -> str:
    """生成递增 ID"""
    n = 1
    while True:
        new_id = f"{prefix}{n:03d}"
        if new_id not in existing_ids:
            return new_id
        n += 1


def tokenize(text: str) -> list:
    """简易中英文分词"""
    # 英文按空格/标点拆分
    # 中文按单字拆分（简易 unigram）
    tokens = []
    # 提取英文单词
    eng_words = re.findall(r"[a-zA-Z]+", text.lower())
    tokens.extend(eng_words)
    # 提取中文字符，按 bigram
    cn_chars = re.findall(r"[\u4e00-\u9fff]", text)
    for i in range(len(cn_chars)):
        tokens.append(cn_chars[i])
        if i + 1 < len(cn_chars):
            tokens.append(cn_chars[i] + cn_chars[i + 1])
    # 过滤停用词
    tokens = [t for t in tokens if t not in STOP_WORDS and len(t) > 0]
    return tokens


def record_to_text(record: dict) -> str:
    """将记录转为可检索的纯文本"""
    parts = []
    for key, val in record.items():
        if key == "id":
            continue
        if isinstance(val, str):
            parts.append(val)
        elif isinstance(val, list):
            parts.append(" ".join(str(v) for v in val))
        elif isinstance(val, dict):
            parts.append(" ".join(str(v) for v in val.values()))
    return " ".join(parts)


# ── TF-IDF 检索引擎 ──────────────────────────────────

class TFIDFIndex:
    """轻量级 TF-IDF 检索"""

    def __init__(self):
        self.documents = []  # [(doc_id, category, text)]
        self.df = Counter()  # document frequency
        self.doc_tf = {}     # {doc_idx: Counter(token -> freq)}

    def add_document(self, doc_id: str, category: str, text: str):
        idx = len(self.documents)
        self.documents.append((doc_id, category, text))
        tokens = tokenize(text)
        tf = Counter(tokens)
        self.doc_tf[idx] = tf
        for token in set(tokens):
            self.df[token] += 1

    def search(self, query: str, category: Optional[str] = None, top_k: int = 10) -> list:
        """返回 [(doc_id, category, score, text), ...]"""
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        n_docs = len(self.documents)
        if n_docs == 0:
            return []

        scores = []
        for idx, (doc_id, cat, text) in enumerate(self.documents):
            if category and cat != category:
                continue
            tf = self.doc_tf.get(idx, Counter())
            score = 0.0
            for token in query_tokens:
                if token in tf:
                    tf_val = tf[token] / max(sum(tf.values()), 1)
                    idf_val = math.log((n_docs + 1) / (self.df.get(token, 0) + 1)) + 1
                    score += tf_val * idf_val
            if score > 0:
                scores.append((doc_id, cat, score, text))

        scores.sort(key=lambda x: -x[2])
        return scores[:top_k]

    def rebuild_from_store(self, data_dir: str):
        """从存储文件重建索引"""
        self.documents = []
        self.df = Counter()
        self.doc_tf = {}

        for cat in CATEGORIES:
            if cat == "profile":
                profile = load_json(os.path.join(data_dir, "profile.json"))
                if profile:
                    text = record_to_text(profile)
                    self.add_document("profile", "profile", text)
            else:
                filepath = os.path.join(data_dir, f"{cat}.jsonl")
                records = load_jsonl(filepath)
                for rec in records:
                    doc_id = rec.get("id", "unknown")
                    text = record_to_text(rec)
                    self.add_document(doc_id, cat, text)

    def save_index(self, data_dir: str):
        """保存索引元数据"""
        index_data = {
            "doc_count": len(self.documents),
            "vocab_size": len(self.df),
            "updated_at": datetime.now().isoformat(),
        }
        save_json(os.path.join(data_dir, "index.json"), index_data)


# ── 核心操作 ──────────────────────────────────────────

def action_init(data_dir: str):
    """初始化知识库"""
    ensure_dir(data_dir)
    ensure_dir(os.path.join(data_dir, "raw_materials"))
    ensure_dir(os.path.join(data_dir, "backups"))

    # 初始化空文件
    profile_path = os.path.join(data_dir, "profile.json")
    if not os.path.exists(profile_path):
        save_json(profile_path, {
            "name": "",
            "real_name": "",
            "gender": "",
            "birthday": "",
            "zodiac": "",
            "mbti": "",
            "occupation": "",
            "city": "",
            "together_since": "",
            "how_met": "",
            "hobbies": [],
            "food_preferences": {"loves": [], "hates": []},
            "tags": [],
        })

    for cat in CATEGORIES:
        if cat == "profile":
            continue
        filepath = os.path.join(data_dir, f"{cat}.jsonl")
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                pass  # 创建空文件

    # 初始化 meta
    meta_path = os.path.join(data_dir, "meta.json")
    if not os.path.exists(meta_path):
        save_json(meta_path, {
            "version": "v1",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "total_records": 0,
            "categories": {cat: 0 for cat in CATEGORIES},
        })

    # 建立空索引
    idx = TFIDFIndex()
    idx.save_index(data_dir)

    print(f"✅ 知识库已初始化：{data_dir}")


def action_add(data_dir: str, category: str, data_str: str):
    """添加记录"""
    if category not in CATEGORIES:
        print(f"❌ 无效分类：{category}，可选：{', '.join(CATEGORIES)}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(data_str)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败：{e}", file=sys.stderr)
        sys.exit(1)

    if category == "profile":
        # Profile 是单个 JSON，merge 更新
        profile_path = os.path.join(data_dir, "profile.json")
        profile = load_json(profile_path)
        profile.update(data)
        save_json(profile_path, profile)
        print(f"✅ 已更新 profile")
    else:
        # 其他分类是 JSONL，追加
        filepath = os.path.join(data_dir, f"{category}.jsonl")
        records = load_jsonl(filepath)
        existing_ids = {r.get("id", "") for r in records}

        # 自动生成 ID
        prefix_map = {
            "timeline": "t",
            "promises": "p",
            "language_patterns": "l",
            "emotional_patterns": "e",
        }
        if "id" not in data:
            data["id"] = gen_id(prefix_map.get(category, "x"), existing_ids)

        # 添加元数据
        data["_added_at"] = datetime.now().isoformat()

        records.append(data)
        save_jsonl(filepath, records)
        print(f"✅ 已添加到 {category}：{data['id']}")

    # 更新 meta
    _update_meta(data_dir)
    # 重建索引
    _rebuild_index(data_dir)


def action_search(data_dir: str, query: str, category: Optional[str] = None, top_k: int = 10):
    """搜索记录"""
    idx = TFIDFIndex()
    idx.rebuild_from_store(data_dir)

    results = idx.search(query, category=category, top_k=top_k)

    if not results:
        print("🔍 未找到匹配记录。")
        return

    print(f"🔍 找到 {len(results)} 条匹配记录：\n")
    for doc_id, cat, score, text in results:
        # 加载原始记录
        if cat == "profile":
            record = load_json(os.path.join(data_dir, "profile.json"))
        else:
            records = load_jsonl(os.path.join(data_dir, f"{cat}.jsonl"))
            record = next((r for r in records if r.get("id") == doc_id), {"text": text})

        print(f"[{cat}] {doc_id} (相关度: {score:.2f})")
        print(f"  {json.dumps(record, ensure_ascii=False)}")
        print()


def action_merge(data_dir: str, input_file: str, mode: str = "incremental"):
    """合并数据"""
    if not os.path.exists(input_file):
        print(f"❌ 文件不存在：{input_file}", file=sys.stderr)
        sys.exit(1)

    with open(input_file, "r", encoding="utf-8") as f:
        new_data = json.load(f)

    added_count = 0

    for category, records in new_data.items():
        if category not in CATEGORIES:
            continue

        if category == "profile":
            profile_path = os.path.join(data_dir, "profile.json")
            profile = load_json(profile_path)
            if isinstance(records, dict):
                profile.update(records)
                save_json(profile_path, profile)
                added_count += 1
        else:
            if not isinstance(records, list):
                continue
            filepath = os.path.join(data_dir, f"{category}.jsonl")
            existing = load_jsonl(filepath)
            existing_ids = {r.get("id", "") for r in existing}

            prefix_map = {
                "timeline": "t",
                "promises": "p",
                "language_patterns": "l",
                "emotional_patterns": "e",
            }

            for rec in records:
                rec_id = rec.get("id", "")
                if mode == "incremental" and rec_id in existing_ids:
                    # 增量模式跳过已有记录
                    continue
                if "id" not in rec or not rec["id"]:
                    rec["id"] = gen_id(prefix_map.get(category, "x"), existing_ids)
                    existing_ids.add(rec["id"])
                rec["_added_at"] = datetime.now().isoformat()
                existing.append(rec)
                added_count += 1

            save_jsonl(filepath, existing)

    _update_meta(data_dir)
    _rebuild_index(data_dir)
    print(f"✅ 合并完成：新增 {added_count} 条记录（模式：{mode}）")


def action_rebuild(data_dir: str):
    """全量重建（清空后重新初始化）"""
    # 清空数据文件（保留目录结构）
    for cat in CATEGORIES:
        if cat == "profile":
            save_json(os.path.join(data_dir, "profile.json"), {})
        else:
            filepath = os.path.join(data_dir, f"{cat}.jsonl")
            with open(filepath, "w", encoding="utf-8") as f:
                pass

    _update_meta(data_dir)
    _rebuild_index(data_dir)
    print("✅ 知识库已清空，可以重新导入数据。")


def action_export(data_dir: str, categories: Optional[str] = None,
                  export_all: bool = False, output: Optional[str] = None):
    """导出数据"""
    cats = CATEGORIES if export_all else (categories.split(",") if categories else CATEGORIES)

    result = {}
    for cat in cats:
        cat = cat.strip()
        if cat not in CATEGORIES:
            continue
        if cat == "profile":
            result["profile"] = load_json(os.path.join(data_dir, "profile.json"))
        else:
            result[cat] = load_jsonl(os.path.join(data_dir, f"{cat}.jsonl"))

    output_text = json.dumps(result, ensure_ascii=False, indent=2)

    if output:
        ensure_dir(os.path.dirname(output) or ".")
        with open(output, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"✅ 已导出到 {output}")
    else:
        print(output_text)


def action_status(data_dir: str):
    """查看知识库状态"""
    meta = load_json(os.path.join(data_dir, "meta.json"))
    profile = load_json(os.path.join(data_dir, "profile.json"))

    print("📊 现任知识库状态")
    print("=" * 40)

    if profile.get("name"):
        print(f"  对象称呼：{profile['name']}")
    if profile.get("together_since"):
        print(f"  在一起：{profile['together_since']}")
    if profile.get("mbti"):
        print(f"  MBTI：{profile['mbti']}")
    if profile.get("zodiac"):
        print(f"  星座：{profile['zodiac']}")

    print()

    total = 0
    for cat in CATEGORIES:
        if cat == "profile":
            count = 1 if profile.get("name") else 0
        else:
            filepath = os.path.join(data_dir, f"{cat}.jsonl")
            count = len(load_jsonl(filepath))
        total += count

        label_map = {
            "profile": "📋 基础档案",
            "timeline": "📅 时间线事件",
            "promises": "🤝 承诺追踪",
            "language_patterns": "🗣️ 语言模式",
            "emotional_patterns": "💡 情感模式",
        }
        print(f"  {label_map.get(cat, cat)}：{count} 条")

    print(f"\n  📦 总记录数：{total}")
    print(f"  📁 数据目录：{data_dir}")
    print(f"  🕐 最后更新：{meta.get('updated_at', '未知')}")
    print(f"  📌 版本：{meta.get('version', 'v1')}")

    # 备份信息
    backup_dir = os.path.join(data_dir, "backups")
    if os.path.exists(backup_dir):
        backups = sorted(os.listdir(backup_dir))
        print(f"  💾 历史备份：{len(backups)} 个")


def action_delete(data_dir: str, category: str, record_id: str):
    """删除指定记录"""
    if category == "profile":
        print("❌ 不能删除 profile，请使用 add 覆盖更新", file=sys.stderr)
        sys.exit(1)

    filepath = os.path.join(data_dir, f"{category}.jsonl")
    records = load_jsonl(filepath)
    new_records = [r for r in records if r.get("id") != record_id]

    if len(new_records) == len(records):
        print(f"❌ 未找到记录：{record_id}", file=sys.stderr)
        sys.exit(1)

    save_jsonl(filepath, new_records)
    _update_meta(data_dir)
    _rebuild_index(data_dir)
    print(f"✅ 已删除 {category} 中的记录：{record_id}")


# ── 内部方法 ──────────────────────────────────────────

def _update_meta(data_dir: str):
    """更新元数据"""
    meta_path = os.path.join(data_dir, "meta.json")
    meta = load_json(meta_path)
    meta["updated_at"] = datetime.now().isoformat()

    total = 0
    for cat in CATEGORIES:
        if cat == "profile":
            profile = load_json(os.path.join(data_dir, "profile.json"))
            count = 1 if profile.get("name") else 0
        else:
            count = len(load_jsonl(os.path.join(data_dir, f"{cat}.jsonl")))
        meta.setdefault("categories", {})[cat] = count
        total += count

    meta["total_records"] = total

    # 递增版本号
    current_v = meta.get("version", "v1")
    v_num = int(re.search(r"\d+", current_v).group()) if re.search(r"\d+", current_v) else 1
    meta["version"] = f"v{v_num}"

    save_json(meta_path, meta)


def _rebuild_index(data_dir: str):
    """重建 TF-IDF 索引"""
    idx = TFIDFIndex()
    idx.rebuild_from_store(data_dir)
    idx.save_index(data_dir)


# ── CLI ───────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="现任.skill 本地 RAG 知识库")
    parser.add_argument("--action", required=True,
                        choices=["init", "add", "search", "merge", "rebuild",
                                 "export", "status", "delete"])
    parser.add_argument("--data-dir", required=True, help="数据目录路径")
    parser.add_argument("--category", help="数据分类")
    parser.add_argument("--data", help="JSON 格式的数据")
    parser.add_argument("--query", help="搜索关键词")
    parser.add_argument("--input", help="合并的输入文件")
    parser.add_argument("--mode", default="incremental", choices=["incremental", "full"],
                        help="合并模式")
    parser.add_argument("--id", help="记录 ID（删除用）")
    parser.add_argument("--output", help="导出输出路径")
    parser.add_argument("--all", action="store_true", help="导出全部分类")
    parser.add_argument("--top-k", type=int, default=10, help="搜索返回数量")

    args = parser.parse_args()

    if args.action == "init":
        action_init(args.data_dir)
    elif args.action == "add":
        if not args.category or not args.data:
            print("❌ add 需要 --category 和 --data 参数", file=sys.stderr)
            sys.exit(1)
        action_add(args.data_dir, args.category, args.data)
    elif args.action == "search":
        if not args.query:
            print("❌ search 需要 --query 参数", file=sys.stderr)
            sys.exit(1)
        action_search(args.data_dir, args.query, category=args.category, top_k=args.top_k)
    elif args.action == "merge":
        if not args.input:
            print("❌ merge 需要 --input 参数", file=sys.stderr)
            sys.exit(1)
        action_merge(args.data_dir, args.input, mode=args.mode)
    elif args.action == "rebuild":
        action_rebuild(args.data_dir)
    elif args.action == "export":
        action_export(args.data_dir, categories=args.category,
                      export_all=args.all, output=args.output)
    elif args.action == "status":
        action_status(args.data_dir)
    elif args.action == "delete":
        if not args.category or not args.id:
            print("❌ delete 需要 --category 和 --id 参数", file=sys.stderr)
            sys.exit(1)
        action_delete(args.data_dir, args.category, args.id)


if __name__ == "__main__":
    main()
