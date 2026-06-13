# ANGRON — TRANSFER LOG

> Journal des transferts inter-frigates.  
> Chaque transfert de fichier entre frigates est consigné ici pour traçabilité et débogage.

---

## FORMAT D'ENTRÉE

```
### [ANGRON-XXX] — TRANSFERT FXX → FYY
- **Date** : YYYY-MM-DD HH:MM
- **Source** : FRIGATE_NOM/OUT/nom_fichier.ext
- **Destination** : FRIGATE_NOM/IN/nom_fichier.ext
- **Taille** : X MB
- **Hash SHA256** : (optionnel)
- **Statut** : OK / FAILED
- **Notes** : —
```

---

## LOG

*(Aucun transfert enregistré — en attente du premier cycle de production)*

---

## CONVENTION DE NOMMAGE DES FICHIERS

| Type | Convention | Exemple |
|------|-----------|---------|
| Script F01_SANGUIS | `script_XXX.md` | `script_001.md` |
| Voix opérateur | `voice_XXX.mp3` | `voice_001.mp3` |
| Prompt Manim | `prompt_XXX.md` | `prompt_001.md` |
| Timestamps Whisper | `timestamps_XXX.json` | `timestamps_001.json` |
| Asset image | `asset_XXX_description.png` | `asset_001_messi_sprint.png` |
| Code Manim | `scene_XXX.py` | `scene_001.py` |
| Render brut | `cruor_render_XXX.mp4` | `cruor_render_001.mp4` |
| Nails output | `nails_out_XXX.mp4` | `nails_out_001.mp4` |
| Final Short | `youtube_short_XXX.mp4` | `youtube_short_001.mp4` |
| Final Long-form | `youtube_longform_XXX.mp4` | `youtube_longform_001.mp4` |

---

## TRANSFERTS PAR FRIGATE

```
F01_SANGUIS/OUT/   → F02_LACERAT/IN/    script_XXX.md
F02_LACERAT/IN/    → F02_LACERAT/OUT/   prompt_XXX.md + timestamps_XXX.json
F02_LACERAT/OUT/   → F03_CRUOR/IN/      prompt_XXX.md + timestamps_XXX.json + assets
F03_CRUOR/OUT/     → F04_NAILS/IN/      cruor_render_XXX.mp4
F02_LACERAT/IN/    → F04_NAILS/IN/      voice_XXX.mp3  (audio direct)
F04_NAILS/OUT/     → F05_NUCERIA/IN/    nails_out_XXX.mp4
F05_NUCERIA/OUT/   → ./outputs/         youtube_short/longform_XXX.mp4
```

---

## STATUT BUILD DES TRANSFERTS

| Transfert | Script responsable | Statut |
|-----------|-------------------|--------|
| F03→F04 (cruor_render) | `finish.sh` (F04) — `--video` arg | DONE — 2026-06-13 |
| F02→F04 (voice direct) | `finish.sh` (F04) — `--audio` arg | DONE — 2026-06-13 |
| F04→F05 (nails_out) | `nuceria.py` (F05) — `--input` arg | DONE — 2026-06-13 |
| F05→outputs | `nuceria.py` (F05) — `--output` arg | DONE — 2026-06-13 |
| F02→F03 (prompt+timestamps) | `render.sh` (F03) — EN COURS | EN COURS |
| F01→F02 (script) | `lacerat.py` (F02) — EN COURS | EN COURS |
| CONCEPT→F01 (script gen) | `sanguis.py` (F01) — EN COURS | EN COURS |
