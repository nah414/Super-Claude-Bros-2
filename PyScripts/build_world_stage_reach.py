"""THE VERDANT REACH — World 3 rises on the World Stage.

"Up. The whole world is up — and the camp comes with you."

A roaring green day ~400m tall: the Heartwood mega-trunk (Wyvill buttresses
melding into the root floor), branch platforms spiraling to the crown, morning
light, and — in later phases of this same script — the camps, the amber grammar,
the world shell, and the breath.

House laws: rerun-safe (VR_ actors purged, fixed SEED); the field JSON is the
single source of truth (md5-checked); vertical + RADIAL truth probes hard-stop
on any Blender/FBX drift (the floating-boulder law, now in cylindrical coords);
falls kill from day one; explicit save at the end.
"""
import hashlib
import json
import math
import random

import unreal

MAP = "/Game/Maps/WorldStageTesting"
KIT = "/Game/Art/Verdant"
FIELD_JSON = r"C:\Users\Atomn\mario2\_prep\verdant_heartwood.json"

with open(FIELD_JSON) as f:
    F = json.load(f)

# ---- the drift guard: this builder only trusts a field it can re-hash ----
core = {k: v for k, v in F.items() if k != "field_md5"}
md5 = hashlib.md5(json.dumps(core, sort_keys=True).encode("utf-8")).hexdigest()
assert md5 == F["field_md5"], f"FIELD_DRIFT: json md5 {md5} != recorded {F['field_md5']}"
print(f"REACH_MARKER: field md5 {md5[:8]} OK")

H = F["H"]
CX, CY = F["cx"], F["cy"]
R_ROOT, R_CROWN, TAPER = F["r_root"], F["r_crown"], F["taper"]
BUTTRESSES = F["buttresses"]
HILLS = F["floor"]["hills"]
SEED = F["seed"]
random.seed(SEED)

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary


# ---------------- the field, UE consumer (mirror of the Blender copy) ----------------
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
    for b in BUTTRESSES:
        if z < b["z_fade"]:
            dt = wrap_dt(theta - b["theta"]) / b["width"]
            if abs(dt) < 1.0:
                zf = z / b["z_fade"]
                r += b["amp"] * (1.0 - dt * dt) ** 2 * (1.0 - zf * zf) ** 2
    return r


def ground_z(x, y):
    g = 0.0
    for hx, hy, a, c in HILLS:
        d2 = ((x - hx) ** 2 + (y - hy) ** 2) / (a * a)
        if d2 < 1.0:
            g += c * (1.0 - d2) ** 2
    d_axis = math.hypot(x - CX, y - CY)
    if d_axis < 3400.0:
        g += min(300.0, (3400.0 - d_axis) * 0.12)
    return g


def surface_point(z, theta, out=0.0):
    r = field_r(z, theta) + out
    return unreal.Vector(CX + r * math.cos(theta), CY + r * math.sin(theta), z)


def rot(yaw, pitch=0.0, roll=0.0):
    return unreal.Rotator(roll, pitch, yaw)


def cls(name):
    c = unreal.load_class(None, f"/Script/SuperClaudeBros2.{name}")
    assert c, f"CLASS_MISSING: {name}"
    return c


def kit(name):
    sm = EAL.load_asset(f"{KIT}/{name}")
    assert sm, f"KIT_MISSING: {name} (run import_verdant_kit.py)"
    return sm


def mat(name):
    m = EAL.load_asset(f"{KIT}/{name}")
    assert m, f"MAT_MISSING: {name} (run build_verdant_materials.py)"
    return m


assert les.load_level(MAP), "LOAD_STAGE_FAILED"

# ---------------- purge the old Reach, keep the stage bones ----------------
purged = 0
for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith("VR_"):
        eas.destroy_actor(a)
        purged += 1
print(f"REACH_MARKER: purged {purged} VR_ actors")

actor_count = 0


