#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: bash build_template.sh GODOT_SOURCE_DIRECTORY OUTPUT_DIRECTORY" >&2
    exit 2
fi

kit_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_dir="$(cd "$1" && pwd)"
mkdir -p "$2"
output_dir="$(cd "$2" && pwd)"
test -f "$source_dir/SConstruct"
command -v emcc >/dev/null
command -v scons >/dev/null

cd "$source_dir"
scons -j2 platform=web target=template_release \
    profile="$kit_dir/GemWorkshop_web.py" \
    build_profile="$kit_dir/GemWorkshop_web.gdbuild" \
    cache_path="$output_dir/scons_cache" cache_limit=4

python3 "$kit_dir/package_template.py" "$source_dir/bin" "$output_dir"
