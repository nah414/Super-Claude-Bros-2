"""Import the IndustrialKit Meshy facades (M2) as static meshes + PBR materials into
/Game/Art/IndustrialKit/<name>/SM_<name>. These are the gritty 3D facade/detail pieces
(pipe-clad walls, ducting, AC arrays, girders...) dressed onto the building shells so the
flat cubes stop reading as tier-1 boxes.

Blender-converted FBX with PBR embedded (separate-PNG import crashes under -run=pythonscript).
NO Nanite (dense Meshy + Nanite = 85s load freeze). Mirrors import_climbkit.py.
"""
import os
import unreal

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
EAL = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

SRC_ROOT = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\industrialkit"
DEST_ROOT = "/Game/Art/IndustrialKit"

done = 0
if os.path.isdir(SRC_ROOT):
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
            print(f"IND_PROP_OK: {name} ({b.max.z - b.min.z:.0f}uu tall)")
            done += 1
        else:
            print(f"IND_PROP_FAIL: {name}")
    EAL.save_directory(DEST_ROOT, recursive=True)
print(f"INDUSTRIALKIT_IMPORT_DONE: {done} props -> {DEST_ROOT}")
