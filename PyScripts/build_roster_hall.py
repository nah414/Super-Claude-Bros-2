"""Build /Game/Maps/RosterHall — a daylight gallery of the whole character bank.

Every SM_ asset under /Game/Art/Roster stands in a row at true design height.
The hero spawns facing the line: walk past your cast, Adam.
"""
import unreal

EAL = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# THE SCRATCH DANCE (hard lesson, twice now): new_level() over an EXISTING map
# fails silently, leaving the startup map (MoonlitGlade!) loaded — every spawn
# then contaminates the GAME LEVEL and save_current_level() saves the damage.
# So: hop to a scratch level, delete the old hall, create it fresh, verify.
# (new_level also refuses to overwrite the SCRATCH itself — delete it first.)
if EAL.does_asset_exist("/Game/Maps/_Scratch"):
    EAL.delete_asset("/Game/Maps/_Scratch")
assert les.new_level("/Game/Maps/_Scratch"), "SCRATCH_LEVEL_FAILED"
if EAL.does_asset_exist("/Game/Maps/RosterHall"):
    assert EAL.delete_asset("/Game/Maps/RosterHall"), "DELETE_OLD_HALL_FAILED"
assert les.new_level("/Game/Maps/RosterHall"), "NEW_HALL_FAILED"

# ---- stage: floor + daylight ----
cube = unreal.load_asset("/Engine/BasicShapes/Cube")
floor = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -50))
floor.static_mesh_component.set_static_mesh(cube)
floor.set_actor_scale3d(unreal.Vector(220.0, 90.0, 1.0))
floor.set_actor_label("HallFloor")

sun = eas.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 800))
sun.set_actor_rotation(unreal.Rotator(0.0, -55.0, 35.0), False)
sun.light_component.set_intensity(8.0)
sun.set_actor_label("Sun")

sky_atm = eas.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0))
sky_atm.set_actor_label("SkyAtmosphere")
skylight = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 600))
skylight.light_component.set_editor_property("real_time_capture", True)
skylight.set_actor_label("SkyLight")

# ---- the cast, in a row ----
assets = [a for a in EAL.list_assets("/Game/Art/Roster", recursive=True)
          if "/SM_" in a]
assets.sort()
n = len(assets)
spacing = 260.0
x0 = -spacing * (n - 1) / 2.0
count = 0
for i, path in enumerate(assets):
    sm = EAL.load_asset(path)
    if not isinstance(sm, unreal.StaticMesh):
        continue
    actor = eas.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(x0 + i * spacing, 500.0, 0.0))
    actor.static_mesh_component.set_static_mesh(sm)
    actor.set_actor_rotation(unreal.Rotator(0.0, 0.0, -90.0), False)  # face the visitor
    actor.set_actor_label(sm.get_name())
    count += 1
print(f"PLACED: {count} characters")

# ---- second wing: the CITY KIT (review gate for stage objects) ----
city = sorted(a for a in EAL.list_assets("/Game/Art/CityKit", recursive=True) if "/SM_" in a)
small_x, big_x = -4500.0, -9000.0
for path in city:
    sm = EAL.load_asset(path)
    if not isinstance(sm, unreal.StaticMesh):
        continue
    b = sm.get_bounding_box()
    width = max(b.max.x - b.min.x, b.max.y - b.min.y)
    tall = (b.max.z - b.min.z) > 800.0
    if tall:
        x = big_x + width / 2.0
        big_x += width + 260.0
        y = 3800.0
    else:
        x = small_x + width / 2.0
        small_x += width + 180.0
        y = 1800.0
    actor = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, 0.0))
    actor.static_mesh_component.set_static_mesh(sm)
    actor.set_actor_rotation(unreal.Rotator(0.0, 0.0, -90.0), False)
    actor.set_actor_label(sm.get_name())
    count += 1
print(f"PLACED_CITY: {len(city)}")

# ---- a LIVE Glimmer (the real enemy, crystal-sprite body) for behavior review ----
try:
    glimmer_cls = unreal.load_class(None, "/Script/SuperClaudeBros2.GlimmerEnemy")
    g = eas.spawn_actor_from_class(glimmer_cls, unreal.Vector(350, -400, 60))
    g.set_actor_label("LiveGlimmer")
    print("LIVE_GLIMMER_PLACED")
except Exception as e:
    print(f"LIVE_GLIMMER_SKIPPED: {e}")

# ---- the visitor ----
start = eas.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, -700, 100))
start.set_actor_rotation(unreal.Rotator(0.0, 0.0, 90.0), False)  # look at the line
start.set_actor_label("PlayerStart")

saved = les.save_current_level()
print(f"SAVE_RESULT: {saved}")
# Leave no scratch behind (we're on RosterHall now, so the asset is deletable).
if EAL.does_asset_exist("/Game/Maps/_Scratch"):
    EAL.delete_asset("/Game/Maps/_Scratch")
if not saved:
    # Belt and braces: save every dirty package the unattended path might hold back.
    ok = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(
        save_map_packages=True, save_content_packages=True)
    print(f"SAVE_DIRTY_FALLBACK: {ok}")
print("ROSTER_HALL_DONE")
