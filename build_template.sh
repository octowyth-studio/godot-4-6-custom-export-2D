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
build_jobs="${GEM_BUILD_JOBS:-2}"

if [[ ! -f "$source_dir/SConstruct" || ! -f "$source_dir/version.py" ]]; then
    echo "A complete matching Godot source checkout is required." >&2
    exit 2
fi
if [[ ! "$build_jobs" =~ ^[1-9][0-9]*$ ]]; then
    echo "GEM_BUILD_JOBS must be a positive integer." >&2
    exit 2
fi
if ! command -v emcc >/dev/null || ! command -v scons >/dev/null; then
    echo "Activate Emscripten 4.0.20 and install SCons before running this script." >&2
    exit 2
fi
python3 -c 'import brotli' || { echo "Install the Python brotli package." >&2; exit 2; }

cd "$source_dir"
for mode in release debug; do
    assertions=no
    if [[ "$mode" == debug ]]; then
        assertions=yes
    fi
    scons -j"$build_jobs" platform=web target="template_$mode" \
        profile="$kit_dir/GemWorkshop_web.py" \
        build_profile="$kit_dir/GemWorkshop_web.gdbuild" \
        use_assertions="$assertions" \
        cache_path="$output_dir/scons_cache" cache_limit=4
done

python3 "$kit_dir/package_template.py" "$source_dir/bin" "$output_dir"
