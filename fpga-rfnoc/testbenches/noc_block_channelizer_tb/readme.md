# generate taps (only needs to be done once)

    python ./python/channelizer.py -t

# generate test input.

The argument can be a list of Normalized discrete frequency (range -1, 1) centers.  The example shown is a two tones centered at .3 and .4.

    python ./python/channelizer.py -i .3 .4

# run the RTL simulation.

    make xsim

# copy .bin files into noc_block_channelizer_tb root.

    find . -iname "*.bin" -exec cp {} ./ \;

# Generate output plots

    python ./python/channelizer.py -c '../chan_output.bin'
