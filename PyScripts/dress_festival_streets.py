"""Dress NeonCity into the warm-cyberpunk FESTIVAL STREETS (World 1 / ANTHROPICA).

v2 — addresses Adam's playtest notes: props GROUNDED on the floor (base at z=0 via each
mesh's bounding box, not sunk), placed ON the walkable path (sidewalks/over the street,
never in the void), oriented to face the street; a continuous GROUND plane + canyon
building-WALLS with collision kill the cliff edges and bound the player; props pulled
OFF ray-tracing to fix the RT memory budget. Idempotent (clears prior Fest_ actors).

Geometry it builds on: walkable surface z=0; street y in [-600,600] + sidewalks to
+-1020; spawn at (-4500,0) facing +X; climb at x~7600 -> rooftop ROOF_Z=2500.
"""
import unreal

EAL = unreal.EditorAssetLibrary
ELSS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

assert unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity"), "LOAD_NEONCITY_FAILED"

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
M_ASPHALT = EAL.load_asset("/Game/Art/CityMat/M_WetAsphalt")
M_WALL = EAL.load_asset("/Game/Art/CityMat/M_Windows_b") or EAL.load_asset("/Game/Art/CityMat/M_Sidewalk")
ROOF_Z = 2500.0
FLOOR_Z = 0.0

removed = 0
for a in eas.get_all_level_actors():
    try:
        if a.get_actor_label().startswith("Fest_"):
            eas.destroy_actor(a); removed += 1
    except Exception:
        pass
print(f"CLEARED {removed} prior Fest_ actors")

LANTERN_CLASS = unreal.load_class(None, "/Script/SuperClaudeBros2.Lantern")
NETMGR_CLASS = unreal.load_class(None, "/Script/SuperClaudeBros2.LightNetworkManager")
placed = {"prop": 0, "lantern": 0, "wall": 0}


def setp(actor, names, value):
    for nm in names:
        try:
            actor.set_editor_property(nm, value); return True
        except Exception:
            continue
    return False


def fprop(name, x, y, scale, yaw=0.0, z=None, rt=False):
    """Grounded by default (base on FLOOR_Z); pass z to override (hanging/rooftop)."""
    sm = EAL.load_asset(f"/Game/Art/FestivalKit/{name}/SM_{name}")
    if not sm:
        unreal.log_warning(f"FESTIVAL_MISSING: {name}"); return None
    bb = sm.get_bounding_box()
    zz = (FLOOR_Z - bb.min.z * scale) if z is None else z
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, zz),
                                   unreal.Rotator(0.0, 0.0, yaw))
    a.static_mesh_component.set_static_mesh(sm)
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    if not rt:
        a.static_mesh_component.set_editor_property("visible_in_ray_tracing", False)
    a.set_actor_label(f"Fest_{name}_{placed['prop']}")
    placed["prop"] += 1
    return a


def wall(x, y, z, sx, sy, sz, label, material=M_WALL, hidden=False):
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z))
    a.static_mesh_component.set_static_mesh(CUBE)
    a.set_actor_scale3d(unreal.Vector(sx / 100.0, sy / 100.0, sz / 100.0))
    if material:
        a.static_mesh_component.set_material(0, material)
    a.static_mesh_component.set_editor_property("visible_in_ray_tracing", False)
    if hidden:
        a.set_actor_hidden_in_game(True)
    a.set_actor_label(f"Fest_{label}")
    placed["wall"] += 1
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
    placed["lantern"] += 1
    return a


# ===================== BOUNDARIES: ground plane + canyon walls (kill the cliffs) =====================
# A continuous city ground under the whole play area — no void to fall into.
wall(2000, 0, -100, 17000, 5200, 200, "Ground", material=M_ASPHALT)
# Solid canyon building-walls flush along both sides of the boulevard (collision + occlude
# the far void). The detailed storefront props sit in FRONT of these for richness.
wall(500, 1350, 1500, 15500, 200, 3000, "CanyonWall_N")
wall(500, -1350, 1500, 15500, 200, 3000, "CanyonWall_S")
# West end-cap behind the spawn so you can't walk back off the world.
wall(-7200, 0, 1500, 200, 2900, 3000, "EndCap_W")

