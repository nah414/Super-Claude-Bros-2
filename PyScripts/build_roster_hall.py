"""Build /Game/Maps/RosterHall — a daylight gallery of the whole character bank.

Every SM_ asset under /Game/Art/Roster stands in a row at true design height.
The hero spawns facing the line: walk past your cast, Adam.
"""
import unreal

EAL = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

les.new_level("/Game/Maps/RosterHall")

# ---- stage: floor + daylight ----
cube = unreal.load_asset("/Engine/BasicShapes/Cube")
floor = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -50))
floor.static_mesh_component.set_static_mesh(cube)
floor.set_actor_scale3d(unreal.Vector(60.0, 30.0, 1.0))
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

# ---- the visitor ----
start = eas.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, -700, 100))
start.set_actor_rotation(unreal.Rotator(0.0, 0.0, 90.0), False)  # look at the line
start.set_actor_label("PlayerStart")

les.save_current_level()
print("ROSTER_HALL_DONE")
