"""STAGE 1 — NEON DISTRICT: /Game/Maps/NeonCity

A futuristic city at night. Light rain. The low glow of neon signs.
Flow: rain alley spawn -> neon boulevard (~150m, platforming) -> back-alley
climb (~25m up) -> rooftop finale with skyline vista + goal beacon.

Design rules: NO moon — the city lights the city (MegaLights: every sign and
lamp casts shadows). Wet asphalt mirrors the neon via Lumen HWRT. Re-runnable:
CityKit meshes are used when present, skipped with a log when not (the level
builds fully procedural first; rerun after the Meshy kit imports).
"""
import random
from collections import Counter

import unreal

random.seed(414)

# Look-dev toggle: "boulevard" plants the spawn mid-street facing the lights
# (for tuning screenshots); "alley" is the SHIPPING spawn (the reveal moment).
SPAWN_MODE = "boulevard"

EAL = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# ---- THE SCRATCH DANCE (hardened: delete scratch first, assert everything) ----
if EAL.does_asset_exist("/Game/Maps/_Scratch"):
    EAL.delete_asset("/Game/Maps/_Scratch")
assert les.new_level("/Game/Maps/_Scratch"), "SCRATCH_LEVEL_FAILED"
if EAL.does_asset_exist("/Game/Maps/NeonCity"):
    assert EAL.delete_asset("/Game/Maps/NeonCity"), "DELETE_OLD_CITY_FAILED"
assert les.new_level("/Game/Maps/NeonCity"), "NEW_CITY_FAILED"

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
CYL = unreal.load_asset("/Engine/BasicShapes/Cylinder")

def mat(name):
    m = EAL.load_asset(f"/Game/Art/CityMat/{name}")
    if not m:
        unreal.log_warning(f"missing material {name}")
    return m

M_ASPHALT = mat("M_WetAsphalt")
M_SIDEWALK = mat("M_Concrete") or mat("M_Sidewalk")   # M1: gritty concrete walkways/fallbacks
M_HOLO = mat("M_HoloBillboard")
M_SIGNS = {s: mat(f"M_Sign_{s}") for s in
           ("kraken", "spark", "lumen", "moth", "warden", "glimmer", "district")}
M_WINDOWS = [mat(f"M_Windows_{v}") for v in ("a", "b", "c")]
M_COLORED = mat("M_IndustrialWindow") or M_WINDOWS[1]   # colored skin so no building reads grey
M_EMISSIVE = EAL.load_asset("/Game/Art/M_VertexLitEmissive")

placed = Counter()


def block(x, y, z, sx, sy, sz, label, material=None, hidden=False, rt=True):
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z))
    a.static_mesh_component.set_static_mesh(CUBE)
    a.set_actor_scale3d(unreal.Vector(sx / 100.0, sy / 100.0, sz / 100.0))
    if material:
        a.static_mesh_component.set_material(0, material)
    if hidden:
        a.set_actor_hidden_in_game(True)
    if not rt:  # decorative geometry stays OUT of the ray-tracing scene (budget)
        a.static_mesh_component.set_editor_property("visible_in_ray_tracing", False)
    a.set_actor_label(label)
    placed[label.split("_")[0]] += 1
    return a


def prop(kit, x, y, z, label, yaw=0.0, scale=1.0, kit_root="CityKit", ground=False):
    """Kit piece if imported; None (logged) if not — the level still builds.
    kit_root selects the asset folder (CityKit | CityTowerKit | ...). ground=True bbox-grounds
    the mesh (base at z) — needed for the centre-pivot Meshy towers in CityTowerKit."""
    sm = EAL.load_asset(f"/Game/Art/{kit_root}/{kit}/SM_{kit}")
    if not sm:
        unreal.log_warning(f"KIT_MISSING: {kit_root}/{kit} (skipped {label})")
        return None
    zz = z
    if ground:
        bb = sm.get_bounding_box()
        zz = z - bb.min.z * scale
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, zz))
    a.static_mesh_component.set_static_mesh(sm)
    a.set_actor_rotation(unreal.Rotator(0.0, 0.0, yaw), False)
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    a.set_actor_label(label)
    placed[kit] += 1
    return a


