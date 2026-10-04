#!/usr/bin/env bash
set -euo pipefail

if ! command -v gs &> /dev/null; then
    echo "Fel: Ghostscript (gs) är inte installerat." >&2
    exit 1
fi

TARGET_DIR="${1:-.}"
OUTPUT_DIR="${TARGET_DIR}/cmyk_output"
mkdir -p "$OUTPUT_DIR"

shopt -s nullglob
for file in "$TARGET_DIR"/*.pdf "$TARGET_DIR"/*.eps; do
    filename=$(basename "$file")
    [[ "$filename" == *"_cmyk."* ]] && continue
    
    ext="${filename##*.}"
    base="${filename%.*}"
    device=$([ "$ext" == "pdf" ] && echo "pdfwrite" || echo "eps2write")
    
    echo "Konverterar: $filename -> ${base}_cmyk.${ext}"
    gs -dSAFER -dBATCH -dNOPAUSE        -sDEVICE="$device"        -sColorConversionStrategy=CMYK        -dProcessColorModel=/DeviceCMYK        -sOutputFile="${OUTPUT_DIR}/${base}_cmyk.${ext}"        "$file" > /dev/null
done
echo "Klart! Filer sparades i: ${OUTPUT_DIR}"
