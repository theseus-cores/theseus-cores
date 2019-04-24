# Noc Blocks

This README describes the noc_blocks provided here and their relevant parameters.

## noc_block_ducddc.v

**Summary**

The "DUCDDC" implements a hacked rational resampler by stitching together the uhd-fpga in-tree DUC and DDC blocks in a back-to-back configuration.

It requires more resources than a more optimal resampler would need. Also keep in mind that there is an intermediate upconversion step. The clock rate needs to support the *upsampled* rate of the incoming samples (after the DUC), even though the final output might be at a tolerable data rate.

**Parameters**

NUM_CHAINS: [default=1] Number of independent DUCDDC chains to instantiate
DUC_NUM_HB: [default=2] Number of half-band interpolators in the DUC
DUC_CIC_MAX_INTERP: [default=16] Maximum interpolation factor for DUC
DDC_NUM_HB: [default=2] Number of half-band decimators in the DDC
DDC_CIC_MAX_DECIM: [default=16] Maximum decimation factor for the DDC

## noc_block_ddc_1_to_n.v

**Summary**

The "DDC_1_TO_N" implements a hacked channelizer by instantiating "N" instances of the uhd-fpga in-tree DDCs, and connecting each DDC's input to the input from the *first* data channel.

While this is obviously not a resource-optimized channelizer, it is convenient that every output is independently sized and tuneable (each output may have any arbitrary frequency offset and any integer decimation factor, unrelated to the neighboring channels).

**Known Issues**

UHD software doesnt really handle the graph propagation well when downstream blocks have more ports than upstream blocks.

A workaround is to follow each DDC channel output with an *independent* 1-channel FIFO. It's not pretty, but it does fool the software into propagating block port 0 up the RFNOC graph.

**Parameters**

NUM_CHAINS: [default=4] Number of DDCs to instantiate (this represents the number of channels)
NUM_HB: [default=2] Number of half-band decimators in the DDC; this applies to all DDCs.
CIC_MAX_DECIM: [default=16] Maximum decimation factor for the DDC; this applies to all DDCs.
