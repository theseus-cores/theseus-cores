#
# Copyright 2018 Ettus Research
#

include $(TOOLS_DIR)/make/viv_ip_builder.mak

LIB_IP_CHANNELIZER_XFFT_SRCS = $(IP_BUILD_DIR)/xfft/xfft.xci

LIB_IP_CHANNELIZER_XFFT_OUTS = $(addprefix $(IP_BUILD_DIR)/xfft/, \
    xfft.xci.out \
    synth/xfft.vhd \
)

$(LIB_IP_CHANNELIZER_XFFT_SRCS) $(LIB_IP_CHANNELIZER_XFFT_OUTS) : $(CHAN_IP_DIR)/xfft/xfft.xci
	$(call BUILD_VIVADO_IP,xfft,$(ARCH),$(PART_ID),$(CHAN_IP_DIR),$(IP_BUILD_DIR),0)
