"""setup.py — compatibility shim for older pip / conda editable installs."""
from setuptools import setup, find_packages

setup(
    name="sysvis",
    version="1.1.0",
    packages=find_packages(),
    install_requires=[
        "rich>=13.0.0",
        "psutil>=5.9.0",
        "py-cpuinfo>=9.0.0",
    ],
    extras_require={"gpu": ["gputil>=1.4.0"]},
    entry_points={"console_scripts": ["sysvis=sysvis.__main__:main"]},
    python_requires=">=3.8",
)