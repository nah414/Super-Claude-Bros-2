"""Forge M_SparkPlasma — the power-VFX material (Adam round 7: 'balls should be
plasma'). Unlit + ADDITIVE + fresnel-shaped emissive: hot core, soft glowing rim,
blooms hard under the cinematic post. One material, tinted per use via the
'Tint' vector parameter (white-hot bolts / orange fire licks / amber shockwave).

Run: UnrealEditor-Cmd.exe <proj> -ExecutePythonScript=PyScripts/build_power_materials.py -RenderOffscreen -unattended
"""
import unreal

DEST = "/Game/Art/FX"
NAME = "M_SparkPlasma"
PATH = f"{DEST}/{NAME}"

tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

if unreal.EditorAssetLibrary.does_asset_exist(PATH):
    unreal.EditorAssetLibrary.delete_asset(PATH)

mat = tools.create_asset(NAME, DEST, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
mat.set_editor_property("two_sided", True)

# Fresnel: 0 facing the camera (the hot core), 1 at the rim (the soft edge).
fres = mel.create_material_expression(mat, unreal.MaterialExpressionFresnel, -700, 0)
fres.set_editor_property("exponent", 2.4)
fres.set_editor_property("base_reflect_fraction", 0.02)

core = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -700, -250)
core.set_editor_property("constant", unreal.LinearColor(12.0, 6.0, 2.0, 1.0))   # white-hot heart

edge = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -700, -120)
edge.set_editor_property("constant", unreal.LinearColor(0.6, 0.18, 0.02, 1.0))  # dim amber halo

lerp = mel.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -450, -100)
ok = []
ok.append(("lerpA", mel.connect_material_expressions(core, "", lerp, "A")))
ok.append(("lerpB", mel.connect_material_expressions(edge, "", lerp, "B")))
ok.append(("lerpAlpha", mel.connect_material_expressions(fres, "", lerp, "Alpha")))

tint = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -450, 120)
tint.set_editor_property("parameter_name", "Tint")
tint.set_editor_property("default_value", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))

mult = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -220, 0)
ok.append(("multA", mel.connect_material_expressions(lerp, "", mult, "A")))
ok.append(("multB", mel.connect_material_expressions(tint, "", mult, "B")))
ok.append(("emissive", mel.connect_material_property(mult, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)))

for name, good in ok:
    print(f"CONNECT {name}: {good}")
if not all(good for _, good in ok):
    raise SystemExit("PLASMA_CONNECT_FAILED")

mel.recompile_material(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat)   # save IMMEDIATELY after recompile (house law)
print("PLASMA_MATERIAL_DONE")
