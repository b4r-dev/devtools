# standard library
import sys
from pathlib import Path


# dependencies
import numpy as np


# constants
DOT = "."
DTYPES = [
    ("time", "a28"),
    ("reserved1", "a4"),
    ("obsnum", "i8"),
    ("scantype", "a8"),
    ("scanmode", "a8"),
    ("chopperpos", "a8"),
    ("scancount", "i8"),
    ("speccount", "i8"),
    ("integtime", "i4"),
    ("reserved2", "a172"),
    ("array", ("f4", 32768)),
]
OBSNUM = "obsnum"


# helper functions
def get_obsnum(xffts: Path, /) -> int:
    """Read the observation number from an XFFTS log."""
    with open(xffts, "rb") as f:
        try:
            log = np.frombuffer(f.read(), dtype=DTYPES)
        except ValueError:
            return 0

        try:
            obsnum = int(log[OBSNUM][0])
        except IndexError:
            return 0

        if 0 < obsnum < 1000000:
            return obsnum
        else:
            return 0


def rename(xffts: Path, /) -> Path:
    """Rename an XFFTS log to include its observation number."""
    if OBSNUM in xffts.name:
        return xffts

    parts = xffts.name.split(DOT)
    parts.insert(1, f"{OBSNUM}{get_obsnum(xffts):0>6}")
    return xffts.rename(xffts.with_name(DOT.join(parts)))


# main part
if __name__ == "__main__":
    try:
        path = Path(sys.argv[1]).resolve()
    except IndexError:
        path = Path().resolve()

    for xffts in list(path.glob("**/xffts*.*")):
        print(f"{xffts} -> {rename(xffts)}")
