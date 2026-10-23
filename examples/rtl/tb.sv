module tb;
    logic [7:0] a, b;
    logic sel;
    logic [7:0] y;
    alu dut(.a(a), .b(b), .sel(sel), .y(y));
    initial begin
        a = 8'd5; b = 8'd7; sel = 1'b1; #1;
        if (y !== 8'd12) $fatal(1, "addition check failed");
        sel = 1'b0; #1;
        if (y !== (8'd5 ^ 8'd7)) $fatal(1, "xor check failed");
        $display("MQV_SIM_PASS");
        $finish;
    end
endmodule
