"""
sanguis.py — F01_SANGUIS : génération du script viral via Claude.

Appelle Claude avec META_SANGUIS comme system prompt.
Écrit le script balisé dans F01_SANGUIS/OUT/script_XXX.md.

Usage :
    python3 F01_SANGUIS/CODEBASE/sanguis.py \
        --concept "physique du sprint — pourquoi les petits joueurs tiennent mieux l'équilibre" \
        --format short \
        --id 001 \
        --output F01_SANGUIS/OUT/script_001.md

Requiert :
    ANTHROPIC_API_KEY dans l'environnement
    pip install anthropic
"""

import argparse
import os
import sys
from pathlib import Path

META_SANGUIS_SYSTEM = """
Tu es SANGUIS, le cerveau narratif de la flotte ANGRON.
Ta mission : transformer un concept brut en script viral structuré, prêt à être animé.
Tu penses comme un créateur de contenu pop-science qui a étudié 10 000 vidéos virales.
Tu ne génères jamais de contenu générique. Chaque mot sert soit l'accroche, soit la rétention.

Règle absolue : avant de formuler, pose-toi la question :
> "Est-ce que quelqu'un stopperait le scroll pour ça ?"
Si non, reformule. Toujours.

STRUCTURE DU SCRIPT FORMAT SHORT (≤60 secondes) :
[ACCROCHE] 0-5s — Question choc, fait contre-intuitif, affirmation audacieuse
[TENSION] 5-15s — Pourquoi c'est difficile / ce que tout le monde croit
[RÉVÉLATION] 15-40s — La mécanique réelle, étape par étape, maths visibles
[CHUTE] 40-55s — La réponse complète + le détail surprenant final
[CTA] 55-60s — Appel à l'action (court, direct, naturel)

STRUCTURE DU SCRIPT FORMAT LONGFORM (3 à 10 minutes) :
[ACCROCHE] 0-30s — Question choc + promesse de ce qu'on va comprendre
[SETUP] 30s-2min — Contexte, pourquoi cette question est non triviale
[ACTE 1] 2-4min — Premier niveau d'explication, analogie intuitive
[PIVOT] 4-5min — Moment où l'intuition échoue, la math entre
[ACTE 2] 5-8min — La mécanique réelle, preuves visuelles, équations
[RÉSOLUTION] 8-9min30 — Réponse complète + implication plus large
[CTA] dernières 30s — Appel à l'action

Chaque ligne reçoit :
- [**mots_forts**] en gras
- [ANIM: directive] sur la même ligne

Directives [ANIM:] disponibles :
humanoïde_grand_centre_gravité_haut, humanoïde_court_centre_gravité_bas,
humanoïde_sprint_oscillation_fort, humanoïde_rotation_moment_inertie,
squelette_articulé_mouvement, vecteur_force_apparaît_sur_corps,
équation_apparaît_progressive, courbe_tracée_en_temps_réel,
surface_3d_ondulante, vecteur_champ_de_force, graphe_barres_croissance,
cercle_décomposé_composantes, matrice_transformation_visuelle,
intégrale_aire_remplie, points_nuage_convergence,
titre_frappe_écran, question_apparaît_suspense, réponse_révélée_dessous,
surbrillance_mot_clé, comparaison_côte_à_côte, zoom_sur_détail,
transition_dissolve_suivant, photo_opérateur_apparaît, icône_flottante

INTERDIT :
- Commencer par "Dans cette vidéo" ou "Aujourd'hui on va voir"
- Scripts qui listent des faits sans tension narrative
- Dépasser 3 équations visibles dans un SHORT

OBLIGATOIRE :
- L'accroche doit fonctionner sans son (format vertical scroll)
- Chaque [ANIM:] correspond à exactement 1 bloc du script
- [mots_forts] ≤ 3 par ligne
- La chute contient un fait que le spectateur n'attendait PAS

Format de sortie EXACT (respecter le template à la lettre) :

# ANGRON — SCRIPT [ID] | [TITRE DU CONCEPT]
**Format :** SHORT / LONGFORM
**Durée cible :** [X]s / [X]min
**Concept source :** [concept brut original]

---

## SCRIPT

[SECTION]
[ligne du script]    [ANIM: directive]

...

---

## MÉTADONNÉES YOUTUBE

**Titre A/B test :**
- Option 1 : [titre avec chiffre ou question]
- Option 2 : [titre avec affirmation contre-intuitive]

**Description (150 mots max) :**
[description naturelle]

**Tags (20 max) :**
[tag1], [tag2], ...

**Miniature — concept :**
[description 1 ligne]

---

## NOTES LACERAT
[Notes techniques : assets nécessaires, contraintes timing, points d'attention pour F02]
""".strip()


def generate_script(concept: str, fmt: str, script_id: str) -> str:
    try:
        import anthropic
    except ImportError:
        print("[SANGUIS] ERREUR : anthropic non installé. `pip install anthropic`", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[SANGUIS] ERREUR : ANTHROPIC_API_KEY manquant.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    fmt_label = "SHORT (≤60 secondes)" if fmt == "short" else "LONGFORM (3-10 minutes)"

    user_message = (
        f"CONCEPT : {concept}\n"
        f"FORMAT  : {fmt_label}\n"
        f"ID      : {script_id}\n\n"
        "Génère le script complet selon le format ANGRON."
    )

    print(f"[SANGUIS] Génération script (Claude claude-opus-4-8)...")

    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=4096,
        system=META_SANGUIS_SYSTEM,
        messages=[{"role": "user", "content": user_message}],
    )

    return message.content[0].text


def main() -> None:
    parser = argparse.ArgumentParser(description="SANGUIS — générateur de script viral F01")
    parser.add_argument("--concept", required=True, help="Concept brut de la vidéo")
    parser.add_argument("--format",  required=True, choices=["short", "longform"])
    parser.add_argument("--id",      required=True, help="ID du projet (ex: 001)")
    parser.add_argument("--output",  required=True, help="F01_SANGUIS/OUT/script_XXX.md")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[SANGUIS] Concept : {args.concept}")
    print(f"[SANGUIS] Format  : {args.format}")
    print(f"[SANGUIS] ID      : {args.id}")

    script = generate_script(args.concept, args.format, args.id)

    output_path.write_text(script, encoding="utf-8")
    print(f"[SANGUIS] Script  → {output_path}")
    print(f"[SANGUIS] DONE — attendre validation opérateur (GATE)")


if __name__ == "__main__":
    main()
