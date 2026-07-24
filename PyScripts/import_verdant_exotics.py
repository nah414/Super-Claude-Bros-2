"""Import the stage-38 EXOTIC PACK -> /Game/Art/Verdant/<name> (+ forged M_<name>).

Six Meshy statement plants for the hero clusters (Adam-authorized, round 3).
Laws honored (import_moonworks_props.py lineage): materials FORGED never
auto-imported, EMISSIVE LEFT EMPTY (Meshy bakes glow — the Brightness War),
normalize-by-height via LOD build scale, Nanite ON, **NO collision** (the
understory is walk-through by Adam's order).
"""
import os

import unreal

SRC_ROOT = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\verdant"
DEST = "/Game/Art/Verdant"

PROPS = {                       # name: normalize height (z, uu)
    "giant_fiddlehead": 1300.0,
    "bellbloom_cluster": 1100.0,
    "paddleleaf_giant": 900.0,
    "seedpod_bush": 700.0,
    "reed_fan": 1200.0,
    "mossbloom_boulder": 450.0,
}

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
tools = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
ML = unreal.MaterialEditingLibrary
sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)


def import_fbx(fbx_path, name):
    ui = unreal.FbxImportUI()
    ui.import_mesh = True
    ui.import_as_skeletal = False
    ui.import_animations = False
    ui.import_materials = False
    ui.import_textures = True          # embedded PBR maps ride in the FBX
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    sd = ui.static_mesh_import_data
    sd.set_editor_property("import_uniform_scale", 1.0)
    sd.set_editor_property("combine_meshes", True)
    sd.set_editor_property("auto_generate_collision", False)   # walk-through
    task = unreal.AssetImportTask()
    task.filename = fbx_path
    task.destination_path = DEST
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = True
    task.options = ui
    tools.import_asset_tasks([task])
    paths = list(task.get_editor_property("imported_object_paths") or [])
    for p in paths:
        a = unreal.load_asset(p.split(".")[0])
        if isinstance(a, unreal.StaticMesh):
            return a
    return None


def forge_material(stem):
    mat_path = f"{DEST}/M_{stem}"
    if EAL.does_asset_exist(mat_path):
        return EAL.load_asset(mat_path)
    mat = tools.create_asset(f"M_{stem}", DEST, unreal.Material, unreal.MaterialFactoryNew())
    base = None
    for cand in EAL.list_assets(DEST, recursive=False):
        an = cand.split("/")[-1].split(".")[0]
        if an.lower().startswith(stem.lower()) and "_" in an:
            t = unreal.load_asset(cand)
            if isinstance(t, unreal.Texture2D):
                base = t
                break
    if base:
        ts = ML.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -450, -100)
        ts.texture = base
        ML.connect_material_property(ts, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = ML.create_material_expression(mat, unreal.MaterialExpressionConstant, -450, 150)
    rough.set_editor_property("r", 0.8)
    ML.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    # EMISSIVE: nothing, deliberately. The Brightness War stays won.
    ML.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    return mat


ok = 0
for stem, target_z in PROPS.items():
    fbx = os.path.join(SRC_ROOT, stem, f"{stem}_ue.fbx")
    if not os.path.isfile(fbx):
        print(f"REACH_FAIL: {stem} fbx missing (run the GLB conversion)")
        continue
    mesh = import_fbx(fbx, stem)
    if not mesh:
        print(f"REACH_FAIL: {stem} did not import")
        continue
    b = mesh.get_bounding_box()
    size = b.max.z - b.min.z
    if size > 1.0:
        s = target_z / size
        bs = sms.get_lod_build_settings(mesh, 0)
        bs.build_scale3d = unreal.Vector(s, s, s)
        sms.set_lod_build_settings(mesh, 0, bs)
    # Meshy auto-import wires baked emission — check the auto material got
    # skipped (import_materials False) and dress the mesh in the forged one.
    mesh.set_material(0, forge_material(stem))
    ns = mesh.get_editor_property("nanite_settings")
    ns.set_editor_property("enabled", True)
    mesh.set_editor_property("nanite_settings", ns)
    EAL.save_loaded_asset(mesh)
    b2 = mesh.get_bounding_box()
    print(f"REACH_MARKER: exotic {stem} {b2.max.x - b2.min.x:.0f}x"
          f"{b2.max.y - b2.min.y:.0f}x{b2.max.z - b2.min.z:.0f}uu nanite=1 col=none")
    ok += 1

EAL.save_directory(DEST, recursive=True)
print(f"REACH_MARKER: exotic pack {ok}/6 imported")
assert ok >= 4, "EXOTICS_INCOMPLETE"
print("VERDANT_EXOTICS_DONE")
