"""Warm the Derived Data Cache for /Game/Maps/RosterHall so the next `-game` launch does
NO synchronous mesh/texture build at boot (that synchronous build is what hard-froze the PC).

Loads the Hall map and force-touches every referenced static & skeletal mesh + their textures.
Touching render data (get_num_lods / get_bounding_box) makes the editor build & cache the
derived data on the CPU side. This is a pure asset-warm pass — run headless under -nullrhi,
no GPU rendering, so it cannot repeat the GPU freeze. It NEVER edits or saves content.
"""
import unreal

EAL = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

MAP = "/Game/Maps/RosterHall"
assert EAL.does_asset_exist(MAP), f"MAP_MISSING: {MAP}"
assert les.load_level(MAP), f"LOAD_LEVEL_FAILED: {MAP}"

static_meshes, skel_meshes = set(), set()

# Touching mesh render data (get_num_lods / get_bounds) forces the editor to build & cache
# the derived data on the CPU. Texture DDC is already built when optimize_citykit_textures.py
# saved each capped texture, so meshes are all we need to warm here.
for actor in eas.get_all_level_actors():
    for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
        sm = comp.get_editor_property("static_mesh")
        if sm and sm.get_path_name() not in static_meshes:
            static_meshes.add(sm.get_path_name())
            sm.get_num_lods()                 # forces FStaticMeshRenderData build/cache
            sm.get_bounding_box()
    for comp in actor.get_components_by_class(unreal.SkeletalMeshComponent):
        sk = comp.get_editor_property("skeletal_mesh")
        if sk and sk.get_path_name() not in skel_meshes:
            skel_meshes.add(sk.get_path_name())
            sk.get_bounds()

print(f"DDC_WARM_DONE: {len(static_meshes)} static meshes, {len(skel_meshes)} skeletal meshes touched")
