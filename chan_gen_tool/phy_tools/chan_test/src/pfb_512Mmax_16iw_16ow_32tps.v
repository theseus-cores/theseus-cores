/*****************************************************************************/
// Implements the M PFB architecture referenced in the
// "A Versatile Multichannel Filter Bank with Multiple Channel Bandwidths" paper.
// This architecture has been mapped to the Xilinx architecture.
// This represents a fully pipelined design that maximizes the FMax potential of the design.
// It is important to understand that filter arms are loaded sequentially. This is referenced in
// the diagram by the incremental changes in the phase subscript through each subsequent delay
// register. The nth index is only updated once per revolution of the filter bank.
//
// It is best to refer to the attached document to understand the layout of the logic. This module
// currently implements 32 taps per phase.
/*****************************************************************************/

module pfb_512Mmax_16iw_16ow_32tps
(
    input clk,
    input sync_reset,

    input [9:0] num_phases,
    input [8:0] phase,

    input s_axis_tvalid,
    input [31:0] s_axis_tdata,
    input s_axis_tlast,
    output s_axis_tready,

    input s_axis_reload_tvalid,
    input [31:0] s_axis_reload_tdata,
    input s_axis_reload_tlast,
    output s_axis_reload_tready,

    output [8:0] phase_out,
    output m_axis_tvalid,
    output [31:0] m_axis_tdata,
    output m_axis_tlast,
    input m_axis_tready
);

wire [24:0] taps[0:31];
wire [47:0] pcouti[0:31];
wire [47:0] pcoutq[0:31];
wire [15:0] pouti, poutq;

wire [31:0] delay[0:31];

reg [8:0] phase_d[0:38];
reg [4:0] tvalid_d;
reg [39:0] tvalid_pipe, next_tvalid_pipe;
reg [39:0] tlast_d, next_tlast_d;

reg [9:0] wr_addr_d[0:95];

reg [31:0] sig, next_sig;
reg [31:0] sig_d1, sig_d2, sig_d3;
reg [9:0] rd_addr, next_rd_addr;
reg [9:0] wr_addr, next_wr_addr;
reg [9:0] rd_addr_d[0:30];

reg [9:0] next_rd_addr_d[0:30];

reg [0:0] offset_cnt, next_offset_cnt;
reg [0:0] offset_cnt_prev, next_offset_cnt_prev;

wire [8:0] rom_addr;
wire [24:0] rom_data;
wire [31:0] rom_we;

reg [9:0] phase_max;
reg [8:0] phase_max_slice;
wire [40:0] fifo_tdata, m_axis_tdata_s;
wire fifo_tvalid;
wire almost_full;
wire take_data;

assign take_data = (s_axis_tvalid & ~almost_full);
assign m_axis_tdata = m_axis_tdata_s[40:9];
assign s_axis_tready = ~almost_full;
assign fifo_tvalid = tvalid_d[4] & tvalid_pipe[39];
assign phase_out = m_axis_tdata_s[8:0];
assign fifo_tdata = {pouti, poutq, phase_d[38]};


