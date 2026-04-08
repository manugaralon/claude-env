#!/usr/bin/env bash
# claude-env setup — personalizes the environment for a new user
set -euo pipefail

CORE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/core" && pwd)"
INSTALL_DIR="${HOME}/.claude"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║         claude-env setup                 ║"
echo "║  Personalized Claude Code environment    ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ─── Gather identity ─────────────────────────────────────────────────────────

read -rp "Your name: " YOUR_NAME
read -rp "Your role (e.g. 'Senior backend engineer', 'ML researcher'): " YOUR_ROLE
read -rp "Technical level (e.g. 'senior', 'mid-level', 'student'): " YOUR_TECH_LEVEL
read -rp "Primary OS (e.g. 'Linux', 'macOS', 'Windows'): " YOUR_OS
read -rp "Conversation language (e.g. 'Spanish', 'English', 'French'): " YOUR_LANGUAGE

echo ""
echo "── Stack ────────────────────────────────────────────────"
read -rp "Frontend (e.g. 'React + Vite + TypeScript + Tailwind v4', or leave blank): " STACK_FRONTEND
read -rp "Backend/DB (e.g. 'Supabase (PostgreSQL + Auth + RLS)', or leave blank): " STACK_BACKEND
read -rp "Deploy (e.g. 'Vercel', 'AWS', or leave blank): " STACK_DEPLOY
read -rp "Testing (e.g. 'Vitest / pytest + real services — no mocks'): " STACK_TESTING
read -rp "Python version (e.g. '3.12+ with Pydantic v2', or leave blank): " STACK_PYTHON

echo ""
echo "── Projects ─────────────────────────────────────────────"
read -rp "Active project 1 name: " PROJECT_1
read -rp "Active project 1 description: " PROJECT_1_DESC
read -rp "Active project 2 name (optional, press Enter to skip): " PROJECT_2
read -rp "Active project 2 description (optional): " PROJECT_2_DESC

# ─── Build stack string ───────────────────────────────────────────────────────

STACK_LINES=""
[[ -n "$STACK_FRONTEND" ]] && STACK_LINES+="- **Frontend:** ${STACK_FRONTEND}\n"
[[ -n "$STACK_BACKEND" ]]  && STACK_LINES+="- **Backend/DB:** ${STACK_BACKEND}\n"
[[ -n "$STACK_DEPLOY" ]]   && STACK_LINES+="- **Deploy:** ${STACK_DEPLOY}\n"
[[ -n "$STACK_TESTING" ]]  && STACK_LINES+="- **Testing:** ${STACK_TESTING}\n"
[[ -n "$STACK_PYTHON" ]]   && STACK_LINES+="- **Python:** ${STACK_PYTHON}\n"

if [[ -z "$STACK_LINES" ]]; then
    YOUR_STACK="*(define your default stack here)*"
else
    YOUR_STACK="$(printf '%b' "$STACK_LINES")"
fi

# ─── Build projects string ────────────────────────────────────────────────────

YOUR_PROJECTS_CONTEXT="Currently working on:"$'\n'"- **${PROJECT_1}** — ${PROJECT_1_DESC}"
[[ -n "$PROJECT_2" ]] && YOUR_PROJECTS_CONTEXT+=$'\n'"- **${PROJECT_2}** — ${PROJECT_2_DESC}"

# ─── Build testing preference ─────────────────────────────────────────────────

YOUR_TESTING_PREFERENCE="${STACK_TESTING:-No test mocks — use real services}"

# ─── Ensure install dir ───────────────────────────────────────────────────────

mkdir -p "$INSTALL_DIR"

# ─── Generate CLAUDE.md ───────────────────────────────────────────────────────

CLAUDE_OUT="${INSTALL_DIR}/CLAUDE.md"

if [[ -f "$CLAUDE_OUT" ]]; then
    echo ""
    read -rp "~/.claude/CLAUDE.md already exists. Overwrite? [y/N] " OVERWRITE
    [[ "${OVERWRITE,,}" != "y" ]] && echo "Skipping CLAUDE.md." && SKIP_CLAUDE=1
fi

if [[ -z "${SKIP_CLAUDE:-}" ]]; then
    sed \
        -e "s|{{YOUR_NAME}}|${YOUR_NAME}|g" \
        -e "s|{{YOUR_ROLE}}|${YOUR_ROLE}|g" \
        -e "s|{{YOUR_LANGUAGE}}|${YOUR_LANGUAGE}|g" \
        -e "s|{{YOUR_PROJECTS_CONTEXT}}|${YOUR_PROJECTS_CONTEXT}|g" \
        "${CORE_DIR}/CLAUDE.md.template" > "$CLAUDE_OUT"

    # Stack is multiline — use python for safe replacement
    python3 - <<PYEOF
import re, sys
path = "${CLAUDE_OUT}"
content = open(path).read()
stack = """${YOUR_STACK}"""
content = content.replace("{{YOUR_STACK}}", stack)
open(path, 'w').write(content)
PYEOF

    echo "✅ CLAUDE.md → ${CLAUDE_OUT}"
fi

# ─── Generate lessons.md ──────────────────────────────────────────────────────

LESSONS_OUT="${INSTALL_DIR}/lessons.md"

if [[ ! -f "$LESSONS_OUT" ]]; then
    cp "${CORE_DIR}/lessons.md.template" "$LESSONS_OUT"
    echo "✅ lessons.md → ${LESSONS_OUT}"
else
    echo "⏭  lessons.md already exists — skipping (preserving your history)"
fi

# ─── Generate memory.md ───────────────────────────────────────────────────────

MEMORY_OUT="${INSTALL_DIR}/memory.md"

if [[ ! -f "$MEMORY_OUT" ]]; then
    sed \
        -e "s|{{YOUR_NAME}}|${YOUR_NAME}|g" \
        -e "s|{{YOUR_ROLE}}|${YOUR_ROLE}|g" \
        -e "s|{{YOUR_TECH_LEVEL}}|${YOUR_TECH_LEVEL}|g" \
        -e "s|{{YOUR_OS}}|${YOUR_OS}|g" \
        -e "s|{{PROJECT_1}}|${PROJECT_1}|g" \
        -e "s|{{PROJECT_1_DESCRIPTION}}|${PROJECT_1_DESC}|g" \
        -e "s|{{PROJECT_2}}|${PROJECT_2:-_none_}|g" \
        -e "s|{{PROJECT_2_DESCRIPTION}}|${PROJECT_2_DESC:-}|g" \
        -e "s|{{YOUR_TESTING_PREFERENCE}}|${YOUR_TESTING_PREFERENCE}|g" \
        "${CORE_DIR}/memory.md.template" > "$MEMORY_OUT"
    echo "✅ memory.md → ${MEMORY_OUT}"
else
    echo "⏭  memory.md already exists — skipping (preserving your profile)"
fi

# ─── Done ─────────────────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  Setup complete. Next steps:             ║"
echo "║  1. Review ~/.claude/CLAUDE.md           ║"
echo "║  2. Set GROQ_API_KEY in your shell       ║"
echo "║  3. Install pipeline deps:               ║"
echo "║     pip install -r pipeline/requirements.txt ║"
echo "║  4. Run the pipeline:                    ║"
echo "║     python3 pipeline/transcribe.py --help ║"
echo "╚══════════════════════════════════════════╝"
echo ""
