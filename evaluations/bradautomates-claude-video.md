---
source: https://github.com/bradautomates/claude-video
type: github-repo
evaluated_date: 2026-06-08
verdict: cherry-pick
tags: [video, multimodal, claude-skill, ffmpeg, whisper]
extracts: [/watch skill — visual frame analysis]
revisit_after:
---

# bradautomates/claude-video

**Summary**: Claude Code plugin providing a `/watch` skill (~1.9k stars, MIT). Paste a video URL/path + a question; it downloads via yt-dlp, extracts frames with ffmpeg at adaptive fps (30 for ≤30s, up to 100 for long video), pulls native captions or Whisper-transcribes, and hands frames as images + a timestamped transcript to Claude's multimodal Read. Install: `/plugin marketplace add bradautomates/claude-video` + `/plugin install watch@claude-video`. Reuses the existing `GROQ_API_KEY`.

## Why this verdict
cherry-pick — adds the ONE thing Manuel's own `claude_env/capture.py` lacks: **visual frame analysis** (on-screen text, UI, slides, motion) and **in-agent conversational** usage. Audio transcription is already solved by capture.py (same Groq Whisper-large-v3 stack). Add the plugin for visual / in-agent video Q&A; keep capture.py for the batch-CLI note-writing workflow it already does well.

## Specific items extracted
- The `/watch` skill, for visual video comprehension inside a Claude conversation.

## Caveats / risks
- Token cost spikes on long video (up to 100 frames × image tokens) — use `--max-frames` / adaptive budget.
- MIT, no lock-in. yt-dlp site-breakage risk (same as capture.py). Single maintainer; young project (2025).
