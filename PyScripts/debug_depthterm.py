"""Fourth instrument: render uv_depth_ramp's DEPTH term as grayscale on the
river. Expected: white mid-channel fading to black at the waterline. Anything
else = the fault is inside the uv builders' wiring."""
import os
import sys

import unreal

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import water_forge as WF

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
DEST = "/Game/Art/Verdant"

path = f"{DEST}/M_ZZ_DepthTermDebug"
if EAL.does_asset_exist(path):
    EAL.delete_asset(path)
m = tools.create_asset("M_ZZ_DepthTermDebug", DEST, unreal.Material,
                       unreal.MaterialFactoryNew())
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
m.set_editor_property("two_sided", True)
body, depth = WF.uv_depth_ramp(m, -2100, 0, (0.16, 0.44, 0.42), (0.02, 0.10, 0.12))
MEL.connect_material_property(depth, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
op = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -500, 400)
op.set_editor_property("r", 1.0)
MEL.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)
MEL.recompile_material(m)
EAL.save_loaded_asset(m)
mesh = EAL.load_asset(f"{DEST}/river_surface")
mesh.set_material(0, m)
EAL.save_loaded_asset(mesh)
print("DEPTHTERM: river renders the uv depth term — white deeps, black shores expected")
print("DEPTHTERM_DONE")
