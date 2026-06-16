"""Import the Festival + Edge Meshy kits as static meshes + their PBR materials.

The props are Blender-converted FBX with the PBR maps EMBEDDED in the FBX, so UE's legacy
FBX importer builds the material itself (basecolor/metallic-roughness/normal/emission) —
no separate PNG import, which would route through Interchange and crash under
-run=pythonscript. Lands in /Game/Art/FestivalKit/<name>/SM_<name>. Mirrors the proven
import_city_kit.py pipeline.
"""
import os
import unreal

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
EAL = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

KITS = [
    r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\festivalkit",
    r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\edgekit",
]
DEST_ROOT = "/Game/Art/FestivalKit"

done = 0
for src_root in KITS:
    if not os.path.isdir(src_root):
        continue
    for name in sorted(os.listdir(src_root)):
        fbx = os.path.join(src_root, name, f"{name}.fbx")
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
print(f"FESTIVAL_IMPORT_DONE: {done} props -> {DEST_ROOT}")
