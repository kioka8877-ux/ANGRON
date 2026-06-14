"""
nuceria.py — F05_NUCERIA : Camouflage final + wipe métadonnées.

Input  : nails_out_[ID].mp4
Output : youtube_[short/longform]_[ID].mp4
         rapport_f05.html
         NUCERIA_DONE.txt

Claude INACTIF pendant l'exécution. Signal de fin : NUCERIA_DONE.txt.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

FINGERPRINTS_INTERDITS = [
    "manim", "remotion", "opencv", "python", "openai",
    "runway", "stable-diffusion", "lavf", "lavc",
    "moviepy", "ffmpeg-python", "angron", "claude",
]

STYLE = {
    "pixel_format": "yuv420p",
    "codec":        "libx264",
    "crf":          18,
    "preset":       "fast",
    "fps":          60,
    "loudnorm":     "I=-14:TP=-1:LRA=11",
    "audio_bitrate": "192k",
    "audio_rate":   48000,
    "audio_channels": 2,
}


def run_ffprobe(path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)


def encode(input_path: Path, output_path: Path, concept: str) -> tuple[bool, str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-fflags", "+bitexact",
        "-i", str(input_path),
        # Vidéo
        "-c:v", STYLE["codec"],
        "-crf", str(STYLE["crf"]),
        "-preset", STYLE["preset"],
        "-pix_fmt", STYLE["pixel_format"],
        "-r", str(STYLE["fps"]),
        # Audio
        "-c:a", "aac",
        "-b:a", STYLE["audio_bitrate"],
        "-ar", str(STYLE["audio_rate"]),
        "-ac", str(STYLE["audio_channels"]),
        "-af", f"loudnorm={STYLE['loudnorm']}",
        # Wipe total des métadonnées
        "-map_metadata", "-1",
        # Titre propre seulement
        "-metadata", f"title={concept}",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stderr


def qa_check(output_path: Path) -> tuple[bool, list[str], dict]:
    probe = run_ffprobe(output_path)
    detected = []

    fmt_tags = probe.get("format", {}).get("tags", {})
    for key, value in fmt_tags.items():
        for fp in FINGERPRINTS_INTERDITS:
            if fp.lower() in str(value).lower() or fp.lower() in key.lower():
                detected.append(f"format.{key}={value}")

    for stream in probe.get("streams", []):
        for key, value in stream.get("tags", {}).items():
            for fp in FINGERPRINTS_INTERDITS:
                if fp.lower() in str(value).lower():
                    detected.append(f"stream[{stream.get('codec_type')}].{key}={value}")

    return len(detected) == 0, detected, probe


def _stream(probe: dict, codec_type: str) -> dict:
    return next((s for s in probe.get("streams", []) if s.get("codec_type") == codec_type), {})


def generate_rapport(
    output_path: Path,
    concept: str,
    fmt: str,
    qa_ok: bool,
    detected: list[str],
    probe: dict,
    duration_s: float,
) -> Path:
    rapport_path = output_path.parent / "rapport_f05.html"

    status_color = "#A6CF98" if qa_ok else "#EF5350"
    status_label = (
        "QA OK — AUCUN FINGERPRINT"
        if qa_ok
        else f"QA FAIL — {len(detected)} fingerprint(s) détecté(s)"
    )

    v = _stream(probe, "video")
    a = _stream(probe, "audio")

    def kbps(stream: dict) -> str:
        br = stream.get("bit_rate")
        return f"{int(br) // 1000} kbps" if br else "—"

    meta_rows = "".join(
        f"<tr><td>{k}</td><td>{v_}</td></tr>"
        for k, v_ in probe.get("format", {}).get("tags", {}).items()
    )
    fp_rows = "".join(f'<tr><td style="color:#EF5350">{fp}</td></tr>' for fp in detected)

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>NUCERIA — Rapport F05</title>
<style>
  body  {{ background:#171717; color:#ECEFF1; font-family:monospace; padding:2rem; margin:0; }}
  h1    {{ color:#58C4DD; margin-bottom:.2rem; }}
  h2    {{ color:#FFF1B6; border-bottom:1px solid #333; padding-bottom:.3rem; margin-top:2rem; }}
  table {{ border-collapse:collapse; width:100%; margin:.5rem 0; }}
  td,th {{ border:1px solid #2a2a2a; padding:.5rem 1rem; text-align:left; }}
  th    {{ background:#1e1e1e; color:#90A4AE; }}
  .status {{ font-size:1.3rem; font-weight:bold; color:{status_color};
             padding:.8rem 1.4rem; border:2px solid {status_color};
             display:inline-block; margin:1rem 0; }}
</style>
</head>
<body>
<h1>NUCERIA — Rapport de Camouflage F05</h1>
<p style="color:#90A4AE">Généré : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
<div class="status">{status_label}</div>

<h2>Production</h2>
<table>
  <tr><th>Concept</th><td>{concept}</td></tr>
  <tr><th>Format</th><td>{fmt}</td></tr>
  <tr><th>Fichier</th><td>{output_path.name}</td></tr>
  <tr><th>Durée encodage</th><td>{duration_s:.1f}s</td></tr>
</table>

<h2>Vidéo</h2>
<table>
  <tr><th>Codec</th><td>{v.get('codec_name','—')}</td></tr>
  <tr><th>Résolution</th><td>{v.get('width','—')}x{v.get('height','—')}</td></tr>
  <tr><th>FPS</th><td>{v.get('r_frame_rate','—')}</td></tr>
  <tr><th>Pixel format</th><td>{v.get('pix_fmt','—')}</td></tr>
  <tr><th>Bitrate</th><td>{kbps(v)}</td></tr>
</table>

<h2>Audio</h2>
<table>
  <tr><th>Codec</th><td>{a.get('codec_name','—')}</td></tr>
  <tr><th>Sample rate</th><td>{a.get('sample_rate','—')} Hz</td></tr>
  <tr><th>Canaux</th><td>{a.get('channels','—')}</td></tr>
  <tr><th>Bitrate</th><td>{kbps(a)}</td></tr>
</table>

<h2>Métadonnées présentes</h2>
<table>
  <tr><th>Clé</th><th>Valeur</th></tr>
  {meta_rows if meta_rows else '<tr><td colspan="2" style="color:#A6CF98">Aucune métadonnée.</td></tr>'}
</table>

<h2>Fingerprints détectés</h2>
{'<p style="color:#A6CF98">Aucun fingerprint — camouflage parfait.</p>' if not detected else f'<table><tr><th>Fingerprint</th></tr>{fp_rows}</table>'}

</body>
</html>"""

    rapport_path.write_text(html, encoding="utf-8")
    return rapport_path


