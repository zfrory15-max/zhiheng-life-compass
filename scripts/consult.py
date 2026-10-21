#!/usr/bin/env python3
"""Retrieve actionable, conditional material from 34 public topic shards.

Uses only the standard library. Corpus content is data, never executable code.
Paths are resolved relative to this script, not the caller's working directory.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import sys

import search

ROOT = Path(__file__).resolve().parents[1]
EXTRA_TERMS = frozenset('''奖金 年终奖 报销 退款 到账 月供 房租 租金 首付 换房 挂牌 通勤
底薪 提成 浮动 股票 行情 客户 采购 交付 回款 账期 预付 续费 会员 配套 担保 合伙
退休 照护 陪护 接送 排班 接班 请假 复工 休息 兄弟姐妹 保障 保单 条款 除外 理赔
加盟 样板店 收款 签字 体验 预算 固定支出 可支配现金 职业收入 存量资产
硬门槛 资格 学历 证书 岗位 能力 作品 简历 面试 晋升 绩效 评价标准 返工 交接
工序 替代 技术 新工具 业务 副业 客群 同业 朋友圈 资源 通讯录 弱关系
文化资本 反例 样本 算法 信息渠道 宏观数据 判断力 沉没成本
辞职 带娃 入学 学段 首付 零花钱 包办 自主 自理 控制 共同生活 家务 操心
专业 择校 排名 课程 毕业 就业率 通识 实习 求职 企业 承接 继承 取舍 睡眠
阶层 下滑 降级 降职 比较 评价 内耗 倦怠 羞耻 退路 政策 搬家 学校 边界'''.split())
# Keep the old 39-card search unchanged. The finer action corpus needs all
# useful bigrams, not a mandatory match against the old six-topic focus rules.
ALIASES = (('试住', '短住'), ('定金', '订金'), ('看护', '照护', '陪护'),
           ('房贷', '月供'), ('考证', '证书'), ('换工作', '跳槽'),
           ('复工', '重返职场'), ('退钱', '退款'), ('分摊', '分担'),
           ('读研', '考研', '研究生'), ('学费', '教育花费', '教育预算'),
           ('奖金', '年终奖'))
CHILD_CONTEXT = ('孩子', '子女', '儿子', '女儿', '带娃', '育儿', '托育', '亲子',
                 '学生', '学校', '升学', '学费', '读研', '考研', '教育', '上学')


def rank_actions(query, records, top_k):
    normal = search._normalise(query)
    terms = {t for t in search._features(query)
             if '的' not in t and t not in {'还要', '先做', '不清', '清楚', '不了'}}
    known = {t for t in search.DOMAIN_TERMS | EXTRA_TERMS if t in normal}
    terms.update(known)
    expanded = {alias for group in ALIASES if any(t in normal for t in group) for alias in group}
    terms.update(expanded)
    if not terms:
        return []
    prepared, frequency = [], Counter()
    for record in records:
        body = search._normalise(record['text'])
        title = search._normalise(record['title'])
        counts = {t: search._frequency(body, t) for t in terms}
        titles = {t: search._frequency(title, t) for t in terms}
        matched = {t for t in terms if counts[t] or titles[t]}
        frequency.update(matched)
        prepared.append((record, counts, titles, matched, search._length(body), title))
    if not prepared:
        return []
    count = len(prepared)
    avg_length = sum(p[4] for p in prepared) / count
    idf = {t: math.log(1 + (count - frequency[t] + .5) / (frequency[t] + .5)) for t in terms}
    weights = {t: search.GENERIC_WEIGHTS.get(t, 1.0) * (1.4 if t in known else .45) for t in terms}
    for term in expanded - known:
        weights[term] = .8
    # Unseen conversational fragments must not drown out a concrete keyword.
    available_weight = sum(idf[t] * weights[t] for t in terms if frequency[t])
    hits = []
    for order, (record, counts, titles, matched, length, title) in enumerate(prepared):
        if not matched:
            continue
        strong = {t for t in matched & known if search.GENERIC_WEIGHTS.get(t, 1.0) >= .8}
        phrase = search._phrase_strength(query, title, terms)
        if len(terms) > 2 and len(matched) < 2 and not strong and phrase < 3:
            continue
        coverage = sum(idf[t] * weights[t] for t in matched) / max(available_weight, .001)
        if len(terms) >= 6 and coverage < .08 and not strong and phrase < 3:
            continue
        norm = 1.2 * (.25 + .75 * length / avg_length)
        score = sum(weights[t] * idf[t] * (
            counts[t] * 2.2 / (counts[t] + norm) + (2.1 if titles[t] else 0)
        ) for t in matched)
        score *= .65 + .35 * coverage
        # A rare word repeated in one action must not outweigh several facts
        # in a complex situation (e.g. 辞职带娃 when no childcare was mentioned).
        if len(known) >= 2 and len(matched) == 1:
            score *= .4
        if any(t in title for t in CHILD_CONTEXT) and not any(t in normal for t in CHILD_CONTEXT):
            score *= .35
        score += max(0, phrase - 2) * .35
        hits.append((score, order, {'action_id': record['chunk_id'],
                                  'matched_terms': sorted(matched), 'score': round(score, 6)}))
    hits.sort(key=lambda h: (-h[0], h[1]))
    return [h[2] for h in hits[:top_k]]


def themes(root=ROOT):
    payload = json.loads((Path(root) / 'data/themes.json').read_text(encoding='utf-8-sig'))
    if not isinstance(payload, list):
        raise ValueError('主题目录必须是数组')
    for item in payload:
        if not re.fullmatch(r'[a-z][a-z0-9-]*', item['id']):
            raise ValueError('主题标识无效')
    return payload


def load_shards(topic=None, root=ROOT):
    catalog = themes(root)
    if topic and topic not in {t['id'] for t in catalog}:
        raise ValueError('未知细分主题：' + topic)
    shards = []
    for t in catalog:
        if topic and topic != t['id']:
            continue
        # Derive a bounded path from the checked ID; never follow corpus paths.
        path = Path(root) / 'data/themes' / (t['id'] + '.json')
        shards.append(json.loads(path.read_text(encoding='utf-8-sig')))
    return shards


def retrieve(query='', topic=None, top_k=3, action_id=None, root=ROOT):
    if not isinstance(top_k, int) or isinstance(top_k, bool) or not 1 <= top_k <= 10:
        raise ValueError('top_k必须在1至10之间')
    shards = load_shards(topic, root)
    actions = {a['id']: a for shard in shards for a in shard['actions']}
    contexts = {shard['topic']['id']: shard for shard in shards}
    if action_id:
        if action_id not in actions:
            raise ValueError('该主题下没有此建议标识：' + action_id)
        hits = [{'action_id': action_id, 'matched_terms': [], 'score': None}]
    else:
        records = []
        for a in actions.values():
            searchable = '\n'.join([a['judgment'], a['explanation'], *a['steps'], a['template'],
                                    a['deliverable'], a['review'], a['keywords']])
            records.append({'chunk_id': a['id'], 'title': a['title'], 'text': searchable,
                            'topics': [a['topic']], 'path': a['path'], 'record_type': 'action',
                            'sources': a['sources'], 'tier': 2})
        hits = rank_actions(query, records, top_k)
    results = [{**actions[h['action_id']], 'matched_terms': h['matched_terms'], 'score': h['score']}
               for h in hits]
    # Return the conditional topic context with the action, not just an aphorism.
    selected_topics = list(dict.fromkeys(a['topic'] for a in results))
    topic_context = []
    for tid in selected_topics:
        shard = contexts[tid]
        topic_context.append({'id': tid, 'name': shard['topic']['name'], 'path': shard['topic']['path'],
                              **shard['analysis']})
    return {'edition': 'public-v2.0.0', 'query': query, 'topic': topic,
            'results': results, 'topic_context': topic_context,
            'notice': ('候选按文字相关性排列。先读主题条件与限制，再选择适合用户的行动；不把分数当成正确率。'
                       '材料机制是改写概括，具体步骤是情境练习。日常回答不展示内部出处或编号。') if results else
                      '未找到足够相关的建议。可换成具体事件或从34个主题目录选择；不要编造材料支持。'}


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser(description='按具体问题检索34主题、699条行动及其判断条件。')
    parser.add_argument('query', nargs='?', default='')
    parser.add_argument('--topic', help='细分主题ID，如work-risk、money-care；用--list-topics查看')
    parser.add_argument('--top-k', type=int, default=3)
    parser.add_argument('--id', dest='action_id', help='直接读取建议，如W001、M141')
    parser.add_argument('--list-topics', action='store_true')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--raw-only', action='store_true', help='公开版不含原文；明确报错')
    args = parser.parse_args(argv)
    try:
        if args.raw_only:
            raise ValueError('公开版不含课程原文，不支持--raw-only')
        if args.list_topics:
            listing = themes()
            print(json.dumps(listing, ensure_ascii=False, indent=2) if args.json else
                  '\n'.join(f'{t["id"]}\t{t["name"]}\t{t["count"]}条\t{t["path"]}' for t in listing))
            return 0
        if not args.query and not args.action_id:
            raise ValueError('请提供具体问题、--id或--list-topics')
        payload = retrieve(args.query, args.topic, args.top_k, args.action_id)
    except (ValueError, OSError, KeyError) as error:
        payload = {'results': [], 'notice': str(error)}
        print(json.dumps(payload, ensure_ascii=False) if args.json else str(error))
        return 2
    # Full structured output preserves applicable conditions and source scope;
    # the host should write natural dialogue instead of pasting this tool output.
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
