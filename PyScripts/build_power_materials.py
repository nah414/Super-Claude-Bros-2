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
fres.set_editor_property("exponent", 3.2)            # tighter core, faster falloff
fres.set_editor_property("base_reflect_fraction", 0.0)

core = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -700, -250)
core.set_editor_property("constant", unreal.LinearColor(18.0, 9.0, 3.0, 1.0))   # white-hot heart (bloom blowout)

edge = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -700, -120)
edge.set_editor_property("constant", unreal.LinearColor(0.04, 0.012, 0.001, 1.0))  # edges DISSOLVE (additive black = invisible — no more oval silhouette)

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

# --- TURBULENCE (round 9): plasma ROILS. World-space noise scrolled by time
# (drifting downward so flames appear to rise) modulates the brightness. ---
wpos = mel.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, -950, 350)
time = mel.create_material_expression(mat, unreal.MaterialExpressionTime, -950, 480)
drift = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -950, 560)
drift.set_editor_property("constant", unreal.LinearColor(40.0, 25.0, -160.0, 0.0))
tmul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -760, 480)
ok.append(("tmulA", mel.connect_material_expressions(time, "", tmul, "A")))
ok.append(("tmulB", mel.connect_material_expressions(drift, "", tmul, "B")))
padd = mel.create_material_expression(mat, unreal.MaterialExpressionAdd, -600, 400)
ok.append(("paddA", mel.connect_material_expressions(wpos, "", padd, "A")))
ok.append(("paddB", mel.connect_material_expressions(tmul, "", padd, "B")))
noise = mel.create_material_expression(mat, unreal.MaterialExpressionNoise, -450, 400)
noise.set_editor_property("scale", 0.035)
noise.set_editor_property("turbulence", True)
noise.set_editor_property("levels", 3)
noise.set_editor_property("output_min", 0.45)
noise.set_editor_property("output_max", 1.45)
# Position pin name varies by version; try both, and if neither sticks the node
# falls back to raw world position — moving effects still roil (meshes travel
# through the static noise field), only perfectly-stationary glow sits still.
pos_ok = mel.connect_material_expressions(padd, "", noise, "Position") \
      or mel.connect_material_expressions(padd, "", noise, "")
print(f"CONNECT noisePos: {pos_ok} (optional — world-position fallback is fine)")
roil = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -80, 100)
ok.append(("roilA", mel.connect_material_expressions(mult, "", roil, "A")))
ok.append(("roilB", mel.connect_material_expressions(noise, "", roil, "B")))
ok.append(("emissive", mel.connect_material_property(roil, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)))

for name, good in ok:
    print(f"CONNECT {name}: {good}")
if not all(good for _, good in ok):
    raise SystemExit("PLASMA_CONNECT_FAILED")

mel.recompile_material(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat)   # save IMMEDIATELY after recompile (house law)
print("PLASMA_MATERIAL_DONE")
