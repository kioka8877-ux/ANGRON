"""
whisper_sync.py — F02_LACERAT : extraction des timestamps Whisper.

Utilise faster-whisper (CTranslate2 — pas de torch, léger, rapide).
Produit whisper_timestamps.json que LACERAT utilise pour storyboarder.

Usage :
    python3 F02_LACERAT/CODEBASE/whisper_sync.py \
        --audio  F02_LACERAT/IN/voice_XXX.mp3 \
        --script F01_SANGUIS/OUT/script_XXX.md \
        --output F02_LACERAT/OUT/whisper_timestamps_XXX.json \
        --format short \
        [--model tiny|base|small|medium|large-v3] \
        [--debug]

Requiert : pip install faster-whisper
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


def parse_script_blocs(script_path: Path) -> list[str]:
    blocs = []
    text = script_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith("[ANIM:"):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            continue
        if stripped.startswith("---"):
            continue
        if stripped.startswith("**") and stripped.endswith("**"):
            continue
        clean = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", stripped)
        if clean:
            blocs.append(clean)
    return blocs


def run_whisper(audio_path: Path, model_size: str = "small", debug: bool = False) -> tuple[list[dict], float]:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("[WHISPER] ERREUR : faster-whisper non installé.", file=sys.stderr)
        print("[WHISPER] → pip install faster-whisper", file=sys.stderr)
        sys.exit(1)

    print(f"[WHISPER] Chargement modèle \'{model_size}\' (cpu / int8)...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    print(f"[WHISPER] Transcription : {audio_path}")
    segments_iter, info = model.transcribe(
        str(audio_path),
        language="en",
        word_timestamps=True,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 300},
    )

    if debug:
        print(f"[WHISPER][DEBUG] Langue détectée  : {info.language} (proba {info.language_probability:.2f})")
        print(f"[WHISPER][DEBUG] Durée audio      : {info.duration:.3f}s")

    segments = []
    for seg in segments_iter:
        entry = {
            "id":    len(segments) + 1,
            "texte": seg.text.strip(),
            "start": round(seg.start, 3),
            "end":   round(seg.end,   3),
        }
        if debug:
            lp = getattr(seg, "avg_logprob",    None)
            ns = getattr(seg, "no_speech_prob", None)
            lp_str = f"{lp:.3f}" if lp is not None else "—"
            ns_str = f"{ns:.3f}" if ns is not None else "—"
            print(
                f"[WHISPER][DEBUG] [{entry[\'start\']:.3f}s → {entry[\'end\']:.3f}s] "
                f"logprob={lp_str} no_speech={ns_str} | {entry[\'texte\']}"
            )
        segments.append(entry)

    duree = segments[-1]["end"] if segments else round(info.duration, 3)
    return segments, duree


def align_blocs(
    whisper_segments: list[dict],
    script_lines: list[str],
    debug: bool = False,
) -> tuple[list[dict], bool]:
    if debug:
        print(
            f"[WHISPER][DEBUG] Alignement : {len(whisper_segments)} segments Whisper "
            f"/ {len(script_lines)} lignes script"
        )

    if len(whisper_segments) == len(script_lines):
        aligned = []
        for i, (seg, line) in enumerate(zip(whisper_segments, script_lines)):
            aligned.append({
                "id":      i + 1,
                "texte":   line,
                "whisper": seg["texte"],
                "start":   seg["start"],
                "end":     seg["end"],
            })
        return aligned, True

    print(
        f"[WHISPER] AVERTISSEMENT : {len(whisper_segments)} segments Whisper "
        f"≠ {len(script_lines)} lignes script.",
        file=sys.stderr,
    )
    print("[WHISPER] Segments bruts transmis — LACERAT fera l\'alignement.", file=sys.stderr)
    return whisper_segments, False


def main() -> None:
    parser = argparse.ArgumentParser(description="LACERAT whisper_sync — timestamps F02")
    parser.add_argument("--audio",  required=True)
    parser.add_argument("--script", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--format", default="short", choices=["short", "longform"])
    parser.add_argument(
        "--model", default="small",
        choices=["tiny", "base", "small", "medium", "large-v3"],
        help="Modèle Whisper (défaut: small — recommandé pop-science)",
    )
    parser.add_argument("--debug", action="store_true", help="Mode débogage verbose")
    args = parser.parse_args()

    audio_path  = Path(args.audio)
    script_path = Path(args.script)
    output_path = Path(args.output)
    done_path   = output_path.parent / "WHISPER_DONE.txt"

    for p, label in [(audio_path, "audio"), (script_path, "script")]:
        if not p.exists():
            print(f"[WHISPER] ERREUR : {label} introuvable : {p}", file=sys.stderr)
            sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.debug:
        print(f"[WHISPER][DEBUG] Audio  : {audio_path} ({audio_path.stat().st_size // 1024} KB)")
        print(f"[WHISPER][DEBUG] Script : {script_path}")
        print(f"[WHISPER][DEBUG] Modèle : {args.model}")
        print(f"[WHISPER][DEBUG] Format : {args.format}")

    script_lines = parse_script_blocs(script_path)
    print(f"[WHISPER] Script : {len(script_lines)} lignes de narration")

    segments, duree_totale = run_whisper(audio_path, model_size=args.model, debug=args.debug)
    print(f"[WHISPER] Segments : {len(segments)}, durée : {duree_totale:.1f}s")

    blocs, aligned = align_blocs(segments, script_lines, debug=args.debug)
    print(f"[WHISPER] Alignement : {\'AUTO (1:1)\' if aligned else \'MANUEL — LACERAT alignera\'}")

    output = {
        "version":      "2.0",
        "engine":       "faster-whisper",
        "model":        args.model,
        "language":     "en",
        "audio":        str(audio_path),
        "script":       str(script_path),
        "format":       args.format,
        "duree_totale": duree_totale,
        "nb_blocs":     len(blocs),
        "aligned":      aligned,
        "blocs":        blocs,
    }

    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[WHISPER] Timestamps → {output_path}")

    done_path.write_text(
        f"WHISPER_DONE\n"
        f"engine=faster-whisper\n"
        f"model={args.model}\n"
        f"language=en\n"
        f"audio={audio_path}\n"
        f"output={output_path}\n"
        f"nb_blocs={len(blocs)}\n"
        f"duree_totale={duree_totale}s\n"
        f"aligned={aligned}\n"
        f"timestamp={datetime.utcnow().isoformat()}\n",
        encoding="utf-8",
    )
    print(f"[WHISPER] Signal  → {done_path}")
    print("[WHISPER] DONE")


if __name__ == "__main__":
    main()
