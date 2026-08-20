#!/usr/bin/env python3
"""Convert a MIDI file to daw-mcp's batch_set_notes note-array format."""
import argparse
import json
import pathlib
import sys

from music21 import converter


def midi_to_notes(midi_path: pathlib.Path) -> pathlib.Path:
    """Parse midi_path and write its notes as [x, y, velocity, duration] JSON, return the output path.

    x/duration are beat positions (music21 quarterLength), matching
    daw-mcp's batch_set_notes ultra-lean note format exactly.
    """
    if not midi_path.is_file():
        raise FileNotFoundError(f"MIDI file not found: {midi_path}")

    try:
        score = converter.parse(str(midi_path))
    except Exception as e:
        raise RuntimeError(f"music21 failed to parse {midi_path}: {e}") from e

    notes = []
    for el in score.flatten().notes:
        pitches = el.pitches if hasattr(el, "pitches") else [el.pitch]
        velocity = el.volume.velocity if el.volume.velocity is not None else 100
        for p in pitches:
            notes.append([
                round(float(el.offset), 4),
                p.midi,
                velocity,
                round(float(el.duration.quarterLength), 4),
            ])
    notes.sort(key=lambda n: n[0])

    target = midi_path.with_suffix(".notes.json")
    if target.exists():
        raise RuntimeError(f"{target} already exists; move or delete it first")
    target.write_text(json.dumps(notes))
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a MIDI file to a batch_set_notes note array.")
    parser.add_argument("midi_path", type=pathlib.Path, help="Path to the input MIDI file")
    args = parser.parse_args()

    try:
        output_path = midi_to_notes(args.midi_path)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
