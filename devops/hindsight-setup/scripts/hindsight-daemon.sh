#!/bin/bash
# Start Hindsight API daemon
# LLM settings: managed by Hermes config.yaml → ~/.hindsight/profiles/hermes.env
# Embedding/Reranker: set below (not managed by Hermes plugin)

ENV_FILE="$HOME/.hindsight/profiles/hermes.env"
PID_FILE="$HOME/.hindsight/profiles/hermes.pid"
LOG_FILE="$HOME/.hindsight/profiles/hermes.log"
API_BIN="$HOME/.hermes/hermes-agent/venv/bin/hindsight-api"
PORT=9177
HEALTH_URL="http://localhost:$PORT/health"

# ── Embedding config (Hermes plugin doesn't manage these) ──
# bge-base-en-v1.5 = 768-dim, matches existing Google embeddings in DB
EMBEDDINGS_MODEL="BAAI/bge-base-en-v1.5"
# ───────────────────────────────────────────────────────────

_load_env() {
  if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
  fi
  export HINDSIGHT_API_EMBEDDINGS_LOCAL_MODEL="$EMBEDDINGS_MODEL"
}

_is_running() {
  [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

_find_running_pids() {
  ps aux | grep "[h]indsight-api.*--port $PORT" | awk '{print $2}'
}

_health_check() {
  curl -sf "$HEALTH_URL" >/dev/null 2>&1
}

case "$1" in
  start)
    RUNNING_PIDS=$(_find_running_pids)
    if [ -n "$RUNNING_PIDS" ]; then
      echo "Hindsight daemon already running (PID(s): $RUNNING_PIDS)"
      FIRST_PID=$(echo "$RUNNING_PIDS" | head -1)
      echo "$FIRST_PID" > "$PID_FILE"
      exit 0
    fi

    rm -f "$PID_FILE"
    _load_env

    if [ -f "$LOG_FILE" ]; then
      LOG_SIZE=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)
      if [ "$LOG_SIZE" -gt 104857600 ] 2>/dev/null; then
        echo "[$(date)] Log truncated (was $(du -h "$LOG_FILE" | cut -f1))" > "$LOG_FILE"
      fi
    fi

    nohup "$API_BIN" --port "$PORT" >> "$LOG_FILE" 2>&1 &
    DAEMON_PID=$!
    echo "$DAEMON_PID" > "$PID_FILE"

    echo "Started (PID $DAEMON_PID). Waiting for readiness (up to 60s)..."
    HEALTHY=false
    for i in $(seq 1 30); do
      if _health_check; then
        echo "Hindsight daemon ready (PID $DAEMON_PID, port $PORT)"
        HEALTHY=true
        break
      fi
      sleep 2
    done

    if $HEALTHY; then
      exit 0
    fi

    if kill -0 "$DAEMON_PID" 2>/dev/null; then
      echo "Process alive but not yet healthy after 60s (model download?)"
      echo "Check: tail -f $LOG_FILE"
      exit 0
    else
      echo "FAILED — process exited during startup. Check $LOG_FILE"
      rm -f "$PID_FILE"
      exit 1
    fi
    ;;

  stop)
    STOPPED=false

    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      if kill -0 "$PID" 2>/dev/null; then
        kill "$PID" 2>/dev/null
        for i in $(seq 1 10); do
          kill -0 "$PID" 2>/dev/null || { STOPPED=true; break; }
          sleep 1
        done
      fi
    fi

    RUNNING_PIDS=$(_find_running_pids)
    if [ -n "$RUNNING_PIDS" ]; then
      echo "$RUNNING_PIDS" | xargs kill -9 2>/dev/null
      STOPPED=true
    fi

    rm -f "$PID_FILE"

    if $STOPPED || [ -z "$(_find_running_pids)" ]; then
      echo "Hindsight daemon stopped"
    else
      echo "Hindsight daemon not running"
    fi
    ;;

  restart)
    "$0" stop
    sleep 2
    "$0" start
    ;;

  status)
    RUNNING_PIDS=$(_find_running_pids)
    if [ -n "$RUNNING_PIDS" ]; then
      FIRST_PID=$(echo "$RUNNING_PIDS" | head -1)
      echo "$FIRST_PID" > "$PID_FILE"
      HEALTH=$(_health_check && echo "healthy" || echo "starting")
      echo "Hindsight daemon running (PID $FIRST_PID, port $PORT) — $HEALTH"
      DB_MAIN=$(du -sh "$HOME/.pg0/instances/hindsight/data/" 2>/dev/null | cut -f1)
      DB_EMBED=$(du -sh "$HOME/.pg0/instances/hindsight-embed-hermes/data/" 2>/dev/null | cut -f1)
      [ -n "$DB_MAIN" ] && echo "  DB: main=${DB_MAIN}  embed=${DB_EMBED}"
      [ -f "$LOG_FILE" ] && echo "  Log: $(du -h "$LOG_FILE" | cut -f1)"
    else
      echo "Hindsight daemon not running"
      rm -f "$PID_FILE"
    fi
    ;;

  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac
