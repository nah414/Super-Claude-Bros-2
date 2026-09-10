"""REPAIR the exotic pack's textures (round 3 postmortem).

Root cause: FBX-embedded textures import under generic names (Image_0,
Image_2, ...) so forge_material's startswith(stem) search never matched —
every exotic wore the bare grey fallback. Worse, all six stems fought over
the same Image_* names. The real 4K base-color PNGs sit in the Meshy drop
folders; import THOSE explicitly as T_<stem>_base and re-forge.
De-glow law still holds: EMISSIVE LEFT EMPTY.
"""
import os

import unreal

SRC_ROOT = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\verdant"
DEST = "/Game/Art/Verdant"
STEMS = ["giant_fiddlehead", "bellbloom_cluster", "paddleleaf_giant",
         "seedpod_bush", "reed_fan", "mossbloom_boulder"]

tools = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
ML = unreal.MaterialEditingLibrary

# ---- purge the colliding embedded-texture strays ----
purged = 0
for path in EAL.list_assets(DEST, recursive=False):
    an = path.split("/")[-1].split(".")[0]
    if an.startswith("Image"):
        a = unreal.load_asset(path.split(".")[0])
        if isinstance(a, unreal.Texture2D):
            EAL.delete_asset(path.split(".")[0])
            purged += 1
print(f"REACH_MARKER: {purged} stray Image_* textures purged")

ok = 0
for stem in STEMS:
    png = os.path.join(SRC_ROOT, stem, f"{stem}_tex0_base_color.png")
    if not os.path.isfile(png):
        print(f"REACH_FAIL: {stem} base-color png missing")
        continue
    task = unreal.AssetImportTask()
    task.filename = png
    task.destination_path = DEST
    task.destination_name = f"T_{stem}_base"
    task.automated = True
    task.save = True
    task.replace_existing = True
    tools.import_asset_tasks([task])
    base = EAL.load_asset(f"{DEST}/T_{stem}_base")
    if not isinstance(base, unreal.Texture2D):
        print(f"REACH_FAIL: {stem} texture did not import")
        continue

    mat_path = f"{DEST}/M_{stem}"
    if EAL.does_asset_exist(mat_path):
        EAL.delete_asset(mat_path)
    mat = tools.create_asset(f"M_{stem}", DEST, unreal.Material,
                             unreal.MaterialFactoryNew())
    mat.set_editor_property("two_sided", True)      # foliage reads from both faces
    ts = ML.create_material_expression(mat, unreal.MaterialExpressionTextureSample,
                                       -450, -100)
    ts.texture = base
    ML.connect_material_property(ts, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = ML.create_material_expression(mat, unreal.MaterialExpressionConstant,
                                          -450, 150)
    rough.set_editor_property("r", 0.8)
    ML.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    # EMISSIVE: nothing, deliberately. The Brightness War stays won.
    ML.recompile_material(mat)
    EAL.save_loaded_asset(mat)

    mesh = EAL.load_asset(f"{DEST}/{stem}")
    if not isinstance(mesh, unreal.StaticMesh):
        print(f"REACH_FAIL: {stem} mesh missing")
        continue
    for si in range(mesh.get_num_sections(0)):
        mesh.set_material(si, mat)
    EAL.save_loaded_asset(mesh)
    print(f"REACH_MARKER: exotic {stem} re-dressed (T_{stem}_base wired)")
    ok += 1

EAL.save_directory(DEST, recursive=True)
print(f"REACH_MARKER: exotic texture repair {ok}/6")
assert ok >= 4, "EXOTIC_TEX_REPAIR_INCOMPLETE"
print("VERDANT_EXOTIC_TEX_DONE")
