#!/bin/bash
# Batch git clone for paper code repos
# Usage: bash clone_repos.sh
# Note: GitHub may be slow from WSL. Try multiple URL variants if a repo fails.

cd "${1:-.}"

clone_repo() {
    local id="$1" url="$2"
    local dir="$id/code"
    [ -d "$dir" ] && [ "$(ls -A $dir 2>/dev/null)" ] && echo "EXISTS: $id" && return
    rm -rf "$dir"
    git clone --depth 1 "$url" "$dir" 2>/dev/null
    if [ -d "$dir" ] && [ "$(ls -A $dir 2>/dev/null)" ]; then
        echo "OK: $id"
    else
        rm -rf "$dir"
        echo "FAIL: $id"
    fi
}

# Example entries - customize per survey
# clone_repo "001_phydnet" "https://github.com/vincent-leguen/PhyDNet.git"
# clone_repo "002_predrnn" "https://github.com/thuml/predrnn-pytorch.git"
