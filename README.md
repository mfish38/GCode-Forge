# GCode-Forge
A G-code post processing script framework and toolset for working with Orca slicer g-code.

# Installation

Install Python. Clone the repository. Install using `pip install -e <path to repo>`.

Windows:
Add the following to "Post-processing Scripts" on the "Other" settings tab.

    "<Absolute path to python>" -m gcode_forge "<Absolute path to .yaml config>"

Example:

    "C:\Users\blend\AppData\Local\Programs\Python\Python312\python.exe" -m gcode_forge "D:\home\GCode-Forge\example.yaml"

# Configuration

You can create different yaml files for different print profiles and reference them using the path argument when setting the slicer config.

See `example.yaml` for an example config file.