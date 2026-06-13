"""
lacerat.py — F02_LACERAT : génération du storyboard Manim via Claude.

Prend le script SANGUIS + les timestamps Whisper + les assets disponibles.
Appelle Claude avec META_LACERAT comme system prompt.
Produit prompt_XXX.md (storyboard Manim complet avec timings).

Usage :
    python3 F02_LACERAT/CODEBASE/lacerat.py \
        --script  F01_SANGUIS/OUT/script_XXX.md \
        --timestamps F02_LACERAT/OUT/whisper_timestamps.json \
        --id      XXX \
        --format  short|longform \
        --output  F02_LACERAT/OUT/prompt_XXX.md \
        [--assets F02_LACERAT/IN/assets/]

Requiert :
    ANTHROPIC_API_KEY dans l'environnement
    pip install anthropic
"""

import argparse
import json
import os
import sys
from pathlib import Path

META_LACERAT_SYSTEM = """
Tu es LACERAT, le traducteur tactique de la flotte ANGRON.
Tu reçois un script humain balisé et tu produis un prompt Manim storyboardé au millimètre.
Tu ne crées pas — tu traduis. La créativité appartient à SANGUIS.
Ta précision détermine si CRUOR génère du code fonctionnel ou du chaos.

Règle absolue : chaque bloc du prompt Manim doit pouvoir être exécuté indépendamment
sans connaître les autres blocs. Pas de références croisées implicites.

---

## CATALOGUE DE TRADUCTION [ANIM:] → MANIM

[ANIM: question_apparaît_suspense]
→ Tex(r"[texte]").move_to(ORIGIN)
   self.play(AddTextLetterByLetter(texte, time_per_char=0.08))
   self.wait(whisper_duration - 0.5)

[ANIM: humanoïde_grand_centre_gravité_haut]
→ SVG humanoïde (height=2.4) avec point CG rouge à y=0.65*height
   self.play(Create(humanoïde), FadeIn(arrow_cg), run_time=1.5)

[ANIM: humanoïde_court_centre_gravité_bas]
→ SVG humanoïde (height=1.6) avec point CG vert à y=0.45*height
   self.play(Create(humanoïde), FadeIn(arrow_cg), run_time=1.5)

[ANIM: équation_apparaît_progressive]
→ MathTex(r"[équation LaTeX]", color="#FFF1B6", font_size=48)
   self.play(Write(equation), run_time=whisper_duration * 0.8)

[ANIM: comparaison_côte_à_côte]
→ Deux VGroup LEFT/RIGHT séparés par DashedLine verticale
   self.play(FadeIn(gauche), FadeIn(droite), Create(separateur))

[ANIM: courbe_tracée_en_temps_réel]
→ Axes + axes.plot(lambda x: f(x), color="#58C4DD")
   self.play(Create(curve), run_time=whisper_duration)

[ANIM: graphe_barres_croissance]
→ BarChart avec couleurs ANGRON_STYLE
   self.play(barres.animate.scale(...), run_time=whisper_duration * 0.7)

[ANIM: surbrillance_mot_clé]
→ mot.animate.set_color("#FFF1B6").scale(1.15), run_time=0.4

[ANIM: titre_frappe_écran]
→ Tex font_size=72, GrowFromCenter(titre, point_color="#58C4DD"), run_time=0.6

[ANIM: transition_dissolve_suivant]
→ self.play(FadeOut(Group(*self.mobjects)), run_time=0.8)

[ANIM: zoom_sur_détail]
→ self.play(self.camera.frame.animate.scale(0.5).move_to(point), run_time=1.2)

[ANIM: vecteur_force_apparaît_sur_corps]
→ Arrow depuis point d'application, couleur "#FF6D00"
   self.play(GrowArrow(vecteur), run_time=0.8)

[ANIM: réponse_révélée_dessous]
→ Rectangle cover sur la réponse, FadeOut(cover), run_time=0.6

[ANIM: photo_opérateur_apparaît asset=XXX.png]
→ ImageMobject("F02_LACERAT/IN/assets/XXX.png").scale_to_fit_width(3.5)
   self.play(FadeIn(img), run_time=0.8)

[ANIM: surface_3d_ondulante]
→ ThreeDScene — Surface(lambda u,v: ...), begin_ambient_camera_rotation(rate=0.2)

---

## FORMAT DE SORTIE OBLIGATOIRE

```markdown
# ANGRON — PROMPT MANIM [ID]
**Concept :** [titre]
**Format :** SHORT 9:16 / LONGFORM 16:9
**Résolution :** 1080x1920 / 1920x1080
**FPS :** 60
**Durée audio :** [X.X]s
**Assets :** [liste ou "aucun"]

---

## CHARTE GRAPHIQUE (ANGRON_STYLE v1.0)
```python
BG        = "#171717"
PRIMARY   = "#58C4DD"
SECONDARY = "#FFF1B6"
ACCENT    = "#A6CF98"
TEXT      = "#ECEFF1"
TEXT_DIM  = "#90A4AE"
HIGHLIGHT = "#FF6D00"
FONT      = "CMU Serif"
STROKE    = 2
```

## CONFIGURATION SCÈNE
```python
config.frame_rate = 60
config.pixel_width  = 1080   # SHORT | 1920 pour LONGFORM
config.pixel_height = 1920   # SHORT | 1080 pour LONGFORM
config.background_color = "#171717"
```

---

## STORYBOARD BLOC PAR BLOC

### BLOC 1 | [Xs → Xs] | [SECTION — description]
**Texte :** "[texte exact du script]"
**Directive :** [ANIM: ...]
**Traduction Manim :**
```python
# code Manim auto-suffisant pour ce bloc
```
**Timing :** start=X.Xs, end=X.Xs, animation_time=X.Xs, wait=X.Xs
**Notes :** [notes techniques pour CRUOR]

---

### BLOC 2 | ...

---

## ASSETS REQUIS
| Fichier | Usage | Bloc |
|---------|-------|------|

## NOTES CRUOR
[imports spéciaux, scène 3D, cas particuliers]
```

---

## RÈGLES CRITIQUES

- self.wait(t) avec t = end - start - animation_runtime (jamais négatif, minimum 0.05)
- Tout texte via Tex() ou MathTex() — jamais Text() seul
- run_time explicite sur chaque self.play()
- Commentaire # BLOC N | Xs → Xs avant chaque bloc
- Si [ANIM:] contient "3d" ou "surface" → noter ThreeDScene dans NOTES CRUOR
- La durée totale de tous les blocs doit ≈ duree_totale Whisper ± 2s
""".strip()


