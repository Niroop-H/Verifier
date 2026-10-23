"""Declarative semiconductor verification coverage catalogue.

This catalogue defines verification units and their evidence prerequisites. It does
not claim that every unit is implemented or executed by the current engine.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VerificationUnit:
    unit_id: str
    domain: str
    title: str
    purpose: str
    required_inputs: tuple[str, ...]
    evidence: tuple[str, ...]
    integration: str
    signoff_critical: bool = True


# integration is deliberately explicit: IMPLEMENTED means a supported flow exists;
# CATALOG_ONLY means planned/documented, not runnable as a complete MQV flow yet.
_UNITS = (
    VerificationUnit("RTL_LINT", "front_end", "RTL lint and static checks", "Detect coding defects, inferred latches, width/sign issues and suspicious constructs.", ("RTL sources", "top module", "lint configuration"), ("lint log", "tool/version", "source hashes"), "IMPLEMENTED"),
    VerificationUnit("ELABORATION", "front_end", "HDL elaboration and hierarchy", "Resolve parameters, generate blocks, packages, interfaces and hierarchy.", ("RTL sources", "top module", "defines/include paths"), ("elaboration log", "resolved hierarchy"), "IMPLEMENTED"),
    VerificationUnit("RTL_SIMULATION", "functional", "RTL simulation and regression", "Execute directed and constrained-random tests against a testbench.", ("RTL sources", "testbench", "simulator configuration"), ("test results", "waveforms when enabled", "coverage summary"), "IMPLEMENTED"),
    VerificationUnit("FUNCTIONAL_COVERAGE", "functional", "Functional coverage closure", "Measure planned feature, scenario and cross coverage against a reviewable coverage model.", ("coverage model", "instrumented testbench", "coverage goals"), ("coverage database", "uncovered-bin report", "waiver review"), "CATALOG_ONLY"),
    VerificationUnit("ASSERTION_CHECKING", "functional", "Assertion-based verification", "Check temporal protocol, safety and liveness properties in simulation or formal engines.", ("assertions/properties", "clock/reset definitions", "RTL or netlist"), ("assertion results", "failure traces"), "CATALOG_ONLY"),
    VerificationUnit("FORMAL_PROPERTIES", "formal", "Formal property verification", "Prove supplied properties within explicit assumptions and proof bounds.", ("formal task", "properties", "assumptions", "engine configuration"), ("proof status", "counterexample traces", "assumption review"), "IMPLEMENTED"),
    VerificationUnit("RTL_NETLIST_EQUIV", "formal", "RTL-to-netlist equivalence", "Compare behavior across synthesis transformations and implementation checkpoints.", ("reference RTL", "candidate netlist", "mapping/black-box setup"), ("equivalence report", "unmatched-point report"), "CATALOG_ONLY"),
    VerificationUnit("CDC", "clock_reset", "Clock-domain crossing analysis", "Find unsafe crossings, synchronizer gaps and reconvergence hazards.", ("RTL/netlist", "clock-domain constraints", "CDC waivers"), ("CDC report", "waiver rationale"), "CATALOG_ONLY"),
    VerificationUnit("RDC_RESET", "clock_reset", "Reset-domain crossing analysis", "Check asynchronous reset crossings, release synchrony and reset-domain interactions.", ("RTL/netlist", "reset intent", "clock/reset constraints"), ("RDC report", "reset-release checks"), "CATALOG_ONLY"),
    VerificationUnit("DFT_SCAN", "testability", "DFT, scan and ATPG readiness", "Evaluate scan architecture, test coverage, test modes and generated test patterns.", ("DFT intent", "technology libraries", "scan rules", "ATPG configuration"), ("DFT rule report", "fault coverage", "pattern summary"), "CATALOG_ONLY"),
    VerificationUnit("SYNTHESIS", "implementation", "Logic synthesis and structural checks", "Map RTL to a technology-independent or technology-mapped netlist and report structural metrics.", ("RTL sources", "constraints", "libraries for mapped synthesis"), ("synthesis log", "netlist", "area/resource summary"), "IMPLEMENTED"),
    VerificationUnit("POWER_ESTIMATION", "implementation", "Dynamic and leakage power estimation", "Estimate power under declared activity, corners and operating conditions.", ("netlist", "Liberty libraries", "activity data", "power intent", "operating corners"), ("power report", "activity coverage", "assumptions"), "CATALOG_ONLY"),
    VerificationUnit("STA_SETUP_HOLD", "timing", "Static timing analysis", "Check setup/hold, recovery/removal, clock relationships and timing exceptions.", ("gate-level netlist", "Liberty libraries", "SDC", "parasitics for post-route STA"), ("setup/hold reports", "unconstrained-path report", "exception review"), "IMPLEMENTED"),
    VerificationUnit("CLOCK_QUALITY", "timing", "Clock-tree and clock-quality analysis", "Assess skew, insertion delay, clock transition and clock-gating checks.", ("clock-tree netlist", "SDC", "Liberty", "parasitics"), ("clock reports", "clock-gating checks"), "CATALOG_ONLY"),
    VerificationUnit("SI_CROSSTALK", "timing", "Signal integrity and crosstalk", "Analyze coupling, noise and crosstalk-induced timing impacts.", ("routed design", "extracted parasitics", "coupling-aware libraries", "signoff settings"), ("SI/noise report", "delta-delay report"), "CATALOG_ONLY"),
    VerificationUnit("FLOORPLAN_PLACE", "physical", "Floorplan and placement checks", "Check utilization, congestion, macro placement, blockages and placement legality.", ("netlist", "floorplan", "technology LEF", "cell LEF", "physical constraints"), ("placement report", "congestion maps", "legality report"), "CATALOG_ONLY"),
    VerificationUnit("CTS", "physical", "Clock-tree synthesis validation", "Validate clock-tree construction and implementation constraints.", ("placed design", "clock constraints", "clock cells", "technology data"), ("CTS report", "clock tree summary"), "CATALOG_ONLY"),
    VerificationUnit("ROUTING", "physical", "Routing and route-quality checks", "Check connectivity, routing completion, congestion and routing constraints.", ("placed/CTS design", "routing layers/rules", "technology LEF", "routing constraints"), ("route report", "unrouted-net report"), "CATALOG_ONLY"),
    VerificationUnit("PARASITIC_EXTRACTION", "physical", "RC parasitic extraction", "Extract interconnect resistance/capacitance for sign-off timing and power.", ("routed layout", "process extraction rules", "layer maps"), ("SPEF or equivalent", "extraction log"), "CATALOG_ONLY"),
    VerificationUnit("PHYSICAL_DRC", "signoff", "Physical design-rule checking", "Check layout against the exact process-specific rule deck.", ("GDSII/OASIS", "exact PDK release", "authorized DRC deck", "layer map"), ("DRC report", "waiver list", "deck/version provenance"), "IMPLEMENTED"),
    VerificationUnit("PHYSICAL_LVS", "signoff", "Layout-versus-schematic", "Compare extracted layout connectivity/devices with the approved reference netlist.", ("GDSII/OASIS", "reference netlist", "device recognition setup", "authorized LVS deck"), ("LVS report", "unmatched devices/nets"), "CATALOG_ONLY"),
    VerificationUnit("ERC_ANTENNA", "signoff", "Electrical and antenna checks", "Check process-specific electrical constraints and antenna violations.", ("layout", "netlist where required", "PDK-specific ERC/antenna rules"), ("ERC report", "antenna report"), "CATALOG_ONLY"),
    VerificationUnit("RELIABILITY_EM", "reliability", "Electromigration and IR-drop", "Assess power-grid voltage drop and current-density/reliability limits.", ("routed layout", "power intent", "activity/current model", "process reliability rules"), ("static/dynamic IR report", "EM report", "corner assumptions"), "CATALOG_ONLY"),
    VerificationUnit("THERMAL_RELIABILITY", "reliability", "Thermal and operating-envelope assessment", "Evaluate temperature-dependent margins using validated thermal/power models.", ("power map", "package/thermal model", "operating profile", "process limits"), ("thermal report", "assumptions and margins"), "CATALOG_ONLY"),
    VerificationUnit("SECURITY_REVIEW", "assurance", "Hardware security and design review", "Review threat model, debug/test access, lifecycle states, secure boot/keys and security properties.", ("security requirements", "threat model", "RTL/netlist", "security properties"), ("review findings", "property evidence", "waiver approvals"), "CATALOG_ONLY"),
    VerificationUnit("SILICON_QUAL", "silicon", "Post-silicon validation and qualification", "Track lab characterization, ATE, environmental and reliability qualification evidence.", ("fabricated samples", "test plan", "ATE/lab setup", "qualification limits"), ("ATE results", "characterization data", "qualification reports"), "EXTERNAL_EVIDENCE"),
)


def list_verification_units() -> tuple[VerificationUnit, ...]:
    """Return the stable catalogue of verification units."""
    return _UNITS


def get_verification_unit(unit_id: str) -> VerificationUnit | None:
    """Look up a unit by its stable identifier."""
    return next((unit for unit in _UNITS if unit.unit_id == unit_id), None)


def catalogue_summary() -> dict[str, int]:
    """Count units by integration maturity without implying execution."""
    summary: dict[str, int] = {}
    for unit in _UNITS:
        summary[unit.integration] = summary.get(unit.integration, 0) + 1
    summary["TOTAL"] = len(_UNITS)
    return summary
