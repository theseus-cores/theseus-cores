/*****************************************************************************/
//
// Author      : Phil Vallance
// File        : grc_word_reader.v
// Description : Test bench utility that reads in a binary file and parses out
//               real and complex signal components.
//
// Rev      Date         Comments
// --   -----------  ------------------------------------------------------
// Module reads a binary file (single line) of small-endian dataread
//
/*****************************************************************************/

`timescale 1ns/100ps
`define SEEK_SET 0
`define SEEK_CUR 1
`define SEEK_END 2

module grc_word_reader
#(parameter NUM_BYTES = 2,
  parameter FRAME_SIZE = 256)
(
	input clk,
	input sync_reset,
	input enable_i,

	input wire integer fd,

	output valid_o,
    output [NUM_BYTES*8 - 1:0] word_o,
	output buffer_end_o,
    output [63:0] len_o,
    output [63:0] word_cnt,

	input ready_i //input ready
);

// parameter FRAME_SIZE = 256;
parameter WORD_BITS = NUM_BYTES * 8;

reg valid_s = 1'b0;
reg next_valid;
// reg buffer_end, next_buffer_end;

integer position = 0;
integer num_read;
integer temp;
integer file_len;
integer offset;
// reg eof;

reg [WORD_BITS-1:0] word_s, next_word = 0;

integer index, next_index = 0;
reg buffer_end, next_buffer_end = 0;

integer total_reads, next_total_reads;
integer num_reads;

reg [63:0] word_cnt_s, next_word_cnt;
// reg [63:0] pkt_cnt_s, next_pkt_cnt;
reg [63:0] len_s, next_len_s;

reg [WORD_BITS - 1:0] memory [FRAME_SIZE - 1:0];

assign ready_data = (valid_s == 1'b0 | (valid_s == 1'b1 & ready_i == 1'b1));
assign valid_o = valid_s;
assign buffer_end_o = buffer_end;
assign len_o = len_s;
assign word_o = word_s;
assign word_cnt = word_cnt_s;

task tsk_reset;
begin
    // Delay file operations by 5 simulation cycles.
    // num_reads = FRAME_SIZE;
    // $display("reader fd = %d",fd);
    #5
    $display("Reader : file descriptor = %d",fd);
    // $display("current file position = %d", $ftell(fd));
    temp = $fseek(fd, position, `SEEK_END);
    file_len = $ftell(fd);
    $display("Reader : file length = %d",file_len);
    offset = $fseek(fd, position, `SEEK_SET);
    $display("Reader - current file position = %d", $ftell(fd));
    // read FRAME_SIZE into memory buffer.
    if (FRAME_SIZE > (file_len / NUM_BYTES)) begin
        num_reads = file_len / NUM_BYTES;
    end else begin
        num_reads = FRAME_SIZE;
    end
    num_read = $fread(memory, fd, 0, num_reads);  //Read in whole number of words.
    $display("number of bytes read = %d, frame size = %d", num_read, FRAME_SIZE);
    $display("memory read time @%0dns",$time);
end
endtask

initial
begin
    tsk_reset();
end
always @(posedge clk) begin
    if (sync_reset == 1'b1) begin
        valid_s <= 1'b0;
        word_s <= 0;
        index <= 0;
        buffer_end <= 1'b0;
        len_s <= 64'd0;
        total_reads = 0;
        word_cnt_s = 0;
        tsk_reset;
    end else begin
        valid_s <= next_valid;
        word_s <= next_word;
        index <= next_index;
        buffer_end <= next_buffer_end;
        len_s <= next_len_s;
        total_reads <= next_total_reads;
        word_cnt_s <= next_word_cnt;
    end
end

// integer num_reads_s;

// reg eof;
always @*
begin
    next_word = word_s;
    next_valid = valid_s;
    next_index = index;
    next_buffer_end = buffer_end;
    next_total_reads = total_reads;
    next_len_s = len_s;
    next_word_cnt = word_cnt_s;
	if (enable_i == 1'b1 && buffer_end == 1'b0) begin
        if (ready_data == 1'b1) begin
			next_valid = 1'b1;
			next_total_reads = total_reads + NUM_BYTES;
			next_word = memory[index];
			next_index = index + 1;
			next_buffer_end = 1'b0;
            next_word_cnt <= word_cnt_s + 1;
            if (index == num_reads - 1) begin
                // read new data into memory
                // get current file position.
                offset = $ftell(fd);
                next_index = 0;
                if ((offset + 1) > file_len) begin
                    next_buffer_end = 1'b1;
                    // start over
                    offset = $fseek(fd, 0, `SEEK_SET);
                    $display("end of file @%0dns",$time);
                end else begin
                    if ((offset + FRAME_SIZE * NUM_BYTES) > file_len) begin
                        num_reads = (file_len - offset) / NUM_BYTES;
                    end else begin
                        num_reads = FRAME_SIZE;
                    end
                    $display("offset = %d",offset);
                    num_read = $fread(memory, fd, 0, num_reads);  //return value is number of bytes read..
                    next_len_s = len_s + (num_read / NUM_BYTES);
                    $display("number of bytes read = %d, frame size = %d", num_read, FRAME_SIZE);
                    $display("memory read time @%0dns",$time);
                end
            end
        end else begin
            if (ready_data == 1'b1) begin
                next_valid = 1'b0;
            end
            if (buffer_end == 1'b1) begin
                next_len_s = len_s + (num_read / NUM_BYTES);
            end
        end
    end else begin
	    if (ready_data == 1'b1) begin
		    next_valid = 1'b0;
	    end
	end
end

endmodule
