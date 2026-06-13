"""Forge M_UnlightPBR — the Unlight's skin (Bible §8 recipe): ink-black albedo,
violet emissive burning at the silhouette (fresnel), worn over the Dragonlord rig.
"""
import unreal

MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
DEST = "/Game/Art/DragonSkelV1"

mat = tools.create_asset("M_UnlightPBR", DEST, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property("used_with_skeletal_mesh", True)

# ink-black albedo with the faintest violet bruise
base = MEL.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -650, -120)
base.set_editor_property("parameter_name", "Base")
base.set_editor_property("default_value", unreal.LinearColor(0.014, 0.011, 0.030, 1.0))
ok_base = MEL.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)

# emissive = fresnel(edge) * burning violet — "violet where a face should be"
fres = MEL.create_material_expression(mat, unreal.MaterialExpressionFresnel, -650, 160)
fres.set_editor_property("exponent", 3.2)
fres.set_editor_property("base_reflect_fraction", 0.02)
violet = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -650, 320)
violet.set_editor_property("constant", unreal.LinearColor(2.8, 0.5, 4.2, 1.0))
mul = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -380, 220)
MEL.connect_material_expressions(fres, "", mul, "A")
MEL.connect_material_expressions(violet, "", mul, "B")
ok_em = MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

metal = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -650, 500)
metal.set_editor_property("r", 0.1)
ok_m = MEL.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
rough = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -650, 620)
rough.set_editor_property("r", 0.62)
ok_r = MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

MEL.recompile_material(mat)
EAL.save_loaded_asset(mat)
print(f"UNLIGHT_MAT_DONE: base={ok_base} emissive={ok_em} metal={ok_m} rough={ok_r}")
