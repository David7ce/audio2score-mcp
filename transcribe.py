#!/usr/bin/env python3
"""Transcribe an audio file to MIDI using basic-pitch."""
import argparse
import contextlib
import io
import pathlib
import sys

from basic_pitch.inference import predict_and_save
from basic_pitch import ICASSP_2022_MODEL_PATH


def transcribe(audio_path: pathlib.Path) -> pathlib.Path:
    """Run basic-pitch on audio_path, return the path to the written .mid file."""
    if not audio_path.is_file():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    output_dir = audio_path.parent
    try:
        # basic-pitch's predict_and_save prints unconditionally (including
        # emoji status lines) straight to stdout. That crashes on a
        # non-UTF-8 Windows console, and would corrupt the MCP server's
        # stdio JSON-RPC stream if it ran uncaptured - redirect it away.
        with contextlib.redirect_stdout(io.StringIO()):
            predict_and_save(
                [str(audio_path)],
                str(output_dir),
                save_midi=True,
                sonify_midi=False,
                save_model_outputs=False,
                save_notes=False,
                model_or_model_path=ICASSP_2022_MODEL_PATH,
            )
    except Exception as e:
        raise RuntimeError(f"basic-pitch failed on {audio_path}: {type(e).__name__}: {e}") from e

    # predict_and_save always names its output "<stem>_basic_pitch.mid" -
    # rename to match this project's "same base filename" convention.
    generated = output_dir / f"{audio_path.stem}_basic_pitch.mid"
    target = output_dir / f"{audio_path.stem}.mid"
    if not generated.is_file():
        raise RuntimeError(f"basic-pitch did not produce expected output: {generated}")
    if target.exists():
        raise RuntimeError(f"{target} already exists; move or delete it first")
    generated.replace(target)
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe an audio file to MIDI.")
    parser.add_argument("audio_path", type=pathlib.Path, help="Path to the input audio file")
    args = parser.parse_args()

    try:
        output_path = transcribe(args.audio_path)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
