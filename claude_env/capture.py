"""capture.py — Instagram/video → structured .md

Supports:
- Video/Reel  → yt-dlp audio download → Groq Whisper transcription
- Image post  → yt-dlp or instaloader download → Groq Llama 4 Vision
- Carousel    → per-image Vision extraction

External deps: yt-dlp, ffmpeg, instaloader (fallback for image-only posts)
"""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from groq import Groq

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
AUDIO_EXTENSIONS = {".mp3", ".m4a", ".wav", ".ogg"}

VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
WHISPER_MODEL = "whisper-large-v3"


def _cookies_path() -> Path:
    return Path(__file__).parent / "cookies.txt"


def _cookies_args() -> list[str]:
    p = _cookies_path()
    return ["--cookies", str(p)] if p.exists() else []


# ─── Metadata ────────────────────────────────────────────────────────────────

def fetch_metadata(url: str) -> dict:  # type: ignore[type-arg]
    result = subprocess.run(
        ["yt-dlp", *_cookies_args(), "--dump-json", "--no-download", url],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode == 0:
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            pass
    return {}


def detect_content_type(metadata: dict) -> str:  # type: ignore[type-arg]
    if metadata.get("entries"):
        return "carousel"
    vcodec = metadata.get("vcodec", "")
    ext = metadata.get("ext", "")
    if vcodec in ("none", "") and ext in ("jpg", "jpeg", "png", "webp"):
        return "image"
    if vcodec and vcodec != "none":
        return "video"
    if ext in ("jpg", "jpeg", "png", "webp"):
        return "image"
    return "video"


# ─── Download ────────────────────────────────────────────────────────────────

def _extract_shortcode(url: str) -> str | None:
    m = re.search(r'/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)', url)
    return m.group(1) if m else None


def download_media(url: str, output_dir: str, as_audio_only: bool = False) -> list[str]:
    template = os.path.join(output_dir, "%(autonumber)s_%(id)s.%(ext)s")
    cmd = ["yt-dlp", *_cookies_args(), "--output", template, "--no-playlist", url]
    if as_audio_only:
        cmd[1:1] = ["--extract-audio", "--audio-format", "mp3", "--audio-quality", "0"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        print(f"  [!] yt-dlp error: {result.stderr[-400:]}")
        return []
    return [str(p) for p in Path(output_dir).iterdir() if p.is_file()]


def download_images_instaloader(url: str, output_dir: str) -> list[str]:
    shortcode = _extract_shortcode(url)
    if not shortcode:
        return []
    cmd = [
        "instaloader", "--no-videos", "--no-video-thumbnails",
        "--dirname-pattern", output_dir,
        "--filename-pattern", "{shortcode}_{typename}_{mediaid}",
        "--", f"-{shortcode}",
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return [
        str(p) for p in Path(output_dir).iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ]


# ─── Content extraction ──────────────────────────────────────────────────────

def transcribe_audio(audio_path: str, client: Groq, language: str = "es") -> str:
    lang = None if language == "auto" else language
    with open(audio_path, "rb") as f:
        response = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), f),
            model=WHISPER_MODEL,
            language=lang,
            response_format="text",
        )
    return str(response)


def extract_image_content(image_path: str, client: Groq) -> str:
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")
    ext = Path(image_path).suffix.lower().lstrip(".")
    mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/jpeg")
    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}"}},
                {"type": "text", "text": (
                    "Analiza esta imagen con detalle.\n"
                    "1. TEXTO VISIBLE: Transcribe literalmente todo el texto que aparezca.\n"
                    "2. CONTENIDO VISUAL: Describe brevemente lo que se ve.\n"
                    "3. MENSAJE PRINCIPAL: Resume en 1-2 frases la idea central.\n"
                    "Si no hay texto visible, describe el contenido visual con precisión."
                )},
            ],
        }],
        max_tokens=2000,
    )
    return str(response.choices[0].message.content)


# ─── Markdown builder ────────────────────────────────────────────────────────

