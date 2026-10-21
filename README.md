# 知衡中产指南

**一份可以直接阅读的行动指南，也是一套可以交给智能体使用的中文 Skill。**

围绕职业、家庭、教育、财富压力和人生选择，帮助你看清现实约束，比较选择的代价，找到下一步可以做的事。

| 入口 | 适合怎样使用 | 内容 |
| --- | --- | --- |
| [网页指南](https://zfrory15-max.github.io/zhiheng-life-compass/) | 自己阅读、搜索、收藏，照着步骤做 | 34 个主题、699 条建议，附标签、重点高亮、三步做法和填写模板 |
| [知衡·人生解局 Skill](SKILL.md) | 让 Codex、WorkBuddy 等智能体结合你的具体处境展开对话 | 34 个主题判断指南、699 条行动、102 条材料机制，另保留 39 张基础卡 |

[在线阅读](https://zfrory15-max.github.io/zhiheng-life-compass/) · [下载 Skill v2 安装包](https://github.com/zfrory15-max/zhiheng-life-compass/raw/refs/heads/main/dist/zhiheng-life-compass-public-v2.0.0.zip) · [浏览 34 个 Skill 主题](references/index.md) · [下载网页包](https://github.com/zfrory15-max/zhiheng-life-compass/raw/refs/heads/main/zhiheng-guide-web.zip)

## Skill：知衡·人生解局

**使用目标：帮助你看清人生困境中的现实约束、关系冲突与个人期待，比较选择的代价，形成可以执行和复盘的下一步行动。**

调用标识：`zhiheng-life-compass`。

适用于职业瓶颈、婚姻家庭、子女教育、财富压力、社会比较和自我价值。例如：有房贷和育儿责任时要不要求职转型，有限的家庭预算如何分配，照护责任怎样协商，面对同龄人比较如何调整自己的安排。

它会先弄清你最想解决的问题。信息不足时，每轮最多问三个关键问题；信息足够后，围绕收入、时间、家庭责任和底线比较可行方案，给出未来七天的一至三个行动，必要时提供沟通话术和复盘信号。

回答采用自然、清醒务实的咨询对话方式，避免空泛安慰和固定报告模板。日常回答不展示课程出处、卡片编号或“来源”栏目；你主动追问依据时再展开。不确定的地方会如实说明。

### 安装 Skill

下载上方的 **Skill v2 安装包**，文件名为 `zhiheng-life-compass-public-v2.0.0.zip`。ZIP 内只有一层 `zhiheng-life-compass/` 技能目录，包含 `SKILL.md`、`references/`、`data/` 和检索脚本。

**Codex**：解压后，把整个 `zhiheng-life-compass` 文件夹放到：

```text
~/.agents/skills/zhiheng-life-compass/
```

Windows 可在文件资源管理器地址栏输入以下路径（`%USERPROFILE%` 会自动对应当前用户目录）：

```text
%USERPROFILE%\.agents\skills\zhiheng-life-compass\
```

确认 `SKILL.md` 直接位于该目录中，在新的对话里选择技能，或输入下面的调用示例。

**WorkBuddy**：在支持 ZIP 技能导入的版本中，从技能导入入口选择同一个 Skill 安装包。具体入口以当前版本为准；本公开包的 WorkBuddy 导入与实际调用尚未实测。

如果已有同名完整版，请先备份到技能扫描目录之外，再安装公开版，避免直接覆盖或合并。公开版没有完整版的课程全文检索能力。

### 调用示例

```text
使用 $zhiheng-life-compass。

我工作进入瓶颈，又承担房贷、育儿和父母养老，
不知道该求稳还是转型。
请先帮我澄清关键问题，再比较选择，给出下一周可以做的事。
```

也可以用自然语言提出具体问题：

> 请使用知衡·人生解局。我们想重新分配家庭照护，但时间和预算都有限，请帮我们拟一份能试行一周的安排。

### Skill 包含什么

- **34 个主题判断指南**：每个主题包含适用情境、三个关键区分、三条材料机制、澄清问题、可比较的做法及限制。
- **699 条具体行动**：与网页建议对应，含判断、做法、填写模板、实际产出和复盘信号；智能体按你的处境挑选和改写。
- **102 条材料机制**：回读所提供文稿的相关上下文后改写，帮助区分相似表象背后的不同原因，而非只复述行动标题。
- **39 张基础知识卡**：保留原有六类问题的基本框架，按需要补充阅读。
- **按需读取**：检索具体问题，同时读取相关主题的条件和限制，通常选一至三个行动。
- **本地检索工具**：可选 Python 3.10+，只用标准库，无需付费 API 或向量数据库。
- **Markdown 阅读入口**：没有 Python 时，可从 [主题目录](references/index.md) 直接读取知识卡。

在技能目录中可以运行：

```bash
python scripts/consult.py "奖金迟发，房贷月底扣款" --top-k 3
python scripts/consult.py "照护老人后怎么复工" --topic family-capacity
python scripts/consult.py --list-topics
```

**v2 已把网页的 34 个主题、699 条建议纳入 Skill，并增加主题层面的判断条件与材料分析。** 例如：收入总额与来源集中、多套房产与同一客群的依赖、家务执行与操心责任、教育花费与独立能力，需要分别判断。下载网页包用于阅读；安装 Skill 请使用上面的 Skill v2 包。

没有 Python，也能直接阅读 [34 主题目录](references/index.md)。原有基础卡检索仍可使用 `python scripts/search.py "关键词"`。

[查看 SKILL.md](SKILL.md) · [使用指南](docs/使用指南.md) · [合成调用示例](references/examples.md) · [验证记录](docs/验证记录.md)

## 网页：699 条可以照着做的建议

网页分为 **34 个主题**，围绕职业收入、能力积累、求职转岗、第二收入、家庭现金、住房与长期支出、伴侣合作、子女教育、养老照护、社会比较和压力下的判断展开。

每条包括：

- **标签**：行动类型、适用场景、成本和时间提示。
- **重点判断**：淡紫色背景标出核心观点。
- **三步做法**：从哪里开始、需要核对什么、怎样往下走。
- **填写模板与检查信号**：做完留下结果，判断该继续、调整还是停止。

先搜索眼前的问题，例如“奖金”“转岗”“陪读”“照护”。挑一条最相关的，照着步骤做，填完模板，再回来看结果。

网页支持完整目录、中文搜索、轻量练习筛选、只看要点、收藏、明暗切换，以及复制执行清单和条目链接。手机可通过顶部主题菜单定位。收藏只保存在当前浏览器，没有账号、个人资料上传或统计脚本。

建议用于比较自己的处境，不承诺避免所有损失或保证生活水平。标签是阅读提示，不是证据评级或收益评分。

### 本机阅读与网页部署

下载 [独立网页包](https://github.com/zfrory15-max/zhiheng-life-compass/raw/refs/heads/main/zhiheng-guide-web.zip) 并解压，打开 `index.html`；也可以在解压目录运行：

```bash
python -m http.server 8770
```

然后访问 `http://localhost:8770/`。更换地址或浏览器后，原地址中的收藏不会自动迁移。

网页采用原生 HTML、CSS 和 JavaScript，无需构建工具。根目录的 `index.html`、`styles.css`、`app.js`、`guide-data.js` 和 `favicon.svg` 是网页文件，`.nojekyll` 用于 GitHub Pages 静态发布。

## 验证与维护

[![检查公开技能包](https://github.com/zfrory15-max/zhiheng-life-compass/actions/workflows/validate.yml/badge.svg)](https://github.com/zfrory15-max/zhiheng-life-compass/actions/workflows/validate.yml)

v2 的验证覆盖主题与行动结构、材料定位、具体情境检索、公开包边界、Markdown链接和ZIP迁移。每项的实际结果与未覆盖范围见 [验证记录](docs/验证记录.md)，远端构建状态见上方徽章。WorkBuddy 导入调用尚未实测；不能将目录规范或 Codex 的结果视为 WorkBuddy 已通过。

Skill 发布包可通过以下命令构建，仓库中下载包的校验值见 [SHA256SUMS.txt](https://github.com/zfrory15-max/zhiheng-life-compass/blob/main/dist/SHA256SUMS.txt)：

```bash
python scripts/build_release.py
```

网页已完成桌面和手机显示、中文搜索、收藏、重点高亮及线上内容数量检查。

## 资料与使用边界

本项目提供知识与工作流程，没有训练或修改模型参数，也不代表课程讲师本人。公开仓库不含课程全文、原始 DOCX、逐字引文或个人文件路径。知识卡的来源登记不能替代原文核验，说明见 [设计与来源](docs/设计与来源.md)。

不作临床诊断，不提供操控他人的做法。涉及现行法律、政策、金融或医疗事实时，需要另行核实。默认不建立长期个人档案，也不代替使用者作不可逆决定。

本项目目前保留权利，尚未附开源许可证，具体见 [RIGHTS.md](RIGHTS.md)。原课程、录音和讲稿的权利属于相应权利人；仓库公开不扩展第三方原材料的使用权限。
