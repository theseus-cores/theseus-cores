//*****************************************************************************
//
// Since the fft is block floating point the apparent signal amplitude can be shifted
// in consecutive fft blocks.  The Exponent shifter, exp_shifter, implements a simple
// low pass filtering the shift signal and provides gain correction mechanism for mitigating
// the amplitude shifts caused by the fft module.  The module also provides buffering
// and flow control logic so that it can directly connected to the rest of the rfnoc
// infrastructure.
//*****************************************************************************

// no timescale needed

module exp_shifter#(
    parameter HEAD_ROOM = 7'd2)
(
    input clk,
    input sync_reset,
    input s_axis_tvalid,
    input [31:0] s_axis_tdata,
    input [23:0] s_axis_tuser,
    input s_axis_tlast,
    output s_axis_tready,

    input [11:0] fft_size,
    input [8:0] avg_len,
    output eob_tag,

    input s_axis_status_tvalid,
    input [7:0] s_axis_status_tdata,
    output s_axis_status_tready,

    output m_axis_tvalid,
    output [31:0] m_axis_tdata,
    output [23:0] m_axis_tuser,
    output m_axis_tlast,
    input m_axis_tready
);


wire s_axis_tready_s;  // delay signals
reg [31:0] tdata_d0, tdata_d1, tdata_d2;

wire [15:0] tdatai, tdataq;

reg [23:0] tuser_d0, tuser_d1, tuser_d2, tuser_d3, tuser_d4, tuser_d5, tuser_d6,  tuser_d7;
reg [7:0] tlast_d;
reg [7:0] take_d;

wire [47:0] pcorr_i, pcorr_q;
wire filter_tready;
reg [15:0] i_val, next_i_val;
reg [15:0] q_val, next_q_val;
wire [31:0] fifo_tdata;
wire [4:0] shift_sig;
wire [4:0] filter_tdata;
wire filter_tvalid;
wire [12:0] filter_out_tdata;
reg [12:0] filter_d, next_filter_d;
wire [4:0] filter_whole;
wire [7:0] lookup;
wire [15:0] corr_fac;
wire chan_0;
wire [10:0] fft_bin;

reg signed [5:0] sub_out, next_sub_out;
reg signed [6:0] shift_val;

