# ANGRON — CAMPAIGN LOG

> Journal de production de la flotte ANGRON.  
> Chaque vidéo produite est consignée ici avec son état, ses métriques et ses observations.

---

## ÉTAT DU CODEBASE

| Frigate | Script principal | Statut build |
|---------|-----------------|--------------|
| F01_SANGUIS | `sanguis.py` | EN COURS |
| F02_LACERAT | `whisper_sync.py` | DONE — 2026-06-13 |
| F03_CRUOR | `render.sh` | DONE — 2026-06-13 |
| F04_NAILS | `finish.sh` | DONE — 2026-06-13 |
| F05_NUCERIA | `nuceria.py` | DONE — 2026-06-13 |

---

## FORMAT D'ENTRÉE

```
### [ANGRON-XXX] — NOM DU CONCEPT
- **Date** : YYYY-MM-DD
- **Format** : Short 9:16 / Long-form 16:9
- **Concept** : description courte
- **Durée vidéo** : Xs
- **Statut** : F01_SANGUIS → F02_LACERAT → F03_CRUOR → F04_NAILS → F05_NUCERIA → UPLOAD → LIVE
- **Observations** : notes opérateur
- **Performances** : vues / likes / rétention (à remplir post-upload)
```

---

## LOG

### [ANGRON-001] — EN ATTENTE
- **Date** : —
- **Format** : —
- **Concept** : —
- **Statut** : `INIT`
- **Observations** : Premier lancement. Validation de toute la chaîne F01→F05.

---

## LÉGENDE STATUTS

| Statut | Signification |
|--------|---------------|
| `INIT` | Projet créé, aucune frigate lancée |
| `F01_DONE` | Script validé par l'opérateur |
| `F02_DONE` | Prompt Manim validé |
| `F03_DONE` | Vidéo brute validée |
| `F04_DONE` | Audio fusionné |
| `F05_DONE` | Camouflage appliqué, MP4 final prêt |
| `UPLOADED` | Vidéo uploadée sur YouTube |
| `LIVE` | Vidéo en ligne, collecte métriques |
| `FAILED` | Échec à une étape — voir observations |