def build_markdown(
    url: str,
    topic: str,
    content: str,
    metadata: dict,  # type: ignore[type-arg]
    content_type: str,
    image_count: int = 1,
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    raw_title = metadata.get("title") or metadata.get("description", "")
    title = (raw_title[:80].replace("\n", " ").strip()) if raw_title else f"Post {metadata.get('id', 'unknown')}"
    uploader = metadata.get("uploader") or metadata.get("channel", "desconocido")
    description = metadata.get("description", "")
    upload_date_raw = metadata.get("upload_date", "")
    upload_date = (
        f"{upload_date_raw[:4]}-{upload_date_raw[4:6]}-{upload_date_raw[6:]}"
        if len(upload_date_raw) == 8 else upload_date_raw
    )

    if content_type == "video":
        duration = int(metadata.get("duration") or 0)
        type_meta = f"duration: {duration // 60}:{duration % 60:02d}" if duration else "duration: unknown"
        content_header = "## Transcripción"
        type_tag = "transcription"
    else:
        type_meta = f"images: {image_count}"
        content_header = f"## Contenido extraído ({image_count} imagen{'es' if image_count > 1 else ''})"
        type_tag = "vision"

    return f"""---
title: "{title}"
url: "{url}"
topic: {topic}
type: {content_type}
author: {uploader}
{type_meta}
upload_date: {upload_date}
processed_date: {now}
tags:
  - {topic}
  - {type_tag}
---

# {title}

**Fuente:** [{uploader}]({url})
**Tipo:** {content_type} | **Subido:** {upload_date}

---

{content_header}

{content}

---

## Descripción original

{description[:500] if description else "_Sin descripción disponible_"}

---

## Notas personales

_[Espacio para tus notas]_

## Ideas clave

_[Las ideas más relevantes]_

## Referencias mencionadas

_[Links, nombres, conceptos del contenido]_
"""


# ─── Core processing ─────────────────────────────────────────────────────────

def process_url(url: str, topic: str, output_dir: Path, client: Groq, language: str = "es") -> bool:
    url = url.strip()
    if not url or url.startswith("#"):
        return True

    print(f"\n{'='*60}\nURL: {url[:70]}...")

    with tempfile.TemporaryDirectory() as tmpdir:
        print("  [1/4] Obteniendo metadatos...")
        metadata = fetch_metadata(url)
        content_type = detect_content_type(metadata)
        print(f"  [✓] Tipo detectado: {content_type}")

        if content_type == "video":
            print("  [2/4] Descargando audio...")
            files = download_media(url, tmpdir, as_audio_only=True)
            audio_files = [f for f in files if Path(f).suffix.lower() in AUDIO_EXTENSIONS]

            if not audio_files:
                print("  [!] Sin audio — reintentando con instaloader...")
                image_files = sorted(download_images_instaloader(url, tmpdir))
                if not image_files:
                    print("  [!] SKIP — ni audio ni imágenes encontrados")
                    return False
                content_type = "carousel" if len(image_files) > 1 else "image"
                content = _extract_images(image_files, client)
                return _write_output(url, topic, content, metadata, content_type, len(image_files), output_dir)

            size_mb = os.path.getsize(audio_files[0]) / 1024 / 1024
            print(f"  [✓] Audio: {Path(audio_files[0]).name} ({size_mb:.1f} MB)")
            print("  [3/4] Transcribiendo con Whisper...")
            try:
                content = transcribe_audio(audio_files[0], client, language)
                print(f"  [✓] {len(content)} caracteres transcritos")
            except Exception as e:
                print(f"  [!] Error transcribiendo: {e}")
                return False

        else:
            print("  [2/4] Descargando imagen(es)...")
            files = download_media(url, tmpdir, as_audio_only=False)
            image_files = sorted(f for f in files if Path(f).suffix.lower() in IMAGE_EXTENSIONS)
            if not image_files:
                print("  [!] SKIP — no se encontraron imágenes")
                return False
            print(f"  [✓] {len(image_files)} imagen(es)")
            content_type = "carousel" if len(image_files) > 1 else "image"
            content = _extract_images(image_files, client)

        return _write_output(url, topic, content, metadata, content_type,
                             1 if content_type == "video" else len(image_files), output_dir)


def _extract_images(image_files: list[str], client: Groq) -> str:
    print(f"  [3/4] Extrayendo contenido con Llama 4 Vision...")
    parts = []
    for i, img_path in enumerate(image_files, 1):
        print(f"        Imagen {i}/{len(image_files)}...")
        try:
            text = extract_image_content(img_path, client)
            parts.append(f"### Imagen {i}\n\n{text}" if len(image_files) > 1 else text)
        except Exception as e:
            parts.append(f"### Imagen {i}\n\n_Error: {e}_")
    return "\n\n---\n\n".join(parts)


def _write_output(
    url: str, topic: str, content: str, metadata: dict,  # type: ignore[type-arg]
    content_type: str, image_count: int, output_dir: Path,
) -> bool:
    print("  [4/4] Generando .md...")
    md = build_markdown(url, topic, content, metadata, content_type, image_count)
    post_id = metadata.get("id") or datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in post_id)
    out = output_dir / f"{topic}_{safe_id}.md"
    out.write_text(md, encoding="utf-8")
    print(f"  [✓] Guardado: {out}")
    return True
