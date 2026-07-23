"""Move StageSpawn to a named Verdant Reach camp anchor (Adam's teleport walk).

Env:  VR_VANTAGE = Roots | Mid | High | Crownbase | Crown   (default Roots)
Run:  $env:VR_VANTAGE='Mid'; powershell -File run_pyscript.ps1 -Script ..\PyScripts\set_vr_vantage.py

Every pad is locally walkable; this script is how Adam visits each altitude
before the climb verbs exist. Reads the same field JSON as the builder —
no coordinates are ever hand-typed twice (the drift law).
"""
import json
import math
import os

import unreal

MAP = "/Game/Maps/WorldStageTesting"
FIELD_JSON = r"C:\Users\Atomn\mario2\_prep\verdant_heartwood.json"

with open(FIELD_JSON) as f:
    F = json.load(f)
H, CX, CY = F["H"], F["cx"], F["cy"]
R_ROOT, R_CROWN, TAPER = F["r_root"], F["r_crown"], F["taper"]


def taper_r(z):
    return R_CROWN + (R_ROOT - R_CROWN) * (1.0 - z / H) ** TAPER


def wrap_dt(dt):
    while dt > math.pi:
        dt -= 2.0 * math.pi
    while dt < -math.pi:
        dt += 2.0 * math.pi
    return dt


def field_r(z, theta):
    r = taper_r(z)
    for b in F["buttresses"]:
        if z < b["z_fade"]:
            dt = wrap_dt(theta - b["theta"]) / b["width"]
            if abs(dt) < 1.0:
                zf = z / b["z_fade"]
                r += b["amp"] * (1.0 - dt * dt) ** 2 * (1.0 - zf * zf) ** 2
    return r


def anchor_pos(name):
    spec = F["camp_anchors"][name]
    if spec["kind"] == "floor":
        return unreal.Vector(spec["x"], spec["y"], 200.0), 90.0
    if spec["kind"] == "cap":
        return unreal.Vector(CX, CY, H - 245.0 + 150.0), 0.0
    sock = next(s for s in F["branch_sockets"] if s["name"] == spec["socket"])
    th = math.radians(sock["theta_deg"])
    r = field_r(sock["z"], th) + 700.0
    x, y = CX + r * math.cos(th), CY + r * math.sin(th)
    return unreal.Vector(x, y, sock["z"] + 160.0), math.degrees(math.atan2(CY - y, CX - x))


name = os.environ.get("VR_VANTAGE", "Roots")
assert name in F["camp_anchors"], f"UNKNOWN_VANTAGE: {name}"
pos, yaw = anchor_pos(name)

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert les.load_level(MAP), "LOAD_STAGE_FAILED"
moved = False
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "StageSpawn":
        a.set_actor_location(pos, False, True)
        a.set_actor_rotation(unreal.Rotator(0.0, 0.0, yaw), False)
        moved = True
        break
assert moved, "STAGESPAWN_MISSING"
assert les.save_current_level(), "SAVE_VANTAGE_FAILED"
print(f"REACH_MARKER: vantage {name} -> ({pos.x:.0f}, {pos.y:.0f}, {pos.z:.0f}) yaw {yaw:.0f}")
print("VANTAGE_DONE")
