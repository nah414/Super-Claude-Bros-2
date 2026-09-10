"""Fifth instrument, atom-level: R = ComponentMask_R(TexCoord) (the suspect),
G = full _edge_prox chain. Healthy: red sweeps 0->1 across the channel, green
0 mid-channel -> 1 at the skirts."""
import os
import sys

import unreal

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import water_forge as WF

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
DEST = "/Game/Art/Verdant"

path = f"{DEST}/M_ZZ_AtomDebug"
if EAL.does_asset_exist(path):
    EAL.delete_asset(path)
m = tools.create_asset("M_ZZ_AtomDebug", DEST, unreal.Material,
                       unreal.MaterialFactoryNew())
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
m.set_editor_property("two_sided", True)

tc = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -900, 0)
ux = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -770, 0)
ux.set_editor_property("r", True)
ux.set_editor_property("g", False)
ux.set_editor_property("b", False)
ux.set_editor_property("a", False)
MEL.connect_material_expressions(tc, "", ux, "")

ep = WF._edge_prox(m, -900, 300)

ap1 = MEL.create_material_expression(m, unreal.MaterialExpressionAppendVector, -300, 60)
MEL.connect_material_expressions(ux, "", ap1, "A")
MEL.connect_material_expressions(ep, "", ap1, "B")
ap2 = MEL.create_material_expression(m, unreal.MaterialExpressionAppendVector, -180, 90)
MEL.connect_material_expressions(ap1, "", ap2, "A")
z = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -300, 220)
z.set_editor_property("r", 0.0)
MEL.connect_material_expressions(z, "", ap2, "B")
MEL.connect_material_property(ap2, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
op = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -900, 500)
op.set_editor_property("r", 1.0)
MEL.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)
MEL.recompile_material(m)
EAL.save_loaded_asset(m)
mesh = EAL.load_asset(f"{DEST}/river_surface")
mesh.set_material(0, m)
EAL.save_loaded_asset(mesh)
print("ATOMDEBUG: R = mask(TexCoord).R, G = edge_prox — read the channels")
print("ATOMDEBUG_DONE")