def glow(x, y, z, color, intensity=2200.0, radius=900.0, label="Neon"):
    li = eas.spawn_actor_from_class(unreal.PointLight, unreal.Vector(x, y, z))
    lc = li.light_component
    lc.set_light_color(color)
    lc.set_intensity(intensity * 0.22)  # NIGHT: glow wins by contrast, not wattage (toned down ~half)
    lc.set_editor_property("attenuation_radius", radius)
    lc.set_editor_property("cast_shadows", True)  # MegaLights eats this for breakfast
    try:  # keep the fog from drinking every light and glowing white
        lc.set_editor_property("volumetric_scattering_intensity", 0.05)
    except Exception as e:
        unreal.log_warning(f"volumetric scattering skip: {e}")
    li.set_actor_label(label)
    placed["Light"] += 1
    return li


SIGN_COLORS = {
    "kraken": unreal.LinearColor(1.0, 0.24, 0.70, 1.0),
    "spark": unreal.LinearColor(1.0, 0.58, 0.16, 1.0),
    "lumen": unreal.LinearColor(1.0, 0.75, 0.24, 1.0),
    "moth": unreal.LinearColor(0.70, 0.35, 1.0, 1.0),
    "warden": unreal.LinearColor(0.24, 0.86, 1.0, 1.0),
    "glimmer": unreal.LinearColor(0.27, 1.0, 0.78, 1.0),
    "district": unreal.LinearColor(0.35, 0.78, 1.0, 1.0),
}


def sign(brand, x, y, z, facing_south=True, w=420.0, label=None):
    """Thin emissive sign panel on a facade + its matching shadowed neon light."""
    h = w * 0.375  # texture is 1024x384
    a = block(x, y, z, w, 14.0, h, label or f"Sign_{brand}", material=M_SIGNS.get(brand))
    ly = y - 170.0 if facing_south else y + 170.0
    glow(x, ly, z, SIGN_COLORS[brand], intensity=2600.0, radius=1000.0, label=f"SignGlow_{brand}")
    return a


# ================================================================ geometry
# Boulevard along X: street y in [-600,600]; sidewalks to ±1000; facades at ±1250.
X0, X1 = -7000.0, 8000.0
STREET_LEN = X1 - X0
CX = (X0 + X1) / 2.0

block(CX, 0, -50, STREET_LEN + 3000, 1200, 100, "Street", material=M_ASPHALT)
block(CX, -810, -38, STREET_LEN + 3000, 420, 100, "Sidewalk_S", material=M_SIDEWALK)
block(CX, 810, -38, STREET_LEN + 3000, 420, 100, "Sidewalk_N", material=M_SIDEWALK)

# Alley: spawn pocket south of the boulevard at the west end.
block(-6600, -1700, -50, 800, 2200, 100, "AlleyFloor", material=M_ASPHALT)
block(-7050, -1700, 450, 100, 2200, 1000, "AlleyWall_W", material=M_SIDEWALK)
block(-6150, -1950, 450, 100, 1700, 1000, "AlleyWall_E", material=M_SIDEWALK)
block(-6600, -2850, 450, 1000, 100, 1000, "AlleyWall_S", material=M_SIDEWALK)
sign("kraken", -6580, -1110, 420, facing_south=True, w=360, label="Sign_AlleyKraken")
glow(-6600, -1500, 300, SIGN_COLORS["kraken"], 1800, 900, "AlleyGlow")

