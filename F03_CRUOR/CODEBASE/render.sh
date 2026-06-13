#!/usr/bin/env bash
# render.sh — F03_CRUOR : render Manim headless via Docker.
#
# Usage :
#   bash F03_CRUOR/CODEBASE/render.sh \
#     --scene F03_CRUOR/CODEBASE/scene_XXX.py \
#     --output F03_CRUOR/OUT/cruor_render_XXX.mp4 \
#     --format short|longform
#
# Claude INACTIF pendant l'exécution. Signal de fin : DONE.txt (OK ou ERROR).

set -euo pipefail

DOCKER_IMAGE="ghcr.io/kioka8877-ux/angron:latest"

# --- Parse args ---
SCENE=""
OUTPUT=""
FORMAT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scene)  SCENE="$2";  shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    --format) FORMAT="$2"; shift 2 ;;
    *) echo "[CRUOR] Argument inconnu : $1" >&2; exit 1 ;;
  esac
done

# --- Validation ---
if [[ -z "$SCENE" || -z "$OUTPUT" || -z "$FORMAT" ]]; then
  echo "[CRUOR] ERREUR : --scene, --output et --format sont obligatoires." >&2
  exit 1
fi

if [[ "$FORMAT" != "short" && "$FORMAT" != "longform" ]]; then
  echo "[CRUOR] ERREUR : --format doit être 'short' ou 'longform'." >&2
  exit 1
fi

if [[ ! -f "$SCENE" ]]; then
  echo "[CRUOR] ERREUR : scene introuvable : $SCENE" >&2
  exit 1
fi

OUTPUT_DIR="$(dirname "$OUTPUT")"
OUTPUT_NAME="$(basename "$OUTPUT")"
DONE_FILE="$OUTPUT_DIR/DONE.txt"
ERROR_LOG="$OUTPUT_DIR/error.log"
WORKSPACE="$(pwd)"

mkdir -p "$OUTPUT_DIR"

echo "[CRUOR] Render Manim headless..."
echo "  Scene  : $SCENE"
echo "  Output : $OUTPUT"
echo "  Format : $FORMAT"
echo "  Image  : $DOCKER_IMAGE"

START_TS=$(date +%s)

# --- Docker render ---
# Monte le workspace en /workspace dans le container.
# Xvfb gère l'affichage OpenGL headless.
# Manim écrit dans /tmp/media/, on récupère le MP4 et on le déplace.
SCENE_IN_CONTAINER="/workspace/$SCENE"
MEDIA_DIR="/tmp/media_cruor"

docker run --rm \
  --name "angron_cruor_$$" \
  -v "${WORKSPACE}:/workspace" \
  -e DISPLAY=:99 \
  "$DOCKER_IMAGE" \
  bash -c "
    set -e
    Xvfb :99 -screen 0 1x1x24 2>/dev/null &
    sleep 1

    manim render \
      --media_dir ${MEDIA_DIR} \
      --format mp4 \
      --fps 60 \
      \"${SCENE_IN_CONTAINER}\" AngronScene \
      2>&1

    # Manim crée une arborescence — on cherche le MP4 produit
    MP4=\$(find ${MEDIA_DIR} -name '*.mp4' | head -1)
    if [[ -z \"\$MP4\" ]]; then
      echo 'ERROR: aucun MP4 trouvé dans ${MEDIA_DIR}' >&2
      exit 2
    fi

    cp \"\$MP4\" /workspace/${OUTPUT}
    echo \"MP4 copié : \$MP4 → /workspace/${OUTPUT}\"
  " 2>&1 | tee "$ERROR_LOG"

DOCKER_EXIT="${PIPESTATUS[0]}"
END_TS=$(date +%s)
RENDER_TIME=$(( END_TS - START_TS ))

if [[ "$DOCKER_EXIT" -ne 0 ]]; then
  echo "[CRUOR] RENDER FAILED (exit $DOCKER_EXIT) — voir $ERROR_LOG" >&2
  cat > "$DONE_FILE" <<EOF
STATUS=ERROR
SCENE=$SCENE
FORMAT=$FORMAT
RENDER_TIME=${RENDER_TIME}s
ERROR_LOG=$ERROR_LOG
EOF
  exit "$DOCKER_EXIT"
fi

# --- Extraire durée et frames via ffprobe ---
DURATION=$(ffprobe -v quiet -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 "$OUTPUT" 2>/dev/null || echo "0")
FRAMES=$(ffprobe -v quiet -select_streams v:0 \
  -show_entries stream=nb_frames \
  -of default=noprint_wrappers=1:nokey=1 "$OUTPUT" 2>/dev/null || echo "0")

echo "[CRUOR] Render OK — durée ${DURATION}s, ${FRAMES} frames, ${RENDER_TIME}s de calcul"

cat > "$DONE_FILE" <<EOF
STATUS=OK
OUTPUT=$OUTPUT
DURATION=${DURATION}s
FRAMES=$FRAMES
RENDER_TIME=${RENDER_TIME}s
FORMAT=$FORMAT
EOF

echo "[CRUOR] Signal  : $DONE_FILE"
echo "[CRUOR] DONE    : $OUTPUT"
