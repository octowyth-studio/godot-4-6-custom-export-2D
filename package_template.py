import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

import brotli


def inspect_template(source_dir, mode):
    stem = f"godot.web.template_{mode}.wasm32"
    candidates = [source_dir / f"{stem}{suffix}.zip" for suffix in (".nothreads", "")]
    candidates = [path for path in candidates if path.is_file()]
    if len(candidates) != 1:
        raise ValueError(f"Expected one {mode} archive in a clean Godot bin folder; found {len(candidates)}.")
    source = candidates[0]
    with zipfile.ZipFile(source) as archive:
        if archive.testzip() is not None:
            raise ValueError(f"Damaged {mode} template ZIP.")
        names = archive.namelist()
        wasm_names = [name for name in names if name.endswith(".wasm")]
        if len(wasm_names) != 1:
            raise ValueError(f"The {mode} archive must contain exactly one WASM file.")
        if not any(name.endswith(".js") for name in names) or not any(name.endswith(".html") for name in names):
            raise ValueError(f"The {mode} archive needs the engine JavaScript and HTML shell.")
        wasm = archive.read(wasm_names[0])
    if len(wasm) <= 8 or wasm[:8] != b"\x00asm\x01\x00\x00\x00":
        raise ValueError(f"Invalid or empty {mode} WASM header.")
    report = {
        "target": f"template_{mode}",
        "output": f"web_nothreads_{mode}.zip",
        "source_archive": source.name,
        "template_zip_bytes": source.stat().st_size,
        "template_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "wasm_sha256": hashlib.sha256(wasm).hexdigest(),
        "wasm_raw_bytes": len(wasm),
        "wasm_gzip_9_bytes": len(gzip.compress(wasm, compresslevel=9, mtime=0)),
        "wasm_brotli_11_bytes": len(brotli.compress(wasm, quality=11)),
    }
    return source, report


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: package_template.py GODOT_BIN_DIRECTORY OUTPUT_DIRECTORY")
    source_dir, output_dir = map(Path, sys.argv[1:])
    try:
        entries = [inspect_template(source_dir, mode) for mode in ("release", "debug")]
        if entries[0][1]["wasm_sha256"] == entries[1][1]["wasm_sha256"]:
            raise ValueError("Release and debug WASM files are identical; check the build targets.")
    except (ValueError, OSError, zipfile.BadZipFile) as error:
        raise SystemExit(str(error)) from error
    output_dir.mkdir(parents=True, exist_ok=True)
    for source, report in entries:
        target = output_dir / report["output"]
        temporary = target.with_suffix(".zip.part")
        shutil.copy2(source, temporary)
        temporary.replace(target)
    report = {
        "templates": {item["target"]: item for _, item in entries},
        "note": "Archive and WASM header checks only; no game runtime test. Compression sizes are estimates, not measured CDN transfers.",
    }
    text = json.dumps(report, indent=2) + "\n"
    (output_dir / "size_report.json").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
