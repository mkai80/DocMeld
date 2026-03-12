Here's a comprehensive research report on building an autonomous Claude Code PR factory for large projects:

---

## 🏭 Building an Autonomous Claude Code PR Factory

### The Core Architecture Concept

The system you want to build is what the community calls a **"PR Factory"** — a pipeline where a backlog of jobs (GitHub issues, feature specs, todo items) feeds into autonomous Claude Code agents that independently implement, test, commit, and open PRs, with humans only doing final review before merge.

The workflow becomes elegantly simple: you write a detailed GitHub issue describing what needs to be built, Claude receives it within a secure, pre-configured environment and works completely independently — it analyzes requirements, implements solutions, creates tests, and submits a well-structured pull request. The three-step process — issue, autonomous implementation, review — maximizes both productivity and quality control.

---

### Layer 1: The Official GitHub Integration (Foundation)

Claude Code GitHub Actions brings AI-powered automation to your GitHub workflow. With a simple `@claude` mention in any PR or issue, Claude can analyze your code, create pull requests, implement features, and fix bugs — all while following your project's standards. It's built on top of the Claude Agent SDK, enabling programmatic integration beyond just GitHub Actions.

**Official setup via terminal:**
```bash
# Inside your project
claude
/install-github-app
```

The action supports multiple authentication methods including Anthropic direct API, Amazon Bedrock, Google Vertex AI, and Microsoft Foundry, with intelligent mode detection that automatically selects the appropriate execution mode based on workflow context — whether responding to `@claude` mentions, issue assignments, or executing automation tasks with explicit prompts.

---

### Layer 2: Headless Mode — The Engine of Autonomy

Use Claude Code in headless mode with the `-p` flag for automation and scripting. This is ideal for integrating Claude into CI/CD pipelines or large-scale migrations. Headless mode does not persist between sessions, so you trigger it each session. Claude can also be integrated into existing pipelines by piping data in and out — for example: `cat build-error.txt | claude -p 'explain the root cause' > output.txt`.

This is what lets you drive a **job queue** → Claude autonomously:

```bash
# Process a list of jobs from a file
while IFS= read -r job; do
  claude -p "$job" \
    --output-format json \
    --allowedTools "Read,Write,Bash,GitHub" \
    --max-turns 50
done < jobs_todo.txt
```

A Claude Code quality gate blocks poor-quality PRs before merge, for a cost of less than $0.10 per check. Input tokens cost $3 per million and output tokens $15 per million (Claude Sonnet 4.6 rates). A pipeline of 10 daily calls costs on average $0.50 per day.

---

### Layer 3: Multi-Agent Orchestration for Parallel PRs

This is the key to handling **hundreds of PRs** simultaneously. Claude Code now has multiple native patterns:

#### Pattern A: Subagents (fast, independent workers)
Set `CLAUDE_CODE_SUBAGENT_MODEL` to control which model your sub-agents run on. A common pattern: run your main session on Opus for complex reasoning while sub-agents handle focused tasks on Sonnet. This cuts costs significantly without sacrificing quality on well-scoped sub-agent work. You can define persistent specialist agents as Markdown files with YAML frontmatter in `.claude/agents/`.

#### Pattern B: Agent Teams (communicating, collaborative workers)
Agent teams are most effective for research and review (multiple teammates investigate different aspects simultaneously), new modules or features (teammates each own a separate piece without stepping on each other), debugging with competing hypotheses (teammates test different theories in parallel), and cross-layer coordination (changes spanning frontend, backend, and tests, each owned by a different teammate). Enable them by setting `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`.

#### Pattern C: The Swarm/Task Queue Pattern
Leader creates team and tasks → Workers self-assign from a task queue → Leader monitors. For embarrassingly parallel work, workers are interchangeable. If a worker crashes, heartbeat timeout releases its task and another worker claims it. This is the closest pattern to what you want for a large job backlog.