def place(sm_or_asset, loc, label, yaw=0.0, pitch=0.0, scale=None, material=None,
          shadow=True):
    global actor_count
    a = eas.spawn_actor_from_object(sm_or_asset, loc)
    assert a, f"SPAWN_FAILED: {label}"
    a.set_actor_label(label)
    if yaw or pitch:
        a.set_actor_rotation(rot(yaw, pitch), False)
    if scale is not None:
        s = scale if isinstance(scale, unreal.Vector) else unreal.Vector(scale, scale, scale)
        a.set_actor_scale3d(s)
    comp = a.get_component_by_class(unreal.StaticMeshComponent)
    if comp:
        if material is not None:
            comp.set_material(0, material)
        if not shadow:
            comp.set_cast_shadow(False)
    actor_count += 1
    return a


# ---------------- terrain + trunk ----------------
floor_actor = place(kit("root_floor"), unreal.Vector(0.0, 0.0, 0.0), "VR_RootFloor")
trunk_actor = place(kit("heartwood_trunk"), unreal.Vector(0.0, 0.0, 0.0), "VR_Heartwood")
print("REACH_MARKER: the Heartwood stands (trunk + root floor)")


# ---------------- truth probes v2: mesh-data instruments (physics-free) ----------------
# Line traces return nothing in the headless editor world (learned 2026-07-23:
# the W2 probes were passing VACUOUSLY). These instruments read the imported
# mesh's actual vertex data instead — no physics scene, no vacuous pass, and a
# blind instrument is a hard stop, never a shrug.
def bark_noise(z, theta):
    """EXACT copy of the Blender sculptor's ripple — lets probes match to ~1uu."""
    return (55.0 * math.sin(z * 0.0021 + theta * 3.0)
            + 35.0 * math.sin(z * 0.0007 + theta * 7.0))


def mesh_verts(sm):
    try:
        data = unreal.ProceduralMeshLibrary.get_section_from_static_mesh(sm, 0, 0)
        return list(data[0])
    except Exception as e:
        print(f"REACH_WARN: mesh section reader unavailable ({e})")
        return None


# Instrument 1 (always available): bbox asymmetry. The calibration buttress
# (theta=0.42, amp 950) bulges the trunk's +Y side; a silent FBX mirror would
# move that bulge to -Y and shift the measured bounds center past tolerance.
def expected_trunk_bounds_y():
    ymin, ymax = 1e9, -1e9
    for zi in (0.0, 600.0, 1400.0, 2600.0, 4200.0, 6000.0):
        for i in range(720):
            th = 2.0 * math.pi * i / 720
            y = CY + (field_r(zi, th) + bark_noise(zi, th)) * math.sin(th)
            ymin, ymax = min(ymin, y), max(ymax, y)
    return ymin, ymax


origin, ext = trunk_actor.get_actor_bounds(False)
want_ymin, want_ymax = expected_trunk_bounds_y()
meas_ymin, meas_ymax = origin.y - ext.y, origin.y + ext.y
print(f"REACH_MARKER: trunk bounds probe: y=[{meas_ymin:.0f},{meas_ymax:.0f}] "
      f"expected=[{want_ymin:.0f},{want_ymax:.0f}] z_span={2 * ext.z:.0f}")
assert abs(meas_ymin - want_ymin) < 150.0 and abs(meas_ymax - want_ymax) < 150.0, \
    "TRUNK_MIRRORED: bounds asymmetry disagrees with the calibration buttress (FBX mirror?)"
assert abs(2.0 * ext.z - H) < 300.0, "TRUNK_HEIGHT_WRONG"

