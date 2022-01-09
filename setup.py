#!/usr/bin/env python3
import pathlib
from setuptools import find_packages, setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name="polyglot-translator",
    version="1.5.4",
    description="Automation CLI tool that, using the DeepL API, generates a JSON or a PO file from a given source file.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/riccardoFasan/polyglot",
    project_urls={
        "BugTracker": "https://github.com/riccardoFasan/polyglot/issues",
        "Homepage": "https://github.com/riccardoFasan/polyglot"
    },
    author="Riccardo Fasan",
    author_email="fasanriccardo21@gmail.com",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    packages=find_packages(exclude=("tests",)),
    include_package_data=True,
    install_requires=[
        "colorama",
        "polib",
        "progressbar2",
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "polyglot=polyglot.__main__:translate_or_print_data",
        ]
    },
)
