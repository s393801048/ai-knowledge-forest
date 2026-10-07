# 补充笔记：Claude Code 进阶配置指南（黑马课程未覆盖内容）

> 来源：繁树星堂《2026 年完整的 Claude 代码设置指南：所有值得安装的技能、插件和配置选项》
> 说明：本文整理黑马 Vibe Coding 课程 [11]~[18] 未覆盖的 Claude Code 进阶配置内容，按七层架构组织。建议学完黑马课程后再阅读本文，将 Claude Code 从"新手模式"升级到"专家模式"。

---

## 第一层：安装与验证（进阶补充）

> 黑马课程讲的是 `npm install -g @anthropic-ai/claude-code` 一种方式，以下补充 2026 年官方推荐方式。

### 1.1 官方推荐：原生安装程序（自动更新）

```bash
# macOS / Linux / WSL
curl -fsSL https://claude.ai/install.sh | bash

# Windows PowerShell
irm https://claude.ai/install.ps1 | iex

# Windows CMD
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

> ⚠️ Windows 用户需额外安装 Git for Windows，让 Claude Code 使用真正的 Bash 而非 PowerShell。

### 1.2 五种包管理器安装方式

| 平台 | 命令 | 特点 |
|------|------|------|
| Homebrew（稳定版） | `brew install --cask claude-code` | 比官方晚一周，不支持自动更新 |
| Homebrew（最新版） | `brew install --cask claude-code@latest` | 每次有新版本时更新 |
| WinGet | `winget install Anthropic.ClaudeCode` | Windows 原生包管理 |
| apt/dnf/apk | 通过 Anthropic 签名软件仓库 | 随系统常规升级 |
| npm | `npm install -g @anthropic-ai/claude-code` | 需 Node 18+，**不要加 sudo** |

> ⚠️ npm 方式注意：必须用 `@latest` 升级（`npm update -g` 可能让你一直用旧版），且 `sudo npm` 会导致权限问题。

### 1.3 验证安装（两步检查）

```bash
claude --version    # 是否安装成功且在 PATH 中
claude doctor       # 深度检查：配置、认证、更新状态、上报最近一次自动更新结果
```

> `claude doctor` 是遇到任何异常时的第一选择。

### 1.4 更新渠道设置

| 渠道 | 行为 | 适用场景 |
|------|------|---------|
| `latest` | 每次新版本发布立即更新 | 想尝鲜 |
| `stable` | 延迟约一周，跳过严重 bug 版本 | Claude Code 对你工作至关重要时（推荐） |

设置方式：`/config` → 选择 `autoUpdatesChannel`。

### 1.5 付费要求

Claude Code 需要付费套餐：Pro / Max / Team / Enterprise，或 Console API 账户。免费 Claude.ai 不含 Claude Code。

---

## 第二层：CLAUDE.md 内存文件（进阶补充）

> 黑马课程 [12] 讲了 CLAUDE.md 和 memory.md 的基本概念，以下为进阶内容。

### 2.1 三层记忆架构

| 层级 | 位置 | 作用 | 共享范围 |
|------|------|------|---------|
| 用户记忆 | `~/.claude/CLAUDE.md` | 个人偏好，跨项目通用 | 仅自己 |
| 项目记忆 | `./CLAUDE.md` | 项目规则、架构、命令 | Git 提交，团队共享 |
| 企业管理策略 | 公司统一配置 | 组织级规则，冲突时最高优先级 | 全公司 |

### 2.2 `/init` 自动生成项目记忆

```
/init
```

- 扫描整个代码库，自动生成 `CLAUDE.md` 初稿
- 包含：技术栈、目录结构、常用命令
- 生成后手动补充：构建/测试命令、代码规范、禁区规则

### 2.3 关键细节

- **不要写太长**：每次会话每一行都消耗 token。用 `@path` 将内容拆分到不同文件，启动时自动加载，但不会增加额外 token 消耗
- **`/compact` 后从磁盘重读**：项目根目录的 `CLAUDE.md` 永远不会被破坏——压缩后 Claude 会从磁盘重新读取。所有不能在会话中丢失的数据都应该放在这里
- 快速启动方式：`/init` → 手动补充 5 行个人偏好 → 完成

---

## 第三层：Skills 技能系统（进阶补充）

> 黑马课程 [17] 讲了如何创建自定义技能，以下为内置技能和技能系统补充。

### 3.1 内置技能（Bundled Skills）

Claude Code 预装以下技能，每次会话自动可用：

| 内置技能 | 功能 |
|---------|------|
| `/code-review` | 代码审查 |
| `/debug` | 调试分析 |
| `/loop` | 循环执行 |
| `/batch` | 批量处理 |
| `/claude-api` | API 调用 |

> 这些技能是基于提示的——Claude 自行决定用哪些工具来完成任务，而不是固定命令。
> 如果不想用：设置 `disableBundledSkills` 为隐藏。

### 3.2 文档生成技能

Claude Code 内置了原生文档生成能力，能按真实文件格式生成文档（不需要第三方库）：

| 技能 | 功能 |
|------|------|
| `docx` | 生成格式正确的 Word 文档 |
| `xlsx` | 生成包含有效公式的 Excel 电子表格 |
| `pptx` | 生成 PPT 演示文稿 |
| `pdf` | 提取 PDF 字段、处理文档内容 |

> ⚠️ 生成电子表格后务必打开核对公式——尤其是涉及客户或财务的内容。验证工作仍是你应尽的职责。

### 3.3 技能优先级与覆盖规则

| 优先级 | 规则 |
|--------|------|
| 企业级 > 个人级 > 项目级 | 同名技能，高优先级覆盖低优先级 |
| 项目自定义覆盖内置 | 项目中同名 `code-review` 技能会完全取代内置 `/code-review` |

> 技能访问也受 `/permissions` 控制：可以按名称完全禁止或允许特定技能。

### 3.4 技能文件模板（90 秒创建）

个人技能存储在 `~/.claude/skills/`，项目技能在 `.claude/skills/`：

```markdown
---
name: changelog-writer
description: Draft a changelog entry from recent git commits in our house style
---