# Street-front buildings (procedural cubes now; Meshy shopfronts join on rerun).
SHOP_KITS = ["shopfront_a", "shopfront_b", "shopfront_c"]
shop_x = X0 + 600
side_flip = False
si = 0
brands = list(M_SIGNS.keys())
while shop_x < X1 - 600:
    y = 1450 if side_flip else -1450
    used = prop(SHOP_KITS[si % 3], shop_x, y, 0, f"Shop_{si:02d}", yaw=(-90 if side_flip else 90))
    if not used:
        block(shop_x, y, 500, 750, 420, 1000 + (si % 3) * 160,
              f"ShopBox_{si:02d}", material=M_COLORED)
    # Every shop wears a sign over the sidewalk.
    sign(brands[si % len(brands)], shop_x, 1180 if side_flip else -1180,
         420 + (si % 3) * 110, facing_south=side_flip,
         label=f"Sign_{si:02d}")
    shop_x += random.uniform(950, 1250)
    side_flip = not side_flip
    si += 1

# Towers rising behind the shops. Prefer the NEW colored Meshy towers (CityTowerKit); fall
# back to the older CityKit towers (recolored so they don't read grey); else a colored cube.
NEON_TOWERS = ["tower_neon_blue", "tower_neon_amber", "tower_neon_teal", "tower_megablock",
               "tower_pagoda_neon", "tower_billboard", "tower_spire_glass", "tower_block_lit"]
for i in range(14):
    tx = X0 + 400 + i * (STREET_LEN / 13.0)
    ty = 2700 if i % 2 == 0 else -2700                          # behind the shops, clear of signs
    yw = (-90 if ty > 0 else 90)
    tscale = 12.0 + (i % 4) * 2.5                               # ~2300..3700uu tall, height variety
    t = prop(NEON_TOWERS[i % len(NEON_TOWERS)], tx, ty, 0, f"Tower_{i:02d}", yaw=yw,
             kit_root="CityTowerKit", scale=tscale, ground=True)
    if t:
        t.static_mesh_component.set_editor_property("visible_in_ray_tracing", False)  # backdrop
    else:
        t = prop(["tower_a", "tower_b", "tower_c", "tower_d"][i % 4], tx, ty, 0,
                 f"Tower_{i:02d}", yaw=yw)
        if t:
            t.static_mesh_component.set_material(0, M_COLORED)   # recolor a grey CityKit tower
    if not t:
        block(tx, ty, 1500, 900, 800, 3000 + (i % 4) * 500,
              f"TowerBox_{i:02d}", material=M_COLORED)

# Street props + platforming chain down the boulevard.
chain = [
    ("dumpster", -4800, -350, 0, 0), ("crate_stack", -4100, 250, 0, 30),
    ("hover_car_a", -3300, -200, 18, 8), ("crate_stack", -2500, 320, 0, -20),
    ("hover_taxi", -1600, -300, 18, -6), ("dumpster", -700, 280, 0, 90),
    ("crate_stack", 200, -250, 0, 15), ("hover_car_b", 1100, 300, 18, 4),
    ("dumpster", 2000, -320, 0, 0), ("crate_stack", 2900, 220, 0, -35),
    ("hover_car_a", 3800, -250, 18, 172), ("crate_stack", 4700, 300, 0, 10),
    ("dumpster", 5600, -300, 0, 90), ("crate_stack", 6400, 250, 0, -15),
]
for i, (kit, x, y, z, yaw) in enumerate(chain):
    if not prop(kit, x, y, z, f"Chain_{i:02d}_{kit}", yaw=yaw):
        block(x, y, 90, 260, 200, 180, f"ChainBox_{i:02d}", material=M_SIDEWALK)

# Street furniture: lamps + vending machines + stands.
for i in range(8):
    lx = X0 + 1000 + i * 1850
    ly = -1050 if i % 2 == 0 else 1050
    if not prop("street_lamp", lx, ly, 0, f"Lamp_{i}", yaw=(0 if ly < 0 else 180)):
        a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(lx, ly, 220))
        a.static_mesh_component.set_static_mesh(CYL)
        a.set_actor_scale3d(unreal.Vector(0.16, 0.16, 4.4))
        a.static_mesh_component.set_material(0, M_SIDEWALK)
        a.set_actor_label(f"LampPole_{i}")
    # Adam round 2: white street light cut 65% — pools of lamplight, not floodlight.
    glow(lx, ly * 0.86, 470, unreal.LinearColor(1.0, 0.92, 0.78, 1.0), 1100, 1100, f"LampGlow_{i}")
