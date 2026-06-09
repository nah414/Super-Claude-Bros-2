"""Build the Feel Gym — SCB2's movement test level — entirely from code.

A floor, an ascending 5-platform staircase (the camera/jump test), a flat gap-jump
line (coyote-time + buffer test), a dash gap, lights, sky, fog, and a PlayerStart.
Run via:  Scripts\\run_pyscript.ps1 -Script PyScripts\\build_feel_gym.py
Saves to: /Game/Maps/FeelGym
"""
import unreal

CUBE = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Fresh empty level.
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


# ---- Ground slab ----
block(0, 0, -50, 12000, 4000, 100, "Floor")

# ---- Test 1: ascending staircase (5 platforms, rising ~150uu each) ----
for i in range(5):
    block(800 + i * 450, 0, 100 + i * 150, 250, 250, 40, f"Stair_{i+1}")

# ---- Test 2: flat gap-jump line (gaps grow: tests buffer + coyote feel) ----
y = 800
x = 600
for i, gap in enumerate((200, 300, 400, 500)):
    block(x, y, 60, 300, 300, 40, f"GapPad_{i+1}")
    x += 300 + gap
block(x, y, 60, 300, 300, 40, "GapPad_End")

# ---- Test 3: dash gap (too wide to jump; spark-dash required) ----
block(600, 1700, 60, 300, 300, 40, "DashPad_A")
block(600 + 300 + 750, 1700, 60, 300, 300, 40, "DashPad_B")

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

# Save.
les.save_current_level()
unreal.log("FEEL_GYM_BUILT: /Game/Maps/FeelGym")
print("FEEL_GYM_BUILT: /Game/Maps/FeelGym")
