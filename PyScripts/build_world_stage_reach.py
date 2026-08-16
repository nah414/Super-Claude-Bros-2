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
    for hx, hy, a, c in F["floor"].get("carves", []):   # the river remembers (v3)
        d2 = ((x - hx) ** 2 + (y - hy) ** 2) / (a * a)
        if d2 < 1.0:
            g -= c * (1.0 - d2) ** 2
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
                          (ridge_pt[0], ridge_pt[1], "root-ridge"),
                          (3400.0, 14400.0, "river-bed"),
                          (F["pool"]["center"][0], F["pool"]["center"][1], "pool-basin")):
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
            comp.set_editor_property("intensity", 1.45)   # v4: 8:1 -> ~6.2:1 fill
            comp.recapture_sky()
print("REACH_MARKER: morning light set (sun -14deg warm, shafts armed)")

# v4 THE EXPOSURE LAW: no PPV existed — engine-default auto exposure (EV100
# -10..+20, unclamped) crushed the shadow side to night-black in daylight.
# ExtendDefaultLuminanceRange=True in DefaultEngine.ini -> values are EV100.
ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0), rot(0))
ppv.set_actor_label("VR_ExposureLaw")
ppv.set_editor_property("unbound", True)
ppv.set_editor_property("priority", 1.0)
ppv.set_editor_property("blend_weight", 1.0)
pps = ppv.get_editor_property("settings")
for pk, pv in (("override_auto_exposure_method", True),
               ("auto_exposure_method", unreal.AutoExposureMethod.AEM_HISTOGRAM),
               # Calibrated by shot (twice): natural sunny EV here is ~2-3; the
               # CEILING at 3.5 is what lifts the shadow side, and the FLOOR
               # stays wide open (-4) so lantern-lit interiors and dawn-sky
               # frames may brighten freely.
               ("override_auto_exposure_min_brightness", True),
               ("auto_exposure_min_brightness", -4.0),
               ("override_auto_exposure_max_brightness", True),
               ("auto_exposure_max_brightness", 3.5),
               ("override_auto_exposure_speed_up", True),
               ("auto_exposure_speed_up", 5.0),
               ("override_auto_exposure_speed_down", True),
               ("auto_exposure_speed_down", 3.0)):
    try:
        pps.set_editor_property(pk, pv)
    except Exception as e:
        print(f"REACH_WARN: exposure {pk}: {e}")
ppv.set_editor_property("settings", pps)
actor_count += 1
print("REACH_MARKER: the exposure law holds (EV100 clamp -4.0..3.5)")