# ===================== THE WARM FESTIVAL LAYER (grounded, on-path) =====================
# Grand entrance torii + arches SPANNING the street (you walk through along +X).
fprop("neon_torii", -3700, 0, 3.4, yaw=90)
fprop("festival_arch", -1400, 0, 4.0, yaw=90)
fprop("festival_arch", 2400, 0, 4.0, yaw=90)
fprop("festival_arch", 5600, 0, 4.0, yaw=90)

# Food stalls / shrines / planters on the SOUTH sidewalk (y=-780), facing the street (+Y).
fprop("ramen_cart", -3000, -780, 1.5, yaw=0)
fprop("produce_stall", -300, -780, 1.5, yaw=0)
fprop("grill_barrel", 1700, -800, 1.4, yaw=0)
fprop("tea_stall", 4200, -780, 1.6, yaw=0)
fprop("brazier_bowl", -1700, -820, 1.2)
fprop("flower_planter", 900, -830, 1.2)
fprop("market_crates", 3000, -830, 1.4)

# NORTH sidewalk (y=+780), facing the street (-Y).
fprop("street_shrine", -2400, 780, 1.4, yaw=180)
fprop("produce_stall", 600, 780, 1.5, yaw=180)
fprop("brazier_bowl", -600, 820, 1.2)
fprop("flower_planter", 2200, 830, 1.2)
fprop("market_crates", 4600, 830, 1.4)
fprop("conduit_machinery", 6200, 860, 1.4)

# Lantern poles alternating along both edges.
px = -3000
while px <= 6800:
    fprop("lantern_pole", px, -960, 2.0)
    fprop("lantern_pole", px + 800, 960, 2.0)
    px += 1700

# Hanging lantern strings + garlands strung OVERHEAD across the street (clear of head height).
for hx in (-2000, 800, 3600, 6000):
    fprop("festival_lanterns", hx, 0, 2.4, z=560)
for hx in (-700, 2100, 4800):
    fprop("paper_garland", hx, 0, 2.2, z=600)

# ===================== THE COLD CYBERPUNK EDGE (behind the wall line / on facades) =====================
fprop("holo_billboard", 1500, 1700, 6.0, yaw=-90, z=1500)       # koi-dragon hologram up high
fprop("mega_sign_tower", -1800, 1650, 5.0)
fprop("mega_sign_tower", 5400, -1650, 5.0)
fprop("neon_storefront", -1000, 1280, 3.0, yaw=180)            # storefront detail on the wall
fprop("neon_storefront", 2800, -1280, 3.0, yaw=0)
fprop("neon_storefront", 5800, 1280, 3.0, yaw=180)
fprop("steam_vent", -2100, -400, 1.5)
fprop("steam_vent", 3300, 400, 1.5)
fprop("cable_bundle", 200, 1320, 1.6, z=700)                   # strung high between buildings
fprop("cable_bundle", 4400, -1320, 1.6, z=700)

# ===================== THE LANTERNS (the interactive heart) =====================
# Warm ambient lanterns lining the route (lit; the festival glow).
ax = -3400
while ax <= 6800:
    lantern(ax, 700, f"amb_{ax}_L", relight_radius=300.0)
    lantern(ax + 850, -700, f"amb_{ax}_R", relight_radius=300.0)
    ax += 1700

# Dark CHECKPOINT lamps along the route — the maintenance worker relights them (hold E).
for i, cx in enumerate((-2400, 800, 3600, 6200)):
    lantern(cx, 0, f"cp_{i}", checkpoint=True, dark=True, relight_radius=0.0, auto=0.0,
            scale=1.1, intensity=1400.0, radius=640.0)

# THE FIRST LANTERN — the dark GOAL at the city's crown (grounded on the roof).
fprop("first_lantern", 11000, 0, 11.0, z=ROOF_Z)
lantern(11000, 0, "FIRST", z=ROOF_Z + 40, goal=True, dark=True, relight_radius=0.0, auto=0.0,
        scale=3.0, intensity=6000.0, radius=2600.0)

# ===================== THE LIGHT-NETWORK MANAGER =====================
mgr = eas.spawn_actor_from_class(NETMGR_CLASS, unreal.Vector(1500, 0, 800))
mgr.set_actor_label("Fest_LightNetworkManager")

saved = ELSS.save_current_level()
print(f"FEST_DRESS_DONE: {placed['prop']} props, {placed['lantern']} lanterns, "
      f"{placed['wall']} walls, mgr=1, saved={saved}")