wire [4:0] curr_shift;
wire almost_full;
wire take;
wire [23:0] m_axis_tuser_s;

  assign take = (s_axis_tvalid == 1'b1 && s_axis_tready_s == 1'b1) ? 1'b1 : 1'b0;
  assign s_axis_tready_s = (almost_full == 1'b0) ? 1'b1 : 1'b0;
  assign s_axis_tready = s_axis_tready_s;
  assign fft_bin = s_axis_tuser[10:0];
  assign filter_whole = filter_d[12:8];
  assign lookup = filter_d[7:0];
  assign tdatai = tdata_d2[31:16];
  assign tdataq = tdata_d2[15:0];

  assign eob_tag = m_axis_tuser_s[23];
  assign m_axis_tuser = m_axis_tuser_s;
  assign fifo_tdata = {i_val,q_val};
  assign chan_0 = (fft_bin == 11'b00000000000 && take == 1'b1) ? 1'b1 : 1'b0;
  assign shift_sig = s_axis_status_tdata[4:0];
  assign filter_tdata = shift_sig;
  assign s_axis_status_tready = filter_tready;
  assign curr_shift = s_axis_tuser[20:16];

  // main clock process
always @(posedge clk, posedge sync_reset) begin
    if (sync_reset == 1'b1) begin
      filter_d <= 0;
      i_val <= 0;
      q_val <= 0;
      sub_out <= 0;
    end else begin
      filter_d <= next_filter_d;
      i_val <= next_i_val;
      q_val <= next_q_val;
      sub_out <= next_sub_out;
    end
end

always @(posedge clk) begin
    shift_val <= $signed({{1{sub_out[5]}},sub_out}) - $signed(HEAD_ROOM);
    take_d <= {take_d[6:0],take};
    tdata_d0 <= s_axis_tdata;
    tdata_d1 <= tdata_d0;
    tdata_d2 <= tdata_d1;
    tuser_d0 <= {s_axis_tlast,s_axis_tuser[22:0]};
    tuser_d1 <= tuser_d0;
    tuser_d2 <= tuser_d1;
    tuser_d3 <= tuser_d2;
    tuser_d4 <= tuser_d3;
    tuser_d5 <= tuser_d4;
    tuser_d6 <= tuser_d5;
    tuser_d7 <= tuser_d6;
    tlast_d <= {tlast_d[6:0],s_axis_tlast};
end

always @*
begin
    next_filter_d = filter_d;
    if (filter_tvalid == 1'b1) begin
        next_filter_d = filter_out_tdata;
    end
    next_sub_out = sub_out;
    if (chan_0 == 1'b1) begin
        next_sub_out = $signed({{1{curr_shift[4]}} ,curr_shift}) - $signed({{1{filter_whole[4]}}, filter_whole});
    end
end

  // latency = 1
always @*
begin
    case(shift_val)
        7'd0 :
        begin
            next_i_val = pcorr_i[30:15];
            next_q_val = pcorr_q[30:15];
        end
        7'd1 :
        begin
            next_i_val = pcorr_i[29:14];
            next_q_val = pcorr_q[29:14];
        end
        7'd2 :
        begin
            next_i_val = pcorr_i[28:13];
            next_q_val = pcorr_q[28:13];
        end
        7'd3 :
        begin
            next_i_val = pcorr_i[27:12];
            next_q_val = pcorr_q[27:12];
        end
        7'd4 :
        begin
            next_i_val = pcorr_i[26:11];
            next_q_val = pcorr_q[26:11];
        end
        7'd5 :
        begin
            next_i_val = pcorr_i[25:10];
            next_q_val = pcorr_q[25:10];
        end
        7'd6 :
        begin
            next_i_val = pcorr_i[24:9];
            next_q_val = pcorr_q[24:9];
        end
        7'd7 :
        begin
            next_i_val = pcorr_i[23:8];
            next_q_val = pcorr_q[23:8];
        end
        -7'd1 :
        begin
            next_i_val = pcorr_i[31:16];
            next_q_val = pcorr_q[31:16];
        end
        -7'd2 :
        begin
            next_i_val = pcorr_i[32:17];
            next_q_val = pcorr_q[32:17];
        end
        -7'd3 :
        begin
            next_i_val = pcorr_i[33:18];
            next_q_val = pcorr_q[33:18];
        end
        -7'd4 :
        begin
            next_i_val = pcorr_i[34:19];
            next_q_val = pcorr_q[34:19];
        end
        -7'd5 :
        begin
            next_i_val = pcorr_i[35:20];
            next_q_val = pcorr_q[35:20];
        end
        -7'd6 :
        begin
            next_i_val = pcorr_i[36:21];
            next_q_val = pcorr_q[36:21];
        end
        -7'd7 :
        begin
            next_i_val = pcorr_i[37:22];
            next_q_val = pcorr_q[37:22];
        end
        default :
        begin
            if (shift_val[6] == 1'b1) begin
                next_i_val = pcorr_i[37:22];
                next_q_val = pcorr_q[37:22];
            end else begin
                next_i_val = pcorr_i[23:8];
                next_q_val = pcorr_q[23:8];
            end
        end
    endcase
end

  cic_M256_N1_R1_iw5_0 u_avg_filter(
    .clk(clk),
    .sync_reset(sync_reset),
    .msetting(avg_len),
    .s_axis_tvalid(s_axis_status_tvalid),
    .s_axis_tdata(filter_tdata),
    .s_axis_tready(filter_tready),
    .m_axis_tvalid(filter_tvalid),
    .m_axis_tready(1'b1),
    .m_axis_tdata(filter_out_tdata));

  // latency = 3.
  exp_shift_sp_rom u_corr_table(
    .clk(clk),
    .addra(lookup),
    .doa(corr_fac));

  // latency 4
  dsp48_shift_corr u_corrI(
    .clk(clk),
    .a(tdatai),
    .b(corr_fac),
    .p(pcorr_i));

  // latency 4
  dsp48_shift_corr u_corrq(
    .clk(clk),
    .a(tdataq),
    .b(corr_fac),
    .p(pcorr_q));

  // Output filter.
  axi_fifo_51 #(
    .DATA_WIDTH(32),
    .ALMOST_FULL_THRESH(16),
    .TUSER_WIDTH(24),
    .ADDR_WIDTH(5))
  u_fifo(
    .clk(clk),
    .sync_reset(sync_reset),
    .s_axis_tvalid(take_d[7]),
    .s_axis_tdata(fifo_tdata),
    .s_axis_tlast(tlast_d[7]),
    .s_axis_tuser(tuser_d7),
    .s_axis_tready(),
    .almost_full(almost_full),
    .m_axis_tvalid(m_axis_tvalid),
    .m_axis_tdata(m_axis_tdata),
    .m_axis_tlast(m_axis_tlast),
    .m_axis_tuser(m_axis_tuser_s),
    .m_axis_tready(m_axis_tready));


endmodule
