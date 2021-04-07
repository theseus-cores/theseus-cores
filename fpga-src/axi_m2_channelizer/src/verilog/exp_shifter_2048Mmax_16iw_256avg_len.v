//*****************************************************************************
//
// Since the fft is block floating point the apparent signal amplitude can be shifted
// in consecutive fft blocks.  The Exponent shifter, exp_shifter, implements a simple
// low pass filtering the shift signal and provides gain correction mechanism for mitigating
// the amplitude shifts caused by the fft module.  The module also provides buffering
// and flow control logic so that it can directly connected to the rest of the
// infrastructure.
//*****************************************************************************

// no timescale needed

module exp_shifter_2048Mmax_16iw_256avg_len#(
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

    output m_axis_tvalid,
    output [31:0] m_axis_tdata,
    output [23:0] m_axis_tuser,
    output m_axis_tlast,
    input m_axis_tready
);


wire s_axis_tready_s;  // delay signals

reg [15:0] tdatai[0:3];
reg [15:0] tdataq[0:3];

reg [23:0] tuser_d[0:4];
reg [4:0] tlast_d;
reg [4:0] take_d;

wire [47:0] pcorr_i, pcorr_q;
wire filter_tready;
reg [15:0] i_val, next_i_val;
reg [15:0] q_val, next_q_val;
wire [31:0] fifo_tdata;
wire [4:0] filter_tdata;
wire filter_tvalid, filter_out_tvalid;
wire [12:0] filter_out_tdata;
reg [12:0] filter_d, next_filter_d;
wire [4:0] filter_whole;
reg [4:0] filter_whole_d;

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
assign fft_bin = tuser_d[1][10:0];
assign filter_whole = filter_d[12:8];

assign eob_tag = m_axis_tuser_s[23];
assign m_axis_tuser = m_axis_tuser_s;
assign fifo_tdata = {i_val, q_val};

assign chan_0 = (fft_bin == 11'd0 && take_d[1] == 1'b1) ? 1'b1 : 1'b0;

assign filter_tdata = s_axis_tuser[20:16];
assign filter_tvalid = (take == 1'b1 && s_axis_tuser[10:0] == 11'd0) ? 1'b1 : 1'b0;
assign curr_shift = tuser_d[1][20:16];

assign pcorr_i = { {16{tdatai[3][15]}}, tdatai[3], {{16{tdatai[3][0]}}} };
assign pcorr_q = { {16{tdataq[3][15]}}, tdataq[3], {{16{tdataq[3][0]}}} };


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

integer m;
always @(posedge clk) begin
    shift_val <= $signed({{1{sub_out[5]}},sub_out}) - $signed(HEAD_ROOM);
    take_d <= {take_d[3:0], take};
    tlast_d <= {tlast_d[3:0], s_axis_tlast};

    tdatai[0] <= s_axis_tdata[31:16];
    tdataq[0] <= s_axis_tdata[15:0];
    for (m=1; m<4; m=m+1) begin
        tdatai[m] <= tdatai[m-1];
        tdataq[m] <= tdataq[m-1];
    end

    tuser_d[0] <= {s_axis_tlast, s_axis_tuser[22:0]};
    for (m=1; m<5; m=m+1) begin
        tuser_d[m] <= tuser_d[m-1];
    end

    filter_whole_d <= filter_whole + filter_d[7];
end

always @*
begin
    // 1 tick delay
    next_filter_d = filter_d;
    if (filter_tvalid == 1'b1) begin
        next_filter_d = filter_out_tdata;
    end
    next_sub_out = sub_out;
    if (chan_0 == 1'b1) begin
        next_sub_out = $signed({{1{curr_shift[4]}} ,curr_shift}) - $signed({{1{filter_whole_d[4]}}, filter_whole_d});
    end
end

  // latency = 1
always @*
begin
    case(shift_val)
        7'd0 :
        begin
            next_i_val = pcorr_i[31:16];
            next_q_val = pcorr_q[31:16];
        end
        7'd1 :
        begin
            next_i_val = pcorr_i[30:15];
            next_q_val = pcorr_q[30:15];
        end
        7'd2 :
        begin
            next_i_val = pcorr_i[29:14];
            next_q_val = pcorr_q[29:14];
        end
        7'd3 :
        begin
            next_i_val = pcorr_i[28:13];
            next_q_val = pcorr_q[28:13];
        end
        7'd4 :
        begin
            next_i_val = pcorr_i[27:12];
            next_q_val = pcorr_q[27:12];
        end
        7'd5 :
        begin
            next_i_val = pcorr_i[26:11];
            next_q_val = pcorr_q[26:11];
        end
        7'd6 :
        begin
            next_i_val = pcorr_i[25:10];
            next_q_val = pcorr_q[25:10];
        end
        7'd7 :
        begin
            next_i_val = pcorr_i[24:9];
            next_q_val = pcorr_q[24:9];
        end
        -7'd1 :
        begin
            next_i_val = pcorr_i[32:17];
            next_q_val = pcorr_q[32:17];
        end
        -7'd2 :
        begin
            next_i_val = pcorr_i[33:18];
            next_q_val = pcorr_q[33:18];
        end
        -7'd3 :
        begin
            next_i_val = pcorr_i[34:19];
            next_q_val = pcorr_q[34:19];
        end
        -7'd4 :
        begin
            next_i_val = pcorr_i[35:20];
            next_q_val = pcorr_q[35:20];
        end
        -7'd5 :
        begin
            next_i_val = pcorr_i[36:21];
            next_q_val = pcorr_q[36:21];
        end
        -7'd6 :
        begin
            next_i_val = pcorr_i[37:22];
            next_q_val = pcorr_q[37:22];
        end
        -7'd7 :
        begin
            next_i_val = pcorr_i[38:23];
            next_q_val = pcorr_q[38:23];
        end
        default :
        begin
            if (shift_val[6] == 1'b1) begin
                next_i_val = pcorr_i[38:23];
                next_q_val = pcorr_q[38:23];
            end else begin
                next_i_val = pcorr_i[24:9];
                next_q_val = pcorr_q[24:9];
            end
        end
    endcase
end

// 20 tick delay
cic_M256_N1_R1_iw5_0 u_avg_filter(
    .clk(clk),
    .sync_reset(sync_reset),
    .msetting(avg_len),
    .s_axis_tvalid(filter_tvalid),
    .s_axis_tdata(filter_tdata),
    .s_axis_tready(filter_tready),
    .m_axis_tvalid(filter_out_tvalid),
    .m_axis_tready(1'b1),
    .m_axis_tdata(filter_out_tdata));

// Output fifo
axi_fifo_51 #(
    .DATA_WIDTH(32),
    .ALMOST_FULL_THRESH(16),
    .TUSER_WIDTH(24),
    .ADDR_WIDTH(5))
u_fifo(
    .clk(clk),
    .sync_reset(sync_reset),
    .s_axis_tvalid(take_d[4]),
    .s_axis_tdata(fifo_tdata),
    .s_axis_tlast(tlast_d[4]),
    .s_axis_tuser(tuser_d[4]),
    .s_axis_tready(),
    .almost_full(almost_full),
    .m_axis_tvalid(m_axis_tvalid),
    .m_axis_tdata(m_axis_tdata),
    .m_axis_tlast(m_axis_tlast),
    .m_axis_tuser(m_axis_tuser_s),
    .m_axis_tready(m_axis_tready));


endmodule
