# Agent Handoff Kit

Agent Handoff Kit 是一个离线 CLI，用于把 Codex、Claude Code、Cursor、ChatGPT 等 AI coding agent 的一次工作整理成可审查、可继续接手的 handoff packet。它从 Markdown/JSON/YAML 输入、git diff 摘要、验证记录、风险说明、未完成事项中生成标准化交接包，支持质量门禁、secret/PII 基础扫描、redaction，以及 Markdown/JSON/continuation prompt 输出。

项目不需要 GitHub token，不调用远程服务，默认只使用 Python 标准库。测试依赖 `pytest`，仅用于开发和 CI。

## 适用场景

- AI coding agent 完成一段实现后，需要把上下文交给人类 reviewer。
- 团队希望让不同 agent 的工作交接格式保持一致。
- PR 前需要检查交接材料是否包含 owner、summary、validation、risks、next steps。
- 需要在分享交接文档前做基础 secret/PII 扫描和脱敏。
- 需要把一次未完成工作转换成可直接粘给 Codex、Claude Code 或 Cursor 的继续执行提示词。
- CI 中希望用 `--check` 阻止缺少关键交接信息的变更。

## 快速开始

```bash
python -m pip install -e ".[dev]"
agent-handoff-kit examples/handoff.md
agent-handoff-kit examples/handoff.json --format json
agent-handoff-kit examples/handoff.md --format prompt --output continuation-prompt.md
agent-handoff-kit examples/handoff.md --check --output handoff-report.md
pytest
```

安装后会得到命令：

```bash
agent-handoff-kit INPUT [--format markdown|json|prompt] [--output PATH] [--check]
```

如果不想安装，也可以在源码目录运行：

```bash
PYTHONPATH=src python -m agent_handoff_kit.cli examples/handoff.md --check
```

Windows PowerShell:

```powershell
$env:PYTHONPATH="src"
python -m agent_handoff_kit.cli examples/handoff.md --check
```

## 输入格式

### Markdown

Markdown 使用标题识别字段，标题大小写不敏感，也支持部分中文标题。

```markdown
# Owner
Platform Tools Team

# Summary
Implemented an offline CLI that creates reviewable AI coding agent handoff packets.

# Validation
- Ran `pytest`.

# Risks
- Redaction is pattern-based and should be reviewed.

# Next Steps
- Tune rules for the team's workflow.
```

支持字段：

- `owner` / `负责人`
- `summary` / `摘要`
- `context` / `背景`
- `changes` / `变更`
- `validation` / `验证`
- `risks` / `风险`
- `next steps` / `未完成事项` / `后续`
- `git diff` / `diff`

### JSON

```json
{
  "owner": "Platform Tools Team",
  "summary": "Implemented an offline CLI for standardized agent handoff packets.",
  "validation": ["pytest"],
  "risks": ["Pattern-based redaction is best effort."],
  "next_steps": ["Review generated packets before sharing."]
}
```

### YAML

YAML 支持一个保守子集：顶层 key、字符串 value、简单字符串列表。这样项目可以保持标准库优先，不强制引入 PyYAML。

```yaml
owner: Platform Tools Team
summary: Implemented an offline CLI for standardized agent handoff packets.
validation:
  - pytest
risks:
  - Pattern-based redaction is best effort.
next_steps:
  - Review generated packets before sharing.
```

## 规则配置

默认质量门禁要求：

- `owner`
- `summary`
- `validation`
- `risks`
- `next_steps`

默认规则还会检查 summary 最小长度，以及 validation、risks、next steps 的最少条目数。可以用 JSON/YAML 覆盖：

```yaml
required_fields:
  - owner
  - summary
  - validation
  - risks
  - next_steps
min_summary_chars: 30
min_validation_items: 1
min_risk_items: 1
min_next_step_items: 1
require_git_diff: false
fail_on_sensitive_findings: true
```

运行：

