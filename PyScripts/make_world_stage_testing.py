# THE NEW SLATE (Adam, July 22): NeonCity is wiped; the build sandbox is now
# /Game/Maps/WorldStageTesting. This is WHERE WE BUILD — worlds get raised and
# torn down here, then promoted into the final game (SBC2) when Adam gates them.
# Old NeonCity is preserved in git at commit cc6dd13 ("Midnight sky pass").
#
# The slate is not a void: a 100m slab + PlayerStart + sun/sky, so launching the
# "SCB2 World Stage Testing" shortcut lands the hero on standable, lit ground.
#
# Run:  powershell -File Scripts\run_pyscript.ps1 -Script ..\PyScripts\make_world_stage_testing.py -Map /Engine/Maps/Entry
import unreal

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary

# --- scratch-dance: never delete the level you are standing in ---
if EAL.does_asset_exist("/Game/Maps/_Scratch"):
    EAL.delete_asset("/Game/Maps/_Scratch")
assert les.new_level("/Game/Maps/_Scratch"), "SCRATCH_FAILED"

if EAL.does_asset_exist("/Game/Maps/NeonCity"):
    assert EAL.delete_asset("/Game/Maps/NeonCity"), "DELETE_NEONCITY_FAILED"
    unreal.log("STAGE_MARKER: NeonCity deleted (git keeps it at cc6dd13)")
else:
    unreal.log("STAGE_MARKER: NeonCity already absent")

assert les.new_level("/Game/Maps/WorldStageTesting"), "NEW_STAGE_FAILED"

# --- the builder's kit: slab, spawn, sun, sky ---
cube = EAL.load_asset("/Engine/BasicShapes/Cube")
slab = eas.spawn_actor_from_object(cube, unreal.Vector(0, 0, -50))
slab.set_actor_scale3d(unreal.Vector(100.0, 100.0, 1.0))   # 100m x 100m, top at z=0
slab.set_actor_label("StageSlab")

ps = eas.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, 0, 200))
ps.set_actor_label("StageSpawn")

sun = eas.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 1000))
rot = unreal.Rotator()
rot.pitch = -50.0
rot.yaw = 30.0
sun.set_actor_rotation(rot, False)
sun.set_actor_label("StageSun")
try:
    sun.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property("atmosphere_sun_light", True)
except Exception as e:
    unreal.log_warning(f"STAGE_MARKER: sun atmosphere flag skipped ({e})")

sky_atmo = eas.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0))
sky_atmo.set_actor_label("StageAtmosphere")
sky_light = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 500))
sky_light.set_actor_label("StageSkyLight")

saved = les.save_current_level()
assert saved, "SAVE_STAGE_FAILED"
unreal.log("STAGE_MARKER: WorldStageTesting saved")

if EAL.does_asset_exist("/Game/Maps/_Scratch"):
    EAL.delete_asset("/Game/Maps/_Scratch")
unreal.log("STAGE_MARKER: DONE")
