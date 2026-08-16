"""Third instrument: render the river's UV0 as color (R=U across, G=V along,
fractional). If U does not sweep dark->bright across the channel, the authored
cross-UV didn't survive import and every uv_* builder is blind."""
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
DEST = "/Game/Art/Verdant"

path = f"{DEST}/M_ZZ_UVDebug"
if EAL.does_asset_exist(path):
    EAL.delete_asset(path)
m = tools.create_asset("M_ZZ_UVDebug", DEST, unreal.Material,
                       unreal.MaterialFactoryNew())
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
m.set_editor_property("two_sided", True)
tc = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -500, 0)
frac = MEL.create_material_expression(m, unreal.MaterialExpressionFrac, -370, 0)
MEL.connect_material_expressions(tc, "", frac, "")
ap = MEL.create_material_expression(m, unreal.MaterialExpressionAppendVector, -240, 0)
MEL.connect_material_expressions(frac, "", ap, "A")
z = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -370, 140)
z.set_editor_property("r", 0.0)
MEL.connect_material_expressions(z, "", ap, "B")
MEL.connect_material_property(ap, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
op = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -500, 220)
op.set_editor_property("r", 1.0)
MEL.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)
MEL.recompile_material(m)
EAL.save_loaded_asset(m)
mesh = EAL.load_asset(f"{DEST}/river_surface")
mesh.set_material(0, m)
EAL.save_loaded_asset(mesh)
print("UVDEBUG: river renders frac(UV0) — red = U across, green = V along")
print("UVDEBUG_DONE")
