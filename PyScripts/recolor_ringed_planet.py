"""Surgical recolor of the ringed sky body (moon_large_red) — rebuild ONLY its self-lit
material to a rust-red, dimmer emissive so it reads as a reddish planet that's visible but
not glowing. Touches only M_moon_large_red_lit + its mesh; the other celestial bodies and
the map are untouched (the placed StaticMeshActor uses the mesh's material, so no map edit).

Values mirror import_celestial.py's table (kept in sync). Reddish hue is web-grounded:
Mars/iron-oxide is rust-red / ochre, not pure red.

  UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/recolor_ringed_planet.py
      -unattended -nosplash -RenderOffscreen -nopause
"""
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

DEST = "/Game/Art/Celestial/moon_large_red"
MESH = f"{DEST}/SM_moon_large_red"
MAT_NAME = "M_moon_large_red_lit"
MAT = f"{DEST}/{MAT_NAME}"

TINT = (1.00, 0.30, 0.17)   # rust-red (Mars iron-oxide); tune here
BRIGHT = 0.50               # emissive scale: visible but not glaring


def find_base_tex():
    cands = [EAL.load_asset(p) for p in EAL.list_assets(DEST, recursive=True)]
    cands = [t for t in cands if isinstance(t, unreal.Texture2D)]
    for t in cands:
        if any(k in t.get_name().lower() for k in ("base", "albedo", "color", "diffuse")):
            return t
    return cands[0] if cands else None


tex = find_base_tex()
if EAL.does_asset_exist(MAT):
    EAL.delete_asset(MAT)
mat = tools.create_asset(MAT_NAME, DEST, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
mat.set_editor_property("two_sided", True)

tintc = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -500, 200)
tintc.set_editor_property("constant",
                          unreal.LinearColor(TINT[0] * BRIGHT, TINT[1] * BRIGHT, TINT[2] * BRIGHT, 1.0))
if tex:
    ts = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -500, 0)
    ts.set_editor_property("texture", tex)
    mul = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -220, 60)
    MEL.connect_material_expressions(ts, "", mul, "A")
    MEL.connect_material_expressions(tintc, "", mul, "B")
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
else:
    MEL.connect_material_property(tintc, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.recompile_material(mat)
EAL.save_loaded_asset(mat)

mesh = EAL.load_asset(MESH)
if mesh:
    mesh.set_material(0, mat)
    EAL.save_loaded_asset(mesh)

print(f"RECOLOR_PLANET: tint={TINT} bright={BRIGHT} "
      f"tex={tex.get_name() if tex else None} mesh={'ok' if mesh else 'MISSING'}")
