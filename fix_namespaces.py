"""Move three tools into the AB namespace and give their files matching names.

    exec(open('U:/AB_Standardization/fix_namespaces.py').read()); run()

Tracker AB-001..012 territory. Three types were not in the AB namespace at all:

    AB:RockMaker::2.0          single colon - the namespace is literally "AB:RockMaker"
    AOD::extended_sweep::2.0   old namespace, and a lowercase name
    AOD::flower_designer::1.0  same

Renaming a type is breaking, so this was checked first: a byte scan across the whole
library found each string only in its own file, and the 65 hits in T-Bone are all under
hip/backup/. Jordan confirmed neither RockMaker nor flower_designer is used anywhere.

ExtendedSweep also gets its filename corrected - it shipped as AB.ExtendedSweep.1.0.hda
while defining version 2.0.

Method: copyToHDAFile writes a NEW definition under the new type name; the old file is
then uninstalled and deleted. Writing via a temp path avoids copying a file onto the one
currently backing the definition being read.
"""
import os
import hou

JOBS = [
    # old type,                   new type,                    old file,                              new file,                              label
    ("AB:RockMaker::2.0",         "AB::RockMaker::2.0",
     "U:/Git/AssetBashTools/Sops/Natural/AB.RockMaker.2.0.hda",
     "U:/Git/AssetBashTools/Sops/Natural/AB.RockMaker.2.0.hda",       "AB Rock Maker"),
    ("AOD::extended_sweep::2.0",  "AB::ExtendedSweep::2.0",
     "U:/Git/AssetBashTools/Sops/Modeling/AB.ExtendedSweep.1.0.hda",
     "U:/Git/AssetBashTools/Sops/Modeling/AB.ExtendedSweep.2.0.hda",  "AB Extended Sweep"),
    ("AOD::flower_designer::1.0", "AB::FlowerDesigner::1.0",
     "U:/Git/AssetBashTools/Sops/Natural/AB.FlowerDesigner.1.0.hda",
     "U:/Git/AssetBashTools/Sops/Natural/AB.FlowerDesigner.1.0.hda",  "AB Flower Designer"),
]


def run():
    done, skipped = [], []
    for old_type, new_type, old_file, new_file, label in JOBS:
        nt = hou.sopNodeTypeCategory().nodeTypes().get(old_type)
        if not nt:
            skipped.append("%s not installed" % old_type)
            continue
        d = nt.definition()
        tmp = new_file + ".tmp"
        if os.path.exists(tmp):
            os.remove(tmp)
        d.copyToHDAFile(tmp, new_name=new_type, new_menu_name=label)

        # drop the old type, then put the new file where it belongs
        try:
            hou.hda.uninstallFile(old_file)
        except Exception:
            pass
        if os.path.exists(old_file):
            os.remove(old_file)
        if os.path.exists(new_file):
            os.remove(new_file)
        os.rename(tmp, new_file)
        hou.hda.installFile(new_file)
        done.append("%s -> %s   (%s)" % (old_type, new_type, os.path.basename(new_file)))
    return done, skipped