// logic implements the sample write address pipelining.
always @(posedge clk)
begin

    phase_max <= num_phases - 1;
    phase_max_slice <= phase_max[8:0];

    phase_d[0] <= rd_addr[8:0];
    phase_d[1] <= phase_d[0] & phase_max_slice;
    phase_d[2] <= phase_d[1];
    sig_d1 <= sig;
    sig_d2 <= sig_d1;
    sig_d3 <= sig_d2;

    wr_addr_d[0] <= wr_addr;
    wr_addr_d[3] <= {~rd_addr[9], rd_addr[8:0]};
    wr_addr_d[6] <= {~rd_addr_d[0][9], rd_addr_d[0][8:0]};
    wr_addr_d[9] <= {~rd_addr_d[1][9], rd_addr_d[1][8:0]};
    wr_addr_d[12] <= {~rd_addr_d[2][9], rd_addr_d[2][8:0]};
    wr_addr_d[15] <= {~rd_addr_d[3][9], rd_addr_d[3][8:0]};
    wr_addr_d[18] <= {~rd_addr_d[4][9], rd_addr_d[4][8:0]};
    wr_addr_d[21] <= {~rd_addr_d[5][9], rd_addr_d[5][8:0]};
    wr_addr_d[24] <= {~rd_addr_d[6][9], rd_addr_d[6][8:0]};
    wr_addr_d[27] <= {~rd_addr_d[7][9], rd_addr_d[7][8:0]};
    wr_addr_d[30] <= {~rd_addr_d[8][9], rd_addr_d[8][8:0]};
    wr_addr_d[33] <= {~rd_addr_d[9][9], rd_addr_d[9][8:0]};
    wr_addr_d[36] <= {~rd_addr_d[10][9], rd_addr_d[10][8:0]};
    wr_addr_d[39] <= {~rd_addr_d[11][9], rd_addr_d[11][8:0]};
    wr_addr_d[42] <= {~rd_addr_d[12][9], rd_addr_d[12][8:0]};
    wr_addr_d[45] <= {~rd_addr_d[13][9], rd_addr_d[13][8:0]};
    wr_addr_d[48] <= {~rd_addr_d[14][9], rd_addr_d[14][8:0]};
    wr_addr_d[51] <= {~rd_addr_d[15][9], rd_addr_d[15][8:0]};
    wr_addr_d[54] <= {~rd_addr_d[16][9], rd_addr_d[16][8:0]};
    wr_addr_d[57] <= {~rd_addr_d[17][9], rd_addr_d[17][8:0]};
    wr_addr_d[60] <= {~rd_addr_d[18][9], rd_addr_d[18][8:0]};
    wr_addr_d[63] <= {~rd_addr_d[19][9], rd_addr_d[19][8:0]};
    wr_addr_d[66] <= {~rd_addr_d[20][9], rd_addr_d[20][8:0]};
    wr_addr_d[69] <= {~rd_addr_d[21][9], rd_addr_d[21][8:0]};
    wr_addr_d[72] <= {~rd_addr_d[22][9], rd_addr_d[22][8:0]};
    wr_addr_d[75] <= {~rd_addr_d[23][9], rd_addr_d[23][8:0]};
    wr_addr_d[78] <= {~rd_addr_d[24][9], rd_addr_d[24][8:0]};
    wr_addr_d[81] <= {~rd_addr_d[25][9], rd_addr_d[25][8:0]};
    wr_addr_d[84] <= {~rd_addr_d[26][9], rd_addr_d[26][8:0]};
    wr_addr_d[87] <= {~rd_addr_d[27][9], rd_addr_d[27][8:0]};
    wr_addr_d[90] <= {~rd_addr_d[28][9], rd_addr_d[28][8:0]};
    wr_addr_d[93] <= {~rd_addr_d[29][9], rd_addr_d[29][8:0]};

    wr_addr_d[1] <= wr_addr_d[0];
    wr_addr_d[2] <= wr_addr_d[1];
    wr_addr_d[4] <= wr_addr_d[3];
    wr_addr_d[5] <= wr_addr_d[4];
    wr_addr_d[7] <= wr_addr_d[6];
    wr_addr_d[8] <= wr_addr_d[7];
    wr_addr_d[10] <= wr_addr_d[9];
    wr_addr_d[11] <= wr_addr_d[10];
    wr_addr_d[13] <= wr_addr_d[12];
    wr_addr_d[14] <= wr_addr_d[13];
    wr_addr_d[16] <= wr_addr_d[15];
    wr_addr_d[17] <= wr_addr_d[16];
    wr_addr_d[19] <= wr_addr_d[18];
    wr_addr_d[20] <= wr_addr_d[19];
    wr_addr_d[22] <= wr_addr_d[21];
    wr_addr_d[23] <= wr_addr_d[22];
    wr_addr_d[25] <= wr_addr_d[24];
    wr_addr_d[26] <= wr_addr_d[25];
    wr_addr_d[28] <= wr_addr_d[27];
    wr_addr_d[29] <= wr_addr_d[28];
    wr_addr_d[31] <= wr_addr_d[30];
    wr_addr_d[32] <= wr_addr_d[31];
    wr_addr_d[34] <= wr_addr_d[33];
    wr_addr_d[35] <= wr_addr_d[34];
    wr_addr_d[37] <= wr_addr_d[36];
    wr_addr_d[38] <= wr_addr_d[37];
    wr_addr_d[40] <= wr_addr_d[39];
    wr_addr_d[41] <= wr_addr_d[40];
    wr_addr_d[43] <= wr_addr_d[42];
    wr_addr_d[44] <= wr_addr_d[43];
    wr_addr_d[46] <= wr_addr_d[45];
    wr_addr_d[47] <= wr_addr_d[46];
    wr_addr_d[49] <= wr_addr_d[48];
    wr_addr_d[50] <= wr_addr_d[49];
    wr_addr_d[52] <= wr_addr_d[51];
    wr_addr_d[53] <= wr_addr_d[52];
    wr_addr_d[55] <= wr_addr_d[54];
    wr_addr_d[56] <= wr_addr_d[55];
    wr_addr_d[58] <= wr_addr_d[57];
    wr_addr_d[59] <= wr_addr_d[58];
    wr_addr_d[61] <= wr_addr_d[60];
    wr_addr_d[62] <= wr_addr_d[61];
    wr_addr_d[64] <= wr_addr_d[63];
    wr_addr_d[65] <= wr_addr_d[64];
    wr_addr_d[67] <= wr_addr_d[66];
    wr_addr_d[68] <= wr_addr_d[67];
    wr_addr_d[70] <= wr_addr_d[69];
    wr_addr_d[71] <= wr_addr_d[70];
    wr_addr_d[73] <= wr_addr_d[72];
    wr_addr_d[74] <= wr_addr_d[73];
    wr_addr_d[76] <= wr_addr_d[75];
    wr_addr_d[77] <= wr_addr_d[76];
    wr_addr_d[79] <= wr_addr_d[78];
    wr_addr_d[80] <= wr_addr_d[79];
    wr_addr_d[82] <= wr_addr_d[81];
    wr_addr_d[83] <= wr_addr_d[82];
    wr_addr_d[85] <= wr_addr_d[84];
    wr_addr_d[86] <= wr_addr_d[85];
    wr_addr_d[88] <= wr_addr_d[87];
    wr_addr_d[89] <= wr_addr_d[88];
    wr_addr_d[91] <= wr_addr_d[90];
    wr_addr_d[92] <= wr_addr_d[91];
    wr_addr_d[94] <= wr_addr_d[93];
    wr_addr_d[95] <= wr_addr_d[94];