When invoked, read the recent commit log, group changes by type (Added/Fixed/Changed),
and write a concise entry in past tense.
```

> `~/.claude/skills/` 下的更改在当前会话立即生效，无需重启。

---

## 第四层：插件与市场平台（全新内容）

> 黑马课程未涉及插件系统，以下为全新内容。

### 4.1 技能 vs 插件

| 概念 | 比喻 | 范围 |
|------|------|------|
| 技能 (Skill) | 个人能力 | 单个功能 |
| 插件 (Plugin) | 能力容器 | 可同时包含：命令、子代理、MCP 服务器、钩子、技能 |

> 一个插件，一次安装，一次卸载——打包了所有相关组件。

### 4.2 市场操作

```bash
# 添加市场（支持 GitHub owner/repo 简写、完整 Git URL、本地路径）
/plugin marketplace add anthropics/skills

# 打开插件管理界面
/plugin

# 在 Discover 标签页搜索并安装
# 安装前务必查看"即将安装列表"——列出该插件添加的所有命令/代理/技能/钩子/MCP/LSP
```

### 4.3 安装范围

| 范围 | 说明 |
|------|------|
| 用户范围 | 仅对自己有效（默认） |
| 项目范围 | 通过 `.claude/settings.json` 共享给团队 |
| 本地范围 | 仅对自己有效，不共享 |

> 插件名称带前缀（如 `/my-plugin:review`），不会发生名称冲突。

### 4.4 核心原则

> ⚠️ **插件是让工具箱能正常使用的最快捷方式——但也是让工具箱臃肿的最快途径。** 每次安装插件都会增加模型需要处理的元素。只安装本月真正会用的。

---

## 第五层：MCP 连接器（全新内容）

> 黑马课程未涉及 MCP（Model Context Protocol），以下为全新内容。

### 5.1 什么是 MCP

Model Context Protocol 服务器让 Claude Code 不再局限于终端——可以直接读写 GitHub、Linear、Notion、Slack、Google Drive、Postgres 等平台的数据。

> 有了 MCP，Claude Code 从"编程工具"变成"实际操作工具"。

### 5.2 两种传输方式

```bash
# HTTP 传输：远程云服务（推荐）
claude mcp add --transport http notion https://mcp.notion.com/mcp

