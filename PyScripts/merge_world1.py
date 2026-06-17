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

# F3 (Adam): no festival gate at the street->canyon seam. Instead a small, PASSABLE rubble +
# debris pile (NO_COLLISION — the hero walks straight through). Meshy rubble lives in CityTowerKit;
# if not imported yet, the seam simply stays open (still passable) until the next rebuild.
RUBBLE_ROOT = "/Game/Art/CityTowerKit"
def seam_rubble(kit, x, y, scale, yaw, label):
    sm = EAL.load_asset(f"{RUBBLE_ROOT}/{kit}/SM_{kit}")
    if not sm:
        unreal.log_warning(f"RUBBLE_MISSING: {kit} (seam stays open, still passable)")
        return
    bb = sm.get_bounding_box()
    rb = eas.spawn_actor_from_class(unreal.StaticMeshActor,
                                    unreal.Vector(x, y, -bb.min.z * scale))
    rb.static_mesh_component.set_static_mesh(sm)
    rb.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    rb.set_actor_rotation(unreal.Rotator(0.0, 0.0, yaw), False)
    rb.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    rb.static_mesh_component.set_editor_property("visible_in_ray_tracing", False)
    rb.set_actor_label(label)

seam_rubble("rubble_pile", gx - 60, -240, 3.4, 15.0, "Seam_Rubble_A")
seam_rubble("debris_chunks", gx - 30, 300, 3.0, -40.0, "Seam_Rubble_B")

saved = les.save_current_level()
print(f"WORLD1_MERGED: cleared={removed} canyon_origin={(OX, OY, OZ)} saved={saved}")
