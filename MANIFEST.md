title: theseus-cores

brief: Open source FPGA cores for digital signal processing

tags:
  - FPGA
  - RFNoC
  - channelizer

author:
  - EJ Kreinar <ejkreinar@gmail.com>

dependencies:
  - UHD (>= 3.13)
  - gnuradio (>= 3.7.0)

repo: https://gitlab.com/theseus-cores/theseus-cores.git

stable_release: HEAD

---

**Theseus Cores**: Open source FPGA cores for digital signal processing and software defined radio, "batteries included".

Specifically, the "batteries included" philosophy indicates this repo is intended to provide basic functioning cores *and* initial hardware implementations for users to start runn inside an existing hardware framework. The primary hardware platform target will be RFNoC; though other platforms can and will likely be supported in the future.

**Example Blocks**: Several examples of DSP utilities and applications provided to RFNOC users include:
  - DUC-DDC: A rational resampler consisting of a "back-to-back" DUC and DDC from the uhd-fpga source repo.
  - 1-to-N DDC: A brute-force channelizer which instantiates a parameterized number of DDCs from the uhd-fpga source repo. Each channel may independently tune and decimate.
  - M/2 Channelizer: A 2x oversampled polyphase channelizer from Phil Valance ([GrCon 2017 Presentation](https://pubs.gnuradio.org/index.php/grcon/article/download/18/11/))