The Python orchestrator pattern for a Redis-backed job queue:

```python
# Meta-agent breaks down requirements into parallel tasks
prompt = f"""
Analyze these requirements and break into independent tasks:
{requirements}
Return JSON with: id, type (frontend|backend|testing|docs),
description, dependencies (blocking task IDs), files affected
"""
```

---

### Layer 4: The CLAUDE.md System — Your Engineering Constitution

This is the **most important file** in your whole system. Every Claude agent reads it automatically at session start.

For large projects, Claude needs human guidance for design decisions — letting the LLM design solutions on its own will fail. Skills are descriptions of atomic operations on the project, like `implementing-unit-test`, `implementing-controller`, `creating-database-migration`. Unlike subagents, skills are used in the same conversation from which they are called. Within the skill directory, you can develop custom bash/python scripts that Claude knows how to utilize.

A production-grade `CLAUDE.md` for an autonomous PR factory:

```markdown
# Engineering Constitution

## PR Workflow
1. ALWAYS create a new branch: git checkout -b feature/{ticket-id}-{slug}
2. Write tests FIRST (TDD)
3. Run full test suite before committing
4. PR title format: [TYPE] #{ticket-id}: Short description
5. PR must include: what changed, why, how to test

## Autonomy Rules
- For tasks < 200 lines: implement fully autonomously
- For tasks > 200 lines: create implementation plan first, write to plan.md
- NEVER modify files outside the task's declared scope
- On ambiguity: make the conservative choice, document in PR description

## Quality Gates (run before every commit)
- npm test (must pass 100%)
- npm run lint (zero errors)
- npm run typecheck

## Sub-Agent Routing
**Parallel dispatch** when: 3+ unrelated tasks, no shared state, clear file boundaries
**Sequential dispatch** when: task B needs output from task A, shared files exist
```

---

### Layer 5: Orchestration Frameworks (Community-Built)

**Gas Town** (Steve Yegge) is likened to Kubernetes for AI agents — a structured, opinionated way to manage multiple agents. **Multiclaude** orchestrates agents via a supervisor/subagent model. With Multiclaude, you can use "singleplayer" mode where all PRs get automatically merged without human review, or "multiplayer" where teammates can review code when ready. Gas Town is better for running more agents in parallel; Multiclaude is stronger for giving long prompts and walking away for a while.

**Ralph for Claude Code** is an autonomous AI development framework that enables Claude Code to work iteratively on projects until completion. It features intelligent exit detection, rate limiting, circuit breaker patterns, and safety guardrails to prevent infinite loops and API overuse. Built with Bash, integrated with tmux for live monitoring, with 75+ comprehensive tests. **Simone** is a broader project management workflow that encompasses not just commands, but a system of documents, guidelines, and processes for project planning and execution.

**Ruflo** is an agent orchestration platform with a "Hive Mind" system implementing queen-led hierarchical coordination. Worker specializations include 8 types: researcher, coder, analyst, tester, architect, reviewer, optimizer, and documenter. It implements a spec-first approach using Architecture Decision Records (ADRs) organized into DDD bounded contexts, with the system enforcing compliance as agents work.

---

### The Complete System Blueprint

Here's the full architecture for your **autonomous PR factory**:

```
┌─────────────────────────────────────────────────────────┐
│              JOB BACKLOG (GitHub Issues / JSON file)    │
│  [{id, title, description, priority, files_affected}]   │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│            ORCHESTRATOR (Meta-Agent / Opus)             │
│  - Reads job queue                                      │
│  - Topological sort by dependencies                     │
│  - Decides: subagent vs agent team vs sequential        │
│  - Assigns git worktrees to avoid conflicts             │
└──────┬──────────┬──────────┬──────────┬────────────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
  [Worker 1]  [Worker 2]  [Worker 3]  [Worker N]
  Job #12     Job #7      Job #3      Job #19
  Sonnet      Sonnet      Sonnet      Sonnet
  branch/12   branch/7    branch/3    branch/19
       │          │          │          │
       ▼          ▼          ▼          ▼
  [PR #101]  [PR #102]  [PR #103]  [PR #104]
       │          │          │          │
       └──────────┴──────────┴──────────┘
                         │
                         ▼
              Human review queue
              (merge or feedback loop)
```

