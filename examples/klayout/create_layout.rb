# Synthetic fixture to verify KLayout runtime plumbing, not a foundry DRC test.
include RBA
layout = Layout.new
layout.dbu = 0.001
top = layout.create_cell("MQV_TOP")
layer_id = layout.layer(1, 0)
top.shapes(layer_id).insert(Box.new(0, 0, 1000, 1000))
layout.write($out)
puts "MQV_KLAYOUT_FIXTURE_CREATED"
