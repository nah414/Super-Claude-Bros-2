"""Dress NeonCity into a COHERENT warm-cyberpunk FESTIVAL STREET (World 1 / ANTHROPICA).

v3 — Adam's "make it make sense / I can't cross / add enterable buildings" notes:
 * The central ROAD stays CLEAR (you walk straight down it). Market stalls sit in
   ORGANIZED ROWS on the sidewalks facing the road; gateways span overhead at intervals.
 * Decorative props are NO-COLLISION, so nothing blocks the path (only buildings/walls/
   ground are solid).
 * ENTERABLE BUILDINGS line both sides — shells with a doorway + interior floor/walls +
   interior dressing, the explorable boundary (the Call-of-Duty-street ask).
 * The old random cold-city clutter (dumpsters / untextured hover-cars / sparse shops) is
   cleared so everything reads at the festival-prop bar.
Grounding: walkable surface z=0; spawn (-4500,0) facing +X; climb x~7600 -> roof 2500.
Idempotent (clears prior Fest_ + the clutter labels).
"""
import unreal

EAL = unreal.EditorAssetLibrary
ELSS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

assert unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity"), "LOAD_FAILED"

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
M_ASPHALT = EAL.load_asset("/Game/Art/CityMat/M_WetAsphalt")
M_BUILD = EAL.load_asset("/Game/Art/CityMat/M_IndustrialWindow") or EAL.load_asset("/Game/Art/CityMat/M_Windows_b")
M_FLOOR = EAL.load_asset("/Game/Art/CityMat/M_Concrete") or EAL.load_asset("/Game/Art/CityMat/M_Sidewalk")
ROOF_Z = 2500.0

# ---- clear prior dressing + the clashing cold-city clutter ----
# NOTE: "ChainBox" must be listed explicitly — "Chain_" does NOT match "ChainBox_NN"
# (the underscore differs), so the white fallback boxes for un-imported hover-car /
# dumpster / crate meshes (build_neon_city.py:180) otherwise survive as street clutter.
CLEAR_PREFIXES = ("Fest_", "Chain_", "ChainBox", "Shop_", "ShopBox_", "Vend_",
                  "NoodleStand", "Kiosk", "Monorail", "Holo_Mid")
removed = 0
for a in eas.get_all_level_actors():
    try:
        lbl = a.get_actor_label()
        if any(lbl.startswith(p) for p in CLEAR_PREFIXES):
            eas.destroy_actor(a); removed += 1
    except Exception:
        pass
print(f"CLEARED {removed} actors (prior dressing + clutter)")

LANTERN_CLASS = unreal.load_class(None, "/Script/SuperClaudeBros2.Lantern")
NETMGR_CLASS = unreal.load_class(None, "/Script/SuperClaudeBros2.LightNetworkManager")
P = {"prop": 0, "wall": 0, "lantern": 0, "bldg": 0}


def setp(actor, names, value):
    for nm in names:
        try:
            actor.set_editor_property(nm, value); return True
        except Exception:
            continue
    return False


def wall(x, y, z, sx, sy, sz, label, material=M_BUILD, solid=True):
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z))
    a.static_mesh_component.set_static_mesh(CUBE)
    a.set_actor_scale3d(unreal.Vector(sx / 100.0, sy / 100.0, sz / 100.0))
    if material:
        a.static_mesh_component.set_material(0, material)
    a.static_mesh_component.set_editor_property("visible_in_ray_tracing", False)
    if not solid:
        a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    a.set_actor_label(f"Fest_{label}")
    P["wall"] += 1
    return a


