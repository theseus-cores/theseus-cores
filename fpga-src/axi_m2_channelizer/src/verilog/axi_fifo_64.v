/*****************************************************************************/
//
// Author      : PJV
// File        : axi_fifo_64
// Description : Generates FIFO with AXI interface. 
//
//                Latency = 3.
//
/*****************************************************************************/

module axi_fifo_64
#( parameter DATA_WIDTH=32,
   parameter ADDR_WIDTH=8)
(
    input clk,
    input sync_reset,
    
    input s_axis_tvalid,
    input [DATA_WIDTH-1:0] s_axis_tdata,
    output s_axis_tready,
    input [8:0] delay,


    output m_axis_tvalid,
    output [DATA_WIDTH-1:0] m_axis_tdata,
    input m_axis_tready
);

localparam ADDR_P1 = ADDR_WIDTH + 1;
localparam FIFO_WIDTH = DATA_WIDTH;
localparam FIFO_MSB = FIFO_WIDTH - 1;
localparam ADDR_MSB = ADDR_WIDTH - 1;
localparam DEPTH = 2 ** ADDR_WIDTH;

reg [ADDR_WIDTH:0] wr_ptr = 0, next_wr_ptr;
reg [ADDR_WIDTH:0] wr_addr = 0, next_wr_addr;
reg [ADDR_WIDTH:0] rd_ptr = 0, next_rd_ptr;

(* ram_style = "block" *) reg [FIFO_MSB:0] buffer [DEPTH-1:0];
wire [FIFO_MSB:0] wr_data;

reg [8:0] delay_d1, next_delay_d1;
wire add_delay;
wire [ADDR_WIDTH:0] delay_s;
// full when first MSB different but rest same
wire full;
// empty when pointers match exactly
wire empty;

// control signals
reg wr;
reg rd;
reg [1:0] occ_reg = 2'b00, next_occ_reg;
reg [FIFO_MSB:0] data_d0, data_d1, next_data_d0, next_data_d1;

// control signals
assign full = ((wr_addr[ADDR_WIDTH] != rd_ptr[ADDR_WIDTH]) && (wr_addr[ADDR_MSB:0] == rd_ptr[ADDR_MSB:0]));
assign s_axis_tready = ~full;
assign m_axis_tvalid = occ_reg[1];
assign empty = (wr_ptr == rd_ptr) ? 1'b1 : 1'b0;

assign wr_data = s_axis_tdata;
assign m_axis_tdata = data_d1;
assign add_delay = (delay != delay_d1) ? 1'b1 : 1'b0;
assign delay_s = {1'b0, delay};

integer i;
initial begin
    for (i = 0; i < DEPTH; i=i+1) begin
        buffer[i] = 0;
    end
end

// Write logic
always @* begin
    wr = 1'b0;
    next_wr_ptr = wr_ptr;
    next_wr_addr = wr_addr;
    next_delay_d1 = delay_d1;

    if (s_axis_tvalid) begin
        // input data valid
        if (~full) begin
            // not full, perform write
            wr = 1'b1;
            next_wr_ptr = wr_ptr + 1;
            if (add_delay == 1'b1) begin
                next_wr_addr = wr_ptr + delay_s + 1;
                next_delay_d1 = delay;
            end else begin
                next_wr_addr = wr_addr + 1;
            end
        end
    end
end

always @(posedge clk) begin
    if (sync_reset) begin
        wr_ptr <= 0;
        wr_addr <= delay_s;
        occ_reg <= 0;
        data_d0 <= 0;
        data_d1 <= 0;
        delay_d1 <= 0;
    end else begin
        wr_ptr <= next_wr_ptr;
        wr_addr <= next_wr_addr;
        occ_reg <= next_occ_reg;
        data_d0 <= next_data_d0;
        data_d1 <= next_data_d1;
        delay_d1 <= next_delay_d1;
    end

    if (wr) begin
        buffer[wr_addr[ADDR_MSB:0]] <= wr_data;
    end
end

// Read logic
always @* begin
    rd = 1'b0;
    next_rd_ptr = rd_ptr;
    next_occ_reg[0] = occ_reg[0];
    next_occ_reg[1] = occ_reg[1];
    next_data_d0 = data_d0;
    next_data_d1 = data_d1;
    if (occ_reg != 2'b11 | m_axis_tready == 1'b1) begin
        // output data not valid OR currently being transferred
        if (~empty) begin
            // not empty, perform read
            rd = 1'b1;
            next_rd_ptr = rd_ptr + 1;
        end
    end

    if (rd) begin
        next_occ_reg[0] = 1'b1;
    end else if (m_axis_tready == 1'b1 || occ_reg[1] == 1'b0) begin
        next_occ_reg[0] = 1'b0;
    end
    if (m_axis_tready == 1'b1 || occ_reg[1] == 1'b0) begin
        next_occ_reg[1] = occ_reg[0];
    end

    if (rd) begin
        next_data_d0 = buffer[rd_ptr[ADDR_MSB:0]];
    end
    if (m_axis_tready | ~occ_reg[1]) begin
        next_data_d1 = data_d0;
    end
end

always @(posedge clk) begin
    if (sync_reset) begin
        rd_ptr <= 0;
    end else begin
        rd_ptr <= next_rd_ptr;
    end

end


endmodule