# stdio 传输：本地子进程（用 -- 分隔服务器自身命令）
claude mcp add --transport stdio myserver -- npx some-mcp-server
```

### 5.3 管理命令

| 命令 | 功能 |
|------|------|
| `claude mcp list` | 列出所有已配置的服务器及健康状态 |
| `claude mcp get <name>` | 查看某个服务器的详细信息 |
| `claude mcp remove <name>` | 删除一个服务器 |

### 5.4 推荐连接顺序

1. **GitHub** — 对大多数开发者最有价值的连接
2. **Linear / Notion** — 只有当它们确实是主要工作平台时才连接
3. 其他平台 — 在觉得有必要之前先不装

> 大多数连接只需"复制 URL → 浏览器完成 OAuth 授权"，无需写代码。

### 5.5 安全提醒

> MCP 服务器能读写你的 GitHub 或 Notion 后，**只有你设定的权限规则才能阻止"有用的智能体"带来麻烦**。在连接任何 MCP 之前，先配好权限（见第六层）。

---

## 第六层：settings.json 与权限系统（全新内容）

> 黑马课程未涉及权限配置，以下为全新内容。

### 6.1 权限规则

规则格式为 `Tool` 或 `Tool(specifier)`，按严格顺序执行：**先 deny → 再 ask → 最后 allow**。只要一个规则命中就停止。

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run test:*)",     // 允许所有测试命令
      "Bash(git status)",          // 允许 git status
      "Read"                        // 允许读取文件
    ],
    "ask": [
      "Bash(git push:*)"           // git push 需要确认
    ],
    "deny": [
      "Read(./.env)",              // 禁止读取 .env
      "Read(./secrets/**)"         // 禁止读取 secrets 目录
    ]
  }
}
```

### 6.2 `deny` 的特殊性

> `deny` 规则**即使在 `bypassPermissions` 模式下仍然生效**。它是保护密钥的最佳方式——像一道屏障，抵御你未来可能犯下的愚蠢操作。

### 6.3 四种工作模式（defaultMode）

| 模式 | 行为 | 适用场景 |
|------|------|---------|
| `default` | 每个敏感操作前询问 | **从这里开始**（推荐） |
| `acceptEdits` | 预批准文件修改，命令仍需确认 | 提高效率时 |
| `dontAsk` | 自动拒绝未明确允许的操作，仅执行 allow 规则和只读操作 | 无人值守循环 |
| `bypassPermissions` | 完全无提示 | ⚠️ 极危险，仅沙箱环境用 |

### 6.4 配置层级与热加载

| 层级 | 位置 | 共享 |
|------|------|------|
| 用户级 | `~/.claude/settings.json` | 仅自己 |
| 项目级 | `.claude/settings.json` | Git 提交，团队共享 |
| 本地 | 本地非共享版本 | 仅自己 |

> Claude Code 持续监控这些文件，保存后自动重新加载——无需重启。

### 6.5 第一天就要做的事

```json
// 最小安全配置：隐藏密钥 + 保持 default 模式
{
  "permissions": {
    "deny": ["Read(./.env)", "Read(./secrets/**)"]
  },
  "defaultMode": "default"
}
```

---

## 第七层：Subagent、命令、Hooks 自动化层（进阶补充）

> 黑马课程 [18]-[21] 讲了 Agent 基础和 Hook 入门，以下为进阶内容。

### 7.1 Subagent YAML 元数据（进阶）

子代理 = Markdown 文件 + YAML 元数据，拥有独立的系统提示、工具集和模型：

