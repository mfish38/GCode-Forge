from setuptools import setup, find_packages

setup(
    name="gcode-forge",
    version="0.0.1",
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'Jinja2',
        'PyYAML'
    ]
)