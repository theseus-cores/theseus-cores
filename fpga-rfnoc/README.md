# RFNoC-Specific FPGA Code

This folder maintains the RFNoC sub-projects.

To use this code in a RFNoC build, point the Out-Of-Tree build to
one (or more) of the subdirectories here to build the IP and include
relevant fpga-src for these modules as the `-I` include-dirs argument.

The valid modules here are:
- dsp-utils
- m2_channelizer

Many of the noc blocks have configurable parameters. It is recommended to build the FPGA image by specifing a YML file with the desired parameters (see the `examples` subfolder here for configuration examples).

# Example RFNoC Build

To build an RFNOC FPGA image with components from the "dsp-utils" subproject, you can use refer to the example YML file [examples/basic-dsp-utils.yml](examples/basic-dsp-utils.yml).

1. Clone the uhd-fpga repo
2. Change directory into `uhd-fpga/usrp3/tools/scripts`
3. Run the UHD image builder: `./uhd_image_builder.py -d x300 -t X300_RFNOC_HG -y <prefix-src>/theseus-cores/fpga-rfnoc/examples/basic-dsp-utils.yml -I <prefix-src>/theseus-cores/fpga-rfnoc/dsp-utils`

As an example, the above syntax will build the "basic-dsp-utils.yml" build definition, while instantiating only the IP relevant to the "dsp-utils" subproject.

# Example RFNoC Testbench

The testbenches in `fpga-rfnoc/testbenches` may be run in an RFNoC simulation
(`make xsim`). Testbenches are provided across all of the submodules (dsp-utils, m2_channelizer, etc).

The testbenches are designed to be "self-checking" so they will
run to completion and indicate success or failure. Consistent with
the RFNoC workflow, testbenches may also be run with `make xsim GUI=1` to
bring up the Vivado waveform viewer for debugging.

Testbenches are not (currently) exposed through a cmake interface at the top-level, but this could be added in the future.

# Noc Blocks

All provided noc_blocks are described here with relevant parameters.

## dsp-utils/noc_block_ducddc.v

**Summary**

The "DUCDDC" implements a hacked rational resampler by stitching together the uhd-fpga in-tree DUC and DDC blocks in a back-to-back configuration.

It requires more resources than a more optimal resampler would need. Also keep in mind that there is an intermediate upconversion step. The clock rate needs to support the *upsampled* rate of the incoming samples (after the DUC), even though the final output might be at a tolerable data rate.

**Parameters**

- NUM_CHAINS: [default=1] Number of independent DUCDDC chains to instantiate
- DUC_NUM_HB: [default=2] Number of half-band interpolators in the DUC
- DUC_CIC_MAX_INTERP: [default=16] Maximum interpolation factor for DUC
- DDC_NUM_HB: [default=2] Number of half-band decimators in the DDC
- DDC_CIC_MAX_DECIM: [default=16] Maximum decimation factor for the DDC

## dsp-utils/noc_block_ddc_1_to_n.v

**Summary**

The "DDC_1_TO_N" implements a hacked channelizer by instantiating "N" instances of the uhd-fpga in-tree DDCs, and connecting each DDC's input to the input from the *first* data channel.

While this is obviously not a resource-optimized channelizer, it is convenient that every output is independently sized and tuneable (each output may have any arbitrary frequency offset and any integer decimation factor, unrelated to the neighboring channels).

**Known Issues**

UHD software doesnt really handle the graph propagation well when downstream blocks have more ports than upstream blocks.

A workaround is to follow each DDC channel output with an *independent* 1-channel FIFO. It's not pretty, but it does fool the software into propagating block port 0 up the RFNOC graph.

**Parameters**

- NUM_CHAINS: [default=4] Number of DDCs to instantiate (this represents the number of channels)
- NUM_HB: [default=2] Number of half-band decimators in the DDC; this applies to all DDCs.
- CIC_MAX_DECIM: [default=16] Maximum decimation factor for the DDC; this applies to all DDCs.