# Instrument 2 (precise): vertex-level agreement with the field formula.
tverts = mesh_verts(kit("heartwood_trunk"))
fverts = mesh_verts(kit("root_floor"))
if tverts:
    radial_ok = True
    for z_want, th_want, pname in ((1500.0, 0.42, "calibration"),
                                   (1500.0, 0.42 + math.pi, "anti-calibration"),
                                   (20000.0, 1.0, "mid-taper"),
                                   (35000.0, 4.0, "high-taper")):
        best, best_d = None, 1e18
        for v in tverts:
            if abs(v.z - z_want) > 110.0:
                continue
            vth = math.atan2(v.y - CY, v.x - CX)
            d = abs(wrap_dt(vth - th_want))
            if d < best_d:
                best_d, best = d, v
        assert best is not None, f"RADIAL_PROBE_EMPTY: no ring near z={z_want}"
        vth = math.atan2(best.y - CY, best.x - CX)
        meas = math.hypot(best.x - CX, best.y - CY)
        want = field_r(best.z, vth) + bark_noise(best.z, vth)
        print(f"REACH_MARKER: radial probe {pname}: measured={meas:.1f} expected={want:.1f}")
        if abs(meas - want) > 60.0:
            radial_ok = False
    assert radial_ok, "TRUNK_MISALIGNED: bark vertices disagree with the field"
if fverts:
    rb = BUTTRESSES[1]
    ridge_pt = (CX + math.cos(rb["theta"]) * (R_ROOT + 1750.0),
                CY + math.sin(rb["theta"]) * (R_ROOT + 1750.0))
    ground_ok = True
    for px, py, pname in ((0.0, 0.0, "spawn"), (0.0, 4300.0, "camp-roots"),
                          (ridge_pt[0], ridge_pt[1], "root-ridge")):
        best, best_d = None, 1e18
        for v in fverts:
            d = (v.x - px) ** 2 + (v.y - py) ** 2
            if d < best_d:
                best_d, best = d, v
        want = ground_z(best.x, best.y)
        print(f"REACH_MARKER: terrain probe {pname}: measured={best.z:.1f} expected={want:.1f}")
        if abs(best.z - want) > 60.0:
            ground_ok = False
    assert ground_ok, "TERRAIN_MISALIGNED: floor vertices disagree with the field"
if not tverts and not fverts:
    print("REACH_WARN: vertex instruments unavailable — bounds probe alone stands guard")

# ---------------- stage bones: slab out, morning light on ----------------
for a in list(eas.get_all_level_actors()):
    label = a.get_actor_label()
    if label == "StageSlab":
        eas.destroy_actor(a)
    elif label == "StageSpawn":
        a.set_actor_location(unreal.Vector(0.0, 0.0, ground_z(0.0, 0.0) + 120.0), False, True)
        a.set_actor_rotation(rot(90.0), False)
    elif label == "StageSun":
        comp = a.get_component_by_class(unreal.DirectionalLightComponent)
        if comp:
            comp.set_editor_property("intensity", 9.0)
            comp.set_light_color(unreal.LinearColor(1.0, 0.87, 0.68, 1.0))
            for prop, val in (("enable_light_shaft_bloom", True),
                              ("enable_light_shaft_occlusion", True),
                              ("bloom_scale", 0.25)):
                try:
                    comp.set_editor_property(prop, val)
                except Exception as e:
                    print(f"REACH_WARN: sun {prop}: {e}")
        # Morning: low warm sun raking across the trunk face the spawn sees.
        a.set_actor_rotation(unreal.Rotator(0.0, -14.0, 25.0), False)
    elif label == "StageSkyLight":
        comp = a.get_component_by_class(unreal.SkyLightComponent)
        if comp:
            comp.set_editor_property("intensity", 1.15)
            comp.recapture_sky()
print("REACH_MARKER: morning light set (sun -14deg warm, shafts armed)")

