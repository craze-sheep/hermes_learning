#!/bin/bash
# Batch PDF download from arxiv
# Usage: bash download_pdfs.sh
# Note: Sequential is more reliable than parallel on slow networks

cd "${1:-.}"

download() {
    local url="$1"
    local dest="$2"
    if [ ! -f "$dest" ]; then
        curl -sL --connect-timeout 20 --max-time 90 -o "$dest" "$url" 2>/dev/null
        if [ $? -eq 0 ] && [ -s "$dest" ] && [ $(stat -c%s "$dest") -gt 5000 ]; then
            echo "OK: $dest ($(du -h "$dest" | cut -f1))"
        else
            rm -f "$dest"
            echo "FAIL: $dest"
        fi
    else
        echo "EXISTS: $dest"
    fi
}

# Example entries - customize per survey
# download "https://arxiv.org/pdf/2003.01460" "001_phydnet/phydnet.pdf"
# download "https://arxiv.org/pdf/2103.09504" "002_predrnn/predrnn.pdf"
