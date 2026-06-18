"""M3 — COMBINE World 1 into one map: append the LANTERN CLIMB canyon onto the east end of
the festival street, in /Game/Maps/NeonCity. Run AFTER build_neon_city.py + dress_festival_streets.py.

Flow of the combined World 1: walk the warm festival boulevard (west->east) -> through a
doorway in the canyon's west cliff -> climb the switchback + spire to relight the First Lantern
at the crown (the single world goal). Idempotent (clears stale old-finale + any prior merge).
"""
import builtins
import os
import sys

builtins._LC_SUPPRESS_AUTORUN = True          # import the canyon builder without auto-running it
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unreal
import build_world1_lantern_climb as lc

EAL = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

assert unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity"), "LOAD_NEONCITY_FAILED"

# ---- clear stale old-finale (if a pre-strip build is loaded) + any prior canyon merge ----
CLEAR = ("Ledge_", "ClimbWall_", "ClimbSign_", "Fire_", "Roof", "GoalBeacon", "GoalShaft",
         "GoalGlow", "Fest_Lantern_FIRST", "Fest_LightNetworkManager", "LC_", "Seam_")
removed = 0
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if any(lbl.startswith(p) for p in CLEAR):
        eas.destroy_actor(a)
        removed += 1
print(f"MERGE_CLEARED: {removed}")

# ---- append the canyon east of the boulevard, floor at street level ----
# Street ground reaches ~world x9500 (top z0). Canyon floor west edge = OX-2600; set OX so it
# meets the street; OZ shifts canyon FLOOR_TOP(350) to street z0. Entry doorway aligns with the
# boulevard centre (canyon-local y=0).
OX, OY, OZ = 12100.0, 0.0, -350.0
lc.build_canyon(origin=(OX, OY, OZ), into_existing=True, spawn=False, add_atmosphere=False,
                save=False, entry_gap_y=0.0)

# ---- seam: a continuous ground strip through the doorway + warm lanterns framing the entrance ----
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
M_ASPHALT = EAL.load_asset("/Game/Art/CityMat/M_WetAsphalt")

a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(9650, 0, -50))
a.static_mesh_component.set_static_mesh(CUBE)
a.set_actor_scale3d(unreal.Vector(12.0, 16.0, 1.0))      # 1200 x 1600 x 100 ground patch over the seam
if M_ASPHALT:
    a.static_mesh_component.set_material(0, M_ASPHALT)
a.static_mesh_component.set_editor_property("visible_in_ray_tracing", False)
a.set_actor_label("Seam_Floor")

# warm lanterns at the doorway (world coords -> reset the canyon offset to 0 first)
lc.OX = lc.OY = lc.OZ = 0.0
gx = OX - 2300                                            # world X of the west cliff / doorway ~9800
lc.lantern(gx - 120, -380, "seam_L", z=40, intensity=1500.0, radius=720.0)
lc.lantern(gx - 120, 380, "seam_R", z=40, intensity=1500.0, radius=720.0)

# F3 (Adam, updated): the street->canyon seam pile is now SOLID and CLIMBABLE — the hero climbs
# OVER it into the staircase. Mesh collision is restored asset-level by restore_rubble_collision.py
# (a BOX, so it has clean vertical faces the climb trace grabs + a flat top the hero walks across to
# drop down the canyon side). Here we place it SOLID + tag it "Climbable". Both piles are taller than
# the ~242uu max jump, so the hero MUST climb. (Component flags don't persist; the asset box is the
# real collision — the tag + profile here are belt-and-suspenders.)
RUBBLE_ROOT = "/Game/Art/CityTowerKit"
def seam_rubble(kit, x, y, scale, yaw, label):
    sm = EAL.load_asset(f"{RUBBLE_ROOT}/{kit}/SM_{kit}")
    if not sm:
        unreal.log_warning(f"RUBBLE_MISSING: {kit} (seam stays open)")
        return
    bb = sm.get_bounding_box()
    rb = eas.spawn_actor_from_class(unreal.StaticMeshActor,
                                    unreal.Vector(x, y, -bb.min.z * scale))
    rb.static_mesh_component.set_static_mesh(sm)
    rb.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    rb.set_actor_rotation(unreal.Rotator(0.0, 0.0, yaw), False)
    rb.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    rb.static_mesh_component.set_collision_profile_name("BlockAll")
    rb.static_mesh_component.set_editor_property("visible_in_ray_tracing", False)
    rb.set_editor_property("tags", [unreal.Name("Climbable")])
    rb.set_actor_label(label)

seam_rubble("rubble_pile", gx - 60, -240, 3.2, 15.0, "Seam_Rubble_A")    # ~272uu: must-climb, walk-over top
seam_rubble("debris_chunks", gx - 30, 300, 3.0, -40.0, "Seam_Rubble_B")  # ~255uu