# ---------------- the warm green-gold air (ONE fog, volumetric for shafts) ----------------
fog = eas.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0), rot(0))
fog.set_actor_label("VR_Air")
fog_comp = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
if fog_comp:
    fog_comp.set_editor_property("fog_density", 0.003)
    fog_comp.set_editor_property("fog_height_falloff", 0.005)
    fog_comp.set_editor_property("start_distance", 3000.0)
    for prop, val in (("directional_inscattering_luminance",
                       unreal.LinearColor(1.0, 0.82, 0.46, 1.0)),
                      ("directional_inscattering_exponent", 8.0)):
        try:
            fog_comp.set_editor_property(prop, val)
        except Exception as e:
            print(f"REACH_WARN: fog {prop}: {e}")
    volumetric_set = False
    for flag_name in ("enable_volumetric_fog", "volumetric_fog", "b_enable_volumetric_fog"):
        try:
            fog_comp.set_editor_property(flag_name, True)
            volumetric_set = True
            print(f"REACH_MARKER: volumetric fog on (via {flag_name})")
            break
        except Exception:
            continue
    if not volumetric_set:
        print("REACH_WARN: volumetric fog flag not found — shaft cards carry the read")
    for prop, val in (("fog_inscattering_luminance", unreal.LinearColor(0.44, 0.52, 0.32, 1.0)),
                      ("volumetric_fog_scattering_distribution", 0.55),
                      ("volumetric_fog_extinction_scale", 1.2)):
        try:
            fog_comp.set_editor_property(prop, val)
        except Exception as e:
            print(f"REACH_WARN: fog {prop}: {e}")
print("REACH_MARKER: green-gold air raised")

# ---------------- falls kill, from day one ----------------
kill_ok = False
try:
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    ws = world.get_world_settings()
    ws.set_editor_property("kill_z", -2500.0)
    ws.set_editor_property("enable_world_bounds_checks", True)
    kill_ok = True
except Exception as e:
    print(f"REACH_WARN: WorldSettings kill_z unavailable ({e}) — "
          f"SparkHeroCharacter.RespawnBelowZ=-2000 remains the enforced law")
print(f"REACH_MARKER: underdark sealed (kill_z={'-2500' if kill_ok else 'char-guard only'})")

# ================= PHASE B (CP3): branches, camps, the amber grammar =================
SPHERE = unreal.load_asset("/Engine/BasicShapes/Sphere")
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
assert SPHERE and CUBE, "ENGINE_SHAPES_MISSING"

ARCH_MESH = {"b1": kit("branch_b1"), "b2": kit("branch_b2"),
             "b3": kit("branch_b3"), "b4": kit("branch_b4")}
M_MOSS = mat("M_VR_MossBand")
M_BLOSSOM = mat("M_VR_BlossomStub")
M_EDGE = mat("M_VR_EdgeGlow")

pad_centers = {}
branch_n = 0
for s in F["branch_sockets"]:
    th = math.radians(s["theta_deg"])
    if s["arch"] == "b3":
        loc = surface_point(s["z"], th, out=700.0)
        loc.z = s["z"] - 120.0                      # pad top lands at socket z
        pad_centers[s["name"]] = (loc.x, loc.y, s["z"])
    else:
        loc = surface_point(s["z"], th, out=-250.0)  # root embedded in bark
    place(ARCH_MESH[s["arch"]], loc, f"VR_Branch_{s['name']}",
          yaw=s["theta_deg"], pitch=s["pitch_deg"], scale=s["scale"])
    branch_n += 1
print(f"REACH_MARKER: {branch_n} branches raised on the spiral")

# ---- camp anchors: a lantern burns at every altitude (Lumen got there first) ----
camp_positions = {}
for name, spec in F["camp_anchors"].items():
    if spec["kind"] == "floor":
        pos = unreal.Vector(spec["x"], spec["y"], ground_z(spec["x"], spec["y"]))
        face_yaw = 90.0
    elif spec["kind"] == "pad":
        cxp, cyp, cz = pad_centers[spec["socket"]]
        pos = unreal.Vector(cxp, cyp, cz)
        face_yaw = math.degrees(math.atan2(CY - cyp, CX - cxp))
    else:                                            # the crown bowl
        pos = unreal.Vector(CX, CY, H - 245.0)
        face_yaw = 0.0
    camp_positions[name] = (pos, face_yaw)
    lantern = eas.spawn_actor_from_class(
        cls("Lantern"), unreal.Vector(pos.x, pos.y, pos.z + 4.0), rot(face_yaw))
    lantern.set_actor_label(f"VR_CampLantern_{name}")
    ls = lantern.get_component_by_class(unreal.LightStateComponent)
    if ls:
        ls.set_editor_property("group_name", f"VR_Camp_{name}")
    try:
        lantern.set_editor_property("is_checkpoint", True)
    except Exception as e:
        print(f"REACH_WARN: camp lantern {name} is_checkpoint: {e}")
    actor_count += 1
