# Theseus Cores

**Theseus Cores**: Open source FPGA cores for digital signal processing and software defined radio, "batteries included".

Specifically, the "batteries included" philosophy indicates this repo is intended to provide basic functioning cores *and* initial hardware implementations for users to start runn inside an existing hardware framework. The primary hardware platform target will be RFNoC; though other platforms can and will likely be supported in the future.

**Why Theseus?** The "Theseus" name refers to Claude Shannon's autonomous maze-solving mouse, considered one of the first examples of artificial intelligence. Shannon, of course, is responsible for essentially spawning the field of information theory, years (arguably decades) ahead of the existing schedule of technological progress. Shannon also, not inconsequentially, invented the modern concept of Boolean computing as his Master's thesis.

**Why Cores?** We started this repo because we noticed a profound lack of open-source FPGA code for digital signal processing applications, and in particular RF signal processing. This project intended to be a centralized location for shared, supported code that can be maintained and used in the future.

Notionally, FPGA code here may be standalone; or it may tie into the [RFNoC
FPGA framework](https://www.ettus.com/sdr-software/detail/rf-network-on-chip).
The repo maintainers are, for the most part, RFNoC users, so the repo will
likely trend towards providing RFNoC support across FPGA and software. However,
it remains a fair use case to interact with primarily the standalone FPGA
code if desired, but your mileage may vary, of course.

## Organization

This repo is broken into several subfolders which the user may interact with
in number of "supported" ways:

- **fpga-src**: Standalone FPGA source code! Amazing!
- **fpga-rfnoc**: FPGA code that *depends on* the RFNoC codebase
([uhd-fpga](https://github.com/ettusresearch/fpga)), including RFNoC
FPGA testbenches.
- **uhd-theseus**: RFNoC-based software drivers, C++ only. These software blocks
link to the public RFNoC API provided in the [UHD repo](https://github.com/ettusresearch/fpga).
The uhd-theseus project is designed to be compatible with a project that
*only* depends on UHD (no gnuradio).
- **gr-theseus**: Gnuradio plugins to access RFNoC blocks from gnuradio companion
and inside a gnuradio flowgraph.

## FPGA Cores

All FPGA code is provided in `fpga-src` where possible. However the top-level entry-point for RFNoC users would be `fpga-rfnoc`, which provides RFNoC hooks/wrappers around the core FPGA code. Review the fpga-rfnoc [README](./fpga-rfnoc/README.md) instructions for:
  - Instructions how to build a relevant FPGA image
  - Instructions how to run RFNoC testbenches
  - [Examples YML builds](./fpga-rfnoc/examples)
  - Description of the provided RFNoC blocks

In summary, FPGA cores provided here:
   - **DUC-DDC** ([detailed description](./fpga-rfnoc/README.md#dsp-utilsnoc_block_ducddcv)): A "hacked" rational resampler, consisting of a DUC and a DDC back-to-back.
   - **1-to-N DDC** ([detailed description](./fpga-rfnoc/README.md#dsp-utilsnoc_block_ddc_1_to_n)): Parameterized instantiations of "N" independent DDCs, where each DDC is connected to the *first* channel (a very basic channelizer).
   - **M/2 Channelizer** ([detailed description](./fpga-rfnoc/README.md#m2_channelizernoc_block_channelizerv)): A [polyphase channelizer](https://pubs.gnuradio.org/index.php/grcon/article/view/18), where each channel outputs 2x sample rate and is compatible with perfect-reconstruction.

## Software Builds (from source)

#### CMake

Software building is handled through cmake. Make sure to call cmake from the top-level (theseus-cores/build), not from subdirectories (e.g., gr-theseus/build, etc).

Feature flags are exposed via CMake to enable UHD or Gnuradio software builds:

- ENABLE_UHD: Turns on the build of uhd-theseus
- ENABLE_GNURADIO: Turns on the build of gr-theseus

For example, the following cmake process will build and install all software (starting in the top-level theseus-cores directory:

```
mkdir build
cd build
cmake .. -DENABLE_UHD=ON -DENABLE_GNURADIO=ON
make
make install
```


#### Pybombs

The `theseus-cores` pybombs recipe provides a build using pybombs. For example, inside a pybombs prefix, run: `pybombs install theseus-cores`

To install a fresh prefix via pybombs, tested on Ubuntu 18.04 and 16.04:
1. Install and update [pybombs](https://github.com/gnuradio/pybombs) using pip
2. Update pybombs recipe repos (specifically gr-recipes, gr-etcetera, and ettus)
3. Install a clean rfnoc prefix: `pybombs prefix init <prefix-name> -R rfnoc`
4. Install theseus-cores into this prefix: `pybombs install theseus-cores`

## Licensing

The theseus-cores repo combines several sub-projects, including both FPGA and software. The licenses are provisioned as follows:

- uhd-theseus: GPLv3
- gr-theseus: GPLv3
- fpga-src: MIT
- fpga-rfnoc: MIT

While UHD and Gnuradio software components are distributed under GPLv3 to maintain compatiblity with their corresponding libraries, we have decided to release the FPGA code under the more permissive MIT license.

## Contributors

- EJ Kreinar (ejkreinar@gmail.com)
- Phil Vallance
