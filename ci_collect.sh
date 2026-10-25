#!/usr/bin/env bash
# Lancé par GitHub Actions : fetch toutes les 5 min pendant ~5h40,
# l'historique vit dans la release GitHub "data".
set -uo pipefail

TAG=data
FILE=historique_stations.csv
DURATION_MIN=${DURATION_MIN:-340}
UPLOAD_EVERY=${UPLOAD_EVERY:-6}   # upload toutes les 6 collectes (~30 min)
PYTHON=${PYTHON:-python}
END=$(( $(date +%s) + DURATION_MIN * 60 ))

# --- récupération de l'historique (on n'écrase jamais la release sans l'avoir lu)
if ! names=$(gh release view "$TAG" --json assets -q '.assets[].name' 2>/dev/null); then
    gh release create "$TAG" --title "$TAG" --notes "données" || exit 1
    names=""
fi
if grep -qx "$FILE" <<< "$names"; then
    ok=0
    for i in 1 2 3 4 5; do
        gh release download "$TAG" -p "$FILE" --clobber && { ok=1; break; }
        sleep 10
    done
    [ "$ok" = 1 ] || { echo "Téléchargement impossible, arrêt pour ne pas écraser l'historique" >&2; exit 1; }
fi
touch "$FILE"
# ligne finale incomplète éventuelle : on termine la ligne
[ -s "$FILE" ] && [ -n "$(tail -c1 "$FILE")" ] && echo >> "$FILE"

# --- intégration (idempotente) de l'historique local figé de la release "data-backfill"
if gh release download data-backfill -p historique_backfill.csv -O backfill.csv --clobber 2>/dev/null; then
    if "$PYTHON" merge_sources.py "$FILE" backfill.csv -o merged.tmp; then
        mv merged.tmp "$FILE"
    else
        echo "Fusion du backfill échouée, historique inchangé" >&2
    fi
    rm -f backfill.csv merged.tmp
fi
START_LINES=$(wc -l < "$FILE")
echo "Historique de départ : $START_LINES lignes"

upload() {
    local n; n=$(wc -l < "$FILE")
    if [ "$n" -lt "$START_LINES" ]; then
        echo "Fichier plus court qu'au départ ($n < $START_LINES), pas d'upload" >&2
        return 1
    fi
    for i in 1 2 3; do
        gh release upload "$TAG" "$FILE" --clobber && { echo "Upload OK ($n lignes)"; return 0; }
        sleep 10
    done
    return 1
}
trap upload EXIT

# --- boucle de collecte, alignée sur les multiples de 5 min
count=0
while [ "$(date +%s)" -lt "$END" ]; do
    sleep $(( 300 - $(date +%s) % 300 ))
    echo "[$(date -u '+%F %T')] fetch"
    "$PYTHON" fetch_data.py > /dev/null || echo "erreur fetch_data.py" >&2
    count=$(( count + 1 ))
    if [ $(( count % UPLOAD_EVERY )) -eq 0 ]; then upload || true; fi
done
