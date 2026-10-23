"""Open PDK catalogue and conservative local readiness inspection.

Finding a PDK directory is not proof of a usable physical-design flow.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class PdkProfile:
    key: str
    name: str
    kind: str
    source_url: str
    root_markers: tuple[str, ...] = ()
    drc_deck_paths: tuple[str, ...] = ()
    lvs_deck_paths: tuple[str, ...] = ()
    liberty_globs: tuple[str, ...] = ()
    evidence: str = "No platform-specific regression evidence is recorded yet."
    note: str = ""
    is_process_pdk: bool = True

PROFILES: dict[str, PdkProfile] = {
    "sky130": PdkProfile(
        key="sky130", name="SkyWater SKY130", kind="open PDK / experimental-preview ecosystem",
        source_url="https://github.com/google/skywater-pdk",
        root_markers=("libraries/sky130_fd_pr", "libraries/sky130_fd_sc_hd"),
        liberty_globs=("libraries/sky130_fd_sc_hd/**/*.lib",),
        note=("The Google source repository provides process/device and library collateral; "
              "a physical flow commonly requires a compatible Open PDKs/OpenROAD platform, "
              "correct submodules, layer maps and suitable DRC/LVS decks. No foundry sign-off claim."),
    ),
    "sky130hd": PdkProfile(
        key="sky130hd", name="SKY130 HD standard-cell library option", kind="library option within SKY130",
        source_url="https://github.com/google/skywater-pdk",
        root_markers=("libraries/sky130_fd_sc_hd",),
        liberty_globs=("libraries/sky130_fd_sc_hd/**/*.lib",),
        note="This is an HD standard-cell library option within SKY130, not a separate process node. Physical rules come from the matching technology platform.",
    ),
    "gf180mcu": PdkProfile(
        key="gf180mcu", name="GlobalFoundries GF180MCU", kind="open PDK / experimental-preview ecosystem",
        source_url="https://github.com/google/gf180mcu-pdk",
        root_markers=("libraries/gf180mcu_fd_pr/latest", "libraries/gf180mcu_fd_sc_mcu7t5v0/latest"),
        liberty_globs=("libraries/gf180mcu_fd_sc_mcu7t5v0/latest/**/*.lib",),
        note=("The official repository uses submodules. Initialize them and use a compatible "
              "platform/rule-deck setup. This profile does not assume a rule deck is bundled in a ZIP."),
    ),
    "ihp_sg13g2": PdkProfile(
        key="ihp_sg13g2", name="IHP SG13G2 130 nm BiCMOS", kind="open PDK / preview collateral",
        source_url="https://github.com/IHP-GmbH/IHP-Open-PDK",
        root_markers=("ihp-sg13g2/libs.tech/klayout/tech/drc/ihp-sg13g2.drc",),
        drc_deck_paths=("ihp-sg13g2/libs.tech/klayout/tech/drc/ihp-sg13g2.drc",),
        lvs_deck_paths=("ihp-sg13g2/libs.tech/klayout/tech/lvs/run_lvs.py",),
        liberty_globs=("ihp-sg13g2/**/*.lib",),
        evidence="CI includes the official IHP DRC golden regression for the activ rule table. This is partial DRC regression evidence; it does not validate all rules, LVS, timing corners, or sign-off.",
        note="Check out the PDK revision and required submodules; verify KLayout version and actual test/deck inputs. Open PDK status does not imply production foundry sign-off.",
    ),
    "asap7": PdkProfile(
        key="asap7", name="ASAP7 predictive 7 nm platform", kind="predictive research platform",
        source_url="https://github.com/The-OpenROAD-Project/asap7",
        root_markers=("README.md",),
        liberty_globs=("**/*.lib",),
        note="Predictive/academic collateral; not a foundry-qualified 7 nm production PDK. Some commercial sign-off decks are distributed separately.",
    ),
    "nangate45": PdkProfile(
        key="nangate45", name="Nangate45 / FreePDK45 educational platform", kind="open research/test platform",
        source_url="https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/tree/master/flow/platforms/nangate45",
        root_markers=("lib/NangateOpenCellLibrary_typical.lib",),
        liberty_globs=("lib/*.lib",),
        note="Used as a synthetic timing-test platform in CI. It is not evidence of compatibility with a commercial foundry process.",
    ),
    "openroad_generic": PdkProfile(
        key="openroad_generic", name="Generic OpenROAD flow backend", kind="flow backend (not a PDK)",
        source_url="https://github.com/The-OpenROAD-Project/OpenROAD",
        note="Backend tools only. A compatible technology platform, libraries, RC/parasitic data and DRC/LVS decks must be selected separately.",
        is_process_pdk=False,
    ),
}

def list_profiles() -> list[dict[str, object]]:
    """Return the static catalogue with explicit evidence and limitations."""
    return [{
        "key": p.key, "name": p.name, "kind": p.kind,
        "source_url": p.source_url, "is_process_pdk": p.is_process_pdk,
        "drc_deck_paths": list(p.drc_deck_paths),
        "lvs_deck_paths": list(p.lvs_deck_paths),
        "evidence": p.evidence, "note": p.note,
    } for p in PROFILES.values()]

def inspect_profile(key: str, root: str | Path) -> dict[str, object]:
    """Inspect a PDK root without claiming runtime or sign-off readiness."""
    if key not in PROFILES:
        raise ValueError(f"Unknown PDK profile: {key}")
    profile = PROFILES[key]
    pdk_root = Path(root).expanduser().resolve()
    if not pdk_root.is_dir():
        return {
            "key": key, "name": profile.name, "root": str(pdk_root),
            "root_found": False, "state": "BLOCKED",
            "markers_found": [], "markers_missing": list(profile.root_markers),
            "drc_decks_found": [], "lvs_decks_found": [], "liberty_files_found": [],
            "evidence": profile.evidence, "note": profile.note,
            "blockers": ["PDK/platform root directory does not exist."],
            "signoff_ready": False,
        }
    found_markers = [m for m in profile.root_markers if (pdk_root / m).exists()]
    missing_markers = [m for m in profile.root_markers if not (pdk_root / m).exists()]
    found_drc = [p for p in profile.drc_deck_paths if (pdk_root / p).is_file()]
    found_lvs = [p for p in profile.lvs_deck_paths if (pdk_root / p).is_file()]
    libraries: list[str] = []
    for pattern in profile.liberty_globs:
        libraries.extend(str(p.relative_to(pdk_root)) for p in pdk_root.glob(pattern) if p.is_file())
        if len(libraries) >= 50:
            libraries = libraries[:50]
            break
    blockers: list[str] = []
    if missing_markers:
        blockers.append("Missing required root marker(s): " + ", ".join(missing_markers))
    if profile.is_process_pdk and not profile.drc_deck_paths:
        blockers.append("No canonical DRC deck path is configured in this profile.")
    elif profile.is_process_pdk and not found_drc:
        blockers.append("Configured DRC deck file is missing.")
    if profile.is_process_pdk and not profile.lvs_deck_paths:
        blockers.append("No canonical LVS adapter/deck path is configured in this profile.")
    elif profile.is_process_pdk and not found_lvs:
        blockers.append("Configured LVS script/deck file is missing.")
    if profile.liberty_globs and not libraries:
        blockers.append("No Liberty (.lib) files were discovered under configured patterns.")
    if not profile.is_process_pdk:
        blockers.append("This entry is a flow backend, not a process PDK.")
    complete_collateral = not blockers and bool(found_markers)
    return {
        "key": key, "name": profile.name, "root": str(pdk_root),
        "root_found": True, "state": "COLLATERAL_PRESENT_NOT_VALIDATED" if complete_collateral else "BLOCKED",
        "markers_found": found_markers, "markers_missing": missing_markers,
        "drc_decks_found": found_drc, "lvs_decks_found": found_lvs,
        "liberty_files_found": libraries,
        "evidence": profile.evidence, "note": profile.note,
        "blockers": blockers,
        "signoff_ready": False,
        "interpretation": "File presence is only a prerequisite check. Run the named positive/negative regression and review its evidence before enabling the flow.",
    }
