#!/usr/bin/env python
# -*- coding: utf-8 -*-
import setuptools
from subprocess import check_output, CalledProcessError, DEVNULL
try:
    date_string = check_output('git log -1 --pretty=format:%cd --date=format:%Y.%m.%d'.split(), stderr=DEVNULL).decode()
except CalledProcessError:
    from datetime import date
    today = date.today()
    date_string = today.strftime("%Y.%m.%d")

with open("./phy_tools/README.md", "r") as fh:
   long_description = fh.read()

setuptools.setup(
    name='phy_tools',
    version="{}".format(date_string),
    install_requires=['ipdb', 'mpmath', 'pylatexenc', 'numba', 'scikit-learn', 'numpy', 'matplotlib', 'scipy', 'pandas', 'dill', 'ffmpeg', 'plotly'],
    extras_require={"streamlit": ["pkginfo", "streamlit"]},
    author="Phil Vallance",
    author_email="pjvalla@gmail.com",
    description="Set of Physical Layer (phy_tools) Tool that utilities for the following areas: fixed point simulation, \
    communication design, verilog and vhdl code generation, FEC algorithms and general signal processing",
    long_description=long_description,
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
)