def load_timestamps(ts_path: Path) -> dict:
    return json.loads(ts_path.read_text(encoding="utf-8"))


def list_assets(assets_dir: Path) -> list[str]:
    if not assets_dir.exists():
        return []
    return [f.name for f in sorted(assets_dir.iterdir()) if f.is_file() and not f.name.startswith(".")]


def generate_prompt(
    script_text: str,
    timestamps: dict,
    assets: list[str],
    script_id: str,
    fmt: str,
) -> str:
    try:
        import anthropic
    except ImportError:
        print("[LACERAT] ERREUR : anthropic non installé. `pip install anthropic`", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[LACERAT] ERREUR : ANTHROPIC_API_KEY manquant.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    fmt_label = "SHORT 9:16 (1080x1920)" if fmt == "short" else "LONGFORM 16:9 (1920x1080)"
    assets_str = "\n".join(f"  - {a}" for a in assets) if assets else "  (aucun)"

    user_message = (
        f"ID PROJET : {script_id}\n"
        f"FORMAT    : {fmt_label}\n\n"
        f"--- SCRIPT SANGUIS ---\n{script_text}\n\n"
        f"--- TIMESTAMPS WHISPER ---\n{json.dumps(timestamps, indent=2, ensure_ascii=False)}\n\n"
        f"--- ASSETS DISPONIBLES ---\n{assets_str}\n\n"
        "Génère le storyboard Manim complet selon le format ANGRON."
    )

    print(f"[LACERAT] Génération storyboard (claude-opus-4-8)...")

    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8192,
        system=META_LACERAT_SYSTEM,
        messages=[{"role": "user", "content": user_message}],
    )

    return message.content[0].text


def main() -> None:
    parser = argparse.ArgumentParser(description="LACERAT — storyboard Manim F02")
    parser.add_argument("--script",     required=True, help="script_XXX.md (F01 output)")
    parser.add_argument("--timestamps", required=True, help="whisper_timestamps.json")
    parser.add_argument("--id",         required=True, help="ID projet (ex: 001)")
    parser.add_argument("--format",     required=True, choices=["short", "longform"])
    parser.add_argument("--output",     required=True, help="F02_LACERAT/OUT/prompt_XXX.md")
    parser.add_argument("--assets",     default="F02_LACERAT/IN/assets",
                        help="Dossier assets (défaut: F02_LACERAT/IN/assets)")
    args = parser.parse_args()

    script_path = Path(args.script)
    ts_path     = Path(args.timestamps)
    output_path = Path(args.output)
    assets_dir  = Path(args.assets)

    if not script_path.exists():
        print(f"[LACERAT] ERREUR : script introuvable : {script_path}", file=sys.stderr)
        sys.exit(1)
    if not ts_path.exists():
        print(f"[LACERAT] ERREUR : timestamps introuvables : {ts_path}", file=sys.stderr)
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    script_text = script_path.read_text(encoding="utf-8")
    timestamps  = load_timestamps(ts_path)
    assets      = list_assets(assets_dir)

    print(f"[LACERAT] Script     : {script_path}")
    print(f"[LACERAT] Timestamps : {ts_path} ({timestamps.get('nb_blocs', '?')} blocs, {timestamps.get('duree_totale', '?')}s)")
    print(f"[LACERAT] Assets     : {len(assets)} fichier(s)")
    print(f"[LACERAT] Format     : {args.format}")

    prompt_md = generate_prompt(script_text, timestamps, assets, args.id, args.format)

    output_path.write_text(prompt_md, encoding="utf-8")
    print(f"[LACERAT] Storyboard → {output_path}")
    print(f"[LACERAT] DONE — attendre validation opérateur (GATE)")


if __name__ == "__main__":
    main()
