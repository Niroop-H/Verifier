include RBA
layout = Layout.new
layout.dbu = 0.001
cell = layout.create_cell("TOP")
layer = layout.layer(1, 0)
width_um = ($width || "0.20").to_f
width_dbu = [(width_um / layout.dbu).round, 1].max
cell.shapes(layer).insert(Box.new(0, 0, 1000, width_dbu))
layout.write($output_file)