def main() -> None:
    parser = argparse.ArgumentParser(description="NUCERIA — Camouflage final ANGRON F05")
    parser.add_argument("--input",   required=True, help="nails_out_[ID].mp4")
    parser.add_argument("--concept", required=True, help="Titre du concept")
    parser.add_argument("--format",  required=True, choices=["short", "longform"])
    parser.add_argument("--output",  required=True, help="youtube_[short/longform]_[ID].mp4")
    args = parser.parse_args()

    input_path  = Path(args.input)
    output_path = Path(args.output)
    done_path   = output_path.parent / "NUCERIA_DONE.txt"

    if not input_path.exists():
        print(f"[NUCERIA] ERREUR : fichier introuvable : {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"[NUCERIA] Encodage + wipe métadonnées...")
    print(f"  Input   : {input_path}")
    print(f"  Output  : {output_path}")
    print(f"  Concept : {args.concept}")

    t0 = datetime.utcnow()
    ok, ffmpeg_log = encode(input_path, output_path, args.concept)
    duration_s = (datetime.utcnow() - t0).total_seconds()

    if not ok:
        print(f"[NUCERIA] ERREUR FFmpeg :\n{ffmpeg_log}", file=sys.stderr)
        sys.exit(2)

    print(f"[NUCERIA] Encodage OK ({duration_s:.1f}s) — QA en cours...")

    qa_ok, detected, probe = qa_check(output_path)

    rapport_path = generate_rapport(
        output_path, args.concept, args.format,
        qa_ok, detected, probe, duration_s,
    )
    print(f"[NUCERIA] Rapport  : {rapport_path}")

    if not qa_ok:
        print(f"[NUCERIA] QA FAIL — {len(detected)} fingerprint(s) :", file=sys.stderr)
        for fp in detected:
            print(f"  - {fp}", file=sys.stderr)
        sys.exit(3)

    done_path.write_text(
        f"NUCERIA_DONE\n"
        f"concept={args.concept}\n"
        f"format={args.format}\n"
        f"output={output_path}\n"
        f"qa=OK\n"
        f"timestamp={datetime.utcnow().isoformat()}\n",
        encoding="utf-8",
    )

    print(f"[NUCERIA] Signal   : {done_path}")
    print(f"[NUCERIA] DONE     : {output_path}")


if __name__ == "__main__":
    main()