prop("noodle_stand", -2200, -950, 0, "NoodleStand", yaw=25)
prop("street_kiosk", 3200, 980, 0, "Kiosk", yaw=200)
prop("vending_machine_a", 600, -1150, 0, "Vend_A", yaw=0)
prop("vending_machine_b", 4400, 1150, 0, "Vend_B", yaw=180)
prop("monorail_pillar", -500, 0, 0, "Monorail_1")
prop("monorail_pillar", 4500, 0, 0, "Monorail_2")

# Mid-boulevard holo billboard on a tower face.
block(1500, 2080, 1500, 900, 20, 340, "Holo_Mid", material=M_HOLO)
glow(1500, 1800, 1500, SIGN_COLORS["district"], 4200, 1600, "HoloGlow_Mid")

# ============================================================== east end
# The old rooftop climb + GoalBeacon were REMOVED here: World 1's finale is now the
# LANTERN CLIMB canyon, appended east of the boulevard by merge_world1.py (the canyon
# crown's First Lantern is the single world goal). The boulevard simply ends here and
# hands off to the canyon mouth via the merge's transition corridor.

# ============================================================ backdrop ring
for i in range(44):
    ang = i * (360.0 / 44.0)
    import math as _m
    bx = CX + _m.cos(_m.radians(ang)) * random.uniform(11500, 16000)
    by = _m.sin(_m.radians(ang)) * random.uniform(5200, 9000)
    h = random.uniform(2400, 7200)
    block(bx, by, h / 2.0, random.uniform(700, 1500), random.uniform(700, 1500), h,
          f"Skyline_{i:02d}", material=M_COLORED, rt=False)

# Boundary walls (invisible) around the playable street.
for x, y, sx, sy in ((CX, -3200, STREET_LEN + 4000, 150), (CX, 3200, STREET_LEN + 4000, 150),
                     (X0 - 1800, 0, 150, 7000), (12600, 0, 150, 7000)):
    block(x, y, 1800, sx, sy, 3600, "Boundary", material=None, hidden=True, rt=False)

# ================================================================ atmosphere
# F4 (Adam): kill the blue. The drop-offs used to show UE's default blue SkyAtmosphere + a
# blue-tinted fog. We remove the SkyAtmosphere entirely, drop the fog to near-nothing and make
# it near-black, and wrap the whole world in a huge inverted STAR-DOME sphere (M_StarNebula) so
# looking out — or DOWN into a drop-off — reads as deep starry space: "the city floating in space."
fog = eas.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0))
fc = fog.component
fc.set_editor_property("enable_volumetric_fog", True)
fc.set_editor_property("fog_density", 0.004)                 # was 0.022 — let the stars read
fc.set_editor_property("fog_inscattering_luminance", unreal.LinearColor(0.004, 0.004, 0.010, 1.0))
fog.set_actor_label("SpaceFog")

# NO SkyAtmosphere (that was the blue). A dim SkyLight only, so geometry isn't pure black.
skylight = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 800))
# real_time_capture OFF: the star sky is static, so a one-time CapturedScene grab of the IsSky
# StarDome is enough. Real-time re-capture cost ~3 GB/frame (6.4 GB peak) AND demanded a sky
# (the "needs a SkyAtmosphere/IsSky" error/loop). Off = ~3.2 GB peak + no error.
skylight.light_component.set_editor_property("real_time_capture", False)
skylight.light_component.set_intensity(0.015)  # near-black space — neon carries the scene
skylight.set_actor_label("SkyLight")