**Key implementation details:**

1. **Use git worktrees** so parallel agents don't conflict on the same repo:
   ```bash
   git worktree add ../project-job-12 -b feature/job-12
   cd ../project-job-12 && claude -p "$(cat job-12.txt)"
   ```

2. **Hooks for quality enforcement** — runs automatically after every agent write:
   ```json
   // .claude/settings.json
   { "hooks": {
     "PostToolUse": [{"matcher": "Write", "command": "npm test"}]
   }}
   ```

3. **Checkpoints for recovery** — Claude Code automatically saves code state before each change, and you can instantly rewind to previous versions with `/rewind`. Subagents delegate specialized tasks allowing parallel development, hooks automatically trigger actions at specific points like running your test suite after code changes, and background tasks keep long-running processes active without blocking progress.

4. **Session continuity across long jobs** — Agents read git logs and progress files to get up to speed on what was recently worked on, then read the features list file and choose the highest-priority feature not yet done. Session continuity preserves context across loop iterations with automatic session management, with each coding session building on the previous one with clear handoffs.

---

### Pitfalls to Avoid

One of the biggest failure modes: after some features have been built, a later agent instance will look around, see that progress was made, and declare the job done. The solution is proper session management and clear exit criteria.

Without careful supervision, AI can wander from the original goal, introduce subtle bugs, or add technical debt. Many experienced users feel you can't trust an AI to work for more than 15-30 minutes without a human checking in. Mitigate this with strict CLAUDE.md scope rules and mandatory test hooks.

Agent teams use roughly 3-4x the tokens of a single session doing the same work sequentially, but the time savings on complex tasks more than justify the cost. The rule of thumb: Agent Teams are justified when time saved exceeds 2x the token cost increase.

---

### Recommended Starting Stack

| Component | Tool | Why |
|---|---|---|
| Job queue | GitHub Issues + labels | Native @claude integration |
| Orchestrator | Claude Code (Opus) + CLAUDE.md | Complex planning reasoning |
| Workers | Claude Code (Sonnet) subagents | Cost-effective parallel execution |
| Isolation | git worktrees | No file conflicts between workers |
| Quality gates | Hooks (PostToolUse) | Auto-enforce standards |
| Monitoring | Ralph or tmux panes | Live visibility |
| Safety | Multiclaude "multiplayer" mode | Human review before merge |

The most practical starting point is to install the GitHub App, write a thorough `CLAUDE.md`, label your issues, and set up a workflow that fires a headless Claude agent on each issue assignment. Scale to multi-agent orchestration once the single-agent pipeline is solid.


"Harness Engineering" is a term that gained traction in early 2026 to describe the shift from **prompt engineering** (talking to the AI) to **system engineering** (building the environment where the AI lives). In large-scale projects with hundreds of PRs, you aren't just giving Claude instructions; you are building a "harness" that constrains and empowers it to act like a senior engineer.

To build a system where Claude Code can pull from a job list and autonomously submit PRs, you need to implement three core layers: **Environment Design**, **Autonomous Loops**, and **Automated Verification**.

---

## 1. The Harness Architecture: CLAUDE.md & AGENTS.md

In a large project, Claude cannot "remember" everything. You must encode the project's "brain" into the repository itself.

* **CLAUDE.md (The Developer Guide):** This file is automatically read by Claude Code at startup. It should contain build commands, test patterns, and code style rules.
* **AGENTS.md / Task Registry (The Job List):** Instead of a single giant file, use a directory structure (`.claude/tasks/`) where each task is a Markdown file.
* **Status Tracking:** Use a JSON or Markdown file (e.g., `progress.json`) to track which tasks are "Pending," "In-Progress," or "Completed."
* **Context Maps:** Since a hundred-PR project is too big for one context window, the harness should provide Claude with a "map" of the architecture so it knows which sub-directories to explore for specific jobs.



