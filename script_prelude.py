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

# Overwrite open() to use temp files as script directory is read-only
builtin_open = builtins.open

files = {}

def tmp_open(file_name: str, mode):
    if file_name in files:
        logging.info(f"tmp_open({file_name}, {mode}): returned {files[file_name]}")
        return builtin_open(files[file_name], mode)
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
