import unreal
DEST = "/Game/Art/HeroSkelV4"
FBX = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\white_anim_crouchwalk\white_crouchwalk_animation_fbx_url.fbx"
unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
skel = unreal.load_asset(f"{DEST}/SCB2Hero_Skeleton")
ui = unreal.FbxImportUI()
ui.import_mesh = False
ui.import_as_skeletal = False
ui.import_animations = True
ui.import_materials = False
ui.import_textures = False
ui.skeleton = skel
ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION
ui.anim_sequence_import_data.set_editor_property("import_uniform_scale", 0.8)
ui.anim_sequence_import_data.set_editor_property("snap_to_closest_frame_boundary", True)
ui.anim_sequence_import_data.set_editor_property("convert_scene", True)
t = unreal.AssetImportTask()
t.filename = FBX
t.destination_path = DEST
t.destination_name = "A_Hero_CrouchWalk"
t.automated = True
t.save = True
t.replace_existing = False
t.options = ui
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
for cand in (f"{DEST}/A_Hero_CrouchWalk_Anim", f"{DEST}/A_Hero_CrouchWalk"):
    a = unreal.load_asset(cand)
    if isinstance(a, unreal.AnimSequence):
        s = a.get_editor_property("skeleton")
        print(f"CROUCH: {cand.split('/')[-1]} len={a.get_play_length():.2f}s "
              f"skeleton={s.get_name() if s else 'NONE'} bound={s == skel}")
        break
else:
    print("CROUCH: NO_ANIMSEQUENCE")
unreal.EditorAssetLibrary.save_directory(DEST, recursive=True)
print("CROUCH_DONE")

