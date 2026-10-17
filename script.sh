#!/usr/bin/env bash
# Usage: ./script.sh start | stop | status
# Lance fetch_data.py toutes les 5 min en arrière-plan.

cd "$(dirname "$(readlink -f "$0")")"

PIDFILE=.fetch.pid
LOG=fetch.log
INTERVAL=300
PYTHON=../env/bin/python
[ -x "$PYTHON" ] || PYTHON=python3

is_running() {
    [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null
}

case "$1" in
    start)
        if is_running; then
            echo "Déjà actif (PID $(cat "$PIDFILE"))"
            exit 0
        fi
        nohup bash -c "
            while true; do
                echo \"[\$(date '+%F %T')] fetch\"
                $PYTHON fetch_data.py || echo 'erreur fetch_data.py'
                sleep $INTERVAL
            done
        " >> "$LOG" 2>&1 &
        echo $! > "$PIDFILE"
        echo "Démarré (PID $!), toutes les $((INTERVAL / 60)) min, logs dans Projet/$LOG"
        ;;
    stop)
        if is_running; then
            pid=$(cat "$PIDFILE")
            pkill -P "$pid" 2>/dev/null   # enfants (sleep / python)
            kill "$pid"
            rm -f "$PIDFILE"
            echo "Arrêté"
        else
            rm -f "$PIDFILE"
            echo "Pas actif"
        fi
        ;;
    status)
        if is_running; then echo "Actif (PID $(cat "$PIDFILE"))"; else echo "Inactif"; fi
        ;;
    *)
        echo "Usage: $0 start|stop|status"
        exit 1
        ;;
esac