end

//tvalid_pipe_proc
always @*
begin
    next_tvalid_pipe[3:0] = {tvalid_pipe[2:0], (s_axis_tvalid & ~almost_full)};
    if (tvalid_d[3] == 1'b1) begin
        next_tvalid_pipe[39:4] = {tvalid_pipe[38:4],tvalid_pipe[3]};
    end else begin
        next_tvalid_pipe[39:4] = tvalid_pipe[39:4];
    end
end

//tlast_proc 
always @*
begin
    next_tlast_d[3:0] = {tlast_d[2:0], s_axis_tlast};
    if (tvalid_d[3] == 1'b1) begin
        next_tlast_d[39:4] = {tlast_d[38:4], tlast_d[3]};
    end else begin
        next_tlast_d[39:4] = tlast_d[39:4];
    end
end

// clock and reset process.
integer m;
always @(posedge clk, posedge sync_reset)
begin
    if (sync_reset == 1'b1) begin
        offset_cnt <= 1;  // this ensures that the first read / write is to offset 0.
        offset_cnt_prev <= 0;
        sig <= 0;
        tvalid_d <= 0;
        tvalid_pipe <= 0;
        tlast_d <= 0;
        for (m=0; m<31; m=m+1) begin
            rd_addr_d[m] <= 0;
        end
        rd_addr <= 0;
        wr_addr <= 0;
    end else begin
        offset_cnt <= next_offset_cnt;
        offset_cnt_prev <= next_offset_cnt_prev;
        sig <= next_sig;
        tvalid_d <= {tvalid_d[3:0], (s_axis_tvalid & ~almost_full)};
        tvalid_pipe <= next_tvalid_pipe;
        tlast_d <= next_tlast_d;
        for (m=0; m<31; m=m+1) begin
            rd_addr_d[m] <= next_rd_addr_d[m];
        end
        rd_addr <= next_rd_addr;
        wr_addr <= next_wr_addr;
    end
end

integer n;
always @(posedge clk)
begin
    if (tvalid_d[3] == 1'b1) begin
        for (n=3; n<40; n=n+1) begin
            phase_d[n] <= phase_d[n - 1];
        end
    end
end

// read and write address update logic.
integer p;
always @*
begin
    next_offset_cnt = offset_cnt;
    next_offset_cnt_prev = offset_cnt_prev;
    next_rd_addr = rd_addr;
    next_wr_addr = wr_addr;
    // increment offset count once per cycle through the PFB arms.
    if (take_data == 1'b1) begin
        if (phase == 9'd0) begin
            next_offset_cnt_prev = offset_cnt;
            next_offset_cnt = offset_cnt + 1;
            next_wr_addr = {offset_cnt + 1, phase};
            next_rd_addr = {offset_cnt, phase};
        end else begin
            next_rd_addr = {offset_cnt_prev, phase};
            next_wr_addr = {offset_cnt, phase};
        end
    end

    if (take_data == 1'b1) begin
        next_sig = s_axis_tdata;
    end else begin
        next_sig = sig;
    end

    // shift through old values.
    if (take_data == 1'b1) begin
        next_rd_addr_d[0] = rd_addr;
        for (p=1; p<31; p=p+1) begin
            next_rd_addr_d[p] = rd_addr_d[p-1];
        end
    end else begin
        for (p=0; p<31; p=p+1) begin
            next_rd_addr_d[p] = rd_addr_d[p];
        end
    end
end

mem_ctrl_pfb_512Mmax_16iw_16ow_32tps tap_ctrl
(
  .clk(clk),
  .sync_reset(sync_reset),

  .s_axis_reload_tdata(s_axis_reload_tdata),
  .s_axis_reload_tlast(s_axis_reload_tlast),
  .s_axis_reload_tvalid(s_axis_reload_tvalid),
  .s_axis_reload_tready(s_axis_reload_tready),

  .taps_addr(rom_addr),
  .taps_we(rom_we),
  .taps_douta(rom_data)
);

// 3 cycle latency
dp_block_read_first_ram #(
  .DATA_WIDTH(32),
  .ADDR_WIDTH(10))
sample_ram_0 (
  .clk(clk), 
  .wea(tvalid_d[3]), 
  .addra(wr_addr_d[2][9:0]),
  .dia(sig_d3), 
  .addrb(rd_addr[9:0]),
  .dob(delay[0])
);

genvar i;
generate
    for (i=1; i<32; i=i+1) begin : TAP_DELAY
        dp_block_read_first_ram #(
          .DATA_WIDTH(32),
          .ADDR_WIDTH(10))
        sample_ram_inst (
          .clk(clk),
          .wea(tvalid_d[3]),
          .addra(wr_addr_d[i*3+2][9:0]),
          .dia(delay[i-1]),
          .addrb(rd_addr_d[i-1][9:0]),
          .dob(delay[i])
        );
    end
endgenerate

// Coefficent memories
// latency = 3.
dp_block_write_first_ram #(
    .DATA_WIDTH(25),
    .ADDR_WIDTH(9))
pfb_taps_0 (
    .clk(clk),
    .wea(rom_we[0]),
    .addra(rom_addr),
    .dia(rom_data),
    .addrb(rd_addr[8:0]),
    .dob(taps[0])
);

genvar nn;
generate
    for (nn=1; nn<32; nn=nn+1) begin : COEFFS
        dp_block_write_first_ram #(
            .DATA_WIDTH(25),
            .ADDR_WIDTH(9))
        pfb_taps_nn
        (
            .clk(clk),
            .wea(rom_we[nn]),
            .addra(rom_addr),
            .dia(rom_data),
            .addrb(rd_addr_d[nn-1][8:0]),
            .dob(taps[nn])
        );
    end
endgenerate


// PFB MAC blocks
dsp48_pfb_mac_0 pfb_mac_i_start (
  .clk(clk),
  .ce(tvalid_d[3]),
  .a(taps[0]),
  .b(delay[0][31:16]),
  .pcout(pcouti[0]),
  .p()
);

// Latency = 4
dsp48_pfb_mac_0 pfb_mac_q_start (
  .clk(clk),
  .ce(tvalid_d[3]),
  .a(taps[0]),
  .b(delay[0][15:0]),
  .pcout(pcoutq[0]),
  .p()
);

genvar j;
generate
    for (j=1; j<32; j=j+1) begin : MAC
        dsp48_pfb_mac pfb_mac_i
        (
          .clk(clk),
          .ce(tvalid_d[3]),
          .pcin(pcouti[j-1]),
          .a(taps[j]),
          .b(delay[j][31:16]),
          .pcout(pcouti[j]),
          .p()
        );

        dsp48_pfb_mac pfb_mac_q
        (
          .clk(clk),
          .ce(tvalid_d[3]),
          .pcin(pcoutq[j-1]),
          .a(taps[j]),
          .b(delay[j][15:0]),
          .pcout(pcoutq[j]),
          .p()
        );
    end
endgenerate

dsp48_pfb_rnd pfb_rnd_i
(
    .clk(clk),
    .ce(tvalid_d[3]),
    .pcin(pcouti[31]),
    .p(pouti)
);

dsp48_pfb_rnd pfb_rnd_q
(
    .clk(clk),
    .ce(tvalid_d[3]),
    .pcin(pcoutq[31]),
    .p(poutq)
);

axi_fifo_3 #(
    .DATA_WIDTH(41),
    .ALMOST_FULL_THRESH(16),
    .ADDR_WIDTH(6))
u_fifo
(
    .clk(clk),
    .sync_reset(sync_reset),

    .s_axis_tvalid(fifo_tvalid),
    .s_axis_tdata(fifo_tdata),
    .s_axis_tlast(tlast_d[39]),
    .s_axis_tready(),

    .almost_full(almost_full),

    .m_axis_tvalid(m_axis_tvalid),
    .m_axis_tdata(m_axis_tdata_s),
    .m_axis_tlast(m_axis_tlast),
    .m_axis_tready(m_axis_tready)
);

endmodule
