"""Murmur — Setup script."""

from setuptools import setup, find_packages

setup(
    name="murmur",
    version="0.1.0",
    description="Private voice dictation tool — your words, your machine.",
    packages=find_packages(),
    python_requires=">=3.11",
    entry_points={
        "console_scripts": [
            "murmur=app.main:main",
        ],
    },
)