def fprop(name, x, y, scale, yaw=0.0, z=None, solid=False):
    """Grounded by bbox (base on z=0) unless z given. Decorative = NO collision by default
    so it never blocks the path; the player walks through/under it."""
    sm = EAL.load_asset(f"/Game/Art/FestivalKit/{name}/SM_{name}")
    if not sm:
        unreal.log_warning(f"MISSING {name}"); return None
    bb = sm.get_bounding_box()
    zz = (0.0 - bb.min.z * scale) if z is None else z
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, zz),
                                   unreal.Rotator(0.0, 0.0, yaw))
    a.static_mesh_component.set_static_mesh(sm)
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    a.static_mesh_component.set_editor_property("visible_in_ray_tracing", False)
    if not solid:
        a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    a.set_actor_label(f"Fest_{name}_{P['prop']}")
    P["prop"] += 1
    return a


def lantern(x, y, label, *, z=0.0, checkpoint=False, goal=False, dark=False,
            relight_radius=300.0, auto=9.0, scale=1.0, intensity=900.0, radius=520.0):
    a = eas.spawn_actor_from_class(LANTERN_CLASS, unreal.Vector(x, y, z))
    setp(a, ["lit_intensity", "LitIntensity"], intensity)
    setp(a, ["lit_radius", "LitRadius"], radius)
    setp(a, ["relight_by_hero_radius", "RelightByHeroRadius"], relight_radius)
    setp(a, ["auto_relight_seconds", "AutoRelightSeconds"], auto)
    setp(a, ["is_checkpoint", "b_is_checkpoint", "bIsCheckpoint"], checkpoint)
    setp(a, ["is_world_goal", "b_is_world_goal", "bIsWorldGoal"], goal)
    setp(a, ["start_dark", "b_start_dark", "bStartDark"], dark)
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    a.set_actor_label(f"Fest_Lantern_{label}")
    P["lantern"] += 1
    return a


def building(cx, front_y, w, depth, h, label, door=True, dress=True):
    """An enterable building: floor + roof + back/side walls + a front wall with a DOOR
    gap. Interior gets a warm lantern + crates so entering is rewarding."""
    sgn = 1.0 if front_y > 0 else -1.0
    back_y = front_y + sgn * depth
    cy = (front_y + back_y) / 2.0
    T = 40.0
    wall(cx, cy, 4, w, depth, 8, f"{label}_floor", material=M_FLOOR)
    wall(cx, cy, h, w, depth, 30, f"{label}_roof")
    wall(cx, back_y, h / 2, w, T, h, f"{label}_back")
    wall(cx - w / 2, cy, h / 2, T, depth, h, f"{label}_sL")
    wall(cx + w / 2, cy, h / 2, T, depth, h, f"{label}_sR")
    if door:
        dw, dh = 380.0, 520.0
        seg = (w - dw) / 2.0
        wall(cx - (dw / 2 + seg / 2), front_y, h / 2, seg, T, h, f"{label}_fL")
        wall(cx + (dw / 2 + seg / 2), front_y, h / 2, seg, T, h, f"{label}_fR")
        wall(cx, front_y, (dh + h) / 2, dw, T, h - dh, f"{label}_lintel")  # wall over the door
        if dress:
            lantern(cx, cy + sgn * 60, f"in_{label}", relight_radius=350.0, scale=0.9)
            fprop("market_crates", cx - w * 0.28, cy, 1.1)
            fprop("market_crates", cx + w * 0.26, cy + sgn * 120, 0.9, yaw=40)
    else:
        wall(cx, front_y, h / 2, w, T, h, f"{label}_front")
    P["bldg"] += 1


# ============================ ENTERABLE BUILDINGS line both sides ============================
# Continuous row, front face at y=+-1150, depth 900 (toward the towers). Alternating
# enterable (door) / solid, so the street is a believable canyon of shops you can enter.
BX0, BSTEP, BW = -4600.0, 1560.0, 1500.0
for i in range(8):
    bx = BX0 + i * BSTEP
    building(bx, 1150, BW, 900, 1700 + (i % 3) * 120, f"BldgN_{i}", door=(i % 2 == 0))
    building(bx + BSTEP / 2, -1150, BW, 900, 1700 + (i % 2) * 160, f"BldgS_{i}", door=(i % 2 == 1))

