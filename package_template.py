import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

import brotli


def main():
    source_dir, output_dir = map(Path, sys.argv[1:])
    candidates = list(source_dir.glob("godot.web.template_release.wasm32*.zip"))
    if len(candidates) != 1:
        raise SystemExit("Use a clean Godot source checkout: expected one release ZIP.")
    with zipfile.ZipFile(candidates[0]) as archive:
        if archive.testzip() is not None:
            raise SystemExit("The template ZIP is damaged.")
        names = [name for name in archive.namelist() if name.endswith(".wasm")]
        if len(names) != 1 or not any(name.endswith(".js") for name in archive.namelist()):
            raise SystemExit("The template ZIP must contain one WASM file and JavaScript.")
        wasm = archive.read(names[0])
    if wasm[:8] != b"\x00asm\x01\x00\x00\x00":
        raise SystemExit("The WASM header is invalid.")
    target = output_dir / "web_nothreads_release.zip"
    shutil.copy2(candidates[0], target)
    report = {
        "template_zip_bytes": target.stat().st_size,
        "template_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "wasm_raw_bytes": len(wasm),
        "wasm_gzip_9_bytes": len(gzip.compress(wasm, compresslevel=9, mtime=0)),
        "wasm_brotli_11_bytes": len(brotli.compress(wasm, quality=11)),
        "note": "Compression measurements only; the host determines transferred bytes. No game test was run.",
    }
    text = json.dumps(report, indent=2) + "\n"
    (output_dir / "size_report.json").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
