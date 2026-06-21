#!/bin/zsh

PROJECT_DIR="/Users/shark-li/Documents/足球⚽️/football-jc-analysis"
API_HEALTH_URL="http://127.0.0.1:8765/api/health"
DASHBOARD_HEALTH_URL="http://127.0.0.1:8766/"
DASHBOARD_URL="http://127.0.0.1:8766/?launcher=desktop"
API_LOG="$PROJECT_DIR/reports/desktop_launcher_api.log"
DASHBOARD_LOG="$PROJECT_DIR/reports/desktop_launcher_dashboard.log"

cd "$PROJECT_DIR" || exit 1
mkdir -p reports

if command -v /opt/homebrew/bin/python3 >/dev/null 2>&1; then
  PYTHON_BIN="/opt/homebrew/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  PYTHON_BIN="/usr/bin/python3"
fi

health_ok() {
  /usr/bin/curl -fsS --max-time 3 "$1" >/dev/null 2>&1
}

if ! health_ok "$API_HEALTH_URL"; then
  /usr/bin/nohup "$PYTHON_BIN" -m src.cli.serve_api --host 127.0.0.1 --port 8765 > "$API_LOG" 2>&1 &
fi

for _ in 1 2 3 4 5 6 7 8; do
  if health_ok "$API_HEALTH_URL"; then
    break
  fi
  /bin/sleep 1
done

if ! health_ok "$DASHBOARD_HEALTH_URL"; then
  /usr/bin/nohup "$PYTHON_BIN" -m src.cli.serve_dashboard --host 127.0.0.1 --port 8766 --api-base http://127.0.0.1:8765 > "$DASHBOARD_LOG" 2>&1 &
fi

for _ in 1 2 3 4 5 6 7 8; do
  if health_ok "$DASHBOARD_HEALTH_URL"; then
    break
  fi
  /bin/sleep 1
done

/usr/bin/open "$DASHBOARD_URL"
