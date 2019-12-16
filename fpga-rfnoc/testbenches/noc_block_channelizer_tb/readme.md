
## Export UHD_FPGA_DIR

Point to desired pybombs prefix (e.g. ```uhd-fpga```) directory

## Generate Tap files.

This only needs to be done once.  Frequency response plots will populate inside the python directory.

    python ./python/channelizer.py -t

## Generate Mask files.

This only needs to be done once.  The mask .bin files will poplulatoin in the noc_block_channelizer_tb directory.

    python ./python/channelizer.py -m

## Generate Test Input.

The argument can be a list of Normalized discrete frequency (range -1, 1) centers.  The example shown is a two tones centered at .3 and .4.  The .bin file will be placed in the noc_block_channelizer_tb directory.

    python ./python/channelizer.py -i .3 .4

## Run the RTL simulation.

This currently takes ~2.5 hrs.

    make xsim

## Plot RTL Sim Output

First copy .bin files into noc_block_channelizer_tb root.

    find . -iname "*.bin" -exec cp {} ./ \;

Generate plots

    python ./python/channelizer.py -c '../chan_output.bin'


## Notes

All of the python commands were run from noc_block_channelizer_tb directory
