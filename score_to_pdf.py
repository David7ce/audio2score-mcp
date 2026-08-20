#!/usr/bin/env python3
"""Render a MIDI/MusicXML file to PDF using MuseScore's converter mode."""
import argparse
import json
import pathlib
import subprocess
import sys
import tempfile

MUSESCORE_EXE = pathlib.Path(r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe")


def score_to_pdf(score_path: pathlib.Path) -> pathlib.Path:
    """Render score_path (MIDI, MusicXML, etc.) to PDF via MuseScore, return the output path."""
    if not score_path.is_file():
        raise FileNotFoundError(f"Score file not found: {score_path}")
    if not MUSESCORE_EXE.is_file():
        raise RuntimeError(f"MuseScore not found at {MUSESCORE_EXE}")

    target = score_path.with_suffix(".pdf")
    if target.exists():
        raise RuntimeError(f"{target} already exists; move or delete it first")

    # Plain "-o out.pdf in.mid" launches a full GUI session and is
    # unreliable outside an interactive desktop (confirmed: crashes on a
    # failed network call, or hangs, when run from an agent/non-interactive
    # context). "-j job.json" converter mode avoids the GUI entirely and is
    # what actually works headless - confirmed working from native
    # PowerShell. Absolute paths in the job file avoid any working
    # directory ambiguity.
    job = [{"in": str(score_path), "out": str(target)}]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(job, f)
        job_path = pathlib.Path(f.name)

    try:
        result = subprocess.run(
            [str(MUSESCORE_EXE), "-j", str(job_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"MuseScore timed out rendering {score_path}") from e
    finally:
        job_path.unlink(missing_ok=True)

    if not target.is_file():
        raise RuntimeError(
            f"MuseScore did not produce {target}. "
            f"stdout: {result.stdout!r} stderr: {result.stderr!r}"
        )
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a MIDI/MusicXML file to PDF via MuseScore.")
    parser.add_argument("score_path", type=pathlib.Path, help="Path to the input score file (.mid, .musicxml, .mxl)")
    args = parser.parse_args()

    try:
        output_path = score_to_pdf(args.score_path)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
