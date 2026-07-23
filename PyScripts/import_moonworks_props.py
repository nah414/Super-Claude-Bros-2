"""Import the stage-29 Moonworks props -> /Game/Art/Moonworks/<name> (+ forged M_<name>).

Meshy drops arrive as bare FBX + loose PBR PNGs, so materials are FORGED per recipe
paragraph 3, not auto-imported: base_color/metallic/roughness/normal wired, EMISSIVE LEFT
EMPTY (Brightness War: Meshy bakes albedo into emission; our C++ lights do the glowing).
Meshes are normalized to canon sizes via LOD build scale so the beam plane (z=150)
strikes every body. MUST run in its own session BEFORE the garden build: the C++
FObjectFinders only look for these assets at module load.
"""
import os

import unreal

SRC_ROOT = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\moonworks"
DEST_ROOT = "/Game/Art/Moonworks"

# name: (normalize_axis, target_uu) — crystal/prism/tree by HEIGHT, flower by WIDTH.
# Stage-29 hero props + stage-30 undergrowth (small/medium filler, Adam round 2).
PROPS = {
    "moon_crystal": ("z", 340.0),
    "moon_prism": ("z", 230.0),
    "moonflower": ("x", 420.0),
    "crystal_tree": ("z", 900.0),
    "crystal_shards": ("z", 120.0),
    "moon_fern": ("z", 180.0),
    "moonstone_boulder": ("z", 220.0),
    "crystal_sapling": ("z", 380.0),
}

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
tools = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
ML = unreal.MaterialEditingLibrary

# NO delete_directory here: once the C++ FObjectFinders compiled in, the CDO LOCKS
# this folder (recipe §2 — delete returns False silently; the July 22 NoneType crash).
# Meshes/textures reimport IN PLACE (replace_existing) and materials are reused.


def import_fbx(fbx_path, dest, name):
    ui = unreal.FbxImportUI()
    ui.import_mesh = True
    ui.import_as_skeletal = False
    ui.import_animations = False
    ui.import_materials = False    # forged below, never auto (reimports clobber autos)
    ui.import_textures = False
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    sd = ui.static_mesh_import_data
    sd.set_editor_property("import_uniform_scale", 1.0)
    sd.set_editor_property("combine_meshes", True)
    sd.set_editor_property("auto_generate_collision", True)   # beams + feet need to LAND

    task = unreal.AssetImportTask()
    task.filename = fbx_path
    task.destination_path = dest
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = True
    task.options = ui
    tools.import_asset_tasks([task])
    paths = list(task.get_editor_property("imported_object_paths") or [])
    return unreal.load_asset(paths[0]) if paths else None


def import_texture(png_path, dest, name, srgb, normal=False):
    task = unreal.AssetImportTask()
    task.filename = png_path
    task.destination_path = dest
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = True
    tools.import_asset_tasks([task])
    paths = list(task.get_editor_property("imported_object_paths") or [])
    tex = unreal.load_asset(paths[0]) if paths else None
    if tex:
        tex.set_editor_property("srgb", srgb)
        if normal:
            tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        EAL.save_loaded_asset(tex)
    return tex


def forge_material(dest, stem, tex):
    mat = tools.create_asset(f"M_{stem}", dest, unreal.Material, unreal.MaterialFactoryNew())
    assert mat, f"MAT_CREATE_FAILED: M_{stem} (locked folder collision?)"

    def sample(texture, y, sampler=None):
        node = ML.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -450, y)
        node.texture = texture
        if sampler is not None:
            node.sampler_type = sampler
        return node

    if tex.get("base_color"):
        ML.connect_material_property(sample(tex["base_color"], -300), "RGB",
                                     unreal.MaterialProperty.MP_BASE_COLOR)
    if tex.get("metallic"):
        ML.connect_material_property(
            sample(tex["metallic"], -40, unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR),
            "R", unreal.MaterialProperty.MP_METALLIC)
    if tex.get("roughness"):
        ML.connect_material_property(
            sample(tex["roughness"], 220, unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR),
            "R", unreal.MaterialProperty.MP_ROUGHNESS)
    if tex.get("normal"):
        ML.connect_material_property(
            sample(tex["normal"], 480, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL),
            "RGB", unreal.MaterialProperty.MP_NORMAL)
    # EMISSIVE: nothing, deliberately. The Brightness War stays won.

    ML.recompile_material(mat)
    EAL.save_loaded_asset(mat)   # recipe 5.7 gotcha: save right after recompile
    return mat


for stem, (axis, target) in PROPS.items():
    src_dir = os.path.join(SRC_ROOT, stem)
    fbx = os.path.join(src_dir, f"{stem}.fbx")
    if not os.path.isfile(fbx):
        print(f"MOONWORKS_SKIP: {stem} (no drop on disk)")
        continue
    dest = f"{DEST_ROOT}"

    mesh = import_fbx(fbx, dest, stem)
    if not isinstance(mesh, unreal.StaticMesh):
        print(f"MOONWORKS_FAIL: {stem} did not import as StaticMesh")
        continue

    tex = {}
    for kind, srgb in (("base_color", True), ("metallic", False), ("roughness", False), ("normal", False)):
        png = os.path.join(src_dir, f"{stem}_tex0_{kind}.png")
        if os.path.isfile(png):
            tex[kind] = import_texture(png, dest, f"T_{stem}_{kind}", srgb, normal=(kind == "normal"))

    mat = EAL.load_asset(f"{DEST_ROOT}/M_{stem}")   # reuse under the folder lock
    if not mat:
        mat = forge_material(dest, stem, tex)
    mesh.set_material(0, mat)

    # Normalize to canon size so the beam plane strikes every body.
    b = mesh.get_bounding_box()
    size = {"x": b.max.x - b.min.x, "y": b.max.y - b.min.y, "z": b.max.z - b.min.z}[axis]
    if size > 1.0:
        s = target / size
        # 5.7: build scale rides MeshBuildSettings via get/set_lod_build_settings
        # (set_lod_build_scale is gone — the AttributeError of 2026-07-22).
        sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        bs = sms.get_lod_build_settings(mesh, 0)
        bs.build_scale3d = unreal.Vector(s, s, s)
        sms.set_lod_build_settings(mesh, 0, bs)
    EAL.save_loaded_asset(mesh)
    b2 = mesh.get_bounding_box()
    print(f"MOONWORKS_OK: {stem} {b2.max.x - b2.min.x:.0f}x{b2.max.y - b2.min.y:.0f}x{b2.max.z - b2.min.z:.0f}uu (minZ {b2.min.z:.0f})")

EAL.save_directory(DEST_ROOT, recursive=True)
print("MOONWORKS_IMPORT_DONE")
