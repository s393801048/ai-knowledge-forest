---
name: knowledge-forest
description: 查 AI知识森林 —— 作者收集的提示词、Skill 和知识卡片。当用户说「找个提示词」「有没有写 XX 的提示词」「查一下知识森林」「装个技能」「查知识卡片」时使用。
---

# AI知识森林

作者收集的提示词、Skill 和知识卡片，全部以静态 JSON 发布，直接读就行，不需要任何配置。

站点：https://s393801048.github.io/ai-knowledge-forest/

## 数据在哪

| 地址 | 内容 | 条数 |
|---|---|---|
| https://s393801048.github.io/ai-knowledge-forest/api/index.json | 目录：各库条数、分类 | — |
| https://s393801048.github.io/ai-knowledge-forest/api/prompts.json | 提示词，每条含**可直接使用的原文** | 117 |
| https://s393801048.github.io/ai-knowledge-forest/api/skills.json | 技能卡片：干什么、从哪下 | 103 |
| https://s393801048.github.io/ai-knowledge-forest/api/cards.json | 知识卡片 | 465 |

## 查提示词

1. 读 `api/prompts.json`，`items` 是数组
2. 每条字段：`name` 名称、`category` 分类、`summary` 一句话、`tags` 标签、
   `prompt` **提示词原文（直接拿去用）**、`detail` 详解、`howto` 怎么用、`source` 来源
3. 按 `name`、`summary`、`tags`、`detail` 匹配用户的关键词
4. 把 `prompt` 原样给用户，需要时用 `howto` 说明要替换哪些占位符

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

## 注意

- 数据在 GitHub Pages 上，国内访问可能慢；重试一两次，或用 `api/index.json`
  里的地址确认服务是否正常
- JSON 比较大（knowledge cards 约 1.2MB），按需读，别一次性全塞进上下文