# ---------------- the warm green-gold air (ONE fog, volumetric for shafts) ----------------
fog = eas.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0), rot(0))
fog.set_actor_label("VR_Air")
fog_comp = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
if fog_comp:
    fog_comp.set_editor_property("fog_density", 0.003)
    fog_comp.set_editor_property("fog_height_falloff", 0.005)
    fog_comp.set_editor_property("start_distance", 2200.0)   # v4: nearer fill
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
        yaw_j = random.uniform(-7.0, 7.0)
        sy_j = random.uniform(0.8, 1.3)
        sz_j = random.uniform(0.7, 1.2)
        # v4: the mouth is a REAL hole now — the one FIN card inside the cut
        # (z 39000, theta ~131) skips placement AFTER burning its 4 draws in
        # original order, so every other card stays byte-identical.
        if band["leg"] == "FIN" and abs(z - 39000.0) < 1.0:
            moss_n += 1
            z += band["step"]
            continue
        loc = surface_point(z - 130.0, th, out=-(300.0 * card_scale - 20.0))
        place(kit("seep_card"), loc, f"VR_Moss_{band['leg']}_{moss_n}",
              yaw=th_deg + yaw_j,
              scale=unreal.Vector(card_scale, card_scale * sy_j,
                                  card_scale * sz_j),
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

# ---- waterfalls v3: SCULPTED TORRENTS (Adam: "the water looks 2D") ----
# Geometry first, shader second: stacked crescent torrent columns (seam-proof
# harmonics), a spill lip pouring over the crest, churn at the landing, one
# backing curtain for parallax. DETERMINISM GUARD: v2 consumed 3*n_seg+4 draws
# per fall — v3 burns exactly that count and draws NOTHING, so every seeded
# thing downstream stays byte-identical.
fall_n = 0
SEG = 3000.0
TSEG = F["falls_geom"]["seg"]
M_TCORE = mat("M_VR_TorrentCore")     # the opaque body inside each crescent
for wf in F["waterfalls"]:
    th = math.radians(wf["theta_deg"])
    r_off = 260.0 if wf["land"] == "floor" else 820.0
    tx, ty = -math.sin(th), math.cos(th)
    n_old = max(1, int(round(wf["drop"] / SEG)))
    for _ in range(3 * n_old + 4):
        random.random()                            # the burn (see guard note)
    n_t = max(1, int(round(wf["drop"] / TSEG)))
    for k in range(n_t):
        z_top = wf["z_top"] - k * TSEG
        seg_r = r_off
        if wf["name"] == "sky_fall" and 38500.0 <= z_top <= 39700.0 + TSEG:
            seg_r = 700.0                          # the hero walks BEHIND the fall here
        loc = surface_point(z_top - TSEG, th, out=seg_r)
        place(kit("falls_torrent"), loc, f"VR_Fall_{wf['name']}_t{k}",
              yaw=wf["theta_deg"], shadow=False)
        fall_n += 1
        # v4: the fall's BODY — masked core crescent tucked inside the shell,
        # yaw-offset so the lumps interleave; z-scale untouched (seam law).
        place(kit("falls_torrent"), loc, f"VR_FallCore_{wf['name']}_t{k}",
              yaw=wf["theta_deg"] + 16.0, scale=unreal.Vector(0.8, 0.8, 1.0),
              material=M_TCORE, shadow=False)
        fall_n += 1
    if F["falls_geom"].get("curtain") and wf["name"] == "sky_fall":
        n_c = max(1, int(round(wf["drop"] / SEG)))
        for k in range(1, n_c):     # v4: top card retired — it pierced the
            loc = surface_point(wf["z_top"] - (k + 1) * SEG, th, out=r_off - 80.0)
            place(kit("water_sheet"), loc, f"VR_FallCurtain_{k}",   # rebased deck
                  yaw=wf["theta_deg"] + 90.0,
                  scale=unreal.Vector(3.4, 1.0, SEG / 1000.0), shadow=False)
            fall_n += 1
    # v4: the sky_fall's lip rides the pushed-out torrent (out 580) — at the
    # rebased ramp crossing (z~39433) the old out=140 lip speared the deck.
    lip_out = 580.0 if wf["name"] == "sky_fall" else r_off - 120.0
    lip = surface_point(wf["z_top"], th, out=lip_out)
    place(kit("falls_lip"), lip, f"VR_FallLip_{wf['name']}",
          yaw=wf["theta_deg"], pitch=-8.0, shadow=False)
    fall_n += 1
    land = surface_point(wf["z_top"] - wf["drop"], th, out=r_off)
    if wf["land"] == "floor":
        land.z = F["pool"]["z_surface"]
        churn_s = 1.4
    else:
        cxp, cyp, cz = pad_centers[f"pad_{wf['land'].lower()}"]
        th_out = math.atan2(cyp - CY, cxp - CX)
        land = unreal.Vector(cxp + math.cos(th_out) * 400.0,
                             cyp + math.sin(th_out) * 400.0, cz - 52.0)
        place(kit("pool_disc"), land, f"VR_Pool_{wf['name']}", scale=1.0, shadow=False)
        fall_n += 1
        churn_s = 0.8
    place(kit("falls_churn"), unreal.Vector(land.x, land.y, land.z + 12.0),
          f"VR_Churn_{wf['name']}", yaw=wf["theta_deg"], scale=churn_s, shadow=False)
    fall_n += 1
    for mi, (ms, mz, moff) in enumerate(((1.5, 80.0, 300.0), (1.1, 40.0, -260.0),
                                         (0.9, 18.0, 60.0))):
        place(kit("mist_puff"),
              unreal.Vector(land.x + tx * moff, land.y + ty * moff, land.z + mz),
              f"VR_Mist_{wf['name']}_{mi}", yaw=float(mi) * 127.0,
              scale=ms, shadow=False)
        fall_n += 1
print(f"REACH_MARKER: {fall_n} waterfall pieces falling from the sky (v3 TORRENTS)")

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
# v3: the EXTERIOR seep ring is gone — translucent violet over sunlit bark can
# only render pastel-pink (Adam's photos + CP-R1 retake both convicted it).
# Daylight was never the seep's canon home; the root-line violet arrives with
# C3's root-dark. The chimney interior keeps its seeps, where dark makes
# violet read TRUE.
seep_n = 0
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

# ================= PHASE E (Round 2): the river, the Hollow, the showdown, LIFE =================
RIV = F["river"]
POOLJ = F["pool"]
ST = F["stair"]
ARN = F["arena"]
CHIM = F["chimney"]
M_TUNSAP = mat("M_VR_TunnelSap")
M_ALPHA = mat("M_VR_AlphaShell")

# ---- the river runs to the world's edge ----
place(kit("river_surface"), unreal.Vector(0.0, 0.0, 0.0), "VR_River", shadow=False)
place(kit("pool_surface"), unreal.Vector(0.0, 0.0, 0.0), "VR_PoolSurface", shadow=False)
# v3: the pool becomes a BODY of water — churn collar at the impact, floating
# foam, rising bubbles (EmberDrift retinted white-teal), rapids rocks upstream.
IMPACT = F["pool"]["impact"]
PZ_S = F["pool"]["z_surface"]
place(kit("churn_ring"), unreal.Vector(IMPACT[0], IMPACT[1], PZ_S + 8.0),
      "VR_PoolChurnRing", shadow=False)
for fi, fth in enumerate((40.0, 160.0, 280.0)):
    place(kit("foam_patch"),
          unreal.Vector(IMPACT[0] + 700.0 * math.cos(math.radians(fth)),
                        IMPACT[1] + 700.0 * math.sin(math.radians(fth)), PZ_S + 16.0),
          f"VR_PoolFoam_{fi}", yaw=fth * 2.0, shadow=False)
bub = eas.spawn_actor_from_class(cls("EmberDrift"),
                                 unreal.Vector(IMPACT[0], IMPACT[1], PZ_S + 60.0), rot(0))
bub.set_actor_label("VR_PoolBubbles")
bub.set_editor_property("num_motes", 70)
bub.set_editor_property("extent", unreal.Vector(450.0, 450.0, 900.0))
bub.set_editor_property("rise_speed", 55.0)
bub.set_editor_property("wander_amp", 28.0)
bub.set_editor_property("mote_scale", 0.02)
bub.set_editor_property("tint", unreal.LinearColor(0.85, 1.15, 1.2, 1.0))
actor_count += 1
for ri, rp in enumerate(F["river"].get("rapids", [])):
    place(kit("knot_boulder"), unreal.Vector(rp["x"], rp["y"], rp["z"] - 60.0),
          f"VR_Rapids_{ri}", yaw=float(ri) * 73.0, scale=0.55 + 0.1 * (ri % 2))
print("REACH_MARKER: the pool breathes (churn, foam, bubbles) + rapids set")
wpA, wpB = RIV["waypoints"][-2], RIV["waypoints"][-1]
seg_l = math.hypot(wpB[0] - wpA[0], wpB[1] - wpA[1])
ltx, lty = (wpB[0] - wpA[0]) / seg_l, (wpB[1] - wpA[1]) / seg_l
lpx, lpy = -lty, ltx
z_edge = RIV["surface_z"][-1]
place(kit("falls_torrent"),
      unreal.Vector(wpB[0] + ltx * 620.0, wpB[1] + lty * 620.0, z_edge - 2650.0),
      "VR_EdgeFall_t", yaw=math.degrees(math.atan2(lty, ltx)) + 180.0,
      scale=unreal.Vector(1.0, 1.0, 0.66), shadow=False)
place(kit("falls_torrent"),
      unreal.Vector(wpB[0] + ltx * 620.0, wpB[1] + lty * 620.0, z_edge - 2650.0),
      "VR_EdgeFall_core", yaw=math.degrees(math.atan2(lty, ltx)) + 196.0,
      scale=unreal.Vector(0.8, 0.8, 0.66), material=M_TCORE, shadow=False)
place(kit("falls_churn"),
      unreal.Vector(wpB[0] + ltx * 680.0, wpB[1] + lty * 680.0, z_edge - 2600.0),
      "VR_EdgeChurn", scale=0.9, shadow=False)
for si, (d_off, p_off, ms) in enumerate(((700.0, 0.0, 2.2), (760.0, 260.0, 1.5))):
    place(kit("mist_puff"),
          unreal.Vector(wpB[0] + ltx * d_off + lpx * p_off,
                        wpB[1] + lty * d_off + lpy * p_off, z_edge - 2400.0),
          f"VR_EdgeMist_{si}", scale=ms, shadow=False)
for si in range(4):
    b_side = 1.0 if si % 2 == 0 else -1.0
    b_d = 400.0 + 700.0 * (si // 2)
    place(CUBE, unreal.Vector(wpB[0] - ltx * b_d + lpx * b_side * (RIV["width"] / 2 + 90),
                              wpB[1] - lty * b_d + lpy * b_side * (RIV["width"] / 2 + 90),
                              z_edge + 60.0),
          f"VR_RiverRim_{si}", yaw=math.degrees(math.atan2(lty, ltx)),
          scale=unreal.Vector(3.0, 0.14, 0.10), material=M_EDGE, shadow=False)
print("REACH_MARKER: the river runs east and falls off the world")

# ==== THE SAPLINE STAIR: weenie mouth -> bore -> OPEN spiral -> THE PLATFORM ====
# Adam's hard requirement honored by construction: theta(1) = 115-625 = 210 deg
# at z 42800 — the arena rim gap, the cloud platform, the showdown.
def stair_point(t, out=0.0, up=0.0):
    th_t = math.radians(ST["bore_theta1_deg"]) - math.radians(ST["sweep_deg"]) * t
    rr = ST["r0"] + (ST["r1"] - ST["r0"]) * t + out
    zc = ST["z0"] + (ST["z1"] - ST["z0"]) * (t ** ST["z_ease"]) + up
    return unreal.Vector(CX + rr * math.cos(th_t), CY + rr * math.sin(th_t), zc), \
           math.degrees(th_t)


th_m = math.radians(ST["mouth_theta_deg"])
GLD = F["gallery"]


def gallery_point(t, r=600.0, up=0.0):
    gth = math.radians(GLD["theta0_deg"]) - math.radians(GLD["sweep_deg"]) * t
    gz = GLD["z0"] + (GLD["z1"] - GLD["z0"]) * t + up
    return unreal.Vector(CX + r * math.cos(gth), CY + r * math.sin(gth), gz), \
        math.degrees(gth)


# v4 THE HYBRID CLIMB: the seal first (liner), then the interior gallery, then
# the rebased exterior ramp. The bore is gone — the mouth is a REAL hole now.
place(kit("trunk_liner"), unreal.Vector(0.0, 0.0, 0.0), "VR_TrunkLiner")
place(kit("verdant_gallery"), unreal.Vector(0.0, 0.0, 0.0), "VR_GalleryDeck")
place(kit("stair_ramp"), unreal.Vector(0.0, 0.0, 0.0), "VR_StairRamp")
mouth_base = surface_point(39000.0 - ST["mouth_r"], th_m, out=-60.0)
place(kit("mouth_ring"), mouth_base, "VR_MouthRing",
      yaw=ST["mouth_theta_deg"] + 90.0)
# the weenie's beam: crossed light-shaft cards rising OVER the crown-bowl rim
for i, ly in enumerate((0.0, 90.0)):
    place(kit("water_sheet"), surface_point(ST["mouth_z"] + 150.0, th_m, out=250.0),
          f"VR_MouthShaft_{i}", yaw=ST["mouth_theta_deg"] + ly,
          scale=unreal.Vector(3.2, 1.0, 2.6), material=mat("M_VR_LightShaft"),
          shadow=False)
# converging sap veins fan into the ring from the FIN band below
for i in range(5):
    vth_deg = ST["mouth_theta_deg"] - 26.0 + i * 13.0
    p = surface_point(ST["mouth_z"] - 900.0 - abs(i - 2) * 260.0,
                      math.radians(vth_deg), out=20.0)
    place(CYL, p, f"VR_MouthVein_{i}", yaw=vth_deg, pitch=-6.0 + abs(i - 2) * 2.0,
          scale=unreal.Vector(0.09, 0.09, 5.5), material=M_TUNSAP, shadow=False)
# 3 amber blossoms crown the ring + 2 moths orbit it
for i, (bth, bz) in enumerate(((ST["mouth_theta_deg"] - 9.0, ST["mouth_z"] + 560.0),
                               (ST["mouth_theta_deg"] + 9.0, ST["mouth_z"] + 560.0),
                               (ST["mouth_theta_deg"], ST["mouth_z"] - 540.0))):
    place(SPHERE, surface_point(bz, math.radians(bth), out=180.0),
          f"VR_MouthBlossom_{i}", scale=1.1, material=M_BLOSSOM, shadow=False)
for i in range(2):
    mm = eas.spawn_actor_from_class(cls("FlitMoth"),
                                    surface_point(ST["mouth_z"] + 200.0 * i, th_m, out=420.0),
                                    rot(0))
    mm.set_actor_label(f"VR_MouthMoth_{i}")
    actor_count += 1
# the rim-gap arch marks the arrival onto the boss platform
th_x = math.radians(ARN["gap_theta_deg"])
place(kit("knothole_arch"),
      unreal.Vector(CX + 2600.0 * math.cos(th_x), CY + 2600.0 * math.sin(th_x),
                    ARN["z_top"] - 4.0),
      "VR_Arch_Emerge", yaw=ARN["gap_theta_deg"] + 90.0, scale=1.25)
# 7 bark rib-arches over the open spiral (rhythm without enclosure)
for i in range(7):
    p, yaw_t = stair_point((i + 0.5) / 7.0, up=10.0)
    place(kit("knothole_arch"), p, f"VR_StairRib_{i}", yaw=yaw_t + 90.0, scale=2.2)
# the sap-light rail: ONE UnderstoryPatch (C++ HISM) of glowing posts.
# (AddComponentByClass is NOT exposed to editor python — the patch actor's
# Instances UPROPERTY is the saved truth, rebuilt on load by construction.)
rail = eas.spawn_actor_from_class(cls("UnderstoryPatch"),
                                  unreal.Vector(0.0, 0.0, 0.0), rot(0))
rail.set_actor_label("VR_StairRail")
rail.set_editor_property("plant_mesh", CYL)
rail.set_editor_property("plant_material", M_TUNSAP)
rail_xf = []
for i in range(40):
    p, _ = stair_point(i / 39.0, out=270.0, up=70.0)
    rail_xf.append(unreal.Transform(p, unreal.Rotator(0.0, 0.0, 0.0),
                                    unreal.Vector(0.06, 0.06, 0.7)))
rail.set_editor_property("instances", rail_xf)
actor_count += 1
# blossoms along the rail + gust cards + gold pollen + the midway checkpoint
for i in range(8):
    p, _ = stair_point((i + 0.5) / 8.0, out=270.0, up=150.0)
    place(SPHERE, p, f"VR_StairBlossom_{i}", scale=0.8, material=M_BLOSSOM,
          shadow=False)
for i, gt in enumerate((0.2, 0.45, 0.7, 0.9)):
    p, yaw_t = stair_point(gt, out=330.0, up=180.0)
    place(kit("seep_card"), p, f"VR_StairGust_{i}", yaw=yaw_t,
          scale=unreal.Vector(2.0, 2.4, 1.6), material=mat("M_VR_Mist"), shadow=False)
p_pol, _ = stair_point(0.55, up=400.0)
pol = eas.spawn_actor_from_class(cls("EmberDrift"), p_pol, rot(0))
pol.set_actor_label("VR_StairPollen")
pol.set_editor_property("num_motes", 30)
pol.set_editor_property("extent", unreal.Vector(900.0, 900.0, 500.0))
pol.set_editor_property("rise_speed", 12.0)
pol.set_editor_property("tint", unreal.LinearColor(2.1, 1.75, 0.5, 1.0))
actor_count += 1
# ---- the gallery dressing: rail, veins, window shafts, the mid checkpoint ----
g_rail = eas.spawn_actor_from_class(cls("UnderstoryPatch"),
                                    unreal.Vector(0.0, 0.0, 0.0), rot(0))
g_rail.set_actor_label("VR_GalleryRail")
g_rail.set_editor_property("plant_mesh", CYL)
g_rail.set_editor_property("plant_material", M_TUNSAP)
g_xf = []
for i in range(40):
    p, _ = gallery_point(i / 39.0, r=380.0, up=232.0)
    g_xf.append(unreal.Transform(p, unreal.Rotator(0.0, 0.0, 0.0),
                                 unreal.Vector(0.045, 0.045, 0.34)))
g_rail.set_editor_property("instances", g_xf)
actor_count += 1
for i in range(6):
    p, gyaw = gallery_point(0.06 + i / 6.0 * 0.9, r=815.0, up=290.0)
    place(CYL, p, f"VR_GallerySapVein_{i}", yaw=gyaw, pitch=-8.0,
          scale=unreal.Vector(0.08, 0.08, 3.0), material=M_TUNSAP, shadow=False)
# the gallery is LANTERN-LIT (the Lamplighter's grammar — amber kept-fire
# marks every safe road): four more lamps between the door and the balcony.
for gi, gt in enumerate((0.18, 0.38, 0.62, 0.82)):
    p_gl, _ = gallery_point(gt, r=560.0, up=10.0)
    gl = eas.spawn_actor_from_class(cls("Lantern"), p_gl, rot(0))
    gl.set_actor_label(f"VR_GalleryLamp_{gi}")
    gls = gl.get_component_by_class(unreal.LightStateComponent)
    if gls:
        gls.set_editor_property("group_name", "VR_Stair")
    actor_count += 1
for wi, wc in enumerate(F["wall_cuts"]["windows"]):
    wth = math.radians(wc["theta_deg"])
    wz = (wc["z0"] + wc["z1"]) / 2.0
    place(kit("water_sheet"), surface_point(wz, wth, out=-260.0),
          f"VR_GalleryShaft_{wi}", yaw=wc["theta_deg"] + 90.0, pitch=-18.0,
          scale=unreal.Vector(1.9, 1.0, 1.5), material=mat("M_VR_LightShaft"),
          shadow=False)
# ---- the balcony burst: arch + a 3-blossom arrow receding along the ledge ----
place(kit("knothole_arch"), surface_point(39400.0, math.radians(115.0), out=40.0),
      "VR_Arch_Balcony", yaw=115.0 + 90.0, scale=1.15)
for bi, bth_d in enumerate((111.0, 107.0, 103.0)):
    bth = math.radians(bth_d)
    place(SPHERE, unreal.Vector(CX + (ST["r0"] + 140.0) * math.cos(bth),
                                CY + (ST["r0"] + 140.0) * math.sin(bth), 39450.0),
          f"VR_BalconyBlossom_{bi}", scale=0.9, material=M_BLOSSOM, shadow=False)
# ---- the rescue net: one catch volume under the gallery's central well ----
try:
    net = eas.spawn_actor_from_class(cls("RescueNet"),
                                     unreal.Vector(CX, CY, 38480.0), rot(0))
    net.set_actor_label("VR_RescueNet_Well")
    net.set_actor_scale3d(unreal.Vector(4.2, 4.2, 1.5))
    porch_p = surface_point(ST["mouth_z"] + 110.0, th_m, out=150.0)
    net.set_editor_property("rescue_target", porch_p)
    net.set_editor_property("rescue_yaw", ST["mouth_theta_deg"] + 180.0)
    actor_count += 1
    print("REACH_MARKER: the rescue net waits under the well")
except Exception as e:
    print(f"REACH_WARN: RescueNet class missing (rebuild C++): {e}")

p_mid, yaw_mid = stair_point(0.485, up=6.0)
p_gmid, _ = gallery_point(0.5, r=600.0, up=6.0)
for name, pos, chk in (("Mouth", surface_point(ST["mouth_z"] + 4.0, th_m, out=200.0), False),
                       ("GalleryMid", p_gmid, True),
                       ("Midway", p_mid, True),
                       ("Arena", unreal.Vector(CX + 1850.0 * math.cos(th_x),
                                               CY + 1850.0 * math.sin(th_x),
                                               ARN["z_top"] + 4.0), True)):
    lant = eas.spawn_actor_from_class(cls("Lantern"), pos, rot(0))
    lant.set_actor_label(f"VR_StairLantern_{name}")
    ls = lant.get_component_by_class(unreal.LightStateComponent)
    if ls:
        ls.set_editor_property("group_name", "VR_Stair")
    if chk:
        try:
            lant.set_editor_property("is_checkpoint", True)
        except Exception as e:
            print(f"REACH_WARN: stair lantern {name}: {e}")
    actor_count += 1
# breadcrumbs: blossoms arc the crown bowl toward the mouth; moss cards ladder
# down the outer bark to its doorstep
for i in range(5):
    d = 120.0 + i * 85.0
    place(SPHERE, unreal.Vector(CX + d * math.cos(th_m), CY + d * math.sin(th_m),
                                H - 250.0 + 40.0),
          f"VR_BowlCrumb_{i}", scale=0.6, material=M_BLOSSOM, shadow=False)
# v4: the ladder flanks the REAL hole instead of hanging inside it
for i, (mz, mth_d) in enumerate(((39650.0, 140.0), (39450.0, 140.0),
                                 (38950.0, 166.0), (38950.0, 111.0))):
    p = surface_point(mz, math.radians(mth_d), out=-(300.0 * 2.0 - 20.0))
    place(kit("seep_card"), p, f"VR_MouthMoss_{i}", yaw=mth_d,
          scale=2.0, material=M_MOSS, shadow=False)
# the canopy clears its corridors: POST-PASS v3 — self-verifying in-place
# SHRINK (zero draws, nothing teleports). v2's lift/push surgery threw giant
# blobs into the upper coil and the arena sky — learned by instrument. v3
# shrinks offenders where they stand until the three protected airs are free:
# the mouth doorstep, the spiral tube (the follow-cam rides IN it), and the
# arena dome. Bounded: three rounds, then an honest report.
mouth_p = surface_point(ST["mouth_z"], th_m, out=0.0)
out_m = (math.cos(th_m), math.sin(th_m))
probe_pts = []
for d in (800.0, 1600.0, 2400.0):
    for da in (-0.7, 0.0, 0.7):        # the approach CONE, not just the axis ray
        ox, oy = math.cos(th_m + da), math.sin(th_m + da)
        for pz in (38850.0, 39350.0):  # v4: the door z-band (real cut 38800-39200)
            probe_pts.append(unreal.Vector(mouth_p.x + ox * d,
                                           mouth_p.y + oy * d, pz))
for k in range(0, 131, 2):
    p, _ = stair_point(k / 130.0)
    for dz in (180.0, 480.0):
        probe_pts.append(unreal.Vector(p.x, p.y, p.z + dz))
for i in range(8):
    aa = 2.0 * math.pi * i / 8.0
    probe_pts.append(unreal.Vector(CX + 3400.0 * math.cos(aa),
                                   CY + 3400.0 * math.sin(aa), 42650.0))
probe_pts.append(unreal.Vector(CX, CY, 43400.0))


def crown_blobs():
    return [b for b in eas.get_all_level_actors()
            if b.get_actor_label().startswith("VR_Canopy_crown")]


def blob_offends(b):
    o, e = b.get_actor_bounds(False)
    for pt in probe_pts:
        if (abs(pt.x - o.x) < e.x and abs(pt.y - o.y) < e.y
                and abs(pt.z - o.z) < e.z):
            return True
    return False


pruned = set()
for _rnd in range(3):
    offenders = [b for b in crown_blobs() if blob_offends(b)]
    if not offenders:
        break
    for b in offenders:
        s = b.get_actor_scale3d()
        b.set_actor_scale3d(unreal.Vector(s.x * 0.55, s.y * 0.55, s.z * 0.55))
        pruned.add(b.get_actor_label())
# a blob PIVOTED inside protected air can shrink forever and never leave —
# the stair carved that space; those blobs simply no longer fit the world.
felled = 0
for b in [b for b in crown_blobs() if blob_offends(b)]:
    eas.destroy_actor(b)
    actor_count -= 1
    felled += 1
print(f"REACH_MARKER: the SAPLINE STAIR rises (mouth, bore, open spiral, "
      f"{len(pruned)} blobs pruned, {felled} felled) — it ends at the showdown")

# ---- the arena among the clouds ----
place(kit("arena_pad"), unreal.Vector(CX, CY, ARN["z_top"] - 128.0), "VR_ArenaPad")
for k in range(ARN["knots"]):
    kth = math.radians((30.0, 100.0, 170.0, 280.0, 330.0)[k])
    kr = 1600.0 + 400.0 * (k % 2)
    place(kit("knot_boulder"),
          unreal.Vector(CX + kr * math.cos(kth), CY + kr * math.sin(kth),
                        ARN["z_top"] + 150.0),
          f"VR_Knot_{k}", yaw=random.uniform(0, 360), scale=random.uniform(1.1, 1.6))
for k in range(6):
    bth = math.radians(k * 60.0 + 15.0)
    place(CUBE, unreal.Vector(CX + (ARN["r"] + 40.0) * math.cos(bth),
                              CY + (ARN["r"] + 40.0) * math.sin(bth),
                              ARN["z_top"] + ARN["rim_h"] + 20.0),
          f"VR_ArenaRim_{k}", yaw=math.degrees(bth) + 90.0,
          scale=unreal.Vector(4.5, 0.14, 0.10), material=M_EDGE, shadow=False)
print("REACH_MARKER: the Beacon bowl waits among the clouds")

# ---- THE SHOWDOWN: the Shellback Alpha holds the crown ----
alpha_cls = unreal.load_class(None, "/Script/SuperClaudeBros2.ShellbackAlpha")
if alpha_cls:
    alpha = eas.spawn_actor_from_class(
        alpha_cls, unreal.Vector(CX, CY + 1300.0, ARN["z_top"] + 90.0 * 1.4 + 8.0), rot(-90.0))
    alpha.set_actor_label("VR_Boss_ShellbackAlpha")
    alpha.set_actor_scale3d(unreal.Vector(1.4, 1.4, 1.4))
    for prop, val in (("aggro_radius", 1500.0), ("AggroRadius", 1500.0)):
        try:
            alpha.set_editor_property(prop, val)
            break
        except Exception:
            continue
    scarred = 0
    for comp in alpha.get_components_by_class(unreal.StaticMeshComponent):
        if comp.get_editor_property("static_mesh"):
            comp.set_material(0, M_ALPHA)
            scarred += 1
    actor_count += 1
    print(f"REACH_MARKER: the SHELLBACK ALPHA holds the crown (scarred {scarred} mesh)")
else:
    print("REACH_WARN: ShellbackAlpha class missing — the crown waits empty")

# ---- LIFE: rolys, glimmers, wings, moths (+ new species when compiled) ----
life_n = 0
for i, (rx, ry) in enumerate(((0.0, 2500.0), (4200.0, 8200.0), (-3800.0, 7000.0),
                              (2600.0, 12900.0), (-1500.0, 3400.0))):
    roly = eas.spawn_actor_from_class(cls("RolyShellback"),
                                      unreal.Vector(rx, ry, ground_z(rx, ry) + 60.0),
                                      rot(random.uniform(0, 360)))
    roly.set_actor_label(f"VR_Roly_{i}")
    for prop in ("aggro_radius", "AggroRadius"):
        try:
            roly.set_editor_property(prop, 700.0)
            break
        except Exception:
            continue
    life_n += 1
glim_spots = []
for sname in ("bough_mid_in", "bough_c", "bough_high_in"):
    s = next(x for x in F["branch_sockets"] if x["name"] == sname)
    th = math.radians(s["theta_deg"])
    base = surface_point(s["z"], th, out=-250.0)
    d = 7600.0 * s["scale"] * 0.45
    glim_spots.append((base.x + math.cos(th) * d, base.y + math.sin(th) * d,
                       s["z"] + math.sin(math.radians(s["pitch_deg"])) * d + 170.0 * s["scale"]))
cxp, cyp, cz = pad_centers["pad_crownbase"]
glim_spots.append((cxp, cyp, cz))
for i, (gx, gy, gz) in enumerate(glim_spots):
    g = eas.spawn_actor_from_class(cls("GlimmerEnemy"),
                                   unreal.Vector(gx, gy, gz + 160.0), rot(0))
    g.set_actor_label(f"VR_Glimmer_{i}")
    life_n += 1
for i in range(7):
    if i < 3:
        wz, wr = random.uniform(38500.0, 41000.0), random.uniform(1800.0, 2600.0)
    elif i < 5:
        wz, wr = 26500.0, random.uniform(2400.0, 3200.0)
    else:
        wz, wr = 42900.0, 3600.0
    wth = random.uniform(0, 2.0 * math.pi)
    w = eas.spawn_actor_from_class(cls("GlassWing"),
                                   unreal.Vector(CX + wr * math.cos(wth),
                                                 CY + wr * math.sin(wth), wz),
                                   rot(random.uniform(0, 360)))
    w.set_actor_label(f"VR_GlassWing_{i}")
    w.set_editor_property("orbit_radius", random.uniform(700.0, 1500.0))
    w.set_editor_property("orbit_speed", random.uniform(200.0, 380.0))
    try:
        w.set_editor_property("glow_tint", unreal.LinearColor(2.2, 1.6, 0.6, 1.0))
    except Exception as e:
        print(f"REACH_WARN: glasswing tint: {e}")
    life_n += 1
moth_i = 0
for band in F["moss_bands"][:2]:
    for t in (0.3, 0.55):
        z = band["z0"] + (band["z1"] - band["z0"]) * t
        th_deg = band["th0"] + (band["th1"] - band["th0"]) * t
        p = surface_point(z, math.radians(th_deg), out=560.0)
        mth = eas.spawn_actor_from_class(cls("FlitMoth"), p, rot(0))
        mth.set_actor_label(f"VR_Moth_{moth_i}")
        moth_i += 1
        life_n += 1
wg = eas.spawn_actor_from_class(cls("FlitMoth"),
                                unreal.Vector(CX, CY - R_CROWN - 700.0, H + 420.0), rot(0))
wg.set_actor_label(f"VR_Moth_{moth_i}")
life_n += 1
for cls_name, spawns in (
        ("LeafGlider", ((CX + 2200.0, CY, 37500.0), (CX - 2600.0, CY + 800.0, 37800.0),
                        (-4000.0, 7200.0, 20500.0), (2800.0, 5200.0, 4200.0))),
        ("BarkSkitter", ((0.0, 0.0, 1500.0), (0.0, 0.0, 2600.0),
                         (0.0, 0.0, 5200.0), (0.0, 0.0, 8000.0)))):
    species = unreal.load_class(None, f"/Script/SuperClaudeBros2.{cls_name}")
    if not species:
        print(f"REACH_WARN: {cls_name} not compiled yet — skipped this pass")
        continue
    for i, (sx2, sy2, sz2) in enumerate(spawns):
        a = eas.spawn_actor_from_class(species, unreal.Vector(sx2, sy2, sz2), rot(0))
        a.set_actor_label(f"VR_{cls_name}_{i}")
        if cls_name == "BarkSkitter":
            for prop, val in (("axis_x", CX), ("axis_y", CY), ("z_mid", sz2)):
                try:
                    a.set_editor_property(prop, val)
                except Exception:
                    pass
        life_n += 1
actor_count += life_n
print(f"REACH_MARKER: {life_n} creatures live in the Reach")

# ---- FOLIAGE: the floor grows an understory ----
FERN, VINE, FUNGUS, FLOWER = (kit("fern_clump"), kit("vine_curtain"),
                              kit("fungus_shelf"), kit("flower_stalk"))


def near_river(x, y):
    best = 1e18
    for wpx, wpy in RIV["waypoints"]:
        best = min(best, math.hypot(x - wpx, y - wpy))
    return best


# v5 ROUND 5 (A6, the needle spikes): near_river() measures distance to the
# nearest WAYPOINT — waypoints sit ~2500uu apart, so a plant mid-segment can
# pass every <430 rejection while standing dead-center in the channel, rooted
# on the carved bed with its tip poking through the surface (Adam's V1-t36
# shards). spine_dist() is the true point-to-segment distance. LAW: existing
# predicates and draw counts stay byte-identical (the seeded world never
# reshuffles) — this is used ONLY to post-filter placements out of the water.
def spine_dist(x, y):
    best = 1e18
    wps = RIV["waypoints"]
    for i in range(1, len(wps)):
        ax, ay = wps[i - 1]
        bx, by = wps[i]
        vx, vy = bx - ax, by - ay
        L2 = vx * vx + vy * vy
        t = 0.0 if L2 <= 0.0 else max(0.0, min(1.0, ((x - ax) * vx + (y - ay) * vy) / L2))
        best = min(best, math.hypot(x - (ax + vx * t), y - (ay + vy * t)))
    return best


# Keepout = beyond the v5 widened waterline (mean half 468, +18% sway = 552);
# at 580uu the carve depth is ~6uu < the 25uu inset, so plants keep dry feet.
RIVER_KEEPOUT = 580.0


def cull_channel(xforms, label):
    kept = [t for t in xforms
            if spine_dist(t.translation.x, t.translation.y) >= RIVER_KEEPOUT]
    if len(kept) != len(xforms):
        print(f"REACH_MARKER: {label} channel cull {len(xforms) - len(kept)} "
              f"plants out of the river (A6)")
    return kept


flora_n = 0
for i in range(12):                                  # the banks get their ferns DIRECTLY
    wpx, wpy = RIV["waypoints"][(i * 2) % len(RIV["waypoints"])]
    ang = random.uniform(0, 2.0 * math.pi)
    d = random.uniform(520.0, 900.0)
    fx, fy = wpx + math.cos(ang) * d, wpy + math.sin(ang) * d
    if math.hypot(fx - CX, fy - CY) < 3600.0 or near_river(fx, fy) < 430.0:
        continue
    # v5 A6: draws FIRST (stream identical), placement gated by the true spine.
    fyaw, fsc = random.uniform(0, 360), random.uniform(0.9, 1.6)
    if spine_dist(fx, fy) >= RIVER_KEEPOUT:
        place(FERN, unreal.Vector(fx, fy, ground_z(fx, fy)), f"VR_BankFern_{i}",
              yaw=fyaw, scale=fsc)
    flora_n += 1
attempts = 0
while flora_n < 30 and attempts < 300:               # then the free wilderness scatter
    attempts += 1
    fx = CX + random.uniform(-13500.0, 13500.0)
    fy = CY + random.uniform(-13500.0, 13500.0)
    if math.hypot(fx - CX, fy - CY) < 3600.0 or near_river(fx, fy) < 450.0:
        continue
    fyaw, fsc = random.uniform(0, 360), random.uniform(0.8, 1.6)   # v5 A6
    if spine_dist(fx, fy) >= RIVER_KEEPOUT:
        place(FERN, unreal.Vector(fx, fy, ground_z(fx, fy)), f"VR_Fern_{flora_n}",
              yaw=fyaw, scale=fsc)
    flora_n += 1
for i in range(18):
    fx = CX + random.uniform(-12000.0, 12000.0)
    fy = CY + random.uniform(-12000.0, 12000.0)
    if math.hypot(fx - CX, fy - CY) < 3600.0 or near_river(fx, fy) < 420.0:
        continue
    fyaw, fsc = random.uniform(0, 360), random.uniform(0.9, 1.5)   # v5 A6
    if spine_dist(fx, fy) >= RIVER_KEEPOUT:
        place(FLOWER, unreal.Vector(fx, fy, ground_z(fx, fy)), f"VR_Flower_{i}",
              yaw=fyaw, scale=fsc)
    flora_n += 1
for i in range(8):
    fz = random.uniform(300.0, 3000.0)
    fth = math.radians(random.uniform(60.0, 130.0))
    p = surface_point(fz, fth, out=-90.0)
    place(FUNGUS, p, f"VR_Fungus_{i}", yaw=math.degrees(fth) - 90.0,
          scale=random.uniform(0.55, 0.95))
    flora_n += 1
vine_i = 0
for s in F["branch_sockets"]:
    if s["arch"] != "b1" or vine_i >= 14:
        continue
    th = math.radians(s["theta_deg"])
    base = surface_point(s["z"], th, out=-250.0)
    for frac in (0.35, 0.65):
        if vine_i >= 14:
            break
        d = 7600.0 * s["scale"] * frac
        place(VINE, unreal.Vector(base.x + math.cos(th) * d, base.y + math.sin(th) * d,
                                  s["z"] + math.sin(math.radians(s["pitch_deg"])) * d
                                  - 360.0 * s["scale"]),
              f"VR_Vine_{vine_i}", yaw=random.uniform(0, 360),
              scale=random.uniform(0.8, 1.2), shadow=False)
        vine_i += 1
        flora_n += 1
for i, sname in enumerate(("bough_a", "bough_c", "bough_d", "bough_f", "bough_g",
                           "bough_i", "spiral_cb_in", "bough_mid_in", "bough_high_in",
                           "bough_j", "twig_a", "twig_c")):
    s = next(x for x in F["branch_sockets"] if x["name"] == sname)
    th = math.radians(s["theta_deg"])
    base = surface_point(s["z"], th, out=-250.0)
    place(FERN, unreal.Vector(base.x + math.cos(th) * 620.0 * s["scale"],
                              base.y + math.sin(th) * 620.0 * s["scale"],
                              s["z"] + 170.0 * s["scale"]),
          f"VR_BoughFern_{i}", yaw=random.uniform(0, 360), scale=0.6)
    flora_n += 1
print(f"REACH_MARKER: {flora_n} plants in the understory")

# ---- the chimney becomes a discovery (the dark room Adam found) ----
door_th = math.radians(CHIM["door_theta_deg"])
for i, (lth_deg, lr) in enumerate(((200.0, 900.0), (250.0, 1100.0), (300.0, 850.0))):
    lth = math.radians(lth_deg)
    lp = unreal.Vector(CX + lr * math.cos(lth), CY + lr * math.sin(lth), 0.0)
    lp.z = ground_z(lp.x, lp.y) + 4.0
    lant = eas.spawn_actor_from_class(cls("Lantern"), lp, rot(0))
    lant.set_actor_label(f"VR_ChimneyLantern_{i}")
    ls = lant.get_component_by_class(unreal.LightStateComponent)
    if ls:
        ls.set_editor_property("group_name", "VR_Chimney")
    if i == 1:
        try:
            lant.set_editor_property("is_checkpoint", True)
        except Exception:
            pass
    actor_count += 1
for i in range(4):
    sth = math.radians(160.0 + i * 50.0)
    p = surface_point(180.0, sth, out=-(300.0 * 1.6 - 30.0))
    place(kit("seep_card"), p, f"VR_ChimneySeep_{i}", yaw=math.degrees(sth) + 180.0,
          scale=1.6, shadow=False)
for i in range(5):
    sr = random.uniform(500.0, 2000.0)
    sth = random.uniform(0, 2.0 * math.pi)
    p = unreal.Vector(CX + sr * math.cos(sth), CY + sr * math.sin(sth), 0.0)
    p.z = ground_z(p.x, p.y) + 30.0
    place(SPHERE, p, f"VR_ChimneySeed_{i}", scale=0.5,
          material=mat("M_VR_VioletSeep"), shadow=False)
for i in range(6):
    d = 600.0 + i * 320.0
    p = unreal.Vector(CX + d * math.cos(door_th), CY + d * math.sin(door_th), 0.0)
    p.z = ground_z(p.x, p.y) + 150.0
    place(CYL, p, f"VR_ChimneyCrumb_{i}", scale=unreal.Vector(0.07, 0.07, 2.4),
          material=M_TUNSAP, shadow=False)
door_p = surface_point(90.0, door_th, out=60.0)
place(kit("knothole_arch"), door_p, "VR_Arch_ChimneyDoor",
      yaw=CHIM["door_theta_deg"] + 90.0, scale=1.1)
# v4: the door glows FROM INSIDE too — an interior arch + the morning light
# blade across the floor, so a hero in the dark room always sees the way out.
place(kit("knothole_arch"), surface_point(90.0, door_th, out=-160.0),
      "VR_Arch_ChimneyDoorIn", yaw=CHIM["door_theta_deg"] - 90.0, scale=1.0)
place(kit("water_sheet"), surface_point(150.0, door_th, out=-450.0),
      "VR_ChimneyDoorShaft", yaw=CHIM["door_theta_deg"] + 90.0, pitch=-24.0,
      scale=unreal.Vector(2.0, 1.0, 1.5), material=mat("M_VR_LightShaft"),
      shadow=False)
print("REACH_MARKER: the chimney is a discovery now (lit, seeded, and it has a door)")

# ==== THE UNDERSTORY: 500 walk-through plants in ~7 HISM actors (Round 3) ====
# A PRIVATE random stream (SEED+77): the seeded world never reshuffles, no
# matter how this section grows. No collision anywhere — Adam walks THROUGH,
# and the parting-brush WPO bends every frond around him.
UNDERSTORY = (("puffgrass_tuft", "M_VR_FrondGold", 140, 0.7, 1.3),
              ("star_rosette", "M_VR_FrondTeal", 70, 0.8, 1.4),
              ("paddle_broadleaf", "M_VR_Frond", 90, 0.8, 1.5),
              ("fiddlehead_curl", "M_VR_Frond", 60, 0.7, 1.3),
              ("seedpod_stalk", "M_VR_FrondGold", 45, 0.8, 1.3),
              ("reed_cluster", "M_VR_FrondGold", 55, 0.7, 1.2),
              ("bellflower_stalk", "M_VR_FrondCream", 40, 0.8, 1.2))
urand = random.Random(SEED + 77)
clusters = []
tries = 0
while len(clusters) < 40 and tries < 600:
    tries += 1
    ux = CX + urand.uniform(-13500.0, 13500.0)
    uy = CY + urand.uniform(-13500.0, 13500.0)
    if math.hypot(ux - CX, uy - CY) < 3400.0 or near_river(ux, uy) < 500.0:
        continue
    clusters.append((ux, uy))
for wpx, wpy in RIV["waypoints"]:                    # double density at the banks
    a2 = urand.uniform(0.0, 2.0 * math.pi)
    d2 = urand.uniform(700.0, 1600.0)
    clusters.append((wpx + math.cos(a2) * d2, wpy + math.sin(a2) * d2))
under_total = 0
for stem, matn, count, s_lo, s_hi in UNDERSTORY:
    ua = eas.spawn_actor_from_class(cls("UnderstoryPatch"),
                                    unreal.Vector(0.0, 0.0, 0.0), rot(0))
    ua.set_actor_label(f"VR_Under_{stem}")
    ua.set_editor_property("plant_mesh", kit(stem))
    ua.set_editor_property("plant_material", mat(matn))
    xforms = []
    guard = 0
    while len(xforms) < count and guard < count * 6:
        guard += 1
        cx2, cy2 = clusters[urand.randrange(len(clusters))]
        px2 = cx2 + urand.uniform(-900.0, 900.0)
        py2 = cy2 + urand.uniform(-900.0, 900.0)
        if math.hypot(px2 - CX, py2 - CY) < 3400.0 or near_river(px2, py2) < 430.0:
            continue
        xforms.append(unreal.Transform(
            unreal.Vector(px2, py2, ground_z(px2, py2)),
            unreal.Rotator(0.0, 0.0, urand.uniform(0.0, 360.0)),
            unreal.Vector(urand.uniform(s_lo, s_hi), urand.uniform(s_lo, s_hi),
                          urand.uniform(s_lo, s_hi))))
    xforms = cull_channel(xforms, f"Under_{stem}")   # v5 A6: post-filter only
    ua.set_editor_property("instances", xforms)
    under_total += len(xforms)
    actor_count += 1
print(f"REACH_MARKER: the understory floods in — {under_total} plants in "
      f"{len(UNDERSTORY)} HISM actors")

# ==== THE EXOTIC CLUSTERS: six Meshy statement plants at the hero spots ====
# Soft-guarded (the stage builds before the pack lands); scale normalized by
# MEASURED height (pool_entry law) so import-scale drift can't shrink them.
EXOTICS = (("giant_fiddlehead", 1300.0), ("bellbloom_cluster", 1100.0),
           ("paddleleaf_giant", 900.0), ("seedpod_bush", 700.0),
           ("reed_fan", 1200.0), ("mossbloom_boulder", 450.0))
exotic_pool = []
sms_exo = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
for stem, canon in EXOTICS:
    sm = EAL.load_asset(f"{KIT}/{stem}")
    if sm:
        # get_bounding_box reports SOURCE units — the import already normalized
        # via LOD build scale, so fold that in or we double-scale (the 25m
        # paddleleaf bug: canon/raw re-applied on top of an applied scale).
        b = sm.get_bounding_box()
        bsz = sms_exo.get_lod_build_settings(sm, 0).build_scale3d.z
        h = max((b.max.z - b.min.z) * bsz, 1.0)
        print(f"REACH_MARKER: exotic {stem} rendered_h {h:.0f} f {canon / h:.2f}")
        exotic_pool.append((stem, sm, canon / h, b.min.z * bsz))
exo_n = 0
if exotic_pool:
    EXO_SPOTS = []
    for i in range(4):                                 # Camp Roots approach
        EXO_SPOTS.append((-900.0 + i * 600.0, 3300.0 + (i % 2) * 500.0))
    for i, eth in enumerate((70.0, 150.0, 230.0, 320.0)):   # pool shore
        EXO_SPOTS.append((IMPACT[0] + 1250.0 * math.cos(math.radians(eth)),
                          IMPACT[1] + 1250.0 * math.sin(math.radians(eth))))
    for i in range(1, 5):                              # river bends, both banks
        wpx, wpy = RIV["waypoints"][i]
        for sgn in (1.0, -1.0):
            EXO_SPOTS.append((wpx + sgn * 780.0, wpy - sgn * 420.0))
    for i in range(4):                                 # spawn vista frame
        EXO_SPOTS.append((-1600.0 + i * 1050.0, 1100.0 + (i % 2) * 420.0))
    for i, (ex, ey) in enumerate(EXO_SPOTS):
        # v5 A6: exotics draw no RNG — the true-spine check is stream-safe here.
        if (near_river(ex, ey) < 460.0 or spine_dist(ex, ey) < 620.0
                or math.hypot(ex - CX, ey - CY) < 3400.0):
            continue
        stem, sm, f, minz = exotic_pool[i % len(exotic_pool)]
        fs = f * (0.85 + 0.3 * ((i * 7) % 5) / 4.0)
        place(sm, unreal.Vector(ex, ey, ground_z(ex, ey) - minz * fs),
              f"VR_Exotic_{stem}_{i}", yaw=float(i) * 47.0, scale=fs)
        exo_n += 1
    print(f"REACH_MARKER: {exo_n} exotic statement plants at the hero spots")
else:
    print("REACH_WARN: exotic pack not imported yet — clusters skipped this pass")

# ==== THE UNDERSTORY DOUBLING (v4): a SECOND pass, NEW private stream ====
# Audit law: raising counts in-place reshuffles species 2-7 (serial stream) —
# the world Adam already walked must not reshuffle. The append pass reuses the
# cluster list READ-ONLY (zero draws from SEED+77) and draws from SEED+177.
u2 = random.Random(SEED + 177)
under2_total = 0
for stem, matn, count, s_lo, s_hi in UNDERSTORY:
    ua = eas.spawn_actor_from_class(cls("UnderstoryPatch"),
                                    unreal.Vector(0.0, 0.0, 0.0), rot(0))
    ua.set_actor_label(f"VR_Under2_{stem}")
    ua.set_editor_property("plant_mesh", kit(stem))
    ua.set_editor_property("plant_material", mat(matn))
    xforms = []
    guard = 0
    while len(xforms) < count and guard < count * 6:
        guard += 1
        cx2, cy2 = clusters[u2.randrange(len(clusters))]
        px2 = cx2 + u2.uniform(-1100.0, 1100.0)
        py2 = cy2 + u2.uniform(-1100.0, 1100.0)
        if math.hypot(px2 - CX, py2 - CY) < 3400.0 or near_river(px2, py2) < 430.0:
            continue
        xforms.append(unreal.Transform(
            unreal.Vector(px2, py2, ground_z(px2, py2)),
            unreal.Rotator(0.0, 0.0, u2.uniform(0.0, 360.0)),
            unreal.Vector(u2.uniform(s_lo, s_hi), u2.uniform(s_lo, s_hi),
                          u2.uniform(s_lo, s_hi))))
    xforms = cull_channel(xforms, f"Under2_{stem}")  # v5 A6: post-filter only
    ua.set_editor_property("instances", xforms)
    under2_total += len(xforms)
    actor_count += 1
print(f"REACH_MARKER: the understory DOUBLES — +{under2_total} plants in "
      f"{len(UNDERSTORY)} more HISM actors")

# ==== THE FULL-FLOOR MEADOW (v4): grass + flowers blanket the whole floor ====
# Adam: "medium size grass and flower patches covering the entire forest
# floor." Own private stream (SEED+91); sway-only materials (no parting) per
# the 8GB audit; the tall understory keeps the parting brush where he walks.
mrand = random.Random(SEED + 91)
SPAN_F = F["floor"]["span"]
meadow_total = 0
for m_stem, m_mat, m_count, m_lo, m_hi in (("meadow_grass", "M_VR_GrassBlade", 9000, 0.9, 1.6),
                                           ("flower_patch", "M_VR_BloomPatch", 2600, 0.9, 1.4)):
    ma = eas.spawn_actor_from_class(cls("UnderstoryPatch"),
                                    unreal.Vector(0.0, 0.0, 0.0), rot(0))
    ma.set_actor_label(f"VR_Meadow_{m_stem}")
    ma.set_editor_property("plant_mesh", kit(m_stem))
    ma.set_editor_property("plant_material", mat(m_mat))
    xforms = []
    guard = 0
    while len(xforms) < m_count and guard < m_count * 5:
        guard += 1
        px2 = CX + mrand.uniform(-SPAN_F / 2.0 + 400.0, SPAN_F / 2.0 - 400.0)
        py2 = CY + mrand.uniform(-SPAN_F / 2.0 + 400.0, SPAN_F / 2.0 - 400.0)
        if math.hypot(px2 - CX, py2 - CY) < 3400.0 or near_river(px2, py2) < 420.0:
            continue
        xforms.append(unreal.Transform(
            unreal.Vector(px2, py2, ground_z(px2, py2)),
            unreal.Rotator(0.0, 0.0, mrand.uniform(0.0, 360.0)),
            unreal.Vector(mrand.uniform(m_lo, m_hi), mrand.uniform(m_lo, m_hi),
                          mrand.uniform(m_lo, m_hi))))
    xforms = cull_channel(xforms, f"Meadow_{m_stem}")  # v5 A6: post-filter only
    ma.set_editor_property("instances", xforms)
    meadow_total += len(xforms)
    actor_count += 1
print(f"REACH_MARKER: the meadow blankets the floor — {meadow_total} clumps in 2 HISM actors")

# ==== THE IVY (v4): leafy spirals wrapping the Heartwood, ~30% coverage ====
# World-anchored helical ribbons (pure math, zero draws) + gold blossom
# accents riding each spiral (teal lives in the ribbon material itself).
IVY = (("ivy_spiral_a", 0.0, 2.6, 300.0, 30500.0),
       ("ivy_spiral_b", 2.094, 2.1, 6000.0, 36500.0),
       ("ivy_spiral_c", 4.189, 2.35, 1500.0, 25500.0))
for ivn, _ith0, _iturns, _iz0, _iz1 in IVY:
    place(kit(ivn), unreal.Vector(0.0, 0.0, 0.0), f"VR_Ivy_{ivn[-1]}", shadow=False)
ivy_bloom = 0
for ivn, _ith0, _iturns, _iz0, _iz1 in IVY:
    for bt in (0.15, 0.35, 0.55, 0.75, 0.9):
        bz = _iz0 + (_iz1 - _iz0) * bt
        bth = _ith0 + 2.0 * math.pi * _iturns * bt
        br = field_r(bz, bth) + bark_noise(bz, bth) + 45.0
        place(SPHERE, unreal.Vector(CX + br * math.cos(bth),
                                    CY + br * math.sin(bth), bz),
              f"VR_IvyBloom_{ivy_bloom}", scale=0.55, material=M_BLOSSOM,
              shadow=False)
        ivy_bloom += 1
print(f"REACH_MARKER: the ivy wraps the Heartwood — 3 spirals, {ivy_bloom} gold blooms")

# ---------------- save law ----------------
print(f"REACH_MARKER: {actor_count} actors placed")
assert les.save_current_level(), "SAVE_REACH_FAILED"
print("REACH_MARKER: SAVE OK")
print("REACH_MARKER: DONE — the Heartwood stands in morning light")