# A continuous low ground plane under it all (no void / no cliffs anywhere on the path).
wall(1000, 0, -100, 16000, 5200, 200, "Ground", material=M_ASPHALT)
# West end-cap behind spawn.
wall(-5500, 0, 900, 200, 2600, 1800, "EndCap_W")

# ============================ ORGANIZED NIGHT-MARKET (clear central road) ============================
# Sidewalk stalls in an even row on each side (y=+-820), facing the road. Decorative.
SOUTH_STALLS = [("ramen_cart", -3400, 0), ("grill_barrel", -1400, 0), ("produce_stall", 700, 0),
                ("tea_stall", 2900, 0), ("ramen_cart", 5100, 0)]
NORTH_STALLS = [("produce_stall", -2400, 180), ("street_shrine", -300, 180), ("tea_stall", 1800, 180),
                ("grill_barrel", 4000, 180), ("produce_stall", 6000, 180)]
for name, x, yaw in SOUTH_STALLS:
    fprop(name, x, -820, 1.5, yaw=yaw)
for name, x, yaw in NORTH_STALLS:
    fprop(name, x, 820, 1.5, yaw=yaw)

# Braziers + planters tucked between stalls (warm pools of light), even spacing.
for x in range(-4000, 6500, 1300):
    side = -870 if (x // 1300) % 2 == 0 else 870
    fprop("brazier_bowl" if (x // 1300) % 2 == 0 else "flower_planter", x, side, 1.15)

# Lantern poles evenly along both kerbs.
for x in range(-4200, 6800, 1600):
    fprop("lantern_pole", x, -1000, 1.9)
    fprop("lantern_pole", x + 800, 1000, 1.9)

# ============================ GATEWAYS over the clear road + overhead strings ============================
fprop("neon_torii", -4200, 0, 3.4, yaw=90)          # the grand entrance, just ahead of spawn
for ax in (-1500, 2000, 5500):
    fprop("festival_arch", ax, 0, 4.0, yaw=90)        # span the road; you walk through
for hx in (-2800, 300, 3700, 6300):
    fprop("festival_lanterns", hx, 0, 2.4, z=620)     # strung high over the road
for hx in (-700, 4600):
    fprop("paper_garland", hx, 0, 2.2, z=660)

# A couple of edgy skyline pieces well above/behind the buildings.
fprop("holo_billboard", 1500, 1900, 6.0, yaw=-90, z=1700)
fprop("mega_sign_tower", -2000, 1850, 5.0)
fprop("mega_sign_tower", 5600, -1850, 5.0)

# ============================ THE INTERACTIVE LANTERNS ============================
# Warm ambient lanterns along the kerbs (lit).
for x in range(-3600, 6400, 1700):
    lantern(x, 640, f"amb_{x}_L")
    lantern(x + 850, -640, f"amb_{x}_R")

# Dark CHECKPOINT lamps at the road edges near each gateway — relight them (hold E).
for i, cx in enumerate((-2600, 700, 3500, 6000)):
    lantern(cx, 560 if i % 2 else -560, f"cp_{i}", checkpoint=True, dark=True,
            relight_radius=0.0, auto=0.0, scale=1.1, intensity=1500.0, radius=680.0)

# NOTE: the rooftop First-Lantern GOAL + the festival LightNetworkManager were REMOVED here.
# World 1's single goal is now the First Lantern at the canyon crown (built by the canyon merge,
# merge_world1.py), and the canyon's LC_LightNetworkManager is the one light hub. The street
# keeps its ambient + dark checkpoint lanterns above.

saved = ELSS.save_current_level()
print(f"FEST_DRESS_DONE: {P['prop']} props, {P['bldg']} buildings, {P['wall']} walls, "
      f"{P['lantern']} lanterns, saved={saved}")