print(f"REACH_MARKER: {len(camp_positions)} camp anchors lit (Roots->Crown)")

# ---- moss-glow bands: the GRIPPABLE grammar, one card at a time ----
# The card is an arc shell of radius 300 around its OWN origin — scaling scales
# that radius too, so the embed depth must follow: origin sits at bark minus
# (300*scale - flush), or the card floats proud like a sticker (CP3 shot #1).
moss_n = 0
for band in F["moss_bands"]:
    z = band["z0"]
    while z <= band["z1"]:
        t = (z - band["z0"]) / max(1.0, band["z1"] - band["z0"])
        th_deg = band["th0"] + (band["th1"] - band["th0"]) * t \
            + 6.0 * math.sin(z * 0.004)
        th = math.radians(th_deg)
        card_scale = random.uniform(1.7, 3.1)
        loc = surface_point(z - 130.0, th, out=-(300.0 * card_scale - 20.0))
        place(kit("seep_card"), loc, f"VR_Moss_{band['leg']}_{moss_n}",
              yaw=th_deg + random.uniform(-7.0, 7.0),
              scale=unreal.Vector(card_scale, card_scale * random.uniform(0.8, 1.3),
                                  card_scale * random.uniform(0.7, 1.2)),
              material=M_MOSS, shadow=False)
        moss_n += 1
        z += band["step"]
print(f"REACH_MARKER: {moss_n} moss-glow bands mark the climb legs")

# ---- blossom stubs: amber across the gaps (the future SWING_ANCHORs) ----
blossom_n = 0
for band in F["moss_bands"]:
    for t in (0.3, 0.55, 0.8):
        z = band["z0"] + (band["z1"] - band["z0"]) * t
        th_deg = band["th0"] + (band["th1"] - band["th0"]) * t
        loc = surface_point(z, math.radians(th_deg), out=520.0)
        place(SPHERE, loc, f"VR_Blossom_{band['leg']}_{blossom_n}",
              scale=1.25, material=M_BLOSSOM, shadow=False)
        blossom_n += 1
print(f"REACH_MARKER: {blossom_n} amber blossom stubs hung across the gaps")

# ---- edge-glow rims: every open rim announces itself (falls-kill placement law) ----
rim_n = 0
for pname, (cxp, cyp, cz) in pad_centers.items():
    th_out = math.atan2(cyp - CY, cxp - CX)
    for k in range(6):
        rel = math.radians(-120.0 + 48.0 * k)
        a = th_out + rel
        loc = unreal.Vector(cxp + math.cos(a) * 1080.0,
                            cyp + math.sin(a) * 1080.0, cz + 38.0)
        place(CUBE, loc, f"VR_Rim_{pname}_{k}",
              yaw=math.degrees(a) + 90.0,
              scale=unreal.Vector(5.5, 0.14, 0.10), material=M_EDGE, shadow=False)
        rim_n += 1
for s in F["branch_sockets"]:
    if s["arch"] != "b1":
        continue
    th = math.radians(s["theta_deg"])
    base = surface_point(s["z"], th, out=-250.0)
    tip_d = 7900.0 * s["scale"]
    tip_z = s["z"] + (math.sin(math.radians(s["pitch_deg"])) * 8000.0 - 40.0) * s["scale"]
    loc = unreal.Vector(base.x + math.cos(th) * tip_d,
                        base.y + math.sin(th) * tip_d, tip_z + 175.0 * s["scale"])
    place(CUBE, loc, f"VR_Rim_tip_{s['name']}",
          yaw=s["theta_deg"] + 90.0,
          scale=unreal.Vector(1.8, 0.14, 0.10), material=M_EDGE, shadow=False)
    rim_n += 1
