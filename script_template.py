# This file is prepended to the pypulseq scripts. It changes some imports
# inside of the exec() environment so that execution works within Azure

import sys
from unittest.mock import MagicMock
import logging
import builtins
import numpy
import tempfile

# Fix for older pypulseq versions
numpy.complex = complex
numpy.float = float
numpy.int = int


# Mock matploblib to supress plots from pulseq scripts
sys.modules['matplotlib'] = MagicMock()
sys.modules['matplotlib.colors'] = MagicMock()
sys.modules['matplotlib.pyplot'] = MagicMock()

# Overwrite pypulseq.Sequence() so that sequences are always global
import pypulseq as pp
builtin_Sequence = pp.Sequence
sequences = []


def Sequence(system=pp.Opts()):
    logging.info("Created Sequence object")
    seq = builtin_Sequence(system)
    global sequences
    sequences.append(seq)
    return seq


pp.Sequence = Sequence

# Overwrite open() to use temp files as script directory is read-only
builtin_open = builtins.open
files = {}


def tmp_open(file_name: str, mode):
    if file_name in files:
        file = files[file_name]
        logging.info(f"tmp_open({file_name}, {mode}): returned {file}")
        return builtin_open(file, mode)
    elif file_name.endswith(".seq"):
        file = tempfile.NamedTemporaryFile(mode, delete=False)
        files[file_name] = file.name
        logging.info(f"tmp_open({file_name}, {mode}): created {file.name}")
        return file
    else:
        logging.info(f"open({file_name}, {mode})")
        return builtin_open(file_name, mode)


builtins.open = tmp_open

# ----------------------------------
# Start of submitted pypulseq script
# ----------------------------------

# INSERT USER SCRIPT HERE

# ----------------------------------
# Start of submitted pypulseq script
# ----------------------------------

# Add a fallback seq.write() if the script did not contain any
if len(files) == 0:
    if len(sequences) == 0:
        logging.error(
            "The provided script did not create a sequence object, "
            "writint an empty sequence to 'empty_fallback.seq'"
        )
        pp.Sequence().write("emtpy_fallback.seq")
    else:
        logging.warning(
            f"{len(sequences)} sequence object exist(s), but none were "
            "written to a file, writing to 'fallback.seq'"
        )
        sequences[0].write("fallback.seq")
