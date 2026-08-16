"""Which material-expression classes actually exist and create in 5.7 Python?
A missing class that returns None leaves inputs unconnected (compiling as 0)
without any error — the silent-zero trap."""
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
DEST = "/Game/Art/Verdant"

path = f"{DEST}/M_ZZ_NodeCheck"
if EAL.does_asset_exist(path):
    EAL.delete_asset(path)
m = tools.create_asset("M_ZZ_NodeCheck", DEST, unreal.Material,
                       unreal.MaterialFactoryNew())

NAMES = ["MaterialExpressionAbs", "MaterialExpressionFrac",
         "MaterialExpressionMax", "MaterialExpressionMin",
         "MaterialExpressionDistance", "MaterialExpressionDotProduct",
         "MaterialExpressionConstant2Vector", "MaterialExpressionSaturate",
         "MaterialExpressionSubtract", "MaterialExpressionDivide",
         "MaterialExpressionOneMinus", "MaterialExpressionSine",
         "MaterialExpressionPanner", "MaterialExpressionAppendVector",
         "MaterialExpressionComponentMask", "MaterialExpressionNormalize",
         "MaterialExpressionFresnel", "MaterialExpressionDepthFade",
         "MaterialExpressionPower", "MaterialExpressionSmoothStep"]
for nm in NAMES:
    cls = getattr(unreal, nm, None)
    if cls is None:
        print(f"NODECHECK: {nm} = NO SUCH CLASS")
        continue
    try:
        node = MEL.create_material_expression(m, cls, 0, 0)
        print(f"NODECHECK: {nm} = {'ok' if node is not None else 'CREATED NONE'}")
    except Exception as ex:
        print(f"NODECHECK: {nm} = CREATE FAILED: {ex}")
EAL.delete_asset(path)
print("NODECHECK_DONE")
