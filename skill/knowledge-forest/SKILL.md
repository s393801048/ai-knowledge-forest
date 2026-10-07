---
name: knowledge-forest
description: 查 AI知识森林 —— 作者收集的提示词、Skill、知识卡片、AI 产品和学习资源。当用户说「找个提示词」「有没有写 XX 的提示词」「查一下知识森林」「装个技能」「查知识卡片」「有没有 XX 类的 AI 工具」「推荐个好用的 AI 产品」「去哪学 XX」时使用。
---

# AI知识森林

作者收集的提示词、Skill、知识卡片、AI 产品和学习资源，全部以静态 JSON 发布，直接读就行，不需要任何配置。

站点：https://s393801048.github.io/ai-knowledge-forest/

## 数据在哪

| 地址 | 内容 | 条数 |
|---|---|---|
| https://s393801048.github.io/ai-knowledge-forest/api/index.json | 目录：各库条数、分类 | — |
| https://s393801048.github.io/ai-knowledge-forest/api/prompts.json | 提示词，每条含**中文译文和英文原文** | 104 |
| https://s393801048.github.io/ai-knowledge-forest/api/skills.json | 技能卡片：干什么、从哪下 | 103 |
| https://s393801048.github.io/ai-knowledge-forest/api/cards.json | 知识卡片 | 489 |
| https://s393801048.github.io/ai-knowledge-forest/api/products.json | AI 产品和 AI 应用 | 318 |
| https://s393801048.github.io/ai-knowledge-forest/api/learn.json | 学习资源：文章、课程、别人的清单、排行榜 | 45 |

## 查提示词

1. 读 `api/prompts.json`，`items` 是数组
2. 每条字段：`name` 中文名、`en` 英文原名、`category` 分类、`summary` 一句话、`tags` 标签、
   `prompt` **中文译文（直接拿去用）**、`prompt_en` 英文原文、`detail` 详解、`howto` 怎么用、`source` 来源
3. 按 `name`、`en`、`summary`、`tags`、`detail` 匹配用户的关键词
4. 把 `prompt` 原样给用户；用户要英文版就给 `prompt_en`。需要时用 `howto` 说明要替换哪些占位符

## 装技能

`api/skills.json` 每条的 `source` 就是**下载地址**，两类：

- `modelscope.cn` 开头：作者自己做的，发布在魔搭社区
- `github.com` 开头：别人做的，在 GitHub

用户说「把 XX 技能装上」时：

1. 在 `api/skills.json` 里按名字找到那条
2. 按 `source` 去把技能下载下来
3. 装到用户的技能目录（Claude Code 是 `~/.claude/skills/`，WorkBuddy 是
   `~/.workbuddy/skills/`），放成 `技能名/SKILL.md` 的结构

站上只收录有公开地址的技能，所以 `source` 一定存在，不会白跑。

## 查知识卡片

读 `api/cards.json`，每条的 `name` 是主题、`summary` 一句话、`body` 是正文
（Markdown）。适合回答「XX 是什么」「XX 原理」这类问题。

## 查 AI 产品和学习资源

`api/products.json` 和 `api/learn.json` 是同一套字段：`name` 名称、`category` 分类、
`summary` 一句话、`tags` 标签、`source` **官网或仓库地址**、`origin` 出处、`body` 详细说明。

产品的 `tags` 里可能带 **GitHub 星标数**（开源项目）或**评价条数**（有多少人用过），
那是作者能验证的客观数字，**本站不提供产品质量评分**。

怎么用：

- 「有没有做 XX 的 AI 工具」「推荐个好用的 XX 工具」→ 搜 `products.json` 的
  `name`、`summary`、`tags`、`category`，把 `summary` 和 `source`（官网）给用户
- 「去哪学 XX」「有没有 XX 的教程」「现在哪个模型最强」→ 搜 `learn.json`
- 只收还在运营的产品；打开的链接打不开说明已关停，提醒作者更新

## 注意

- 数据在 GitHub Pages 上，国内访问可能慢；重试一两次，或用 `api/index.json`
  里的地址确认服务是否正常
- JSON 比较大（knowledge cards 约 1.2MB），按需读，别一次性全塞进上下文