# The star-dome: engine Sphere, huge, two-sided M_StarNebula so it renders from the inside. Big
# enough to enclose both the boulevard and the merged canyon (centred between them).
star_sphere = EAL.load_asset("/Engine/BasicShapes/Sphere")
M_STARS = mat("M_StarNebula")
if star_sphere and M_STARS:
    dome = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(6000, 0, 2000))
    dome.static_mesh_component.set_static_mesh(star_sphere)
    dome.set_actor_scale3d(unreal.Vector(1200.0, 1200.0, 1200.0))  # ~60000uu radius — encloses W1
    dome.static_mesh_component.set_material(0, M_STARS)
    dome.static_mesh_component.set_editor_property("cast_shadow", False)
    dome.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    try:
        dome.static_mesh_component.set_editor_property("visible_in_ray_tracing", False)
    except Exception:
        pass
    dome.set_actor_label("StarDome")
else:
    unreal.log_warning("STARDOME_SKIP: missing /Engine/BasicShapes/Sphere or M_StarNebula")

ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
ppv.set_editor_property("unbound", True)
pps = ppv.get_editor_property("settings")
def pp(prop_name, value):
    try:
        pps.set_editor_property(f"override_{prop_name}", True)
        pps.set_editor_property(prop_name, value)
    except Exception as e:
        unreal.log_warning(f"pp skip {prop_name}: {e}")
pp("bloom_method", unreal.BloomMethod.BM_FFT)
pp("bloom_intensity", 0.5)      # was 1.15 — the over-bright lights were blooming into glare
pp("bloom_threshold", 1.6)
pp("auto_exposure_min_brightness", -1.6)
pp("auto_exposure_max_brightness", -1.6)
pp("film_grain_intensity", 0.12)
pp("vignette_intensity", 0.35)
pp("scene_fringe_intensity", 0.3)
pp("local_exposure_shadow_contrast_scale", 0.8)
pp("color_saturation", unreal.Vector4(1.05, 1.05, 1.05, 1.0))
pp("color_gain_shadows", unreal.Vector4(1.03, 0.95, 1.16, 1.0))    # violet shadows
pp("color_gain_highlights", unreal.Vector4(0.94, 1.04, 1.16, 1.0)) # cyan highlights
ppv.set_editor_property("settings", pps)
ppv.set_actor_label("CityPost")

# Rain.
rain_cls = unreal.load_class(None, "/Script/SuperClaudeBros2.RainCurtain")
rain = eas.spawn_actor_from_class(rain_cls, unreal.Vector(-6600, -1700, 400))
rain.set_actor_label("Rain")

# Glimmers on the sidewalks.
glimmer_cls = unreal.load_class(None, "/Script/SuperClaudeBros2.GlimmerEnemy")
for i, (gx, gy) in enumerate(((-3600, -820), (-1200, 830), (1700, -830), (3900, 820), (6100, -820))):
    g = eas.spawn_actor_from_class(glimmer_cls, unreal.Vector(gx, gy, 60))
    g.set_actor_label(f"Glimmer_{i+1}")
    placed["Glimmer"] += 1

# The visitor.
if SPAWN_MODE == "boulevard":
    start = eas.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(-4500, 0, 120))
    start.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), False)   # face east, down the lights
else:
    start = eas.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(-6600, -2500, 120))
    start.set_actor_rotation(unreal.Rotator(0.0, 0.0, 90.0), False)  # face +Y, out of the alley
start.set_actor_label("PlayerStart")

unreal.log(f"NEON_PLACED: {dict(placed)}")
saved = les.save_current_level()
print(f"SAVE_RESULT: {saved}")
assert saved, "CITY_SAVE_FAILED"
if EAL.does_asset_exist("/Game/Maps/_Scratch"):
    EAL.delete_asset("/Game/Maps/_Scratch")
print("NEON_CITY_BUILT: /Game/Maps/NeonCity")