```bash
agent-handoff-kit examples/handoff.md --config examples/rules.yaml --check
```

如果只想扫描敏感信息但不让其导致 `--check` 失败，保持 `fail_on_sensitive_findings: false`。也可以临时使用：

```bash
agent-handoff-kit handoff.md --check --fail-on-sensitive
```

## Redaction 与敏感信息扫描

默认会扫描并脱敏报告输出中的常见敏感信息：

- Email
- 电话号码
- GitHub token 形态
- OpenAI API key 形态
- AWS access key 形态
- `api_key`、`token`、`secret`、`password` 等字段名相关的通用模式

如需扫描但保留原文输出：

```bash
agent-handoff-kit handoff.md --no-redact
```

注意：这是基础模式匹配，不是完整 DLP 系统。发布或外发前仍应人工检查。

## 输出示例

Markdown 输出：

```markdown
# Agent Handoff Packet

Status: PASS

## Owner
Platform Tools Team

## Quality Gate
- PASS: no quality issues found

## Sensitive Data Scan
- PASS: no sensitive data patterns found
```

JSON 输出：

```json
{
  "passed": true,
  "packet": {
    "owner": "Platform Tools Team",
    "summary": "Implemented an offline CLI for standardized agent handoff packets."
  },
  "rules": [],
  "findings": []
}
```

Continuation prompt 输出：

```bash
agent-handoff-kit examples/handoff.md --format prompt --output continuation-prompt.md
```

生成的 `continuation-prompt.md` 会包含：

- 当前目标、owner、背景和已完成变更。
- 已运行验证命令、已知风险和下一步行动。
- 质量门禁与敏感信息扫描结果。
- 给下一位 agent 的执行约束：先确认 worktree、保留用户改动、优先处理高风险未完成项、完成后更新交接包。

## CI 用法

GitHub Actions 示例已包含在 `.github/workflows/ci.yml`：

```yaml
- name: Install
  run: python -m pip install -e ".[dev]"
- name: Test
  run: pytest
- name: Example quality gate
  run: agent-handoff-kit examples/handoff.md --check --format json
- name: Build continuation prompt
  run: agent-handoff-kit examples/handoff.md --format prompt --output build/continuation-prompt.md
```

`--check` 退出码：

- `0`: 解析成功，质量门禁通过。
- `1`: 解析成功，但质量门禁失败。
- `2`: 输入文件、解析或配置错误。

## 限制

- YAML 只支持顶层 key 和简单字符串列表；复杂 YAML 请使用 JSON 或 Markdown。
- Redaction 基于正则表达式，可能漏报或误报。
- 质量规则关注交接完整性，不判断代码正确性。
- CLI 离线运行，不会读取远程仓库状态，也不会发布 GitHub 仓库。
- `--diff` 接收 diff 文件内容；如果需要实时 diff，请在外部运行 `git diff > diff.txt` 后传入。

## 维护说明

- 保持 `src/agent_handoff_kit` 中模块职责清晰：解析、规则、脱敏、渲染、CLI 分离。
- 新增规则时同步更新 README、示例配置和测试。
- 新增敏感信息模式时添加 redaction 测试，并避免在测试数据中放真实 secret。
- 发布前运行 `pytest` 和 `agent-handoff-kit examples/handoff.md --check`。
- 依赖策略是标准库优先；引入依赖前需要说明价值和安全影响。

---

## English

Agent Handoff Kit is an offline CLI for turning work from AI coding agents such as Codex, Claude Code, Cursor, and ChatGPT into a reviewable handoff packet that another developer can continue from. It reads Markdown/JSON/simple YAML inputs, optional git diff summaries, validation notes, risks, and next steps, then produces standardized Markdown, JSON, or agent-ready continuation prompts with quality gates, basic secret/PII scanning, and redaction.

It does not require a GitHub token, does not call remote services, and has no runtime dependencies outside the Python standard library. `pytest` is used only for development and CI.

## Use Cases

