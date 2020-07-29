"""
Reads indexed UNIX fortune files and outputs a fortune cookie.

Fortune index files contain the following header:
typedef struct {                                /* information table */
#define VERSION         2
        u_int32_t       str_version;            /* version number */
        u_int32_t       str_numstr;             /* # of strings in the file */
        u_int32_t       str_longlen;            /* length of longest string */
        u_int32_t       str_shortlen;           /* length of shortest string */
#define STR_RANDOM      0x1                     /* randomized pointers */
#define STR_ORDERED     0x2                     /* ordered pointers */
#define STR_ROTATED     0x4                     /* rot-13'd text */
        u_int32_t       str_flags;              /* bit field for flags */
        u_int8_t        stuff[4];               /* long aligned space */
#define str_delim       stuff[0]                /* delimiting character */
} STRFILE;
"""
import codecs
import struct
import random
from pathlib import Path
from typing import List
from dataclasses import dataclass
from tama import api, TamaBot

fortunes: List["FortuneFile"] = []


@dataclass
class FortuneFile:
    name: str
    total: int
    # Note: the last offset leads an empty string
    offsets: List[int]
    data: bytes
    rotated: bool


def load_fortunes():
    idx_paths = [Path("data/fortune"), Path("data/fortune/off")]
    indexes = [
        idx for p in idx_paths for idx in p.iterdir()
        if idx.suffix == ".dat"
    ]
    for idx in indexes:
        datafile = Path(str(idx)[:-4])
        with idx.open("rb") as dat:
            hdr = struct.unpack(">IIIIIcxxx", dat.read(24))
            version, numstr, longlen, shortlen, flags, delim = hdr
            f_random = flags & 0x1
            f_ordered = flags & 0x2
            f_rotated = flags & 0x4
            offsets = []
            for i in range(numstr+1):
                offset, = struct.unpack(">I", dat.read(4))
                offsets.append(offset)
        with datafile.open("rb") as db:
            data = db.read()
        fortunes.append(FortuneFile(
            name=idx.stem, total=numstr, offsets=offsets, data=data,
            rotated=bool(f_rotated)
        ))


def get_fortune() -> str:
    # FIXME: Conditional probability means this will make smaller file fortunes
    # much more prevalent. Make a fairer random choice.
    file: FortuneFile = random.choice(fortunes)
    print(file.name)
    # We don't want to get the last index as it's empty
    rand = random.randint(0, file.total-1)
    idx, next_idx = file.offsets[rand:rand+2]
    # -3 removes \n%\n
    cookie = file.data[idx:next_idx-3]
    # Replace tabs for spaces
    cookie = cookie.replace(b"\t", b"    ")
    # Decode text
    cookie = cookie.decode("utf-8")
    # Deal with rot-13
    if file.rotated:
        print("rot")
        cookie = codecs.decode(cookie, "rot_13")
    return cookie


@api.command()
def fortune(_, channel: str = None, client: TamaBot.Client = None) -> None:
    cookie = get_fortune()
    for line in cookie.split("\n"):
        client.message(channel, line)


# FIXME: This is being loaded on module load with hardcoded paths until on_load
# api call is done
load_fortunes()
