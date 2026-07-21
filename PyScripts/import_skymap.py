"""Import the all-sky map FBX (carrying the embedded equirect star/Milky-Way PNG) and expose the
texture as /Game/Art/Sky/T_StarMap. Legacy FBX importer with Interchange OFF (headless-safe), mirrors
import_citytowerkit.py. The carrier mesh + its auto-material are deleted; only the Texture2D is kept.

  UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/import_skymap.py -unattended -nosplash -nopause
"""
import unreal

FBX = r"C:\Users\Atomn\mario2\_prep\star_data\skymap.fbx"
DEST = "/Game/Art/Sky"
EAL = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")

before = set(EAL.list_assets(DEST, recursive=True)) if EAL.does_directory_exist(DEST) else set()

ui = unreal.FbxImportUI()
ui.import_mesh = True
ui.import_as_skeletal = False
ui.import_animations = False
ui.import_materials = True
ui.import_textures = True
ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH

t = unreal.AssetImportTask()
t.filename = FBX
t.destination_path = DEST
t.destination_name = "SM_SkyMapCarrier"
t.automated = True
t.save = True
t.replace_existing = True
t.options = ui
tools.import_asset_tasks([t])

after = set(EAL.list_assets(DEST, recursive=True))
new = sorted(after - before)
print(f"IMPORTED_ASSETS: {new}")

# find the imported Texture2D, cap + sRGB, rename to T_StarMap
star_tex = None
for ap in after:
    a = EAL.load_asset(ap)
    if isinstance(a, unreal.Texture2D):
        star_tex = ap
        break
assert star_tex, "SKYMAP_TEX_NOT_FOUND after import"
tex = EAL.load_asset(star_tex)
tex.set_editor_property("srgb", True)
try:
    tex.set_editor_property("max_texture_size", 4096)
except Exception as e:
    unreal.log_warning(f"max_texture_size skip: {e}")
EAL.save_loaded_asset(tex)

TARGET = f"{DEST}/T_StarMap"
if star_tex != TARGET:
    if EAL.does_asset_exist(TARGET):
        EAL.delete_asset(TARGET)
    EAL.rename_asset(star_tex, TARGET)
print(f"STARMAP_TEXTURE: {TARGET}")

# drop the carrier mesh + any auto-imported material (we only needed the texture)
for ap in new:
    a = EAL.load_asset(ap)
    if isinstance(a, (unreal.StaticMesh, unreal.MaterialInterface)) and EAL.does_asset_exist(ap):
        EAL.delete_asset(ap)
print("IMPORT_SKYMAP_DONE")
