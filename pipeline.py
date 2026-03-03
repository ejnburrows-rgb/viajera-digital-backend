"""4-step processing pipeline for Viajera Digital."""

import os
import subprocess
import time
import json
import glob
from typing import Callable, Optional, Dict, Any

from groq import Groq
from exports import generate_all_exports

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
TEMP_DIR = os.environ.get("TEMP_DIR", "/tmp/viajera")
MAX_DURATION = int(os.environ.get("MAX_VIDEO_DURATION_MINUTES", 150))

DECIMA_SYSTEM_PROMPT = """ROL: Eres un experto transcriptor especializado en poesía improvisada cubana y décima espinela, con profundo conocimiento de métrica española, rima consonante y estructura poética tradicional.

TAREA: Dado el siguiente texto transcrito de un evento de repentismo cubano, identifica y estructura TODAS las décimas presentes.

ESTRUCTURA OBLIGATORIA POR DÉCIMA:
- Esquema de rima: ABBAACCDDC (rima consonante obligatoria)
- Métrica: Versos octosílabos (8 sílabas métricas por verso, contando sinalefas, sinéresis y diéresis según las reglas de métrica española)
- Exactamente 10 versos por décima

INSTRUCCIONES:
1. Identifica dónde comienza y termina cada décima en la transcripción
2. Convierte el habla oral en versos escritos de 8 sílabas
3. Verifica el esquema de rima ABBAACCDDC con rima consonante
4. Atribuye cada décima al poeta correcto basándote en cambios de voz/turno
5. Clasifica cada décima como: "controversia", "polemica", o "punto"
6. Si un verso no alcanza 8 sílabas naturalmente, ajusta con sinéresis/diéresis poética
7. Si la rima oral no es perfecta, busca la palabra consonante más cercana que mantenga el sentido
8. Mantén regionalismos cubanos y vocabulario del campo
9. Preserva el orden cronológico exacto — NO reordenes las décimas

PRIORIDAD: Precisión métrica > Rima exacta > Sentido literal

Para el TOP 4, selecciona las 4 mejores décimas (2 por poeta) evaluando:
- Densidad de imágenes (metáforas, símiles, lenguaje sensorial)
- Complejidad de juegos de palabras (dobles sentidos, rimas internas)
- Fuerza dialógica (efectividad de respuesta al oponente)
- Impacto emocional (cambios de tono, vulnerabilidad, intensidad)
- Integridad estructural (10 versos completos sin titubeos)

También genera:
- event_summary: resumen narrativo de 3-5 oraciones del evento completo
- technical_winner: análisis breve de quién tuvo mejor desempeño técnico y por qué

FORMATO DE RESPUESTA: JSON estricto, sin texto adicional fuera del JSON.
{
  "event_summary": "Resumen narrativo...",
  "technical_winner": "Análisis del ganador técnico...",
  "decimas": [
    {
      "number": 1,
      "poet_id": "poet_a",
      "type": "controversia",
      "lines": ["verso 1", "verso 2", "verso 3", "verso 4", "verso 5", "verso 6", "verso 7", "verso 8", "verso 9", "verso 10"]
    }
  ],
  "top_4": [
    {
      "decima_number": 1,
      "poet_id": "poet_a",
      "analysis": "Análisis literario en español, 3-5 oraciones."
    }
  ]
}"""


def get_groq_client():
    return Groq(api_key=GROQ_API_KEY)


def update_progress(progress_cb, step, percent, message=""):
    if progress_cb:
        progress_cb(step, percent, message)