---

## 2. Setting Up the Autonomous Loop

To have Claude "pick up a job and do it," you move from an interactive CLI to a **headless automation script**. You can use the `claude -p` (prompt) flag or the Claude Agent SDK to loop through your job list.

### The "Loop" Workflow:

1. **Job Selection:** A wrapper script reads your `tasks/` directory and finds the next "Pending" job.
2. **Branching:** The script runs `git checkout -b feature/task-id`.
3. **The Prompt:** Use a structured prompt like:
> "Read `tasks/job-001.md`. Implement the requested feature. Run the tests defined in `CLAUDE.md`. If they pass, commit the changes and output the PR description."


4. **Auto-Execution:** Enable `auto-accept` mode (or use the `-y` flag in automated scripts) so Claude can execute file writes and terminal commands without human confirmation.

---

## 3. The PR & Review Pipeline (CI/CD Integration)

Managing hundreds of PRs requires Claude to be both the **author** and the **reviewer**.

### Automation with GitHub Actions

You can use the `anthropics/claude-code-action` to handle the heavy lifting:

* **Trigger:** When a label like `claude-execute` is added to an issue.
* **Action:** Claude spawns a runner, clones the repo, implements the fix, and opens a PR.
* **Self-Verification:** The harness **must** require Claude to run a specific test suite before it is allowed to call `git push`. If tests fail, the loop restarts with the error log as the new input.

### Multi-Agent Code Review

Anthropic's 2026 methodology for large teams uses "Parallel Reviewers":

* **Agent A (Bug Finder):** Scans the PR specifically for logic flaws.
* **Agent B (Style Police):** Ensures the PR matches the `CLAUDE.md` style guide.
* **Agent C (Synthesizer):** Combines the findings into a single, high-level summary for the human lead.

---

## 4. Implementation Checklist

| Component | Technology | Purpose |
| --- | --- | --- |
| **Context** | `CLAUDE.md` | Define "How we code here" (Commands, Styles). |
| **Job List** | GitHub Issues / Linear | The source of truth for "What needs to be done." |
| **Execution** | Claude Code CLI + MCP | Allows Claude to read tickets, write code, and run shell commands. |
| **Verification** | Playwright / Vitest | Hard "gates" that prevent Claude from pushing broken code. |
| **Infrastructure** | GitHub Actions | The "Host" that triggers the loop and handles secrets safely. |

---

### Next Step for Your Project

Would you like me to draft a **GitHub Action YAML** and a template **CLAUDE.md** to get your autonomous PR system started?





