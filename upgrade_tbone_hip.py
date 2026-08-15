"""Headless: lift LM_UrbanDevelopment_v057 onto current AB versions, save v058.

    hython U:/AB_Standardization/upgrade_tbone_hip.py

Run this with the Houdini GUI CLOSED. Jordan has a single FX seat, and starting a
second Houdini alongside his session is what dropped him to Limited Commercial
before.

Why it exists: archiving the superseded HDA versions (27a28ba) broke this scene -
Houdini pins the exact versioned type when a .hip is saved, so v057 binds to
AB::ButtonPanels::1.0, AB::CityGridGenerator::1.1 and 12 more that had left the
scan path. Scenes must be upgraded BEFORE the old versions are archived, not
after. The archive was restored in 164070c; this closes the gap so it can be
redone safely.

Reads v057, never writes it. Output goes to a new v058, per the zero-padded
version convention.
"""
import os
import sys

import hou

sys.path.insert(0, "U:/Git/AssetBashTools/scripts")
import ab_upgrade  # noqa: E402

SRC = "C:/Projects/USC_T-Bone/03_ProjectFiles/houdini/hip/LM_UrbanDevelopment_v057.hip"
DST = "C:/Projects/USC_T-Bone/03_ProjectFiles/houdini/hip/LM_UrbanDevelopment_v058.hip"


def rule(t):
    print("\n" + "=" * 78)
    print(t)
    print("=" * 78)
    sys.stdout.flush()


rule("LOAD  %s" % os.path.basename(SRC))
print("%.1f MB" % (os.path.getsize(SRC) / 1048576.0))
sys.stdout.flush()
try:
    hou.hipFile.load(SRC, suppress_save_prompt=True, ignore_load_warnings=True)
    print("loaded")
except hou.LoadWarning as e:
    print("loaded WITH WARNINGS:\n%s" % str(e)[:3000])
sys.stdout.flush()

# Anything that failed to resolve is a node Houdini could not bind to a definition.
unresolved = []
for n in hou.node("/obj").allSubChildren():
    try:
        if n.type().definition() is None and n.type().name().startswith("AB"):
            unresolved.append((n.path(), n.type().name()))
    except Exception:
        pass
rule("UNRESOLVED AB NODES AFTER LOAD: %d" % len(unresolved))
for p, t in unresolved[:25]:
    print("   %-58s %s" % (p, t))

rule("PRELOAD THE HDA LIBRARY  (AFTER the load - order matters)")
# Loading a .hip RESETS the installed HDA table to what the scene references:
# HighwaySignGenerator::5.0 was installed and verified, then vanished the moment
# the hip loaded, leaving 4.9 looking like the newest. Preloading before the load
# accomplishes nothing.
print("installed %d file(s)" % ab_upgrade.preload_library())
for t in ("AB::HighwaySignGenerator::5.0", "AB::StreetSignGenerator::3.0",
          "AB::SignHighway::2.0"):
    print("   %-38s installed=%s"
          % (t, t in hou.sopNodeTypeCategory().nodeTypes()))
sys.stdout.flush()

rule("DRY RUN")
cands = ab_upgrade.report()

rule("APPLY")
upgraded, failed, dropped = ab_upgrade.upgrade()

rule("SAVE  %s" % os.path.basename(DST))
# the first run produced a defective v058 (contents carried across); replace it
if os.path.exists(DST):
    print("replacing the earlier defective %s" % os.path.basename(DST))
hou.hipFile.save(DST)
print("saved %s  (%.1f MB)" % (DST, os.path.getsize(DST) / 1048576.0))

rule("SUMMARY")
print("upgraded      : %d" % len(upgraded))
print("failed        : %d" % len(failed))
print("dropped parms : %d node(s)" % len(dropped))
print("unresolved    : %d" % len(unresolved))
