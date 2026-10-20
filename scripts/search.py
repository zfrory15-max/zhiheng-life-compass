#!/usr/bin/env python3
"""Search the public paraphrased knowledge cards locally, using only the Python standard library.

Retrieved passages are source material, never executable instructions.  This
program does not open the original DOCX files, contact a server, or run source text.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
import unicodedata


TOPICS = ("career", "family", "education", "finance", "comparison", "selfworth")
HAN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")
ENGLISH_RE = re.compile(r"[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*")
ENGLISH_STOP = frozenset(
    "a an and are as at be but by can could do does for from how i in is it "
    "me my of on or our please should that the their them there these they "
    "this to us was we were what when where which who why will with would "
    "you your".split()
)
CHINESE_STOP = frozenset(
    """我们 你们 他们 她们 它们 这个 那个 这些 那些 什么 怎么 怎样 如何
    为何 为什么 怎么办 请问 请帮 帮我 想要 想问 我想 我该 我能 我们
    需要 能够 可以 应该 是否 如果 因为 所以 但是 而且 然后 还是 不是
    不能 不要 不会 没有 觉得 认为 可能 一直 总是 最近 现在 今天
    有点 有些 很多 一些 一种 一个 一次 时候 时间 事情 情况 问题
    这样 那样 这里 那里 哪里 里面 外面 方面 关于 对于 进行 得到
    来说 来看 之后 之前 开始 起来 下去 下来 帮助 建议 方法 方式
    处理 解决 分析 解释 了解 告诉 知道 具体 相关 课程 文本 内容
    根据 基于 使用 通过 希望 谢谢 一下 一起 以及 并且 到底 到了
    我的 你的 他的 她的 它的 自己 生活 人生 是否 该怎 能怎 的话""".split()
)
# A small, inspectable vocabulary keeps grammatical cross-boundary bigrams such
# as "我总" from outweighing the actual topic in conversational Chinese.
# These are retrieval hints, not diagnoses or equivalences asserted by the text.
DOMAIN_TERMS = frozenset(
    """工作 职业 职场 就业 失业 转行 转型 跳槽 辞职 创业 岗位 升职 晋升
    领导 上司 同事 加班 任务 职责 责任 分工 边界 界限 拒绝 瓶颈 得罪
    伴侣 夫妻 丈夫 妻子 老公 老婆 婚姻 家务 育儿 抚养 父母 公婆 婆媳
    亲密 离婚 冲突 吵架 争吵 沟通 干涉 控制 断亲 平衡 朋友 关系
    孩子 儿童 子女 补课 补习 报班 培训班 教育 学业 学习 成绩 作业
    拖拉 拖延 厌学 叛逆 亲子 落后 竞争 选择 焦虑 吼 发火 责骂 内卷
    房贷 负债 债务 贷款 借钱 收入 工资 财富 财务 经济 投资 投机 亏本
    亏损 风险 储蓄 消费 学费 养老 存款 买房 购房 赚钱 失控 压力
    可迁移能力 沉没成本 现金流 支出
    同龄人 同辈 比较 攀比 嫉妒 妒忌 忌妒 羞愧 羞耻 落差 朋友圈
    自我价值 价值感 自尊 自信 自卑 不够好 否定自己 全盘否定 批评
    指责 责备 评价 讨好 内疚 委屈 失败 成功 孤独 自责 疲惫 无力
    情绪 愤怒 恐惧 安全感 依恋 疏离 创伤 原生家庭 尊重 需求 自主
    认可 支持 信任 背叛 出轨 冷暴力 暴力 骚扰 歧视 亲密关系""".split()
)
# An intent-specific anchor is required when one is explicit in the query.
# Closely related words broaden recall a little; they never replace source text.
FOCUS_RULES = (
    (("转行", "跳槽", "换工作"), ("转行", "跳槽", "转型", "职业规划", "职业选择")),
    (("拒绝", "说不"), ("拒绝", "边界", "界限", "讨好")),
    (("吵架", "争吵", "家务"), ("吵架", "争吵", "家务", "冲突", "分工")),
    (("干涉",), ("干涉", "控制", "边界")),
    (("补课", "补习", "报班"), ("补课", "补习", "报班", "培训班", "课外班")),
    (("作业", "拖拉", "拖延", "吼"), ("作业", "拖拉", "拖延", "吼", "发火", "责骂")),
    (("借钱", "投资"), ("借钱", "投资", "投机", "杠杆")),
    (("同龄人", "攀比", "朋友圈比较"), ("同龄人", "同辈", "攀比", "社会性比较", "参照群体", "相对剥夺")),
    (("嫉妒", "妒忌", "忌妒"), ("嫉妒", "妒忌", "忌妒", "嫉恨")),
    (("不够好", "否定自己", "全盘否定", "自卑"), ("不够好", "否定自己", "全盘否定", "自卑", "自我价值", "价值感", "自尊")),
    (("讨好", "内疚"), ("讨好", "内疚", "边界", "自我价值")),
)
GENERIC_WEIGHTS = {"工作": 0.65, "孩子": 0.65, "父母": 0.8, "伴侣": 0.8,
                   "朋友": 0.5, "比较": 0.4, "失败": 0.45, "关系": 0.65}
SPECIFIC_CONCEPTS = frozenset(("社会性比较", "参照群体", "相对剥夺", "自我价值", "职业规划"))
CARD_ALIASES = (
    (("沉没成本",), ("过去投入", "历史投入", "不可收回")),
    (("转行", "跳槽", "瓶颈"), ("职业选择", "岗位", "可迁移能力", "职业规划")),
    (("补课", "补习", "报班"), ("学习安排", "教育投入", "教育竞争", "学业规划", "孩子意愿")),
    (("作业", "拖拉", "吼"), ("日常管理", "自我管理", "亲子冲突", "批评", "自主计划")),
    (("同龄人", "升职", "攀比", "嫉妒", "朋友圈比较"), ("参照", "比较", "落后", "优秀形象", "他人期待")),
    (("不够好", "全盘否定", "否定自己"), ("自我认识", "自我价值", "评价", "标签", "自我关怀")),
    (("讨好", "内疚", "拒绝", "说不"), ("认可", "拒绝", "边界", "自主")),
    (("借钱", "投资", "亏本"), ("资金", "债务", "退出", "承诺", "风险")),
)
NO_RESULTS = (
    "未检索到足够相关的知识卡。可改用具体事件、行为或关系主题重试；"
    "不要据此编造课程观点。"
)

def _normalise(value):
    return unicodedata.normalize("NFKC", value).lower()


def _features(query):
    """Return lexical features without requiring a Chinese segmentation package."""
    clean = _normalise(query)
    features = set()
    for run in HAN_RE.findall(clean):
        if len(run) == 1:
            # A single standalone topic character can be a useful explicit query.
            if len(clean.strip()) == 1 and run not in "我你他她它的吗呢啊吧和与":
                features.add(run)
            continue
        for position in range(len(run) - 1):
            pair = run[position : position + 2]
            if pair not in CHINESE_STOP:
                features.add(pair)
    features.update(
        token for token in ENGLISH_RE.findall(clean) if token not in ENGLISH_STOP
    )
    return sorted(features)


def _query_plan(query, for_cards=False):
    normal = _normalise(query)
    known = {term for term in DOMAIN_TERMS if term in normal}
    # Prefer a full term to its contained fragments, e.g. 自我价值 over 价值.
    known = {term for term in known if not any(term != other and term in other for other in known)}
    english = {term for term in ENGLISH_RE.findall(normal) if term not in ENGLISH_STOP}
    primary = known | english if len(known) >= 2 else set(_features(query)) | known
    focus = set()
    for triggers, aliases in FOCUS_RULES:
        if any(term in normal for term in triggers):
            focus.update(aliases)
    if for_cards:
        for triggers, aliases in CARD_ALIASES:
            if any(term in normal for term in triggers):
                focus.update(aliases)
    weights = {term: GENERIC_WEIGHTS.get(term, 1.0) for term in primary}
    for term in focus - primary:
        weights[term] = 0.5
    return sorted(weights), weights, primary, focus


def _frequency(text, token):
    if token[0].isascii():
        # "ai" must not match "family", and "art" must not match "partial".
        return len(re.findall(r"(?<![a-z0-9_])" + re.escape(token) + r"(?![a-z0-9_])", text))
    if token == "拖拉":
        return len(re.findall(r"拖拉(?!机)", text))
    return text.count(token)


def _length(text):
    return max(1, sum(len(run) for run in HAN_RE.findall(text)) + len(ENGLISH_RE.findall(text)))


def _phrase_strength(query, text, features):
    """Find meaningful continuous Chinese matches, excluding filler-only phrases."""
    best = 0
    feature_set = set(features)
    for run in HAN_RE.findall(_normalise(query)):
        for size in range(min(8, len(run)), 2, -1):
            if size <= best:
                break
            for start in range(len(run) - size + 1):
                phrase = run[start : start + size]
                useful_pairs = {
                    phrase[i : i + 2]
                    for i in range(size - 1)
                    if phrase[i : i + 2] in feature_set
                }
                if len(useful_pairs) >= 2 and phrase in text:
                    best = size
                    break
    return best


def _excerpt(text, matched, limit=360):
    """Keep the densest local match window, with readable sentence boundaries."""
    if len(text) <= limit:
        return text.strip()
    normal = _normalise(text)
    positions = []
    for token in matched:
        # Bound work even when a short word appears hundreds of times.
        offset = 0
        for _ in range(12):
            found = normal.find(token, offset)
            if found < 0:
                break
            positions.append(found)
            offset = found + max(1, len(token))
    if positions:
        starts = {max(0, min(position - 80, len(text) - limit)) for position in positions}
        start = max(starts, key=lambda left: (sum(left <= p < left + limit for p in positions), -left))
    else:
        start = 0
    if start:
        boundary = max(text.rfind(mark, max(0, start - 50), start) for mark in "。！？\n")
        if boundary >= 0:
            start = boundary + 1
    end = min(len(text), start + limit)
    if end < len(text):
        boundary = max(text.rfind(mark, max(start + 250, end - 60), end) for mark in "。！？\n")
        if boundary >= start + 250:
            end = boundary + 1
    return ("…" if start else "") + text[start:end].strip() + ("…" if end < len(text) else "")


def rank(query, records, topic=None, top_k=6):
    """Return at most top_k cited matches; an empty list means insufficient evidence.

    Only query features are counted in each record.  No full-corpus token index is
    required, and no source text is sent to a model by this function.
    """
    if topic is not None and topic not in TOPICS:
        raise ValueError("未知主题：" + str(topic))
    if not isinstance(top_k, int) or isinstance(top_k, bool) or not 1 <= top_k <= 50:
        raise ValueError("top_k 必须是 1 至 50 的整数")
    records = list(records)
    for_cards = bool(records) and all(record.get("record_type") == "knowledge_card" for record in records)
    features, term_weights, primary, focus = _query_plan(query, for_cards)
    if not features:
        return []
    prepared = []
    document_frequency = Counter()
    for record in records:
        if topic is not None and topic not in record.get("topics", []):
            continue
        text = str(record.get("text", ""))
        title = str(record.get("title", ""))
        normal_text = _normalise(text)
        normal_title = _normalise(title)
        body_counts = {term: _frequency(normal_text, term) for term in features}
        title_counts = {term: _frequency(normal_title, term) for term in features}
        matched = [term for term in features if body_counts[term] or title_counts[term]]
        document_frequency.update(matched)
        prepared.append((record, normal_text, normal_title, body_counts, title_counts, matched, _length(normal_text)))
    if not prepared:
        return []
    count = len(prepared)
    average_length = sum(item[-1] for item in prepared) / count
    inverse_frequency = {
        term: math.log(1.0 + (count - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5))
        for term in features
    }
    query_weight = sum(inverse_frequency[term] * term_weights[term] for term in primary)
    matches = []
    for order, (record, text, title, body_counts, title_counts, matched, length) in enumerate(prepared):
        if not matched:
            continue
        matched_focus = focus.intersection(matched)
        if focus and not matched_focus:
            continue
        matched_primary = primary.intersection(matched)
        concept_match = bool(SPECIFIC_CONCEPTS.intersection(matched_focus))
        if for_cards:
            concept_match = concept_match or len(matched_focus) >= 2
        coverage = min(1.0, sum(inverse_frequency[term] * term_weights[term] for term in matched) / query_weight)
        phrase_length = _phrase_strength(query, title + "\n" + text, features)
        # A long, mostly unrelated request must not match on one generic overlap.
        # A continuous meaningful phrase can preserve an otherwise sparse match.
        if len(primary) >= 6 and not concept_match and (len(matched_primary) < 2 or (coverage < 0.22 and phrase_length < 4)):
            continue
        if len(primary) >= 3 and coverage < 0.12 and not concept_match:
            continue
        score = 0.0
        length_norm = 1.2 * (0.25 + 0.75 * length / average_length)
        for term in matched:
            frequency = body_counts[term]
            if frequency:
                score += term_weights[term] * inverse_frequency[term] * (frequency * 2.2) / (frequency + length_norm)
            if title_counts[term]:
                score += term_weights[term] * inverse_frequency[term] * 1.8
        score *= 0.65 + 0.35 * coverage
        score += min(phrase_length, 8) * 0.08
        tier = record.get("tier", 2)
        score *= {1: 1.04, 2: 1.0, 3: 0.96}.get(tier, 1.0)
        result = {
            "chunk_id": record.get("chunk_id", ""),
            "doc_id": record.get("doc_id", ""),
            "section_id": record.get("section_id", ""),
            "title": record.get("title", ""),
            "topics": record.get("topics", []),
            "score": round(score, 6),
            "excerpt": str(record["core"]) if for_cards else _excerpt(str(record.get("text", "")), matched),
            "path": record.get("path", ""),
            "sources": record.get("sources", []),
            "risk_flags": record.get("risk_flags", []),
            "tier": tier,
            "matched_terms": matched,
            "matched_focus": sorted(matched_focus),
            "match_type": "related_concept" if concept_match and len(matched_primary) < 2 else "lexical_terms",
            "record_type": record.get("record_type", "transcript"),
        }
        if for_cards:
            result.update({
                "card_id": record["card_id"],
                "conditions": record.get("conditions", []),
                "limits": record.get("limits", []),
                "evidence_type": record.get("evidence_type", "课程观点概括"),
                "exercise_type": record.get("exercise_type", "技能设计，不是讲师逐字建议"),
            })
        matches.append((score, order, result))
    matches.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] for item in matches[:top_k]]


def _portable_path(value):
    if not isinstance(value, str) or not value:
        return False
    path = value.split("#", 1)[0].replace("\\", "/")
    return bool(path) and not path.startswith("/") and ":" not in path and ".." not in PurePosixPath(path).parts


def card_records(cards):
    """Adapt curated cards to the same lexical ranker without altering sources."""
    records = []
    for card in cards:
        if not isinstance(card, dict) or not isinstance(card.get("id"), str):
            raise ValueError("知识卡缺少有效 id")
        identifier = card["id"]
        if not re.fullmatch(r"[A-Za-z0-9_-]+", identifier) or card.get("topic") not in TOPICS:
            raise ValueError("知识卡 id 或 topic 无效")
        if not isinstance(card.get("core"), str) or not isinstance(card.get("sources"), list):
            raise ValueError("知识卡缺少 core 或 sources")
        for locator in card["sources"]:
            if not isinstance(locator, dict) or not _portable_path(locator.get("path")):
                raise ValueError("知识卡来源路径无效")
        fields = [card.get("title", ""), card["core"]]
        for name in ("conditions", "questions", "actions"):
            values = card.get(name, [])
            if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
                raise ValueError("知识卡 %s 必须是字符串数组" % name)
            fields.extend(values)
        records.append({
            **card,
            "card_id": identifier,
            "chunk_id": "",
            "doc_id": "",
            "section_id": "",
            "record_type": "knowledge_card",
            "topics": [card["topic"]],
            "text": "\n".join(fields),
            "path": "references/topics/%s.md#%s" % (card["topic"], identifier.lower()),
            "risk_flags": [],
            "tier": 1,
        })
    return records


def search_corpus(query, topic=None, top_k=6, raw_only=False, skill_root=None):
    """Search the public cards only; never fall back to a private corpus."""
    if raw_only:
        raise ValueError("公开版不包含课程原文，不支持 --raw-only；请检索知识卡。")
    root = Path(skill_root) if skill_root else Path(__file__).resolve().parents[1]
    with (root / "data/cards.json").open(encoding="utf-8-sig") as stream:
        cards = json.load(stream)
    if not isinstance(cards, list):
        raise ValueError("cards.json 必须是数组")
    results = rank(query, card_records(cards), topic, top_k)
    return {
        "query": query,
        "results": results,
        "edition": "public",
        "search_mode": "cards_only",
        "notice": (
            "以下是公开知识卡的词法检索候选；请阅读适用条件和限制。"
            "观点为改写概括，练习为技能设计；来源登记不等于原文或事实核验。"
            "公开版未附课程原文，不可将检索结果冒充讲师逐字表述。"
        ) if results else NO_RESULTS,
    }


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="检索知衡·人生解局公开版的39张知识卡。")
    parser.add_argument("query", help="自然语言问题或具体关键词")
    parser.add_argument("--topic", choices=TOPICS)
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument("--json", action="store_true", help="输出 UTF-8 JSON")
    parser.add_argument("--raw-only", action="store_true",
                        help="兼容性提示：公开版不含原文，此选项会明确报错")
    args = parser.parse_args(argv)
    if not 1 <= args.top_k <= 50:
        parser.error("--top-k 必须在1至50之间")
    try:
        payload = search_corpus(args.query, args.topic, args.top_k, args.raw_only)
    except (ValueError, OSError) as error:
        payload = {"query": args.query, "results": [],
                   "notice": "无法检索：" + str(error), "edition": "public"}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(payload["notice"], file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload["notice"])
        for number, result in enumerate(payload["results"], 1):
            print(f"\n{number}. {result['title']} [{result['card_id']}]")
            print(result["excerpt"])
            print("知识卡：" + result["path"])
            print("适用条件：" + "；".join(result["conditions"]))
            print("限制：" + "；".join(result["limits"]))
            print("来源线索（不含原文）：" + json.dumps(result["sources"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
