#!/bin/bash
# Free the TCP port used by `make serve`.
#
# Only kills a process whose *entire* command line equals the expected one, so a
# port taken by something else is reported rather than killed. SIGTERM alone is
# not enough: python's http.server shuts down gracefully and can hang while a
# browser keep-alive connection is still open, so we escalate to SIGKILL and
# only return once the port is genuinely free.
#
# Usage: free_port.sh <port> <exact command line>
set -uo pipefail

PORT="${1:?port required}"
CMD="${2:?command line required}"

# PIDs listening on $PORT, via ss, falling back to lsof.
listening_pids() {
  if command -v ss > /dev/null 2>&1; then
    ss -ltnp 2>/dev/null \
      | awk -v p=":$PORT\$" '$4 ~ p' \
      | grep -o 'pid=[0-9]*' | cut -d= -f2 | sort -u
  elif command -v lsof > /dev/null 2>&1; then
    lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | sort -u
  fi
}

# True while any process still holds the port.
port_busy() { [ -n "$(listening_pids)" ]; }

# Wait up to ~3s for the port to be released.
wait_for_free() {
  for _ in $(seq 30); do
    port_busy || return 0
    sleep .1
  done
  return 1
}

port_busy || exit 0

for pid in $(listening_pids); do
  # tr: /proc cmdline is NUL-separated.
  actual=$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null | sed 's/ *$//')
  if [ "$actual" != "$CMD" ]; then
    echo "Port $PORT is held by PID $pid, which is not our server:" >&2
    echo "  $actual" >&2
    echo "Refusing to kill it. Stop it yourself, or use a different port:" >&2
    echo "  make serve PORT=8001" >&2
    exit 1
  fi
done

kill $(listening_pids) 2> /dev/null
if ! wait_for_free; then
  # Graceful shutdown blocked (usually an open browser connection) - force it.
  kill -9 $(listening_pids) 2> /dev/null
  if ! wait_for_free; then
    echo "Could not free port $PORT (still held by: $(listening_pids))" >&2
    exit 1
  fi
fi

echo "Stopped previous server on port $PORT"
