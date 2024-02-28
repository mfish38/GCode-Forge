# GCode-Forge
A G-code post processing script framework and toolset for working with Orca slicer g-code.

# Installation

Install Python. Clone the repository. Install using `pip install -e <path to repo>`.

Windows:
Add the following to "Post-processing Scripts" on the "Other" settings tab.

    "<Absolute path to python>" -m gcode_forge

Example:

    "C:\Users\blend\AppData\Local\Programs\Python\Python312\python.exe" -m gcode_forge

# Configuration

Configuration will eventually be done using config files. Currently all configuration is done by modifying the data structures in `gcode_forge/__main__.py`

