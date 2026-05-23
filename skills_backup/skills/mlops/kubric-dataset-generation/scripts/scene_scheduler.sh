#!/usr/bin/env bash
# Docker container queue scheduler — starts next scene when a slot opens
# Called by Hermes cronjob every 30 minutes
# Self-destructs when queue is empty (removes cronjob + script + queue file)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

QUEUE_FILE="$HOME/.hermes/scripts/scene_queue.txt"
LOCK_FILE="$SCRIPT_DIR/scene_scheduler.lock"
LOG_FILE="$SCRIPT_DIR/scene_scheduler.log"
MAX_RUNNING=2

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG_FILE"
}

exec 200>"$LOCK_FILE"
if ! flock -n 200; then
    log "another scheduler instance is running, skip"
    exit 0
fi

if [ ! -s "$QUEUE_FILE" ]; then
    log "queue is empty, self-destructing"
    hermes cron remove f0d5f698fce4 2>/dev/null
    rm -f "$0" "$QUEUE_FILE"
    exit 0
fi

running_count="$(
    docker ps --format '{{.Names}}' 2>>"$LOG_FILE" \
        | grep '_dataset' \
        | wc -l
)"
running_count="${running_count//[[:space:]]/}"

log "running _dataset containers: $running_count"

if [ "$running_count" -ge "$MAX_RUNNING" ]; then
    log "max running containers reached ($running_count/$MAX_RUNNING), wait"
    exit 0
fi

IFS= read -r queue_head < "$QUEUE_FILE"

if [ -z "$queue_head" ]; then
    log "queue head is empty, remove it"
    sed -i '1d' "$QUEUE_FILE"
    exit 0
fi

read -r name scene levels_args <<< "$queue_head"

if [ -z "$name" ] || [ -z "$scene" ]; then
    log "invalid queue head: $queue_head"
    exit 1
fi

if docker ps -a --format '{{.Names}}' 2>>"$LOG_FILE" | grep -x -- "$name" >/dev/null; then
    log "container already exists: $name"
    sed -i '1d' "$QUEUE_FILE"
    exit 0
fi

scene_number="${scene#S}"

log "starting container: name=$name scene=$scene levels_args=$levels_args"

if docker run -d --gpus all \
    --name "$name" \
    --user "$(id -u):$(id -g)" \
    -e KUBRIC_USE_GPU=True \
    -e KUBRIC_GPU_BACKEND=OPTIX \
    -e PYTHONDONTWRITEBYTECODE=1 \
    -v /home/lzy/project/slot-datamaking:/workspace \
    -v /home/lzy/project/slot-datamaking/kubric:/kubric \
    -w /workspace \
    kubric-gpu \
    "task/task6-脚本编写/generate_s${scene_number}_dataset.py" \
    $levels_args >> "$LOG_FILE" 2>&1; then
    sed -i '1d' "$QUEUE_FILE"
    log "container started successfully: $name"
else
    log "container failed to start, keep queue head: $name"
    exit 1
fi

# Check if queue is now empty after successful start
if [ ! -s "$QUEUE_FILE" ]; then
    log "all tasks dispatched, self-destructing"
    hermes cron remove f0d5f698fce4 2>/dev/null
    rm -f "$0" "$QUEUE_FILE"
fi
