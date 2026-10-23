"""Open PDK catalogue with honest per-root readiness checks.

PDK root presence is not equivalent to a validated DRC/LVS flow. The registry
only marks a deck as present when the concrete expected file is found.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class PdkProfile:
    key: str
    name: str
    source_url: str
    root_markers: tuple[str, ...]
    drc_deck_paths: tuple[str, ...]
    lvs_deck_paths: tuple[str, ...]
    liberty_globs: tuple[str, ...]
    status_note: str
    is_pdk: bool = True

PROFILES: dict[str, PdkProfile] = {
    "sky130": PdkProfile(
        "sky130", "SkyWater SKY130", "https://github.com/google/skywater-pdk",
        ("libraries/sky130_fd_sc_hd", "libraries/sky130_fd_pr"),
        (), (), ("**/*.lib",),
        "Experimental-preview collateral. The Google repository uses submodules; a runnable platform and DRC/LVS decks may require the Open PDKs/OpenROAD platform setup."
    ),
    "sky130hd": PdkProfile(
        "sky130hd", "SkyWater SKY130 HD standard-cell option", "https://github.com/google/skywater-pdk",
        ("libraries/sky130_fd_sc_hd",),
        (), (), ("**/*tt*.lib", "**/*typ*.lib",),
        "A library option within SKY130, not a separate process node. Requires a compatible platform and technology rule decks."
    ),
    "gf180mcu": PdkProfile(
        "gf180mcu", "GlobalFoundries GF180MCU", "https://github.com/google/gf180mcu-pdk",
        ("libraries/gf180mcu_fd_pr", "libraries/gf180mcu_fd_sc_mcu7t5v0"),
        (), (), ("**/*.lib",),
        "Experimental-preview collateral. The official repository has submodules; validate the exact OpenROAD/OpenPDK platform and external layout decks used."
    ),
    "ihp_sg13g2": PdkProfile(
        "ihp_sg13g2", "IHP SG13G2 130 nm BiCMOS", "https://github.com/IHP-GmbH/IHP-Open-PDK",
        ("ihp-sg13g2/libs.tech/klayout/tech/sg13g2.lyt",),
        ("ihp-sg13g2/libs.tech/klayout/tech/drc/ihp-sg13g2.drc",),
        ("ihp-sg13g2/libs.tech/klayout/tech/lvs/sg13g2.lvs",),
        ("ihp-sg13g2/**/*.lib",),
        "Preview-only collateral. Validate required submodules, library corners, KLayout version and deck prerequisites."
    ),
    "asap7": PdkProfile(
        "asap7", "ASAP7 predictive 7 nm", "https://github.com/The-OpenROAD-Project/asap7",
        ("README.md",),
        (), (), ("**/*.lib",),
        "Predictive research platform, not a foundry-qualified 7 nm production process. Calibre decks are separately distributed and are not in the public repository."
    ),
    "openroad_generic": PdkProfile(
        "openroad_generic", "Generic OpenROAD backend", "https://github.com/The-OpenROAD-Project/OpenROAD",
        (), (), (), (),
        "Flow backend only; not a PDK. A technology platform, libraries, RC tables and physical-verification decks must be selected separately.",
        is_pdk=False
    ),
}

def list_profiles() -> list[dict[str, object]]:
    return [{
        "key": p.key, "name": p.name, "source_url": p.source_url,
        "is_pdk": p.is_pdk, "status_note": p.status_note,
        "drc_deck_paths": list(p.drc_deck_paths),
        "lvs_deck_paths": list(p.lvs_deck_paths),
    } for p in PROFILES.values()]

def inspect_profile(key: str, root: str | Path) -> dict[str, object]:
    if key not in PROFILES:
        raise ValueError(f"Unknown PDK profile: {key}")
    profile = PROFILES[key]
    pdk_root = Path(root).expanduser().resolve()
    if not pdk_root.is_dir():
        return {
            "key": key, "name": profile.name, "root": str(pdk_root),
            "root_found": False, "profile_ready": False,
            "drc_decks_found": [], "lvs_decks_found": [], "liberty_files_found": [],
            "status_note": profile.status_note,
            "blockers": ["PDK root directory does not exist"],
        }
    missing_markers = [marker for marker in profile.root_markers if not (pdk_root / marker).exists()]
    found_drc = [str(pdk_root / rel) for rel in profile.drc_deck_paths if (pdk_root / rel).is_file()]
    found_lvs = [str(pdk_root / rel) for rel in profile.lvs_deck_paths if (pdk_root / rel).is_file()]
    liberty_files: list[str] = []
    for pattern in profile.liberty_globs:
        liberty_files.extend(str(p) for p in pdk_root.glob(pattern) if p.is_file())
        if len(liberty_files) >= 25:
            break
    blockers = []
    if missing_markers:
        blockers.append("Missing root markers: " + ", ".join(missing_markers))
    if profile.is_pdk and not profile.drc_deck_paths:
        blockers.append("No canonical DRC deck path is registered; configure an authorized compatible deck")
    elif profile.is_pdk and not found_drc:
        blockers.append("Configured DRC deck not found")
    if profile.is_pdk and not profile.lvs_deck_paths:
        blockers.append("No canonical LVS deck path is registered; configure an authorized compatible deck")
    elif profile.is_pdk and not found_lvs:
        blockers.append("Configured LVS deck not found")
    return {
        "key": key, "name": profile.name, "root": str(pdk_root), "root_found": True,
        "missing_root_markers": missing_markers, "drc_decks_found": found_drc,
        "lvs_decks_found": found_lvs, "liberty_files_found": liberty_files[:25],
        "profile_ready": bool(profile.is_pdk and not blockers),
        "status_note": profile.status_note, "blockers": blockers,
    }
