
//     Licensed to the Apache Software Foundation (ASF) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The ASF licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at
// 
//   http://www.apache.org/licenses/LICENSE-2.0
// 
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.  


/*****************************************************************************/
//
// Author      : Phil Vallance
// File        : dp_block_write_first_ram.v
// Description : Implements a single port RAM with block ram. The ram is a fully
//               pipelined implementation -- 3 clock cycles from new read address
//               to new data                                                     
//
//
/*****************************************************************************/


module dp_block_write_first_ram
#(parameter DATA_WIDTH=32,
  parameter ADDR_WIDTH=8)
(
  input clk, 

  input wea,
  input [ADDR_WIDTH-1:0] addra,
  input [ADDR_WIDTH-1:0] addrb,
  input [DATA_WIDTH-1:0] dia,
  output [DATA_WIDTH-1:0] dob
);

localparam ADDR_P1 = ADDR_WIDTH + 1;
localparam DATA_MSB = DATA_WIDTH - 1;
localparam ADDR_MSB = ADDR_WIDTH - 1;
localparam DEPTH = 2 ** ADDR_WIDTH;

(* ram_style = "block" *) reg [DATA_MSB:0] ram [DEPTH-1:0];

reg [ADDR_MSB:0] addra_d;
reg [ADDR_MSB:0] addrb_d;
reg wea_d;
reg [DATA_MSB:0] dia_d;
reg [DATA_MSB:0] dob_d;
reg [DATA_MSB:0] ram_pipe;
assign dob = dob_d;

integer i;
initial begin
    for (i = 0; i < DEPTH; i=i+1) begin
        ram[i] = 0;
    end
end

// port a
always @(posedge clk)
begin
    if (wea_d == 1'b1) begin
      ram[addra_d] <= dia_d;
    end
    dia_d <= dia;
    addra_d <= addra;
    wea_d <= wea;
end

// port b
always @(posedge clk)
begin
    addrb_d <= addrb;
    ram_pipe <= ram[addrb_d];
    dob_d <= ram_pipe;
end

endmodule
