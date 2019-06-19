//***************************************************************************--
//
// Author : PJV
// File : channelizer_top
// Description : Top level wrapper for the M/2 Polyphase Channelizer bank.
//
//***************************************************************************--

// no timescale needed
`include "chan_rfnoc_sim.vh"

module channelizer_top#(
    parameter DATA_WIDTH = 32)
(
    input clk,
    input sync_reset,

    input s_axis_tvalid,
    input [31:0] s_axis_tdata,
    output s_axis_tready,

    input s_axis_reload_tvalid,
    input [31:0] s_axis_reload_tdata,
    input s_axis_reload_tlast,
    output s_axis_reload_tready,

    // down selection FIFO interface
    input s_axis_select_tvalid,
    input [31:0] s_axis_select_tdata,
    input s_axis_select_tlast,
    output s_axis_select_tready,

    input [11:0] fft_size,
    input [8:0] avg_len,
    input [15:0] payload_length,
    output eob_tag,

    output m_axis_tvalid,
    output [31:0] m_axis_tdata,
    output [23:0] m_axis_tuser,
    output m_axis_tlast,
    input m_axis_tready
);

// currently only supporting up to 2048 bins.
// Average Floating Point Exponent averaging length

localparam FFT_8 = 8;
localparam FFT_16 = 16;
localparam FFT_32 = 32;
localparam FFT_64 = 64;
localparam FFT_128 = 128;
localparam FFT_256 = 256;
localparam FFT_512 = 512;
localparam FFT_1024 = 1024;
localparam FFT_2048 = 2048;

localparam [4:0] RESET_ZEROS = 5'd0;
localparam [4:0] RESET_HIGH_CNT = 5'b01000;  // buffer signals

reg [4:0] nfft, next_nfft;
reg [11:0] fft_size_s;
wire event_frame_started;
wire event_tlast_unexpected;
wire event_tlast_missing;
wire event_status_channel_halt;
wire event_data_in_channel_halt;
wire event_data_out_channel_halt;  // reset signals

reg async_reset, async_reset_d1;
reg reset_int,  next_reset_int;
reg [4:0] reset_cnt, next_reset_cnt;

// internal payload_length register
reg [15:0] payload_length_s, payload_length_m1;

wire buffer_tvalid;
wire [DATA_WIDTH - 1:0] buffer_tdata;
wire buffer_tlast;
wire [10:0] buffer_phase;
wire buffer_tready;
// pfb signals
wire pfb_tvalid;
wire [DATA_WIDTH - 1:0] pfb_tdata;
wire pfb_tlast;
wire [10:0] pfb_phase;
wire [10:0] circ_phase;
wire pfb_tready;

// circular buffer signals
wire circ_tvalid;
wire [DATA_WIDTH - 1:0] circ_tdata;
wire [DATA_WIDTH - 1:0] circ_tdata_s;
wire circ_tlast;  // signal circ_phase : std_logic_vector(10 downto 0);
wire circ_tready;

// fft data signals
wire fft_tvalid;
wire [DATA_WIDTH - 1:0] fft_tdata;
wire [DATA_WIDTH - 1:0] fft_tdata_s;
wire [23:0] fft_tuser;
wire fft_tlast;
wire fft_tready;

// fft config signals.
reg fft_config_tvalid, next_fft_config_tvalid;
wire fft_config_tready;
wire [15:0] fft_config_tdata;  // fft status signals

// exp shift signals
wire shift_tvalid;
wire [DATA_WIDTH - 1:0] shift_tdata;
wire [23:0] shift_tuser;
wire shift_tlast;
wire shift_tready;
wire shift_eob_tag;

// down select signals
wire down_sel_tvalid;
wire [DATA_WIDTH-1:0] down_sel_tdata;
wire [23:0] down_sel_tuser;
wire down_sel_tlast;
wire down_sel_tready;

wire m_axis_tvalid_s;
wire [DATA_WIDTH-1:0] m_axis_tdata_s;
wire [23:0] m_axis_tuser_s;
wire m_axis_tlast_s;
wire m_axis_tready_s;

wire [7:0] m_axis_status_tdata;
wire m_axis_status_tvalid;
wire m_axis_status_tready = 1'b1;

localparam S_CONFIG = 0, S_IDLE = 1;
reg config_state, next_config_state;

assign fft_config_tdata = {11'b00000000000,nfft};
assign fft_tdata = {fft_tdata_s[15:0],fft_tdata_s[31:16]};
assign circ_tdata = {circ_tdata_s[15:0],circ_tdata_s[31:16]};
assign s_axis_reload_tready = 1'b1;

//

always @*
begin
    next_fft_config_tvalid = 1'b0;
    next_config_state = config_state;
    next_nfft = nfft;
    case(config_state)
        S_CONFIG :
        begin
            if (fft_config_tready == 1'b1) begin
                next_fft_config_tvalid = 1'b1;
                next_config_state = S_IDLE;
            end
            if (fft_size == FFT_8) begin
                next_nfft = 5'b00011;
            end else if (fft_size == FFT_16) begin
                next_nfft = 5'b00100;
            end else if (fft_size == FFT_32) begin
                next_nfft = 5'b00101;
            end else if (fft_size == FFT_64) begin
                next_nfft = 5'b00110;
            end else if (fft_size == FFT_128) begin
                next_nfft = 5'b00111;
            end else if (fft_size == FFT_256) begin
                next_nfft = 5'b01000;
            end else if (fft_size == FFT_512) begin
                next_nfft = 5'b01001;
            end else if (fft_size == FFT_1024) begin
                next_nfft = 5'b01010;
            end else begin
                next_nfft = 5'b01011;
            end
        end
        S_IDLE :
        begin
            if (async_reset == 1'b1 && async_reset_d1 == 1'b0) begin
                next_config_state = S_CONFIG;
            end else begin
                next_config_state = S_IDLE;
            end
        end
        default :
        begin
        end
    endcase
end

always @(posedge clk, posedge sync_reset)
begin
    if (sync_reset == 1'b1) begin
        config_state <= S_IDLE;
        fft_config_tvalid <= 1'b0;
        nfft <= 5'b00111;
        fft_size_s <= 12'd128;
        // default to 128
        reset_cnt <= 5'd31;
        reset_int <= 1'b1;
    end else begin
        config_state <= next_config_state;
        fft_config_tvalid <= next_fft_config_tvalid;
        nfft <= next_nfft;
        if (fft_size != 0) begin
            fft_size_s <= fft_size;
        end
        reset_cnt <= next_reset_cnt;
        reset_int <= next_reset_int;
    end
end

always @(posedge clk)
begin
    async_reset <= !(sync_reset | reset_int);
    async_reset_d1 <= async_reset;
    payload_length_s <= payload_length;
    payload_length_m1 <= payload_length_s - 1;
end

  // ensures that reset pulse is wide enough for all blocks.
always @*
begin
    next_reset_cnt = reset_cnt;
    if (fft_size_s != fft_size || payload_length_s != payload_length) begin
        next_reset_cnt = RESET_HIGH_CNT;
    end else if (reset_cnt != 0) begin
        next_reset_cnt = reset_cnt - 1;
    end
    if (reset_cnt != RESET_ZEROS) begin
        next_reset_int = 1'b1;
    end else begin
        next_reset_int = 1'b0;
    end
end

input_buffer #(
    .DATA_WIDTH(DATA_WIDTH),
    .FFT_SIZE_WIDTH(12))
u_input_buffer(
    .clk(clk),
    .sync_reset(reset_int),

    .s_axis_tvalid(s_axis_tvalid),
    .s_axis_tdata(s_axis_tdata),
    .s_axis_tready(s_axis_tready),

    .fft_size(fft_size_s),
    .phase(buffer_phase),

    .m_axis_tvalid(buffer_tvalid),
    .m_axis_tdata(buffer_tdata),
    .m_axis_final_cnt(buffer_tlast),
    .m_axis_tready(buffer_tready)
);

pfb_2x_16iw_16ow_32tps u_pfb(
    .clk(clk),
    .sync_reset(reset_int),

    .s_axis_tvalid(buffer_tvalid),
    .s_axis_tdata(buffer_tdata),
    .s_axis_tlast(1'b0),
    .s_axis_tready(buffer_tready),

    .fft_size(fft_size_s),
    .phase(buffer_phase),
    .phase_out(pfb_phase),

    .s_axis_reload_tvalid(s_axis_reload_tvalid),
    .s_axis_reload_tdata(s_axis_reload_tdata),
    .s_axis_reload_tlast(s_axis_reload_tlast),
    .s_axis_reload_tready(s_axis_reload_tready),

    .m_axis_tvalid(pfb_tvalid),
    .m_axis_tdata(pfb_tdata),
    .m_axis_tlast(pfb_tlast),
    .m_axis_tready(pfb_tready)
);

circ_buffer #(
    .DATA_WIDTH(DATA_WIDTH),
    .FFT_SIZE_WIDTH(12))
u_circ_buffer(
    .clk(clk),
    .sync_reset(reset_int),

    .s_axis_tvalid(pfb_tvalid),
    .s_axis_tdata(pfb_tdata),
    .s_axis_tlast(pfb_tlast),
    .s_axis_tready(pfb_tready),

    .fft_size(fft_size_s),
    .phase(pfb_phase),
    .phase_out(circ_phase),

    .m_axis_tvalid(circ_tvalid),
    .m_axis_tdata(circ_tdata_s),
    .m_axis_tlast(circ_tlast),
    .m_axis_tready(circ_tready)
);

xfft u_fft(
    .aclk(clk),
    .aresetn(async_reset),
    .s_axis_config_tvalid(fft_config_tvalid),
    .s_axis_config_tdata(fft_config_tdata),
    .s_axis_config_tready(fft_config_tready),
    .s_axis_data_tvalid(circ_tvalid),
    .s_axis_data_tdata(circ_tdata),
    .s_axis_data_tlast(circ_tlast),
    .s_axis_data_tready(circ_tready),
    .m_axis_data_tvalid(fft_tvalid),
    .m_axis_data_tdata(fft_tdata_s),
    .m_axis_data_tuser(fft_tuser),
    .m_axis_data_tlast(fft_tlast),
    .m_axis_data_tready(fft_tready),
    .m_axis_status_tvalid(m_axis_status_tvalid),
    .m_axis_status_tdata(m_axis_status_tdata),
    .m_axis_status_tready(m_axis_status_tready),
    .event_frame_started(event_frame_started),
    .event_tlast_unexpected(event_tlast_unexpected),
    .event_tlast_missing(event_tlast_missing),
    .event_data_in_channel_halt(event_data_in_channel_halt)
);

exp_shifter u_shifter(
    .clk(clk),
    .sync_reset(reset_int),

    .s_axis_tvalid(fft_tvalid),
    .s_axis_tdata(fft_tdata),
    .s_axis_tuser(fft_tuser),
    .s_axis_tlast(fft_tlast),
    .s_axis_tready(fft_tready),

    .fft_size(fft_size_s),
    .avg_len(avg_len),

    .m_axis_tvalid(shift_tvalid),
    .m_axis_tdata(shift_tdata),
    .m_axis_tuser(shift_tuser),
    .m_axis_tlast(shift_tlast),

    .eob_tag(shift_eob_tag),
    .m_axis_tready(shift_tready)
);

downselect #(
    .DATA_WIDTH(DATA_WIDTH))
u_downselect(
    .clk(clk),
    .sync_reset(reset_int),

    .s_axis_tvalid(shift_tvalid),
    .s_axis_tdata(shift_tdata),
    .s_axis_tuser(shift_tuser),
    .s_axis_tlast(shift_tlast),
    .s_axis_tready(shift_tready),

    .eob_tag(shift_eob_tag),

    // down selection FIFO interface
    .s_axis_select_tvalid(s_axis_select_tvalid),
    .s_axis_select_tdata(s_axis_select_tdata),
    .s_axis_select_tlast(s_axis_select_tlast),
    .s_axis_select_tready(s_axis_select_tready),

    .m_axis_tvalid(down_sel_tvalid),
    .m_axis_tdata(down_sel_tdata),
    .m_axis_tuser(down_sel_tuser),
    .m_axis_tlast(down_sel_tlast),
    .m_axis_tready(down_sel_tready),

    .eob_downselect(eob_tag)
);

count_cycle_cw16_65 #(
    .DATA_WIDTH(DATA_WIDTH),
    .TUSER_WIDTH(24))
u_final_cnt
(
    .clk(clk),
    .sync_reset(reset_int),

    .s_axis_tvalid(down_sel_tvalid),
    .s_axis_tdata(down_sel_tdata),
    .cnt_limit(payload_length_m1),
    .s_axis_tuser(down_sel_tuser),
    .s_axis_tlast(down_sel_tlast),
    .s_axis_tready(down_sel_tready),

    .m_axis_tvalid(m_axis_tvalid_s),
    .m_axis_tdata(m_axis_tdata_s),
    .m_axis_final_cnt(m_axis_tlast_s),
    .m_axis_tuser(m_axis_tuser_s),
    .count(),
    .m_axis_tlast(),
    .m_axis_tready(m_axis_tready_s)
);

`ifdef SIM_BIN_WRITE

    localparam buffer_out = "buffer_output.bin";
    localparam pfb_out = "pfb_output.bin";
    localparam circ_out = "circ_output.bin";
    localparam fft_out = "fft_output.bin";
    localparam exp_out = "exp_output.bin";
    localparam down_select_out = "down_select_output.bin";
    localparam final_out = "final_output.bin";

    integer buffer_descr, pfb_descr, circ_descr, fft_descr, exp_descr, down_descr, final_descr;

    initial begin
        buffer_descr = $fopen(buffer_out, "wb");
        pfb_descr = $fopen(pfb_out, "wb");
        circ_descr = $fopen(circ_out, "wb");
        fft_descr = $fopen(fft_out, "wb");
        exp_descr = $fopen(exp_out, "wb");
        down_descr = $fopen(down_select_out, "wb");
        final_descr = $fopen(final_out, "wb");
    end

    wire buffer_take, pfb_take, circ_take, fft_take, exp_take, down_take, final_take;

    wire [63:0] buffer_st_tdata;
    wire [63:0] pfb_st_tdata;
    wire [63:0] fft_st_tdata;
    wire [31:0] circ_st_tdata;
    wire [63:0] exp_st_tdata;
    wire [63:0] down_st_tdata;
    wire [63:0] final_st_tdata;

    assign buffer_st_tdata = {21'd0, buffer_phase, buffer_tdata};
    assign pfb_st_tdata = {21'd0, pfb_phase, pfb_tdata};
    assign fft_st_tdata = {8'd0, fft_tuser, fft_tdata};
    assign exp_st_tdata = {8'd0, shift_tuser, shift_tdata};
    assign down_st_tdata = {8'd0, down_sel_tuser, down_sel_tdata};
    assign final_st_tdata = {8'd0, m_axis_tuser_s, m_axis_tdata_s};

    assign circ_st_tdata = circ_tdata_s;

    assign buffer_take = buffer_tvalid & buffer_tready;
    assign pfb_take = pfb_tvalid & pfb_tready;

    assign circ_take = circ_tvalid & circ_tready;
    assign fft_take = fft_tvalid & fft_tready;
    assign exp_take = shift_tvalid & shift_tready;
    assign down_take = down_sel_tvalid & down_sel_tready;
    assign final_take = m_axis_tvalid_s & m_axis_tready_s;

    grc_word_writer #(
        .LISTEN_ONLY(1),
        .ARRAY_LENGTH(1024),
        .NUM_BYTES(8)
    )
    u_buffer_wr
    (
        .clk(clk),
        .sync_reset(reset_int),
        .enable(1'b1),

        .fd(buffer_descr),

        .valid(buffer_take),
        .word(buffer_st_tdata),

        .wr_file(1'b0),

        .rdy_i(1'b1),
        .rdy_o()
        );

    grc_word_writer #(
        .LISTEN_ONLY(1),
        .ARRAY_LENGTH(1024),
        .NUM_BYTES(8)
    )
    u_pfb_wr
    (
        .clk(clk),
        .sync_reset(reset_int),
        .enable(1'b1),

        .fd(pfb_descr),

        .valid(pfb_take),
        .word(pfb_st_tdata),

        .wr_file(1'b0),

        .rdy_i(1'b1),
        .rdy_o()
    );

    grc_word_writer #(
        .LISTEN_ONLY(1),
        .ARRAY_LENGTH(1024),
        .NUM_BYTES(4)
    )
    u_circ_wr
    (
        .clk(clk),
        .sync_reset(reset_int),
        .enable(1'b1),

        .fd(circ_descr),

        .valid(circ_take),
        .word(circ_st_tdata),

        .wr_file(1'b0),

        .rdy_i(1'b1),
        .rdy_o()
    );

    grc_word_writer #(
        .LISTEN_ONLY(1),
        .ARRAY_LENGTH(1024),
        .NUM_BYTES(8)
        )
    u_fft_wr
    (
        .clk(clk),
        .sync_reset(reset_int),
        .enable(1'b1),

        .fd(fft_descr),

        .valid(fft_take),
        .word(fft_st_tdata),

        .wr_file(1'b0),

        .rdy_i(1'b1),
        .rdy_o()
        );

    grc_word_writer #(
        .LISTEN_ONLY(1),
        .ARRAY_LENGTH(1024),
        .NUM_BYTES(8)
        )
    u_exp_wr
    (
        .clk(clk),
        .sync_reset(reset_int),
        .enable(1'b1),

        .fd(exp_descr),

        .valid(exp_take),
        .word(exp_st_tdata),

        .wr_file(1'b0),

        .rdy_i(1'b1),
        .rdy_o()
        );

    grc_word_writer #(
        .LISTEN_ONLY(1),
        .ARRAY_LENGTH(1024),
        .NUM_BYTES(8)
        )
    u_downselect_wr
    (
        .clk(clk),
        .sync_reset(reset_int),
        .enable(1'b1),

        .fd(down_descr),

        .valid(down_take),
        .word(down_st_tdata),

        .wr_file(1'b0),

        .rdy_i(1'b1),
        .rdy_o()
        );

    grc_word_writer #(
        .LISTEN_ONLY(1),
        .ARRAY_LENGTH(1024),
        .NUM_BYTES(8)
        )
    u_final_wr
    (
        .clk(clk),
        .sync_reset(reset_int),
        .enable(1'b1),

        .fd(final_descr),

        .valid(final_take),
        .word(final_st_tdata),

        .wr_file(1'b0),

        .rdy_i(1'b1),
        .rdy_o()
        );

`endif


endmodule