- Hand off completed AI coding work to a human reviewer.
- Normalize handoff output across different coding agents and teams.
- Require owner, summary, validation, risks, and next steps before PR review.
- Run a basic secret/PII scan before sharing handoff notes.
- Convert unfinished work into a prompt that the next Codex, Claude Code, Cursor, or ChatGPT session can continue from.
- Enforce handoff completeness in CI with `--check`.

## Quick Start

```bash
python -m pip install -e ".[dev]"
agent-handoff-kit examples/handoff.md
agent-handoff-kit examples/handoff.json --format json
agent-handoff-kit examples/handoff.md --format prompt --output continuation-prompt.md
agent-handoff-kit examples/handoff.md --check --output handoff-report.md
pytest
```

Installed command:

```bash
agent-handoff-kit INPUT [--format markdown|json|prompt] [--output PATH] [--check]
```

Run from source without installation:

```bash
PYTHONPATH=src python -m agent_handoff_kit.cli examples/handoff.md --check
```

## Input Formats

Markdown inputs use headings as fields. JSON inputs use the same normalized field names. YAML support is intentionally limited to top-level keys and simple string lists so the project can stay standard-library first.

Supported fields:

- `owner`
- `summary`
- `context`
- `changes`
- `validation`
- `risks`
- `next_steps`
- `git_diff`

Example JSON:

```json
{
  "owner": "Platform Tools Team",
  "summary": "Implemented an offline CLI for standardized agent handoff packets.",
  "validation": ["pytest"],
  "risks": ["Pattern-based redaction is best effort."],
  "next_steps": ["Review generated packets before sharing."]
}
```

## Rule Configuration

Default gates require `owner`, `summary`, `validation`, `risks`, and `next_steps`. You can override them with JSON or simple YAML:

```yaml
required_fields:
  - owner
  - summary
  - validation
  - risks
  - next_steps
min_summary_chars: 30
min_validation_items: 1
min_risk_items: 1
min_next_step_items: 1
require_git_diff: false
fail_on_sensitive_findings: true
```

Run with:

```bash
agent-handoff-kit examples/handoff.md --config examples/rules.yaml --check
```

## Output Examples

Markdown reports include normalized handoff sections, quality gate results, and sensitive-data scan results. JSON reports contain `passed`, `packet`, `rules`, and `findings` keys for automation. Prompt reports are written as continuation prompts for the next agent session, including objective, context, completed changes, validation already run, known risks, next actions, gate findings, and explicit working instructions.

```bash
agent-handoff-kit examples/handoff.md --format markdown
agent-handoff-kit examples/handoff.md --format json
agent-handoff-kit examples/handoff.md --format prompt --output continuation-prompt.md
```

## CI Usage

Use `--check` to fail builds when required handoff information is missing:

```yaml
- name: Install
  run: python -m pip install -e ".[dev]"
- name: Test
  run: pytest
- name: Example quality gate
  run: agent-handoff-kit examples/handoff.md --check --format json
- name: Build continuation prompt
  run: agent-handoff-kit examples/handoff.md --format prompt --output build/continuation-prompt.md
```

Exit codes:

- `0`: parsed successfully and quality gates passed.
- `1`: parsed successfully but quality gates failed.
- `2`: file, parse, or config error.

## Limitations

- Simple YAML support is deliberately limited.
- Redaction is regex-based and may miss or misclassify sensitive data.
- Quality gates check handoff completeness, not code correctness.
- The CLI is offline and does not publish or inspect remote repositories.
- Use `git diff > diff.txt` externally, then pass `--diff diff.txt` when needed.

## Maintenance

- Keep parsing, rules, redaction, rendering, and CLI modules separated.
- Update tests, examples, and README whenever behavior changes.
- Avoid committing real secrets in tests or examples.
- Run `pytest` and `agent-handoff-kit examples/handoff.md --check` before release.
- Prefer the Python standard library unless a dependency has a clear benefit.