def get_audio_duration(filepath):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", filepath],
            capture_output=True, text=True, timeout=30
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def download_audio(youtube_url, job_id, progress_cb=None):
    update_progress(progress_cb, "downloading_audio", 5, "Descargando audio de YouTube...")

    job_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    output_path = os.path.join(job_dir, "audio.wav")

    try:
        subprocess.run(
            ["yt-dlp", "--extract-audio", "--audio-format", "wav",
             "--postprocessor-args", "-ar 16000 -ac 1",
             "--output", os.path.join(job_dir, "audio.%(ext)s"),
             "--no-playlist", "--quiet", youtube_url],
            capture_output=True, text=True, timeout=300, check=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error descargando audio: {e.stderr[:200]}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Tiempo de descarga excedido (5 minutos)")

    wav_files = glob.glob(os.path.join(job_dir, "audio*.wav"))
    if not wav_files:
        audio_files = glob.glob(os.path.join(job_dir, "audio*"))
        if audio_files:
            subprocess.run(
                ["ffmpeg", "-i", audio_files[0], "-ar", "16000", "-ac", "1",
                 output_path, "-y"],
                capture_output=True, timeout=120
            )
        else:
            raise RuntimeError("No se pudo descargar el audio del video")
    else:
        if wav_files[0] != output_path:
            os.rename(wav_files[0], output_path)

    duration = get_audio_duration(output_path)
    if duration > MAX_DURATION * 60:
        raise RuntimeError(f"El video excede el limite de {MAX_DURATION} minutos")

    update_progress(progress_cb, "downloading_audio", 18,
                    f"Audio descargado: {int(duration/60)} minutos")
    return output_path


def chunk_audio(audio_path, job_id, chunk_minutes=20):
    duration = get_audio_duration(audio_path)
    chunk_seconds = chunk_minutes * 60
    overlap = 30

    if duration <= chunk_seconds + overlap:
        return [audio_path]

    job_dir = os.path.join(TEMP_DIR, job_id)
    chunks = []
    start = 0
    idx = 0

    while start < duration:
        chunk_path = os.path.join(job_dir, f"chunk_{idx:03d}.wav")
        length = chunk_seconds + overlap if start + chunk_seconds < duration else duration - start
        subprocess.run(
            ["ffmpeg", "-i", audio_path, "-ss", str(start), "-t", str(length),
             "-c", "copy", chunk_path, "-y"],
            capture_output=True, timeout=60
        )
        chunks.append(chunk_path)
        start += chunk_seconds
        idx += 1

    return chunks


def ensure_file_size(filepath, max_mb=25):
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    if size_mb <= max_mb:
        return filepath

    compressed = filepath.replace(".wav", "_compressed.wav")
    subprocess.run(
        ["ffmpeg", "-i", filepath, "-ar", "16000", "-ac", "1", "-b:a", "64k",
         compressed, "-y"],
        capture_output=True, timeout=60
    )
    return compressed


def transcribe_audio(audio_path, job_id, progress_cb=None):
    update_progress(progress_cb, "transcribing", 20, "Preparando transcripcion...")

    chunks = chunk_audio(audio_path, job_id)
    client = get_groq_client()
    full_transcript = []
    total_chunks = len(chunks)

    for i, chunk_path in enumerate(chunks):
        chunk_path = ensure_file_size(chunk_path)
        progress_pct = 20 + int(40 * (i / total_chunks))
        update_progress(progress_cb, "transcribing", progress_pct,
                        f"Transcribiendo segmento {i+1} de {total_chunks}...")

        for attempt in range(3):
            try:
                with open(chunk_path, "rb") as f:
                    transcription = client.audio.transcriptions.create(
                        file=(os.path.basename(chunk_path), f.read()),
                        model="whisper-large-v3-turbo",
                        language="es",
                        response_format="text",
                    )
                full_transcript.append(transcription)
                break
            except Exception as e:
                if "429" in str(e) or "rate" in str(e).lower():
                    time.sleep(10 * (2 ** attempt))
                elif attempt == 2:
                    raise RuntimeError(f"Error transcribiendo segmento {i+1}: {str(e)[:200]}")
                else:
                    time.sleep(5)

        if i < total_chunks - 1:
            time.sleep(3)

    update_progress(progress_cb, "transcribing", 58, "Transcripcion completada")
    return "\n".join(full_transcript)


def structure_decimas(transcript, poet_a_name, poet_b_name, progress_cb=None):
    update_progress(progress_cb, "structuring_decimas", 62,
                    "Estructurando decimas con IA...")

    client = get_groq_client()

    user_prompt = (
        f"POETA A: {poet_a_name}\n"
        f"POETA B: {poet_b_name}\n\n"
        f"TRANSCRIPCION:\n{transcript[:15000]}"
    )

    for attempt in range(2):
        try:
            extra = ""
            if attempt > 0:
                extra = ("\n\nIMPORTANTE: Responde SOLO con JSON valido, "
                         "sin markdown, sin ```json```, sin texto extra.")
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": DECIMA_SYSTEM_PROMPT + extra},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=8000,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content.strip()
            result = json.loads(raw)
            break
        except json.JSONDecodeError:
            if attempt == 1:
                raise RuntimeError("La IA no genero JSON valido despues de 2 intentos")
        except Exception as e:
            if attempt == 1:
                raise RuntimeError(f"Error estructurando decimas: {str(e)[:200]}")
            time.sleep(5)

    update_progress(progress_cb, "structuring_decimas", 78,
                    f"Encontradas {len(result.get('decimas', []))} decimas")

    for dec in result.get("decimas", []):
        dec["poet_name"] = poet_a_name if dec.get("poet_id") == "poet_a" else poet_b_name

    for entry in result.get("top_4", []):
        entry["poet_name"] = poet_a_name if entry.get("poet_id") == "poet_a" else poet_b_name
        for dec in result.get("decimas", []):
            if dec["number"] == entry.get("decima_number"):
                entry["lines"] = dec["lines"]
                break

    return result


def run_pipeline(job_id, youtube_url, poet_a_name, poet_b_name, progress_cb=None):
    audio_path = download_audio(youtube_url, job_id, progress_cb)
    duration_seconds = get_audio_duration(audio_path)
    duration_minutes = int(duration_seconds / 60)

    transcript = transcribe_audio(audio_path, job_id, progress_cb)

    structured = structure_decimas(transcript, poet_a_name, poet_b_name, progress_cb)

    update_progress(progress_cb, "generating_exports", 82, "Generando PDF, TXT, JSON...")

    decimas = structured.get("decimas", [])
    top_4 = structured.get("top_4", [])

    for i, entry in enumerate(top_4):
        entry["rank"] = i + 1

    poet_a_count = sum(1 for d in decimas if d.get("poet_id") == "poet_a")
    poet_b_count = len(decimas) - poet_a_count

    result = {
        "status": "complete",
        "event_title": "Canturia",
        "event_detail": "",
        "event_summary": structured.get("event_summary", ""),
        "technical_winner": structured.get("technical_winner", ""),
        "total_decimas": len(decimas),
        "duration_minutes": duration_minutes,
        "poets": [
            {"id": "poet_a", "name": poet_a_name, "decima_count": poet_a_count},
            {"id": "poet_b", "name": poet_b_name, "decima_count": poet_b_count},
        ],
        "decimas": decimas,
        "top_4": top_4,
    }

    export_dir = os.path.join(TEMP_DIR, job_id, "exports")
    paths = generate_all_exports(result, export_dir)

    result["downloads"] = {
        "pdf_url": f"/downloads/{job_id}/pdf",
        "txt_url": f"/downloads/{job_id}/txt",
        "json_url": f"/downloads/{job_id}/json",
    }
    result["_export_paths"] = paths

    update_progress(progress_cb, "complete", 100, "Completado!")
    return result
