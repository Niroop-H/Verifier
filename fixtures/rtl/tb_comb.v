module tb_comb;
  reg a;
  reg b;
  wire y;
  comb dut(.a(a), .b(b), .y(y));
  initial begin
    a = 0; b = 0; #1; if (y !== 0) $fatal(1, "00 failed");
    a = 0; b = 1; #1; if (y !== 0) $fatal(1, "01 failed");
    a = 1; b = 0; #1; if (y !== 0) $fatal(1, "10 failed");
    a = 1; b = 1; #1; if (y !== 1) $fatal(1, "11 failed");
    $display("MQV_SIM_PASS");
    $finish;
  end
endmodule
