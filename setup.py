#!/usr/bin/env python

from setuptools import setup

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("requirements.txt") as f:
    requires = f.read()

setup(
    name="yt_dlpr",
    version="0.1",
    description="Rich output of yt-dlp.",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Folke",
    author_email="folke.ishii@gmail.com",
    url="https://github.com/Secozzi/yt-dlpr",
    install_requires=requires,
    license="MIT license",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Quality Assurance",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3 :: Only",
    ],
    packages=["yt_dlpr"],
    entry_points = {
        "console_scripts": [
            "yt-dlpr=yt_dlpr.__init__:main"
        ]
    }
)
