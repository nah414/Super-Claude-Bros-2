"""Verdant Reach save-law verifier — disk is the only truth.

Runs -NoRender (pure asset checks): confirms the umap and every Verdant asset
exist ON DISK (the promotion lesson: memory-only saves die with the session),
then loads the level and counts VR_ actors. Read-only; changes nothing.
"""
import os
import time

import unreal

PROJ = r"C:\Users\Atomn\mario2\SuperClaudeBros2"
MAP = "/Game/Maps/WorldStageTesting"

checks_ok = True

umap = os.path.join(PROJ, "Content", "Maps", "WorldStageTesting.umap")
if os.path.isfile(umap):
    age_min = (time.time() - os.path.getmtime(umap)) / 60.0
    print(f"REACH_MARKER: umap ON DISK ({os.path.getsize(umap)//1024} KB, "
          f"saved {age_min:.0f} min ago)")
else:
    print("REACH_FAIL: WorldStageTesting.umap MISSING ON DISK")
    checks_ok = False

for rel, want in (("Content\\Art\\Verdant", 30), ("Content\\Audio\\Verdant", 4)):
    d = os.path.join(PROJ, rel)
    n = len([f for f in os.listdir(d) if f.endswith(".uasset")]) if os.path.isdir(d) else 0
    status = "REACH_MARKER" if n >= want else "REACH_FAIL"
    print(f"{status}: {rel} holds {n} .uasset files (want >= {want})")
    checks_ok = checks_ok and n >= want

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert les.load_level(MAP), "LOAD_STAGE_FAILED"
labels = [a.get_actor_label() for a in eas.get_all_level_actors()]
vr = [l for l in labels if l.startswith("VR_")]
by_kind = {}
for l in vr:
    kind = l.split("_")[1][:12]
    by_kind[kind] = by_kind.get(kind, 0) + 1
print(f"REACH_MARKER: {len(vr)} VR_ actors on the stage: "
      + ", ".join(f"{k}={v}" for k, v in sorted(by_kind.items())))
for bone in ("StageSpawn", "StageSun", "StageAtmosphere", "StageSkyLight"):
    if bone not in labels:
        print(f"REACH_FAIL: stage bone missing: {bone}")
        checks_ok = False
if not any(l.startswith("VR_Boss_") for l in labels):
    print("REACH_FAIL: the Shellback Alpha is missing from the crown")
    checks_ok = False
# R7 families (the 2026-08-31 walk answered): underwater volumes (A),
# streamer ribbons + plunge rocks/mist (C), the stairwell + its lamps (E).
for fam, want in (("VR_Underwater_", 7), ("VR_Streamer", 8),
                  ("VR_PlungeRock_", 3), ("VR_PlungeMist_", 1),
                  ("VR_Stairwell", 1), ("VR_StairwellLamp_", 10)):
    n = len([l for l in labels if l.startswith(fam)])
    status = "REACH_MARKER" if n >= want else "REACH_FAIL"
    print(f"{status}: R7 family {fam}* = {n} (want >= {want})")
    checks_ok = checks_ok and n >= want
# the purple sheets stay retired (workstream E)
n_seep = len([l for l in labels if l.startswith("VR_ChimneySeep")
              or l.startswith("VR_ChimneySeed")])
if n_seep:
    print(f"REACH_FAIL: {n_seep} violet seep/seed actors survive — E says zero")
    checks_ok = False
else:
    print("REACH_MARKER: the purple sheets stay retired (0 seep/seed actors)")
checks_ok = checks_ok and len(vr) >= 500

assert checks_ok, "VERDANT_VERIFY_FAILED"
print("VERDANT_VERIFY_DONE — the Reach is real on disk")
