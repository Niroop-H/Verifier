#!/usr/bin/env bash
set -euo pipefail
ROOT="$(pwd)"
cd "$ROOT"
mkdir -p artifacts
LOG="$ROOT/artifacts/regression.log"
: > "$LOG"
log() { printf '[%s] %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a "$LOG"; }
require_tool() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "BLOCKED: mandatory tool not found on PATH: $1"
    exit 2
  fi
}
for tool in iverilog vvp verilator yosys ghdl z3 sby klayout sta; do require_tool "$tool"; done
run_ok() {
  local name="$1"; shift
  local out="artifacts/$name.log"
  log "RUN: $name"
  if "$@" >"$out" 2>&1; then
    log "PASS: $name"
  else
    local rc=$?
    log "FAIL: $name (exit=$rc; see $out)"
    tail -n 60 "$out" || true
    return 1
  fi
}
expect_diagnostic() {
  local name="$1"; local pattern="$2"; shift 2
  local out="artifacts/$name.log"
  log "RUN expected-negative: $name"
  if "$@" >"$out" 2>&1; then
    log "FAIL: $name unexpectedly succeeded"
    return 1
  fi
  if ! grep -Eiq "$pattern" "$out"; then
    log "FAIL: $name returned nonzero without expected diagnostic: $pattern"
    tail -n 60 "$out" || true
    return 1
  fi
  log "PASS: $name rejected bad input with expected diagnostic"
}
GOOD="fixtures/projects/good/comb.v"
TB="fixtures/projects/good/tb_comb.v"
BAD="fixtures/rtl/bad.v"
run_ok tool_iverilog_version iverilog -V
run_ok tool_vvp_version vvp -V
run_ok tool_verilator_version verilator --version
run_ok tool_yosys_version yosys -V
run_ok tool_ghdl_version ghdl --version
run_ok tool_z3_version z3 --version
run_ok tool_klayout_version klayout -v
run_ok tool_opensta_version sta -version
run_ok verilator_lint_good verilator --lint-only -Wno-fatal --top-module comb "$GOOD"
expect_diagnostic verilator_lint_bad "missing_signal|%Error" verilator --lint-only --top-module bad "$BAD"
run_ok iverilog_compile_good iverilog -g2012 -Wall -s comb -o artifacts/comb.vvp "$GOOD"
run_ok iverilog_simulation_compile iverilog -g2012 -s tb_comb -o artifacts/tb_comb.vvp "$GOOD" "$TB"
run_ok vvp_self_checking_testbench vvp artifacts/tb_comb.vvp
grep -q "MQV_SIM_PASS" artifacts/vvp_self_checking_testbench.log
expect_diagnostic iverilog_rejects_bad_rtl "missing_signal|Unable to bind|error" iverilog -g2012 -s bad -o artifacts/bad.vvp "$BAD"
run_ok yosys_synthesis_good yosys -p "read_verilog -sv $GOOD; hierarchy -check -top comb; proc; opt; check; stat"
expect_diagnostic yosys_rejects_bad_rtl "missing_signal|implicitly declared|ERROR" yosys -p "read_verilog -sv $BAD; hierarchy -check -top bad; proc; opt; check"
run_ok ghdl_analyze_good ghdl -a --std=08 --workdir=artifacts fixtures/vhdl/good.vhd
expect_diagnostic ghdl_rejects_bad_vhdl "error|expected|unexpected" ghdl -a --std=08 --workdir=artifacts fixtures/vhdl/bad.vhd
mkdir -p artifacts/formal
cp fixtures/formal/* artifacts/formal/
(cd artifacts/formal && sby -f good.sby > formal-good.log 2>&1)
grep -q "DONE (PASS" artifacts/formal/formal-good.log
log "PASS: formal_good_property_proved"
if (cd artifacts/formal && sby -f bad.sby > formal-bad.log 2>&1); then
  log "FAIL: formal_false_property_unexpectedly_passed"; exit 1
fi
grep -q "DONE (FAIL" artifacts/formal/formal-bad.log
log "PASS: formal_false_property_counterexample_found"
mkdir -p artifacts/sta
curl --fail --location --retry 3 \
  https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-flow-scripts/eda8e552974d47a12616294dddf4012d892548d3/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib \
  --output artifacts/sta/NangateOpenCellLibrary_typical.lib
cp fixtures/timing/sta_smoke.v artifacts/sta/sta_smoke.v
cp fixtures/timing/pass.sdc artifacts/sta/pass.sdc
cp fixtures/timing/tight.sdc artifacts/sta/tight.sdc
cat > artifacts/sta/run_pass.tcl <<'EOF'
read_liberty {artifacts/sta/NangateOpenCellLibrary_typical.lib}
read_verilog {artifacts/sta/sta_smoke.v}
link_design sta_smoke
read_sdc {artifacts/sta/pass.sdc}
check_setup
report_checks -path_delay max -fields {slew cap input net fanout} -digits 4
exit
EOF
run_ok opensta_real_timing_pass sta -no_splash -exit artifacts/sta/run_pass.tcl
grep -Eiq "slack[[:space:]]+\([[:space:]]*MET[[:space:]]*\)" artifacts/opensta_real_timing_pass.log
cat > artifacts/sta/run_fail.tcl <<'EOF'
read_liberty {artifacts/sta/NangateOpenCellLibrary_typical.lib}
read_verilog {artifacts/sta/sta_smoke.v}
link_design sta_smoke
read_sdc {artifacts/sta/tight.sdc}
check_setup
report_checks -path_delay max -fields {slew cap input net fanout} -digits 4
exit
EOF
run_ok opensta_real_timing_violation_report sta -no_splash -exit artifacts/sta/run_fail.tcl
grep -Eiq "slack[[:space:]]+\([[:space:]]*VIOLATED[[:space:]]*\)" artifacts/opensta_real_timing_violation_report.log
mkdir -p artifacts/drc
run_ok klayout_make_good_layout klayout -b -r fixtures/physical/make_layout.rb -rd output_file=artifacts/drc/good.gds -rd width=0.20
run_ok klayout_make_bad_layout klayout -b -r fixtures/physical/make_layout.rb -rd output_file=artifacts/drc/bad.gds -rd width=0.02
run_ok klayout_drc_good klayout -b -r fixtures/physical/smoke_drc.rb -rd input_file=artifacts/drc/good.gds -rd report_file=artifacts/drc/good.lyrdb
run_ok klayout_drc_bad klayout -b -r fixtures/physical/smoke_drc.rb -rd input_file=artifacts/drc/bad.gds -rd report_file=artifacts/drc/bad.lyrdb
python3 - <<'PY'
import xml.etree.ElementTree as ET
good = ET.parse("artifacts/drc/good.lyrdb").getroot()
bad = ET.parse("artifacts/drc/bad.lyrdb").getroot()
assert good.tag.lower().endswith("report-database"), good.tag
assert bad.tag.lower().endswith("report-database"), bad.tag
assert len(good.findall(".//item")) == 0, "clean geometry unexpectedly violated minimum width"
assert len(bad.findall(".//item")) > 0, "violating geometry produced no DRC item"
print("KLayout DRC parser: clean=PASS, narrow-shape=FAIL as expected")
PY
log "PASS: all required EDA smoke regressions completed"
