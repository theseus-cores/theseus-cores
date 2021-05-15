module dsp48_pfb_rnd
(
    input clk,
    input ce,

    input [47:0] pcin,
    output [15:0] p
);

wire [47:0] p_s;
reg p_d = 1'b0;


assign p = p_s[39:24];

always @(posedge clk)
begin
    if (ce == 1'b1) begin
		p_d <= p_s[0];
    end
end

DSP48E1 #(
    // Feature Control Attributes: Data Path Selection
    .A_INPUT("DIRECT"), // Selects A input source, "DIRECT" (A port) or "CASCADE" (ACIN port)
    .B_INPUT("DIRECT"), // Selects B input source, "DIRECT" (B port) or "CASCADE" (BCIN port)
    .USE_DPORT("FALSE"), // Select D port usage (TRUE or FALSE)
    .USE_MULT("NONE"), // Select multiplier usage ("MULTIPLY", "DYNAMIC", or "NONE")
    // Pattern Detector Attributes: Pattern Detection Configuration
    .AUTORESET_PATDET("NO_RESET"), // "NO_RESET", "RESET_MATCH", "RESET_NOT_MATCH"
    .MASK(48'h3fffffffffff), // 48-bit mask value for pattern detect (1=ignore)
    .PATTERN(48'h000000000000), // 48-bit pattern match for pattern detect
    .SEL_MASK("MASK"), // "C", "MASK", "ROUNDING_MODE1", "ROUNDING_MODE2"
    .SEL_PATTERN("PATTERN"), // Select pattern value ("PATTERN" or "C")
    .USE_PATTERN_DETECT("NO_PATDET"), // Enable pattern detect ("PATDET" or "NO_PATDET")
    // Register Control Attributes: Pipeline Register Configuration
    .ACASCREG(1), // Number of pipeline stages between A/ACIN and ACOUT (0, 1 or 2)
    .ADREG(0), // Number of pipeline stages for pre-adder (0 or 1)
    .ALUMODEREG(1), // Number of pipeline stages for ALUMODE (0 or 1)
    .AREG(1), // Number of pipeline stages for A (0, 1 or 2)
    .BCASCREG(1), // Number of pipeline stages between B/BCIN and BCOUT (0, 1 or 2)
    .BREG(1), // Number of pipeline stages for B (0, 1 or 2)
    .CARRYINREG(1), // Number of pipeline stages for CARRYIN (0 or 1)
    .CARRYINSELREG(1), // Number of pipeline stages for CARRYINSEL (0 or 1)
    .CREG(0), // Number of pipeline stages for C (0 or 1)
    .DREG(0), // Number of pipeline stages for D (0 or 1)
    .INMODEREG(1), // Number of pipeline stages for INMODE (0 or 1)
    .MREG(0), // Number of multiplier pipeline stages (0 or 1)
    .OPMODEREG(1), // Number of pipeline stages for OPMODE (0 or 1)
    .PREG(1), // Number of pipeline stages for P (0 or 1)
    .USE_SIMD("ONE48") // SIMD selection ("ONE48", "TWO24", "FOUR12")
)
dsp_48_inst (
    // Cascade: 30-bit (each) output: Cascade Ports
    .ACOUT(), // 30-bit output: A port cascade output
    .BCOUT(), // 18-bit output: B port cascade output
    .CARRYCASCOUT(), // 1-bit output: Cascade carry output
    .MULTSIGNOUT(), // 1-bit output: Multiplier sign cascade output
    .PCOUT(), // 48-bit output: Cascade output
    // Control: 1-bit (each) output: Control Inputs/Status Bits
    .OVERFLOW(), // 1-bit output: Overflow in add/acc output
    .PATTERNBDETECT(), // 1-bit output: Pattern bar detect output
    .PATTERNDETECT(), // 1-bit output: Pattern detect output
    .UNDERFLOW(), // 1-bit output: Underflow in add/acc output
    // Data: 4-bit (each) output: Data Ports
    .CARRYOUT(), // 4-bit output: Carry output
    .P(p_s), //-- 48-bit output: Primary data output
    // Cascade: 30-bit (each) input: Cascade Ports
    .ACIN(30'd0), // 30-bit input: A cascade data input
    .BCIN(18'd0), // 18-bit input: B cascade input
    .CARRYCASCIN(1'b0), // 1-bit input: Cascade carry input
    .MULTSIGNIN(1'b0), // 1-bit input: Multiplier sign input
    .PCIN(pcin), // 48-bit input: P cascade input
    // Control: 4-bit (each) input: Control Inputs/Status Bits
    .ALUMODE(4'd0), // 4-bit input: ALU control input
    .CARRYINSEL(3'd0), // 3-bit input: Carry select input
    .CEINMODE(1'b1), // 1-bit input: Clock enable input for INMODEREG
    .CLK(clk), // 1-bit input: Clock input
    .INMODE(5'd19), // 5-bit input: INMODE control input
    .OPMODE(7'd28), // 7-bit input: Operation mode input
    .RSTINMODE(1'b0), // 1-bit input: Reset input for INMODEREG
    // Data: 30-bit (each) input: Data Ports
    .A(30'd1), // 30-bit input: A data input
    .B(18'd1), // 18-bit input: B data input
    .C(48'd8388607), // 48-bit input: C data input
    .CARRYIN(p_d), // 1-bit input: Carry input signal
    .D(25'd0), // 25-bit input: D data input
    // Reset/Clock Enable: 1-bit (each) input: Reset/Clock Enable Inputs
    .CEA1(ce), // 1-bit input: Clock enable input for 1st stage AREG
    .CEA2(1'b0), // 1-bit input: Clock enable input for 2nd stage AREG
    .CEAD(ce), // 1-bit input: Clock enable input for ADREG
    .CEALUMODE(1'b1), // 1-bit input: Clock enable input for ALUMODERE
    .CEB1(ce), // 1-bit input: Clock enable input for 1st stage BREG
    .CEB2(1'b0), // 1-bit input: Clock enable input for 2nd stage BREG
    .CEC(ce), // 1-bit input: Clock enable input for CREG
    .CECARRYIN(ce), // 1-bit input: Clock enable input for CARRYINREG
    .CECTRL(1'b1), // 1-bit input: Clock enable input for OPMODEREG and CARRYINSELREG
    .CED(ce), // 1-bit input: Clock enable input for DREG
    .CEM(ce), // 1-bit input: Clock enable input for MREG
    .CEP(ce), // 1-bit input: Clock enable input for PREG
    .RSTA(1'b0), // 1-bit input: Reset input for AREG
    .RSTALLCARRYIN(1'b0), // 1-bit input: Reset input for CARRYINREG
    .RSTALUMODE(1'b0), // 1-bit input: Reset input for ALUMODEREG
    .RSTB(1'b0), // 1-bit input: Reset input for BREG
    .RSTC(1'b0), // 1-bit input: Reset input for CREG
    .RSTCTRL(1'b0), // 1-bit input: Reset input for OPMODEREG and CARRYINSELREG
    .RSTD(1'b0), // 1-bit input: Reset input for DREG and ADREG
    .RSTM(1'b0), // 1-bit input: Reset input for MREG
    .RSTP(1'b0) // 1-bit input: Reset input for PREG
);

endmodule
