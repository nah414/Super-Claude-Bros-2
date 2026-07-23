# THE PROMOTION (Adam, July 23): World 2 was gated last night ("It's perfect my
# friend!") — so it graduates out of the sandbox. WorldStageTesting (the World 2
# build) is duplicated to /Game/Maps/MoonlitGlade — its forever home on the World
# Road — and the stage is then wiped back to the blank builder's kit (slab + spawn
# + sun + sky) so World 3 (the Verdant Reach) can rise on clean ground.
#
# The old June MoonlitGlade.umap (early glade sculpt, superseded) is deleted here;
# git keeps it, like it keeps everything. NeonCity remains at cc6dd13.
#
# Run:  powershell -File Scripts\run_pyscript.ps1 -Script ..\PyScripts\promote_world2_reset_stage.py -Map /Engine/Maps/Entry
import unreal

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary

STAGE = "/Game/Maps/WorldStageTesting"
GLADE = "/Game/Maps/MoonlitGlade"

# --- scratch-dance: never delete the level you are standing in ---
if EAL.does_asset_exist("/Game/Maps/_Scratch"):
    EAL.delete_asset("/Game/Maps/_Scratch")
assert les.new_level("/Game/Maps/_Scratch"), "SCRATCH_FAILED"

# --- 1) retire the old June glade (superseded; git keeps it) ---
if EAL.does_asset_exist(GLADE):
    assert EAL.delete_asset(GLADE), "DELETE_OLD_GLADE_FAILED"
    unreal.log_warning("PROMOTE_MARKER: old MoonlitGlade (June sculpt) deleted — git keeps it")
else:
    unreal.log_warning("PROMOTE_MARKER: no old MoonlitGlade found")

# --- 2) promote: World 2 graduates from the stage to its forever home ---
assert EAL.does_asset_exist(STAGE), "STAGE_MISSING"
assert EAL.duplicate_asset(STAGE, GLADE), "PROMOTE_FAILED"
assert EAL.does_asset_exist(GLADE), "GLADE_NOT_CREATED"
# THE SAVE LAW OF PROMOTION (learned 2026-07-23, first run): duplicate_asset
# creates the copy IN MEMORY ONLY — without an explicit save_asset the umap
# never reaches disk and dies with the session. Save it, then TRUST ONLY DISK.
assert EAL.save_asset(GLADE, only_if_is_dirty=False), "SAVE_GLADE_FAILED"
unreal.log_warning("PROMOTE_MARKER: WorldStageTesting duplicated -> MoonlitGlade + SAVED (World 2 promoted)")

# --- 3) wipe the stage (World 2 is safe: promoted + committed at 7d71569) ---
assert EAL.delete_asset(STAGE), "DELETE_STAGE_FAILED"
unreal.log_warning("PROMOTE_MARKER: stage wiped")

# --- 4) rebuild the blank builder's kit: slab, spawn, sun, sky ---
assert les.new_level(STAGE), "NEW_STAGE_FAILED"

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
    unreal.log_warning(f"PROMOTE_MARKER: sun atmosphere flag skipped ({e})")

sky_atmo = eas.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0))
sky_atmo.set_actor_label("StageAtmosphere")
sky_light = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 500))
sky_light.set_actor_label("StageSkyLight")

assert les.save_current_level(), "SAVE_STAGE_FAILED"
unreal.log_warning("PROMOTE_MARKER: blank WorldStageTesting saved")

# --- clean the scratch litter ---
if EAL.does_asset_exist("/Game/Maps/_Scratch"):
    EAL.delete_asset("/Game/Maps/_Scratch")
unreal.log_warning("PROMOTE_MARKER: DONE")
