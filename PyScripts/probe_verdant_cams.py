"""CAMERA SIGHTLINE PROBE v2 — the instrument that finally sees.

v1 failed twice: it tested camera POINTS (photobombs stand between lens and
subject) and it capped occluder bounds at 3600uu (seven crown blobs are
bigger — the exact ones doing the burying). v2 marches samples along each
cam->target SIGHTLINE against every solid actor up to extent 8000, excluding
only the world-shell giants and the water/air/stair SUBJECTS we shoot at.
Headless-safe: bounds need no physics scene.
"""
import unreal

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MAP = "/Game/Maps/WorldStageTesting"
assert les.load_level(MAP), "LOAD_STAGE_FAILED"

SIGHTS = [
    ("skyfall_D", (-300.0, 15800.0, 1000.0), (-248.0, 11836.0, 1500.0)),
    ("skyfall_A", (-3400.0, 13600.0, 1400.0), (-248.0, 11836.0, 1200.0)),
    ("pool_W", (-2900.0, 12237.0, 1000.0), (-283.0, 12237.0, 250.0)),
    ("pool_A", (-3400.0, 13600.0, 1400.0), (-283.0, 12237.0, 250.0)),
    ("weenie_low", (-2451.0, 11057.0, 38500.0), (-653.0, 9548.0, 38650.0)),
    ("weenie_door", (-1800.0, 10400.0, 38400.0), (-653.0, 9548.0, 38500.0)),
    ("ramp_emerge", (-2600.0, 4497.0, 42800.0), (-746.0, 6440.0, 42436.0)),
    ("arena", (-3637.0, 6900.0, 43600.0), (0.0, 10300.0, 42934.0)),
    ("wade", (6350.0, 13750.0, 620.0), (7280.0, 14580.0, 150.0)),
    ("wade_b", (6050.0, 14350.0, 700.0), (7280.0, 14580.0, 150.0)),
    ("river", (10500.0, 15400.0, 250.0), (9800.0, 16200.0, -150.0)),
    ("river_b", (10900.0, 16900.0, 350.0), (10142.0, 16360.0, -100.0)),
]

SKIP_PREFIX = ("VR_RootFloor", "VR_Heartwood", "VR_CanopyBelow", "VR_Mouth",
               "VR_Stair", "VR_Arch", "VR_Arena", "VR_Boss", "VR_Knot",
               "VR_BowlCrumb")
SKIP_ANY = ("River", "Fall", "Pool", "Churn", "Mist", "Foam", "Curtain",
            "Cloud", "Rapids", "Understory", "Pollen", "Bubble", "Drift",
            "Gloom", "Lantern", "Moth", "Breath")

boxes = []
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl.startswith(SKIP_PREFIX) or any(s in lbl for s in SKIP_ANY):
        continue
    o, e = a.get_actor_bounds(False)
    if max(e.x, e.y, e.z) < 8000.0:
        boxes.append((lbl, o, e))
print(f"REACH_MARKER: {len(boxes)} solid occluders indexed")

for name, cam, tgt in SIGHTS:
    dx, dy, dz = tgt[0] - cam[0], tgt[1] - cam[1], tgt[2] - cam[2]
    length = max(1.0, (dx * dx + dy * dy + dz * dz) ** 0.5)
    n = max(6, int(length / 250.0))
    hits = []
    for i in range(n + 1):
        t = 0.03 + 0.89 * i / n            # stop shy of the subject itself
        x, y, z = cam[0] + dx * t, cam[1] + dy * t, cam[2] + dz * t
        for lbl, o, e in boxes:
            if (abs(x - o.x) < e.x and abs(y - o.y) < e.y
                    and abs(z - o.z) < e.z and lbl not in hits):
                hits.append(lbl)
    verdict = "CLEAR" if not hits else "BLOCKED " + ",".join(hits[:4])
    print(f"REACH_MARKER: sight {name} {verdict}")
print("VERDANT_CAM_PROBE_DONE")
