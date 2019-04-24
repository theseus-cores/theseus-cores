# RFNoC-Specific FPGA Code

This folder maintains the RFNoC sub-projects.

To use this code in a RFNoC build, point the Out-Of-Tree build to
one (or more) of the subdirectories here to build the IP and include
relevant fpga-src for these modules as the `-I` include-dirs argument.

The valid modules here are:
- [dsp-utils](./dsp-utils/README.md)
- [m2_channelizer](./m2_channelizer/README.md)

Many of the noc blocks have configurable parameters. It is recommended to build the FPGA image by specifing a YML file with the desired parameters (see the `examples` subfolder here for configuration examples).

## Example

To build an RFNOC FPGA image with components from the "dsp-utils" subproject, you can use refer to the example YML file `examples/basic-dsp-utils.yml`.

1. Clone the uhd-fpga repo
2. Change directory into `uhd-fpga/usrp3/tools/scripts`
3. Run the UHD image builder: `./uhd_image_builder.py -d x300 -t X300_RFNOC_HG -y <prefix-src>/theseus-cores/fpga-rfnoc/examples/basic-dsp-utils.yml -I <prefix-src>/theseus-cores/fpga-rfnoc/dsp-utils`

As an example, the above syntax will build the "basic-dsp-utils.yml" build definition, while instantiating only the IP relevant to the "dsp-utils" subproject.