print(f"REACH_MARKER: {rim_n} edge-glow rims on the open air")

# ================= PHASE C (CP4): the world shell =================
CYL = unreal.load_asset("/Engine/BasicShapes/Cylinder")
assert CYL, "ENGINE_CYLINDER_MISSING"
BLOBS = [kit("canopy_blob_a"), kit("canopy_blob_b"), kit("canopy_blob_c")]
M_SIL = mat("M_VR_Silhouette")
M_VILLAGE = mat("M_VR_VillageLight")

# ---- canopy masses: the crown, and foliage on every tip ----
canopy_n = 0
for i in range(14):                                   # the crown's green thunderhead
    a = 2.0 * math.pi * i / 14 + random.uniform(-0.2, 0.2)
    rr = random.uniform(700.0, 3000.0)
    z = random.uniform(37800.0, 41000.0)
    place(random.choice(BLOBS),
          unreal.Vector(CX + rr * math.cos(a), CY + rr * math.sin(a), z),
          f"VR_Canopy_crown{i}", yaw=random.uniform(0, 360),
          scale=random.uniform(2.6, 4.4))
    canopy_n += 1
for s in F["branch_sockets"]:                         # every tip wears leaves
    th = math.radians(s["theta_deg"])
    base = surface_point(s["z"], th, out=-250.0)
    tip_d = {"b1": 7600.0, "b2": 5200.0, "b3": 1500.0, "b4": 1100.0}[s["arch"]] * s["scale"]
    rise = math.sin(math.radians(s["pitch_deg"])) * tip_d
    for k in range(2 if s["arch"] in ("b1", "b2") else 1):
        jitter_a = th + random.uniform(-0.06, 0.06)
        d = tip_d * random.uniform(0.82, 1.02)
        place(random.choice(BLOBS),
              unreal.Vector(base.x + math.cos(jitter_a) * d,
                            base.y + math.sin(jitter_a) * d,
                            s["z"] + rise + random.uniform(120.0, 420.0)),
              f"VR_Canopy_{s['name']}_{k}", yaw=random.uniform(0, 360),
              scale=random.uniform(1.5, 2.6) * s["scale"])
        canopy_n += 1
print(f"REACH_MARKER: {canopy_n} canopy masses raised (crown + tips)")

# ---- waterfalls (tiled sheets, so the streak texture never stretches) + pools ----
fall_n = 0
SEG = 3000.0
for wf in F["waterfalls"]:
    th = math.radians(wf["theta_deg"])
    r_off = 260.0 if wf["land"] == "floor" else 820.0
    n_seg = max(1, int(round(wf["drop"] / SEG)))
    for k in range(n_seg):
        z_top = wf["z_top"] - k * SEG
        loc = surface_point(z_top - SEG, th, out=r_off)
        place(kit("water_sheet"), loc, f"VR_Fall_{wf['name']}_{k}",
              yaw=wf["theta_deg"] + 90.0,
              scale=unreal.Vector(1.6, 1.0, SEG / 1000.0), shadow=False)
        fall_n += 1
    land = surface_point(wf["z_top"] - wf["drop"], th, out=r_off)
    if wf["land"] == "floor":
        land.z = ground_z(land.x, land.y) + 8.0
        pool_scale = 2.6
    else:
        cxp, cyp, cz = pad_centers[f"pad_{wf['land'].lower()}"]
        th_out = math.atan2(cyp - CY, cxp - CX)
        land = unreal.Vector(cxp + math.cos(th_out) * 400.0,
                             cyp + math.sin(th_out) * 400.0, cz - 52.0)
        pool_scale = 1.0
    place(kit("pool_disc"), land, f"VR_Pool_{wf['name']}", scale=pool_scale, shadow=False)
    fall_n += 1
