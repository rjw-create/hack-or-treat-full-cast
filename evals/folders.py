"""Which output folder the evals commands read when none is given on the command line."""
import os
import sys
from pathlib import Path

from core.config import output_dir

# Same path the README's placeholder step writes to, relative to the repo root where the commands run.
PLACEHOLDER_DIR = Path("output") / "placeholder"


def default_folder():
    """(folder, is_placeholder), or (None, False) after printing what to do when neither folder exists.

    The real render lives outside the repo, so a fresh clone doesn't have it; the placeholder output is
    the next best thing. A folder set with FULLCAST_OUTPUT_DIR is used as given, never swapped.
    """
    real = output_dir()
    if real.is_dir() or os.environ.get("FULLCAST_OUTPUT_DIR"):
        return real, False
    if PLACEHOLDER_DIR.is_dir():
        print(f"No real render at {real.as_posix()}; using the placeholder output in {PLACEHOLDER_DIR.as_posix()}.",
              file=sys.stderr)
        return PLACEHOLDER_DIR, True
    print(f"ERROR no output folder to check: {real.as_posix()} and {PLACEHOLDER_DIR.as_posix()} are both missing. "
          "Run the placeholder steps in the README first (python -m core.placeholders --out output/placeholder), "
          "from the repo root.", file=sys.stderr)
    return None, False
