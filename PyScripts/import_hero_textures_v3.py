"""Import the retextured hero's 4K PBR maps + build M_HeroPBR + assign to SCB2Hero.

Maps come from the Meshy retexture task (same UVs as the rigged mesh). Material:
clear-coat (wet sci-fi shell) with base/metallic/roughness/normal/emissive wired.
Every connect_material_property result is checked â€” silent unconnected pins gave
us white materials once before (fix_materials.py lesson).
"""
import os

import unreal

TEX_DIR = r"C:\Users\Atomn\mario2\_prep\meshy_api_drops\hero_retex"
DEST = "/Game/Art/HeroSkelV3"
MAPS = {
    "base_color": ("T_Hero_BaseColor", True, unreal.TextureCompressionSettings.TC_DEFAULT),
    "metallic": ("T_Hero_Metallic", False, unreal.TextureCompressionSettings.TC_DEFAULT),
    "roughness": ("T_Hero_Roughness", False, unreal.TextureCompressionSettings.TC_DEFAULT),
    "normal": ("T_Hero_Normal", False, unreal.TextureCompressionSettings.TC_NORMALMAP),
    "emission": ("T_Hero_Emission", True, unreal.TextureCompressionSettings.TC_DEFAULT),
}

tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

# ---- 1) textures ----
textures = {}
for kind, (name, srgb, comp) in MAPS.items():
    src = os.path.join(TEX_DIR, f"hero_tex0_{kind}.png")
    if not os.path.isfile(src):
        print(f"TEX_MISSING: {src}")
        continue
    task = unreal.AssetImportTask()
    task.filename = src
    task.destination_path = DEST
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = True
    tools.import_asset_tasks([task])
    tex = unreal.load_asset(f"{DEST}/{name}")
    if not tex:
        raise SystemExit(f"TEX_IMPORT_FAILED: {name}")
    tex.set_editor_property("srgb", srgb)
    tex.set_editor_property("compression_settings", comp)
    textures[kind] = tex
    print(f"TEX_OK: {name}")

# ---- 2) M_HeroPBR ----
mat_path = f"{DEST}/M_HeroPBR"
if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
    unreal.EditorAssetLibrary.delete_asset(mat_path)
mat = tools.create_asset("M_HeroPBR", DEST, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_CLEAR_COAT)
# Without this usage flag, -game refuses the material on skeletal meshes and
# renders DefaultMaterial gray ("missing bUsedWithSkeletalMesh=True" in the log).
mat.set_editor_property("used_with_skeletal_mesh", True)
mat.set_editor_property("used_with_morph_targets", True)


def sample(kind, sampler, x, y):
    e = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, x, y)
    e.texture = textures[kind]
    e.sampler_type = sampler
    return e


ok = []
if "base_color" in textures:
    e = sample("base_color", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, -700, -400)
    ok.append(("base", mel.connect_material_property(e, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)))
if "metallic" in textures:
    e = sample("metallic", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR, -700, -150)
    ok.append(("metal", mel.connect_material_property(e, "R", unreal.MaterialProperty.MP_METALLIC)))
if "roughness" in textures:
    e = sample("roughness", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR, -700, 100)
    ok.append(("rough", mel.connect_material_property(e, "R", unreal.MaterialProperty.MP_ROUGHNESS)))
if "normal" in textures:
    e = sample("normal", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, -700, 350)
    ok.append(("normal", mel.connect_material_property(e, "RGB", unreal.MaterialProperty.MP_NORMAL)))
if "emission" in textures:
    e = sample("emission", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, -900, 600)
    mult = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -500, 600)
    boost = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -700, 750)
    boost.set_editor_property("r", 4.0)  # bloom-tuned amber eye glow
    mel.connect_material_expressions(e, "RGB", mult, "A")
    mel.connect_material_expressions(boost, "", mult, "B")
    ok.append(("emissive", mel.connect_material_property(mult, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)))

# Wet shell: 5.7's Python enum no longer exposes the clear-coat pins
# (MP_CUSTOM_DATA0/1 removed), but UNCONNECTED clear-coat pins default to
# coat=1.0 / coat-roughness=0.1 â€” setting the shading model alone is the wet look.

for name, good in ok:
    print(f"CONNECT {name}: {good}")
if not all(good for _, good in ok):
    raise SystemExit("MATERIAL_CONNECT_FAILED")

mel.recompile_material(mat)
# save_loaded_asset IMMEDIATELY after recompile â€” the fix_materials.py pattern.
# (A trailing save_directory left the expression graph unsaved: 0 expressions on reload.)
unreal.EditorAssetLibrary.save_loaded_asset(mat)

# ---- 3) assign to the skeletal mesh ----
sm = unreal.load_asset(f"{DEST}/SCB2Hero")
if not isinstance(sm, unreal.SkeletalMesh):
    raise SystemExit("NO_SKELMESH")
mats = list(sm.get_editor_property("materials"))
for i in range(len(mats)):
    mats[i] = unreal.SkeletalMaterial(
        material_interface=mat,
        material_slot_name=mats[i].get_editor_property("material_slot_name"))
sm.set_editor_property("materials", mats)
unreal.EditorAssetLibrary.save_loaded_asset(sm)
print(f"ASSIGNED M_HeroPBR to {len(mats)} slot(s)")

unreal.EditorAssetLibrary.save_directory(DEST, recursive=True)

chk = unreal.load_asset(mat_path)
print(f"VERIFY_USAGE skeletal={chk.get_editor_property('used_with_skeletal_mesh')}")
print("HERO_TEXTURES_DONE")