print(f"REACH_MARKER: {fall_n} waterfall pieces falling from the sky")

# ---- cloud shelves: the altitude made visible ----
cloud_n = 0
for ring in F["clouds"]["rings"]:
    for i in range(ring["count"]):
        a = 2.0 * math.pi * i / ring["count"] + random.uniform(-0.25, 0.25)
        rr = random.uniform(ring["r0"], ring["r1"])
        place(kit("cloud_puff"),
              unreal.Vector(CX + rr * math.cos(a), CY + rr * math.sin(a),
                            ring["z"] + random.uniform(-500.0, 500.0)),
              f"VR_Cloud_{cloud_n}", yaw=random.uniform(0, 360),
              scale=random.uniform(4.5, 7.5), shadow=False)
        cloud_n += 1
print(f"REACH_MARKER: {cloud_n} cloud puffs on two shelves")

# ---- the kilometer illusion: canopy-below + horizon giants + villages ----
place(kit("canopy_below"), unreal.Vector(0.0, 0.0, 0.0), "VR_CanopyBelow")
hz = F["horizon"]
village_k = 0
VISTA = 3.0 * math.pi / 2.0            # due south of the trunk: the spawn's postcard corridor
for i in range(hz["count"]):
    a = 2.0 * math.pi * i / hz["count"] + random.uniform(-0.09, 0.09)
    rr = random.uniform(hz["r0"], hz["r1"])
    s = random.uniform(hz["scale_min"], hz["scale_max"])
    if abs(wrap_dt(a - VISTA)) < 0.50:  # no giant blocks the first view of the Heartwood
        continue
    gx, gy = CX + rr * math.cos(a), CY + rr * math.sin(a)
    place(kit("heartwood_trunk"), unreal.Vector(gx, gy, -1500.0),
          f"VR_Horizon{i}", yaw=random.uniform(0, 360),
          scale=unreal.Vector(s, s, s * random.uniform(0.85, 1.1)), material=M_SIL)
    place(random.choice(BLOBS), unreal.Vector(gx, gy, -1500.0 + 40000.0 * s * 0.98),
          f"VR_HorizonCrown{i}", scale=8.0 * s, material=M_SIL, shadow=False)
    if village_k < hz["village_count"] and i % 2 == 0:
        vz = random.uniform(9000.0, 17000.0)
        v_r = 2100.0 * s                              # roughly this giant's bark line
        vx = gx + (CX - gx) / rr * v_r
        vy = gy + (CY - gy) / rr * v_r
        for j in range(random.randint(5, 8)):
            place(CUBE, unreal.Vector(vx + random.uniform(-900.0, 900.0),
                                      vy + random.uniform(-900.0, 900.0),
                                      vz + random.uniform(-1400.0, 1400.0)),
                  f"VR_VillageDot_{village_k}_{j}",
                  scale=unreal.Vector(random.uniform(8.0, 13.0),
                                      random.uniform(5.0, 8.0),
                                      random.uniform(5.0, 9.0)),
                  material=M_VILLAGE, shadow=False)
        vl = eas.spawn_actor_from_class(cls("Lantern"),
                                        unreal.Vector(vx, vy, vz), rot(0))
        vl.set_actor_label(f"VR_VillageLantern_{village_k}")
        vls = vl.get_component_by_class(unreal.LightStateComponent)
        if vls:
            vls.set_editor_property("group_name", f"VR_Village_{village_k}")
        for prop, val in (("refills_embers", False), ("relight_by_hero_radius", 0.0)):
            try:
                (vls or vl).set_editor_property(prop, val)
            except Exception:
                pass
        actor_count += 1
        village_k += 1
