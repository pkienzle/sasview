"""
     Installation script for SANS fitting
"""
import sys
if len(sys.argv) == 1:
    sys.argv.append('install')
# Then build and install the modules
from distutils.core import setup, Extension

setup(
    name="park_integration",
    version = "1.0.0",
    description = "Python module for fitting",
    author = "University of Tennessee",
    #author_email = "",
    url = "http://danse.chem.utk.edu",
    # Use the pure python modules
    package_dir = {"sans":"src/sans",
                   "sans.fit":"src/sans/fit"},
    packages = ["sans.fit", "sans"]
    )
        