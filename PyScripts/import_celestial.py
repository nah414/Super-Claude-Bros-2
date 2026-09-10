"""Import the Meshy celestial bodies (planet + 2 moons) as static meshes into /Game/Art/Celestial,
cap their textures to 2K, and give each a SELF-LIT emissive material (base-color texture x tint x
brightness, unlit two-sided) so they glow against the dark sky like the old moons did — but now with
real cratered/banded detail. The large moon is tinted warm red-rust (Meshy returned it pale).
Legacy FBX import, Interchange OFF (headless-safe). NO Nanite. Mirrors import_citytowerkit.py.

  UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/import_celestial.py -unattended -nosplash -nopause
"""
import os
import unreal

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

SRC = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\celestial"
DEST = "/Game/Art/Celestial"

# body -> (emissive tint, brightness)
BODIES = {
    "planet_gasgiant": ((1.00, 0.97, 0.90), 1.2),
    "moon_large_red":  ((1.00, 0.30, 0.17), 0.50),   # RUST-RED reddish planet (web-grounded Mars/iron-oxide); visible, not glary (Adam)
    "moon_small_pale": ((0.34, 0.28, 0.26), 0.60),   # DARK moon (Adam: small one much darker), reads in front of the light one
}


def find_base_tex(paths):
    texs = [EAL.load_asset(p) for p in paths]
    texs = [t for t in texs if isinstance(t, unreal.Texture2D)]
    for t in texs:
        if any(k in t.get_name().lower() for k in ("base", "albedo", "color", "diffuse")):
            return t, texs
    return (texs[0] if texs else None), texs


def emissive_mat(name, dest, tex, tint, bright):
    path = f"{dest}/{name}"
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    mat = tools.create_asset(name, dest, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", True)
    tintc = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -500, 200)
    tintc.set_editor_property("constant", unreal.LinearColor(tint[0] * bright, tint[1] * bright, tint[2] * bright, 1.0))
    if tex:
        ts = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -500, 0)
        ts.set_editor_property("texture", tex)
        mul = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -220, 60)
        MEL.connect_material_expressions(ts, "", mul, "A")
        MEL.connect_material_expressions(tintc, "", mul, "B")
        MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    else:
        MEL.connect_material_property(tintc, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    return mat


done = 0
for name, (tint, bright) in BODIES.items():
    fbx = os.path.join(SRC, name, f"{name}_ue.fbx")
    if not os.path.isfile(fbx):
        print(f"MISSING_FBX: {fbx}")
        continue
    dest = f"{DEST}/{name}"
    if EAL.does_directory_exist(dest):
        EAL.delete_directory(dest)

    ui = unreal.FbxImportUI()
    ui.import_mesh = True
    ui.import_as_skeletal = False
    ui.import_animations = False
    ui.import_materials = True
    ui.import_textures = True
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    ui.static_mesh_import_data.set_editor_property("combine_meshes", True)

    t = unreal.AssetImportTask()
    t.filename = fbx
    t.destination_path = dest
    t.destination_name = f"SM_{name}"
    t.automated = True
    t.save = True
    t.replace_existing = True
    t.options = ui
    tools.import_asset_tasks([t])

    paths = list(t.get_editor_property("imported_object_paths") or []) + list(EAL.list_assets(dest, recursive=True))
    mesh = None
    for p in paths:
        a = EAL.load_asset(p)
        if isinstance(a, unreal.StaticMesh):
            mesh = a
            break
    base, texs = find_base_tex(paths)
    for tx in texs:                       # cap to 2K
        try:
            tx.set_editor_property("max_texture_size", 2048)
            EAL.save_loaded_asset(tx)
        except Exception as e:
            unreal.log_warning(f"texcap skip {tx.get_name()}: {e}")

    if not mesh:
        print(f"CELESTIAL_FAIL: {name} (no mesh)")
        continue
    mat = emissive_mat(f"M_{name}_lit", dest, base, tint, bright)
    mesh.set_material(0, mat)
    EAL.save_loaded_asset(mesh)
    b = mesh.get_bounding_box()
    print(f"CELESTIAL_OK: {name} basetex={base.get_name() if base else None} "
          f"size={b.max.x-b.min.x:.0f}uu mat=M_{name}_lit")
    done += 1

EAL.save_directory(DEST, recursive=True)
print(f"IMPORT_CELESTIAL_DONE: {done}/{len(BODIES)} -> {DEST}")
