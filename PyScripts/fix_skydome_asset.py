"""Robust respawn-loop fix. Component collision edits (set_collision_enabled / profile name) do
NOT persist through the level save in this workflow (bit the gates, rubble, and the dome). The
ONLY method proven to persist is stripping collision at the ASSET level. The dome used the shared
/Engine/BasicShapes/Sphere (can't edit that). So: duplicate it into the project, strip the copy's
collision (0 simple + USE_SIMPLE_AS_COMPLEX = no collision geometry at all), and repoint the
StarDome at the collision-free copy. Mesh-assignment + asset-collision both serialize reliably.
Run -RenderOffscreen (loads + saves the map; safe now under software Lumen)."""
import unreal

EAL = unreal.EditorAssetLibrary
SMES = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

DST = "/Game/Art/SM_SkyDome"
if not EAL.does_asset_exist(DST):
    EAL.duplicate_asset("/Engine/BasicShapes/Sphere", DST)
mesh = EAL.load_asset(DST)
SMES.remove_collisions(mesh)
bs = mesh.get_editor_property("body_setup")
if bs:
    bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
EAL.save_asset(DST)
print(f"SKYDOME_MESH_READY: {DST} simple_collision={SMES.get_simple_collision_count(mesh)}")

assert unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity"), "LOAD_FAILED"
n = 0
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "StarDome":
        a.static_mesh_component.set_static_mesh(mesh)
        n += 1
        print(f"SKYDOME_REPOINTED: {a.get_actor_label()} -> {mesh.get_name()}")
saved = les.save_current_level()
print(f"SKYDOME_ASSET_FIX_DONE: repointed={n} saved={saved}")
