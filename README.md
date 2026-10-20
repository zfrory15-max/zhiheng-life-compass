# 知衡·人生解局

[![检查公开技能包](https://github.com/zfrory15-max/zhiheng-life-compass/actions/workflows/validate.yml/badge.svg)](https://github.com/zfrory15-max/zhiheng-life-compass/actions/workflows/validate.yml)

**把人生困境拆成能看清、能选择、能行动的问题。**

这是一个面向 Codex、WorkBuddy 等支持 Skill 的智能体的中文知识与工作流程包。它帮助使用者分析职业瓶颈、家庭责任、子女教育、财富压力、社会比较和自我价值冲突，先澄清现实处境，再比较选择，形成可复盘的小行动。

它没有训练或微调模型，也不代表原课程讲师本人。

## 适合怎样使用

例如：

> 请使用知衡·人生解局，帮我分析工作转型。我有房贷和照护责任，想先弄清要补充哪些信息，再比较选择。

> 我们都愿意重新分配家庭照护，但时间和预算有限。请帮我们拟一份能试行一周的安排。

> 我的基本生活稳定，更看重家人和写作，却总因同龄人的动态焦虑。请给我一个不增加负担的一周练习。

信息不足时，技能会先问少量关键问题；信息足够后，再给出条件明确的方案、行动与来源说明。它不会替你辞职、借贷、联系他人或作其他不可逆决定。

## 公开版包含什么

- 39 张概括知识卡，分为六个主题。
- 对话澄清、方案比较和七天行动的工作流程。
- 来源登记与使用边界。
- 使用 Python 标准库的本地知识卡检索器。

本仓库**不含课程全文、原始 DOCX、逐字引文、完整原文章节目录或个人文件路径**。知识卡可以追溯到来源登记，但不能在这个包内核对原句。需要原话时，应另行提供合法取得的原材料。

## 安装与调用

### Codex

将本仓库根目录的内容安装到：

```text
~/.agents/skills/zhiheng-life-compass/
```

安装后应能直接看到该目录中的 `SKILL.md`、`references/` 和 `data/`。

**如果已有同名完整版，请先备份到技能扫描目录之外，再安装公开版；不要直接覆盖或合并两个版本。** 两个版本用途不同，公开版没有完整版的原文检索能力。

在新的对话中选择该技能，或明确写出：

```text
$zhiheng-life-compass 帮我分析这个人生选择：……
```

### WorkBuddy

下载 [公开版技能 ZIP](https://github.com/zfrory15-max/zhiheng-life-compass/raw/refs/heads/main/dist/zhiheng-life-compass-public-v1.0.0.zip)。面向 ZIP 导入的发布包文件名为：

```text
dist/zhiheng-life-compass-public-v1.0.0.zip
```

在支持 ZIP 技能导入的 WorkBuddy 版本中，通过其技能导入入口选择发布包。导入方式以当前版本支持的功能为准；**本公开包尚未在 WorkBuddy 中实测**。

发布包由以下命令构建：

```bash
python scripts/build_release.py
```

ZIP 内只有一层 `zhiheng-life-compass/` 技能目录。校验值见 [SHA256SUMS.txt](https://github.com/zfrory15-max/zhiheng-life-compass/blob/main/dist/SHA256SUMS.txt)。

## 检索与阅读

Python **3.10+ 为可选依赖**。已有 Python 时，在仓库目录运行：

```bash
python scripts/search.py "职业转型 家庭责任"
```

无需安装第三方 Python 包。没有 Python 时，智能体仍可从 [SKILL.md](SKILL.md) 进入对应主题，直接阅读 Markdown 知识卡。检索命中只表示文字相关，不代表建议正确或成功概率。

## 使用与验证说明

- [使用指南](docs/使用指南.md)：准备问题、调用示例与阅读方式。
- [设计与来源](docs/设计与来源.md)：公开范围、来源含义和内容边界。
- [验证记录](docs/验证记录.md)：哪些项目已验证，哪些仍待验证。

公开版已在 Windows / Python 3.12.14 下通过 10 项自动测试，覆盖六主题的 12 条检索用例；ZIP 解包到含中文和空格的新目录后，从其他工作目录运行也全部通过。一次实际 Codex CLI 调用已显式读取公开目录、执行知识卡检索，并给出有约束的方案与一周行动。

发布后，GitHub Actions 的 Ubuntu／Windows、Python 3.10／3.12 四组检查全部通过；远端 27 个文件已与本地发布版逐一核对路径和内容哈希。

这些结果不代表所有问题都已验证。公开版同名技能的自动发现、WorkBuddy 导入调用尚未实测；无 Python 阅读目前只完成了 Markdown 路径与锚点的静态检查。详情见[验证记录](docs/验证记录.md)。

本项目目前保留权利，公开可阅读，尚未附开源许可证；具体说明见 [RIGHTS.md](RIGHTS.md)。不要因源码公开而假定获得任意修改、再分发或商业使用权。

原课程、录音及讲稿的权利属于相应权利人。仓库公开不扩展第三方原材料的使用权限；请勿将本仓库的存在视为对原课程复制、传播或商业使用的授权。