# ===================== CANYON (4) + SPIRAL-STAIRCASE (15) ENEMIES = 19 (anti-lag + colored) =====
# The 21 street/room enemies (idx 1-21) are placed by dress_festival_streets.py; here we add the 4
# canyon switchback + 15 spiral-staircase ones (idx 22-40), now that the canyon exists -> 40 total.
# "Enemy_" is intentionally NOT in this script's CLEAR list (so we don't wipe dress's 21); instead we
# pre-clear only idx >= 22 below so a standalone merge re-run can't duplicate the canyon/spiral set.
import re as _re
ENEMY_CLASSES = {
    "Glimmer":  unreal.load_class(None, "/Script/SuperClaudeBros2.GlimmerEnemy"),
    "Roly":     unreal.load_class(None, "/Script/SuperClaudeBros2.RolyShellback"),
    "FlitMoth": unreal.load_class(None, "/Script/SuperClaudeBros2.FlitMoth"),   # spiral lights
}
_SKIN_MATS = {}
_SKIN_BY_KIND = {"Glimmer": "M_EnemyGlimmer", "Roly": "M_EnemyRoly", "FlitMoth": "M_EnemyMoth"}


def _enemy_antilag(actor, kind):
    for comp in actor.get_components_by_class(unreal.PrimitiveComponent):
        try:
            comp.set_editor_property("ld_max_draw_distance", 9000.0)
        except Exception:
            pass
        try:
            comp.set_editor_property("visible_in_ray_tracing", False)
        except Exception:
            pass
    for sk in actor.get_components_by_class(unreal.SkeletalMeshComponent):
        try:
            sk.set_editor_property("visibility_based_anim_tick_option",
                                   unreal.VisibilityBasedAnimTickOption.ONLY_TICK_POSE_WHEN_RENDERED)
        except Exception:
            pass
    if kind == "FlitMoth":
        for lt in actor.get_components_by_class(unreal.PointLightComponent):
            for _p, _v in (("cast_shadows", False), ("cast_dynamic_shadows", False),
                           ("max_draw_distance", 4000.0), ("max_distance_fade_range", 800.0)):
                try:
                    lt.set_editor_property(_p, _v)
                except Exception:
                    pass


def _tint_enemy(actor, kind):
    name = _SKIN_BY_KIND.get(kind)
    if not name:
        return
    if name not in _SKIN_MATS:
        _SKIN_MATS[name] = EAL.load_asset(f"/Game/Art/CityMat/{name}")
    mat = _SKIN_MATS[name]
    if not mat:
        return
    for sm in actor.get_components_by_class(unreal.StaticMeshComponent):
        if "Eye" in sm.get_name():
            continue
        try:
            sm.set_material(0, mat)
        except Exception:
            pass


def _spawn_enemy(kind, x, y, z, idx):
    cls = ENEMY_CLASSES.get(kind)
    if not cls:
        return False
    a = eas.spawn_actor_from_class(cls, unreal.Vector(x, y, z))
    a.set_actor_label(f"Enemy_{kind}_{idx:02d}")
    _enemy_antilag(a, kind)
    _tint_enemy(a, kind)
    return True


# Re-run safe: drop only idx >= 22 (canyon + spiral); dress's idx 1-21 are left alone.
for _ex in list(eas.get_all_level_actors()):
    _mm = _re.match(r"Enemy_\w+_(\d+)$", _ex.get_actor_label())
    if _mm and int(_mm.group(1)) >= 22:
        eas.destroy_actor(_ex)

CANYON_ENEMIES = [
    ("Glimmer", 10735, 2200, 1970), ("Roly", 11485, -2200, 3840),
    ("Glimmer", 11360, 2200, 5195), ("Roly", 12860, 0, 6260),
]
# 15 up the spire spiral staircase (landings 1-7). World Z = canyon Z - 350 (merge OZ). Inward of
# each 500x500 landing centre so patrol/roll AI never walks off the edge. 8 Glimmer + 5 Roly + 2 Moth.
SPIRAL_ENEMIES = [
    ("Glimmer", 11380, 170, 5690), ("Roly", 11420, -190, 5690),
    ("Glimmer", 12230, -600, 6110), ("Glimmer", 11970, -600, 6110), ("FlitMoth", 12100, -560, 6220),
    ("Roly", 12700, 0, 6530), ("Glimmer", 12820, 180, 6530),
    ("Glimmer", 12230, 600, 6950), ("Roly", 11970, 600, 6950),
    ("Glimmer", 11440, -160, 7370), ("FlitMoth", 11500, 140, 7480),
    ("Roly", 12180, -620, 7790), ("Glimmer", 12020, -620, 7790),
    ("Roly", 12620, 150, 8210), ("Glimmer", 12640, -170, 8210),
]
_cn = 0
for _j, (_k, _x, _y, _z) in enumerate(CANYON_ENEMIES + SPIRAL_ENEMIES, start=22):
    if _spawn_enemy(_k, _x, _y, _z, _j):
        _cn += 1
print(f"W1_ENEMIES_CANYON_SPIRAL: {_cn}/19")
print(f"W1_ENEMIES_CANYON: {_cn}/4")

saved = les.save_current_level()
print(f"WORLD1_MERGED: cleared={removed} canyon_origin={(OX, OY, OZ)} saved={saved}")
