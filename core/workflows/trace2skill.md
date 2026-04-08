# Trace2Skill — Build skills from real execution traces

Source: [Trace2Skill paper](https://arxiv.org/pdf/2603.25158) (Alibaba Qwen team) + [buildthisnow.com](https://www.buildthisnow.com/blog/trace-to-skill)

Skills built from real execution traces consistently beat hand-written ones. A 35B model with evolved skills outperformed a 122B model using a human-written skill on hard benchmarks.

---

## When to use this

When you have a task you'll run repeatedly and it has specific failure modes. Not worth it for one-offs.

---

## 4 steps

### 1. Generate 20 task variations

```
Generate 20 variations of this task for a Claude Code agent:

Task: [your task]

- 5 easy, straightforward versions
- 8 normal versions
- 4 hard versions with tricky edge cases
- 3 adversarial versions designed to break the agent

Output: a numbered list. Each item is a complete, self-contained task prompt.
```

Then run them:

```bash
claude -p "[variation 1]"
claude -p "[variation 2]"
# repeat for all 20
```

Sessions are saved automatically to `~/.claude/projects/[your-project]/`.

### 2. Write your feedback

Look at the output of each run. One sentence per run. 10-15 minutes total.

```
Run 1: good
Run 2: bad — too many cards, looks cluttered
Run 3: good
...
```

You judge the output. The agents read the traces. That's the split.

### 3. Spawn 4 analysts in parallel

```
Run these 4 agents in parallel. Give each the same context.

Task: [your task description]
Project slug: [your-project]

My feedback:
Run 1: good
Run 2: bad — [reason]
[... all 20]

Agents to run:
- error-analyst
- success-analyst
- structure-analyst
- edge-analyst
```

Each agent reads the session files and extracts rules from a different angle.

### 4. Merge into SKILL.md

```
Merge these 4 analyst outputs into a single SKILL.md.

Task: [your task]
Existing SKILL.md: [paste or "none"]

[paste all 4 analyst outputs]

Merging rules:
- Merge rules that say the same thing
- When two rules conflict, keep the one with more run evidence
- 8+ runs: core rule (main SKILL.md)
- 4-7 runs: guidance (main SKILL.md, secondary section)
- 2-3 runs: edge case (references/ subfolder)
- 1 run: discard
- Max 30 rules in the main file
```

---

## Output structure

```
.claude/
  agents/
    error-analyst.md
    success-analyst.md
    structure-analyst.md
    edge-analyst.md
  skills/
    [your-task]/
      SKILL.md
      references/
        edge-cases.md
```

---

## SKILL.md format

```markdown
# [Task name]

## When to use this skill
[one short paragraph]

## Core rules
[numbered list — from 8+ run evidence]

## Patterns
[bullet points — from 4-7 run evidence]

## Failure modes
["If X, do Y" format]
```
