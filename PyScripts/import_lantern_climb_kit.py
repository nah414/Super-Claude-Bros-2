"""Import the LanternClimb Meshy kit as static meshes + PBR materials into
/Game/Art/LanternClimbKit/<name>/SM_<name>.

The props are Blender-converted FBX with the PBR maps EMBEDDED (separate-PNG texture import
routes through Interchange and crashes under -run=pythonscript). Mirrors import_festival_kit.py.
NO Nanite is enabled here (Nanite on dense Meshy props caused an 85s load freeze).
"""
import os
import unreal

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
EAL = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

SRC_ROOT = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\lanternclimbkit"
DEST_ROOT = "/Game/Art/LanternClimbKit"

done = 0
for name in sorted(os.listdir(SRC_ROOT)):
    fbx = os.path.join(SRC_ROOT, name, f"{name}.fbx")
    if not os.path.isfile(fbx):
        continue
    dest = f"{DEST_ROOT}/{name}"
    if EAL.does_directory_exist(dest):
        EAL.delete_directory(dest)

    ui = unreal.FbxImportUI()
    ui.import_mesh = True
    ui.import_as_skeletal = False
    ui.import_animations = False
    ui.import_materials = True
    ui.import_textures = True
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    sd = ui.static_mesh_import_data
    sd.set_editor_property("import_uniform_scale", 1.0)
    sd.set_editor_property("combine_meshes", True)

    t = unreal.AssetImportTask()
    t.filename = fbx
    t.destination_path = dest
    t.destination_name = f"SM_{name}"
    t.automated = True
    t.save = True
    t.replace_existing = True
    t.options = ui
    tools.import_asset_tasks([t])

    mesh = None
    for p in (t.get_editor_property("imported_object_paths") or []):
        a = unreal.load_asset(p)
        if isinstance(a, unreal.StaticMesh):
            mesh = a
            break
    if mesh:
        b = mesh.get_bounding_box()
        print(f"PROP_OK: {name} ({b.max.z - b.min.z:.0f}uu tall)")
        done += 1
    else:
        print(f"PROP_FAIL: {name}")

EAL.save_directory(DEST_ROOT, recursive=True)
print(f"LANTERN_KIT_IMPORT_DONE: {done} props -> {DEST_ROOT}")