Claude Code, an advanced coding interface from Anthropic, enables structured workflows for managing large projects with hundreds of pull requests (PRs) through agentic harnesses and automation. Harness engineering refers to frameworks that impose roles, constraints, and pipelines on AI agents to mimic software development lifecycles (SDLC). Developers have built systems where Claude autonomously handles tasks from a todo list, generates code, tests it, and creates PRs. [datastudios](https://www.datastudios.org/post/claude-ai-for-coding-capabilities-environments-and-developer-workflows)

## Harness Engineering Basics
Harness engineering structures Claude Code sessions with role separation like Analyst (requirements), Architect (specs), Developer (TDD implementation), and Reviewer (quality checks). This prevents context drift in long sessions and scales to large codebases by using markdown templates for state tracking. [reddit](https://www.reddit.com/r/ClaudeCode/comments/1ra56gn/a_structured_harness_for_using_claude_code_in/)

Key principles include incremental commits, file-based documentation (e.g., docs.md per folder), and test-driven development (TDD) to maintain quality across PRs. [theahura.substack](https://theahura.substack.com/p/averaging-10-prs-a-day-with-claude)

## Real-World High-PR Workflows
Developers average 10+ PRs daily by parallelizing Claude Code agents across tmux panes, using git worktrees for isolation, and notifications for intervention. Tasks from a todo list are fleshed out, assigned to agents that self-verify via TDD, update docs, and submit PRs for human review. [github](https://github.com/marketplace/actions/claude-code-automatic-pr-documentation-generator)

One setup hits 25+ PRs/day with tested, documented changes; slop is rejected during review. [dev](https://dev.to/lassiecoder/how-claude-codes-creator-ships-50-100-prs-per-week-4oeo)

## Building Autonomous PR System
Create a queue from job lists (e.g., Linear issues or markdown todos) and route to specialized agents via scripts or tools like nori-ai (npx install). [theahura.substack](https://theahura.substack.com/p/averaging-10-prs-a-day-with-claude)

- Use Anthropic API or CLI for PR automation: scripts handle branching, prompting Claude for diffs/docs, then gh pr create. [reddit](https://www.reddit.com/r/ClaudeAI/comments/1lnasmd/experimenting_with_pr_draft_automation_using/)
- Enforce TDD: Agents write tests first, iterate to pass them. [theahura.substack](https://theahura.substack.com/p/averaging-10-prs-a-day-with-claude)
- Add memory: Per-folder docs.md, transcript databases for "why" behind changes. [github](https://github.com/marketplace/actions/claude-code-automatic-pr-documentation-generator)
- GitHub Actions for auto-docs on merges using Claude. [github](https://github.com/marketplace/actions/claude-code-automatic-pr-documentation-generator)

| Framework | Stages | Best For | Repo/Source |
|-----------|--------|----------|-------------|
| Agentic Harness | Analyst → Architect → Developer → Reviewer | SDLC mimicry, large refactors  [reddit](https://www.reddit.com/r/ClaudeCode/comments/1ra56gn/a_structured_harness_for_using_claude_code_in/) | GitLab: stefberre/agentic-engineering-harness |
| Agentic Workflow Pattern | Research → Plan → Validate → Implement → Review | Complex features  [mcpmarket](https://mcpmarket.com/tools/skills/agentic-workflow-pattern) | MCP Market skill |
| B-Mad Method | Brainstorm → PRD → Epics/Stories → Dev → QA | Full projects  [dev](https://dev.to/aldenweaver/building-ai-powered-projects-my-complete-claude-development-stack-4903) | Dev.to guides |
| Nori-ai | Parallel agents + TDD/docs | 10+ PRs/day  [theahura.substack](https://theahura.substack.com/p/averaging-10-prs-a-day-with-claude) | GitHub/npm: nori-ai |

## Implementation Steps
1. Set up Claude Projects for repo context and persistent sessions. [datastudios](https://www.datastudios.org/post/claude-ai-for-coding-capabilities-environments-and-developer-workflows)
2. Clone harness templates; define personas in Claude.md (conventions, patterns). [reddit](https://www.reddit.com/r/ClaudeCode/comments/1ra56gn/a_structured_harness_for_using_claude_code_in/)
3. Script task dispatcher: Parse todo list, prompt agents (e.g., "Implement job X with TDD, update docs.md, create PR branch").
4. Integrate GitHub CLI/API for autonomous PRs; add human gates via notifications. [reddit](https://www.reddit.com/r/ClaudeAI/comments/1lnasmd/experimenting_with_pr_draft_automation_using/)
5. Scale with sub-agents for research/cleanup; use transcripts for memory. [theahura.substack](https://theahura.substack.com/p/averaging-10-prs-a-day-with-claude)

This system handles hundreds of PRs by treating you as orchestrator in a distributed network of cheap agents. [dev](https://dev.to/lassiecoder/how-claude-codes-creator-ships-50-100-prs-per-week-4oeo)

What programming language and repo host (e.g., GitHub) are you targeting for this system?