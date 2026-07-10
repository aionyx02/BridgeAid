#!/usr/bin/env bash
#
# BridgeAid deploy — build the Docker image and (re)create the container.
#
# Two modes, chosen by whether SSH_HOST is set:
#   * Local build   (SSH_HOST empty): run on a host that has Docker + this repo.
#   * Remote deploy (SSH_HOST set):   run from your dev machine — the build
#     context is shipped over SSH, built on the remote, and the container is
#     (re)created there. No registry needed.
#
# Config resolution: environment vars  >  scripts/deploy.env  >  built-in defaults.
# Copy scripts/deploy.env.example -> scripts/deploy.env (gitignored) for your host.
#
# Usage:
#   scripts/deploy.sh                 # deploy per config (local or remote)
#   SSH_HOST=my-vps scripts/deploy.sh # one-off remote target
#   PORT=9000 scripts/deploy.sh       # one-off port override
#
# Requires: docker (+ curl) on the build host; ssh + tar for remote mode.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ---- config (env > deploy.env > defaults) ----
# deploy.env uses ':=' so real environment variables still take precedence.
[ -f "$SCRIPT_DIR/deploy.env" ] && . "$SCRIPT_DIR/deploy.env"
: "${IMAGE:=bridgeaid:latest}"
: "${NAME:=bridgeaid}"
: "${PORT:=8080}"                       # host port on 127.0.0.1 (container always listens on 8080)
: "${SSH_HOST:=}"                       # empty => build locally
: "${REMOTE_DIR:=bridgeaid}"            # dir under the remote $HOME for the build context
: "${ENV_FILE:=$REPO_ROOT/.line.env}"  # docker --env-file (LINE secrets etc.); optional
: "${PUBLIC_URL:=}"                     # only used for the closing message

# Files the image build needs (keep in sync with the Dockerfile COPY lines) + this script.
SHIP="pyproject.toml uv.lock Dockerfile .dockerignore backend demo data scripts/deploy.sh"

server_run() {
  cd "$REPO_ROOT"
  echo "==> build $IMAGE  (arch $(uname -m))"
  docker build -t "$IMAGE" .

  echo "==> (re)create container '$NAME' on 127.0.0.1:$PORT"
  docker rm -f "$NAME" >/dev/null 2>&1 || true

  local env_args=()
  if [ -f "$ENV_FILE" ]; then
    env_args=(--env-file "$ENV_FILE")
    echo "    env-file: $ENV_FILE"
  else
    echo "    WARNING: no env-file at $ENV_FILE -> degraded mode (LINE disabled)"
  fi

  docker run -d --name "$NAME" --restart unless-stopped \
    "${env_args[@]}" \
    -p "127.0.0.1:$PORT:8080" "$IMAGE" >/dev/null

  echo "==> wait for health"
  local ok=0 i
  for i in $(seq 1 30); do
    if curl -sf "http://localhost:$PORT/healthz" >/dev/null 2>&1; then ok=1; echo "    ready after ${i}s"; break; fi
    sleep 1
  done
  if [ "$ok" != 1 ]; then
    echo "    ERROR: not healthy after 30s; last logs:"; docker logs --tail 20 "$NAME" || true; exit 1
  fi
  echo -n "==> /healthz: "; curl -s "http://localhost:$PORT/healthz"; echo
  [ -n "$PUBLIC_URL" ] && echo "==> public: $PUBLIC_URL/  (demo: $PUBLIC_URL/demo/)"
  return 0
}

# Already on the build host (invoked by the remote branch, or a local build with no SSH_HOST).
if [ "${1:-}" = "--server-run" ] || [ -z "$SSH_HOST" ]; then
  server_run
  exit 0
fi

# Remote mode: ship the context + this script, then run --server-run on the remote.
echo "==> ship build context to $SSH_HOST:~/$REMOTE_DIR"
ssh "$SSH_HOST" "mkdir -p '$REMOTE_DIR/scripts'"
tar czf - -C "$REPO_ROOT" $SHIP | ssh "$SSH_HOST" "tar xzf - -C '$REMOTE_DIR'"
echo "==> build + deploy on $SSH_HOST"
# ENV_FILE is intentionally not forwarded: the remote resolves its own default
# ($REMOTE_DIR/.line.env). Override via a remote scripts/deploy.env if needed.
ssh "$SSH_HOST" "IMAGE='$IMAGE' NAME='$NAME' PORT='$PORT' PUBLIC_URL='$PUBLIC_URL' bash '$REMOTE_DIR/scripts/deploy.sh' --server-run"
