# Generic smoke deck only; not a foundry rule deck.
report("MAH Quantum Verify DRC smoke", $report_file)
source($input_file)
metal1 = input(1, 0)
metal1.width(0.05.um).output("M1.MIN_WIDTH", "Metal 1 minimum width less than 0.05um")
