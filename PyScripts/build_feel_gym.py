"""Build the Feel Gym v2 — SCB2's movement test level — entirely from code.

v2 honors the first playtest lesson: HEROES NEED SOLID GROUND. A huge floor,
a full perimeter wall (no edge to fall off), the ascending staircase, the
growing-gap line over a shallow catch-pit (misses land softly; the C++ respawn
guard backstops everything), a dash gap, lights, sky, fog, and a PlayerStart.

Run via:  Scripts\\run_pyscript.ps1 -Script PyScripts\\build_feel_gym.py
Saves to: /Game/Maps/FeelGym
"""
import unreal

CUBE = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Overwrite the previous gym cleanly. NEVER delete the currently-loaded level
# (the editor starts ON FeelGym via EditorStartupMap and asserts if we saw off
# the branch we're sitting on) — step onto a scratch level first.
if unreal.EditorAssetLibrary.does_asset_exist("/Game/Maps/FeelGym"):
    les.new_level("/Game/Maps/_Scratch")
    unreal.EditorAssetLibrary.delete_asset("/Game/Maps/FeelGym")
les.new_level("/Game/Maps/FeelGym")


def block(x, y, z, sx, sy, sz, label):
    """A scaled cube StaticMeshActor (cube asset is 100uu, so scale = size/100)."""
    actor = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z))
    actor.set_actor_label(label)
    mesh = actor.static_mesh_component
    mesh.set_static_mesh(CUBE)
    actor.set_actor_scale3d(unreal.Vector(sx / 100.0, sy / 100.0, sz / 100.0))
    actor.set_mobility(unreal.ComponentMobility.STATIC)
    return actor


# ---- The arena: a big solid floor with a full perimeter wall ----
FX, FY = 20000, 12000           # floor footprint (200m x 120m)
CX = 5000                       # arena center x (the course runs toward +x)
block(CX, 0, -50, FX, FY, 100, "Floor")
WALL_H, WALL_T = 900, 200       # tall enough that double-jump + dash can't escape
block(CX, FY / 2 + WALL_T / 2, WALL_H / 2, FX + 2 * WALL_T, WALL_T, WALL_H, "Wall_North")
block(CX, -(FY / 2 + WALL_T / 2), WALL_H / 2, FX + 2 * WALL_T, WALL_T, WALL_H, "Wall_South")
block(CX + FX / 2 + WALL_T / 2, 0, WALL_H / 2, WALL_T, FY, WALL_H, "Wall_East")
block(CX - FX / 2 - WALL_T / 2, 0, WALL_H / 2, WALL_T, FY, WALL_H, "Wall_West")

# ---- Test 1: ascending staircase (5 platforms, rising ~150uu each) ----
for i in range(5):
    block(800 + i * 450, 0, 100 + i * 150, 250, 250, 40, f"Stair_{i+1}")

# ---- Test 2: gap-jump line (gaps grow; the main floor catches any miss) ----
y = 1200
x = 600
for i, gap in enumerate((200, 300, 400, 500)):
    block(x, y, 160, 300, 300, 40, f"GapPad_{i+1}")
    x += 300 + gap
block(x, y, 160, 300, 300, 40, "GapPad_End")

# ---- Test 3: dash gap (too wide to jump; spark-dash required) ----
block(600, 2400, 160, 300, 300, 40, "DashPad_A")
block(600 + 300 + 750, 2400, 160, 300, 300, 40, "DashPad_B")

# ---- Light + atmosphere ----
sun = eas.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 1000))
sun.set_actor_label("Sun")
sun.set_actor_rotation(unreal.Rotator(0.0, -42.0, 35.0), False)
sun.light_component.set_intensity(8.0)

sky_light = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 900))
sky_light.set_actor_label("SkyLight")
sky_light.light_component.set_editor_property("real_time_capture", True)

eas.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0)).set_actor_label("SkyAtmosphere")
fog = eas.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0))
fog.set_actor_label("HeightFog")

start = eas.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, 0, 120))
start.set_actor_label("PlayerStart")

# Pin OUR game mode on the map itself (belt & suspenders: PIE honors this even if
# project/user settings drift), so Play always spawns the Spark Hero.
try:
    hero_gm = unreal.load_class(None, "/Script/SuperClaudeBros2.SparkHeroGameMode")
    for a in eas.get_all_level_actors():
        if isinstance(a, unreal.WorldSettings):
            a.set_editor_property("default_game_mode", hero_gm)
            unreal.log("WorldSettings: game mode pinned to SparkHeroGameMode")
            break
except Exception as e:  # never let the pin break the gym build
    unreal.log_warning(f"could not pin game mode on WorldSettings: {e}")

# Save, and sweep up the scratch level if we used one.
les.save_current_level()
if unreal.EditorAssetLibrary.does_asset_exist("/Game/Maps/_Scratch"):
    unreal.EditorAssetLibrary.delete_asset("/Game/Maps/_Scratch")
unreal.log("FEEL_GYM_BUILT: /Game/Maps/FeelGym (v2: walled arena)")
print("FEEL_GYM_BUILT: /Game/Maps/FeelGym (v2: walled arena)")
