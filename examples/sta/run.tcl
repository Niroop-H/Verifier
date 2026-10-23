read_liberty [file join [file dirname [info script]] tiny.lib]
read_verilog [file join [file dirname [info script]] inverter.v]
link_design top
create_clock -name virtual_clk -period 1.0
set_input_delay 0.10 -clock virtual_clk [get_ports a]
set_output_delay 0.10 -clock virtual_clk [get_ports y]
report_checks -path_delay max -format full_clock_expanded
exit