```markdown
---
name: code-reviewer
description: Reviews code for quality, security, and best practices
tools: Read, Glob, Grep
model: sonnet
---

You are a code reviewer. When invoked, analyze the changes and give
specific, actionable feedback on quality, security, and best practices.
```

> 关键字段 `tools`：限制子代理只能读取，就无法修改你没要求它改的内容。**审查者应该只读。**

### 7.2 `/agents` 管理界面

- 新增"运行"标签页，查看正在运行或刚完成的子代理
- 可打开、停止子程序
- 插件提供的代理与你自己的代理并列显示

### 7.3 命令与技能统一

旧的 `.claude/commands/` Markdown 格式仍有效（旧版），现在的做法是使用技能机制（`SKILL.md`）：
- 用户可以直接调用（斜杠命令）
- Claude 也可以自动执行

> **一次编写，同时获得两种功能。**

### 7.4 Hooks 五种生命周期事件

Hook = shell 命令或 HTTP 调用，保存在 `settings.json` 中，在特定生命周期事件触发：

| 事件类型 | 触发时机 | 典型用途 |
|---------|---------|---------|
| `SessionStart` | 每次会话开始 | 初始化环境 |
| `SessionEnd` | 每次会话结束 | 清理、日志记录 |
| `UserPromptSubmit` | 每次用户提交提示 | 预处理输入 |
| `Stop` | 每次停止时 | 运行测试 |
| `PreToolUse` | 每次调用工具前 | **拦截操作**（如阻止编辑受保护路径） |
| `PostToolUse` | 每次调用工具后 | 格式化、代码检查、自动记录 |

### 7.5 Hook 配置示例

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/lint-check.sh"
          }
        ]
      }
    ]
  }
}
```

> 你的脚本通过 stdin 以 JSON 接收事件数据（`session_id`、`cwd`、`tool_name`、`tool_input`），可以随心设计各种自动化。

### 7.6 经过验证的有效 Hook 实践

| 事件 | 用途 |
|------|------|
| 保存时 | 自动格式化代码（Prettier/ESLint） |
| Stop 时 | 自动运行测试套件 |
| PostToolUse | 记录所有 Bash 命令到日志 |
| PreToolUse | 阻止编辑受保护路径 |

---

## 推荐入门套装：8 步一站式配好 Claude Code

> 只需一个下午，把二进制程序变成真正的"队友"。

| 步骤 | 操作 | 命令/位置 |
|------|------|---------|
| 1. 安装 | 用原生安装程序，选 stable 渠道 | `claude --version` → `claude doctor` 验证 |
| 2. 认证 | Pro/Max/Team 或 Console API 密钥 | 浏览器引导 |
| 3. 内存 | 在主仓库运行 `/init`，补充 5 行个人偏好 | `~/.claude/CLAUDE.md` + `./CLAUDE.md` |
| 4. 技能 | 为自己最常重复的任务写一个个人技能 | `~/.claude/skills/<name>/SKILL.md` |
| 5. 插件 | 添加市场，只装本月用的 | `/plugin marketplace add anthropics/skills` → `/plugin` → Discover |
| 6. MCP | 先连 GitHub | `claude mcp add --transport http github <url>` → `claude mcp list` |
| 7. 权限 | 把 `.env` 和 secrets 加入 deny，保持 default 模式 | `.claude/settings.json` |
| 8. 自动化 | 添加 PostToolUse lint 钩子 + 只读审查子代理 | `/agents` + `settings.json` hooks |

---

## 核心心法

> ⚠️ **精简总比臃肿好**：每个插件、技能、MCP 服务器都会增加模型处理负担。最佳配置往往非常简单，但精心设计。
>
> ⚠️ **过度安装是 Claude Code 性能变差的最常见原因**。
>
> 🛡️ **权限不是可以拖延的事**：一旦 MCP 能写入你的 GitHub，只有你设定的规则才能阻止灾难。请在第一天就配好 deny 规则。
>
> ✅ **验证仍是你的职责**：AI 生成的电子表格包含公式——请核实，尤其是涉及客户或财务的内容。