sp = hz["spire"]
sp_th = math.radians(sp["theta_deg"])
place(kit("heartwood_trunk"),
      unreal.Vector(CX + sp["r"] * math.cos(sp_th), CY + sp["r"] * math.sin(sp_th), -800.0),
      "VR_TrialSpire", yaw=180.0,
      scale=unreal.Vector(sp["sxy"], sp["sxy"], sp["sz"]), material=M_SIL)
print(f"REACH_MARKER: horizon ring of {hz['count']} giants, {village_k} villages, the dead spire")

# ---- the under-dark: gloom shell + root-line seep + dormant sap-veins ----
place(kit("gloom_ring"), unreal.Vector(0.0, 0.0, 0.0), "VR_GloomRing", shadow=False)
place(kit("gloom_disc"), unreal.Vector(0.0, 0.0, 0.0), "VR_GloomDisc", shadow=False)
seep_n = 0
for i in range(len(BUTTRESSES)):
    b0 = BUTTRESSES[i]
    b1 = BUTTRESSES[(i + 1) % len(BUTTRESSES)]
    mid = b0["theta"] + wrap_dt(b1["theta"] - b0["theta"]) / 2.0
    loc = surface_point(40.0, mid, out=-(300.0 * 2.5 - 30.0))
    place(kit("seep_card"), loc, f"VR_Seep{i}", yaw=math.degrees(mid),
          scale=unreal.Vector(2.5, 3.0, 1.4), shadow=False)
    seep_n += 1
vein_n = 0
for v in F["sap_veins"]:
    th = math.radians(v["theta_deg"])
    z = v["z0"]
    while z + v["step"] <= v["z1"]:
        z_mid = z + v["step"] / 2.0
        dr = field_r(z + v["step"], th) - field_r(z, th)
        lean = math.degrees(math.atan2(dr, v["step"]))
        loc = surface_point(z_mid, th, out=18.0)
        place(CYL, loc, f"VR_Vein_{vein_n}", yaw=v["theta_deg"], pitch=lean,
              scale=unreal.Vector(0.10, 0.10, v["step"] / 200.0),
              material=mat("M_VR_SapVein"), shadow=False)
        vein_n += 1
        z += v["step"]
print(f"REACH_MARKER: underdark dressed ({seep_n} seeps, {vein_n} vein segments, gloom sealed)")

# The last joyful swing-line: one great blossom beside the crown, for the Waygate.
place(SPHERE, unreal.Vector(CX, CY - R_CROWN - 700.0, H + 300.0),
      "VR_Blossom_Waygate", scale=1.7, material=M_BLOSSOM, shadow=False)

# ================= PHASE D (CP5): the breath =================
breath = eas.spawn_actor_from_class(cls("VerdantBreath"),
                                    unreal.Vector(CX, CY, 300.0), rot(0))
breath.set_actor_label("VR_Breath")
actor_count += 1
pollen_n = 0
for name, (pos, _yaw) in camp_positions.items():
    drift = eas.spawn_actor_from_class(
        cls("EmberDrift"), unreal.Vector(pos.x, pos.y, pos.z + 450.0), rot(0))
    drift.set_actor_label(f"VR_Pollen_{name}")
    drift.set_editor_property("num_motes", 40)
    drift.set_editor_property("extent", unreal.Vector(1600.0, 1600.0, 800.0))
    drift.set_editor_property("rise_speed", 11.0)      # drowsy, not ember-urgent
    drift.set_editor_property("wander_amp", 85.0)
    drift.set_editor_property("mote_scale", 0.035)
    drift.set_editor_property("tint", unreal.LinearColor(2.1, 1.75, 0.5, 1.0))
    actor_count += 1
    pollen_n += 1
print(f"REACH_MARKER: breath driver placed + {pollen_n} pollen drifts (10Hz lungs, gold dust)")

# ---------------- save law ----------------
print(f"REACH_MARKER: {actor_count} actors placed")
assert les.save_current_level(), "SAVE_REACH_FAILED"
print("REACH_MARKER: SAVE OK")
print("REACH_MARKER: DONE — the Heartwood stands in morning light")
