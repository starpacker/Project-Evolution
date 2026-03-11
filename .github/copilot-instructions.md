# Copilot Workspace Instructions

## Agent-Driven Workflow

This workspace has **two orchestration systems** — choose based on complexity:

### Option A: RUG (Repeat Until Good) — Lightweight orchestration
1. **User submits a request** to `@RUG`
2. **RUG decomposes** → delegates to `SWE` and `QA` subagents → validates → repeats until done

### Option B: Gem Team — Full project orchestration with DAG-based planning
1. **User submits a request** to `@gem-orchestrator`
2. **gem-orchestrator** runs 4 phases: Research → Planning → Execution → Summary
3. Uses structured `plan.yaml` with wave-based parallel execution

## Available Agents

### 🎯 Orchestrators (pick ONE for complex tasks)
| Agent | Best For |
|-------|----------|
| `RUG` | Quick orchestration — decompose, delegate to SWE/QA, validate, repeat |
| `gem-orchestrator` | Full project orchestration — research → plan → implement → review → document |

### 💻 Implementation Agents
| Agent | Best For |
|-------|----------|
| `SWE` | Senior software engineer — feature development, debugging, refactoring, testing (from awesome-copilot RUG plugin) |
| `gem-implementer` | TDD implementation — write tests first, minimal code to pass, verify (from awesome-copilot gem-team plugin) |
| `Thinking Beast Mode` | Deep autonomous problem-solving requiring extensive research and creative solutions |

### 🔍 Research & Planning Agents
| Agent | Best For |
|-------|----------|
| `gem-researcher` | Codebase analysis — multi-pass hybrid retrieval, structured YAML findings (from awesome-copilot gem-team plugin) |
| `gem-planner` | DAG-based planning — task decomposition, pre-mortem analysis, wave assignment (from awesome-copilot gem-team plugin) |
| `Context Architect` | Dependency mapping, planning multi-file changes, architecture diagrams |

### ✅ Quality & Review Agents
| Agent | Best For |
|-------|----------|
| `QA` | Test planning, test writing, bug hunting, edge-case analysis |
| `gem-reviewer` | Security review — OWASP Top 10, secrets detection, PRD compliance (from awesome-copilot gem-team plugin) |
| `Debug Mode Instructions` | Systematic debugging — reproduce, hypothesize, fix, verify |

### 🧠 Thinking & Analysis Agents
| Agent | Best For |
|-------|----------|
| `Critical thinking mode instructions` | Challenging assumptions, probing reasoning, finding logical flaws |
| `Prompt Engineer` | Analyzing and improving prompts and instructions |

### 📚 Documentation Agent
| Agent | Best For |
|-------|----------|
| `gem-documentation-writer` | Technical docs, diagrams, code-documentation parity (from awesome-copilot gem-team plugin) |

## When to Use Which Agent

- **Simple coding task** → `@SWE` or direct chat
- **Complex multi-step project** → `@RUG` (lightweight) or `@gem-orchestrator` (full planning)
- **"I'm stuck on a bug"** → `@Debug Mode Instructions`
- **"Review my code for security"** → `@gem-reviewer`
- **"Is this approach correct?"** → `@Critical thinking mode instructions`
- **"Research this codebase"** → `@gem-researcher`
- **"Write docs for this"** → `@gem-documentation-writer`

## Project Context

This workspace contains Python-based data analysis and visualization scripts, primarily for scientific research (benchmark analysis, model comparison, correlation studies). Key tools: Python 3.10+, conda environments, Jupyter notebooks, matplotlib, pandas, numpy, scipy.

