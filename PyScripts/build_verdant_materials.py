"""Forge the VERDANT REACH material family + MPC_VerdantBreath.

One collection scalar ("Breath", driven 10Hz by AVerdantBreath) makes the whole
world inhale: canopy WPO sway, moss-band glow, waterfall shimmer, blossom pulse.
Palette law in material form: greens + sun-gold + bronze everywhere; violet
exists ONLY in the under-dark pair (Gloom/Seep); amber is the safety grammar
(MossBand, BlossomStub, EdgeGlow). Emissives stay damped — the Brightness War
stays won. Rerun-safe: materials are deleted + reforged, the MPC is updated.
"""
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
DEST = "/Game/Art/Verdant"

assert hasattr(unreal, "MaterialParameterCollectionFactoryNew"), \
    "MPC_FACTORY_MISSING: MaterialParameterCollectionFactoryNew not in this build's python API"

# ------------------------------------------------------------------ the MPC
MPC_PATH = f"{DEST}/MPC_VerdantBreath"
mpc = EAL.load_asset(MPC_PATH)
if not mpc:
    mpc = tools.create_asset("MPC_VerdantBreath", DEST,
                             unreal.MaterialParameterCollection,
                             unreal.MaterialParameterCollectionFactoryNew())
assert mpc, "MPC_CREATE_FAILED"
params = []
for pname, dv in (("Breath", 0.5), ("Gust", 0.0)):
    p = unreal.CollectionScalarParameter()
    p.set_editor_property("parameter_name", pname)
    p.set_editor_property("default_value", dv)
    params.append(p)
mpc.set_editor_property("scalar_parameters", params)
EAL.save_loaded_asset(mpc)
print("REACH_MARKER: MPC_VerdantBreath ready (Breath, Gust)")


def tex(stem):
    t = EAL.load_asset(f"{DEST}/T_{stem}")
    assert t, f"TEXTURE_MISSING: T_{stem} (run import_verdant_kit.py first)"
    return t


def new_mat(name):
    path = f"{DEST}/{name}"
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    m = tools.create_asset(name, DEST, unreal.Material, unreal.MaterialFactoryNew())
    assert m, f"MAT_CREATE_FAILED: {name}"
    return m


def finish(mat, marker):
    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    print(f"REACH_MARKER: {marker}")
    return mat


def sample(mat, texture, x, y, linear=False):
    n = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, x, y)
    n.texture = texture
    if linear:
        n.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
    return n


def const(mat, v, x, y):
    n = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, x, y)
    n.set_editor_property("r", v)
    return n


def const3(mat, r, g, b, x, y):
    n = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, x, y)
    n.set_editor_property("constant", unreal.LinearColor(r, g, b, 1.0))
    return n


def breath_node(mat, x, y):
    n = MEL.create_material_expression(mat, unreal.MaterialExpressionCollectionParameter, x, y)
    n.set_editor_property("collection", mpc)
    n.set_editor_property("parameter_name", "Breath")
    return n


def mul(mat, a, b, x, y, a_out="", b_out=""):
    n = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, x, y)
    MEL.connect_material_expressions(a, a_out, n, "A")
    MEL.connect_material_expressions(b, b_out, n, "B")
    return n


def add(mat, a, b, x, y, a_out="", b_out=""):
    n = MEL.create_material_expression(mat, unreal.MaterialExpressionAdd, x, y)
    MEL.connect_material_expressions(a, a_out, n, "A")
    MEL.connect_material_expressions(b, b_out, n, "B")
    return n


def set_translucent_unlit(mat, two_sided=True):
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", two_sided)


# ------------------------------------------------------------------ M_VR_Bark
m = new_mat("M_VR_Bark")
MEL.connect_material_property(sample(m, tex("bark"), -450, -150), "RGB",
                              unreal.MaterialProperty.MP_BASE_COLOR)
MEL.connect_material_property(const(m, 0.8, -450, 120), "",
                              unreal.MaterialProperty.MP_ROUGHNESS)
finish(m, "M_VR_Bark forged")

# ------------------------------------------------------------ M_VR_GroundMoss
m = new_mat("M_VR_GroundMoss")
MEL.connect_material_property(sample(m, tex("ground_moss"), -450, -150), "RGB",
                              unreal.MaterialProperty.MP_BASE_COLOR)
MEL.connect_material_property(const(m, 0.9, -450, 120), "",
                              unreal.MaterialProperty.MP_ROUGHNESS)
finish(m, "M_VR_GroundMoss forged")

# -------------------------------------------------------------- M_VR_Canopy
# Leaves that BREATHE: WPO = sin(time + worldX) * Breath * sway amplitude.
m = new_mat("M_VR_Canopy")
m.set_editor_property("two_sided", True)
MEL.connect_material_property(sample(m, tex("canopy_top"), -700, -220), "RGB",
                              unreal.MaterialProperty.MP_BASE_COLOR)
MEL.connect_material_property(const(m, 0.85, -700, 40), "",
                              unreal.MaterialProperty.MP_ROUGHNESS)
t_node = MEL.create_material_expression(m, unreal.MaterialExpressionTime, -1150, 260)
wp = MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -1150, 380)
wpx = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -1000, 380)
wpx.set_editor_property("r", True)
wpx.set_editor_property("g", False)
wpx.set_editor_property("b", False)
wpx.set_editor_property("a", False)
MEL.connect_material_expressions(wp, "", wpx, "")
phase = add(m, mul(m, t_node, const(m, 0.16, -1000, 250), -880, 280),
            mul(m, wpx, const(m, 0.00013, -1000, 460), -880, 400), -760, 330)
sine = MEL.create_material_expression(m, unreal.MaterialExpressionSine, -640, 330)
MEL.connect_material_expressions(phase, "", sine, "")
sway = mul(m, mul(m, sine, breath_node(m, -640, 470), -520, 380),
           const(m, 42.0, -520, 520), -420, 420)
ap1 = MEL.create_material_expression(m, unreal.MaterialExpressionAppendVector, -300, 400)
MEL.connect_material_expressions(sway, "", ap1, "A")
MEL.connect_material_expressions(mul(m, sway, const(m, 0.6, -420, 560), -360, 520), "", ap1, "B")
ap2 = MEL.create_material_expression(m, unreal.MaterialExpressionAppendVector, -180, 430)
MEL.connect_material_expressions(ap1, "", ap2, "A")
MEL.connect_material_expressions(mul(m, sway, const(m, 0.25, -420, 640), -300, 580), "", ap2, "B")
MEL.connect_material_property(ap2, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
finish(m, "M_VR_Canopy forged (breathing WPO)")

# ------------------------------------------------------------ M_VR_MossBand
# The GRIPPABLE grammar: masked moss blotches, green-gold, brightening on Breath.
m = new_mat("M_VR_MossBand")
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
m.set_editor_property("two_sided", True)
MEL.connect_material_property(const3(m, 0.10, 0.16, 0.05, -700, -220), "",
                              unreal.MaterialProperty.MP_BASE_COLOR)
mask = sample(m, tex("moss_mask"), -700, 40, linear=True)
MEL.connect_material_property(mask, "R", unreal.MaterialProperty.MP_OPACITY_MASK)
glow_amt = add(m, const(m, 0.5, -700, 300), mul(m, breath_node(m, -700, 380),
               const(m, 0.7, -700, 460), -580, 400), -460, 340)
glow = mul(m, mul(m, const3(m, 0.5, 0.85, 0.22, -460, 200), glow_amt, -320, 260),
           mask, -200, 220, b_out="R")
MEL.connect_material_property(glow, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
finish(m, "M_VR_MossBand forged (breath-pulsed)")

# ------------------------------------------------------------- M_VR_Cloud
m = new_mat("M_VR_Cloud")
set_translucent_unlit(m)
c_mask = sample(m, tex("cloud_soft"), -600, -80, linear=True)
MEL.connect_material_property(mul(m, c_mask, const3(m, 0.85, 0.83, 0.78, -600, 160),
                                  -420, 0, a_out="R"), "",
                              unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.connect_material_property(mul(m, c_mask, const(m, 0.26, -600, 320), -420, 240, a_out="R"),
                              "", unreal.MaterialProperty.MP_OPACITY)
finish(m, "M_VR_Cloud forged (soft)")

# --------------------------------------------------------- M_VR_WaterSheet
m = new_mat("M_VR_WaterSheet")
set_translucent_unlit(m)
pan = MEL.create_material_expression(m, unreal.MaterialExpressionPanner, -900, -60)
pan.set_editor_property("speed_y", 0.55)
streak = sample(m, tex("water_streak"), -700, -60, linear=True)
MEL.connect_material_expressions(pan, "", streak, "Coordinates")
bright = add(m, const(m, 0.7, -700, 260), mul(m, breath_node(m, -700, 340),
             const(m, 0.5, -700, 420), -580, 360), -460, 300)
MEL.connect_material_property(mul(m, mul(m, streak, const3(m, 1.05, 1.30, 1.55, -520, 60),
                                         -400, 0, a_out="R"), bright, -280, 40), "",
                              unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.connect_material_property(mul(m, streak, const(m, 0.45, -520, 420), -400, 380, a_out="R"),
                              "", unreal.MaterialProperty.MP_OPACITY)
finish(m, "M_VR_WaterSheet forged (falling panner)")

# --------------------------------------------------------------- M_VR_Pool
m = new_mat("M_VR_Pool")
set_translucent_unlit(m, two_sided=False)
MEL.connect_material_property(const3(m, 0.10, 0.34, 0.38, -450, -60), "",
                              unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.connect_material_property(const(m, 0.55, -450, 160), "",
                              unreal.MaterialProperty.MP_OPACITY)
finish(m, "M_VR_Pool forged")

# -------------------------------------------------------------- M_VR_Gloom
m = new_mat("M_VR_Gloom")
m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
m.set_editor_property("two_sided", True)
MEL.connect_material_property(const3(m, 0.020, 0.008, 0.050, -450, -60), "",
                              unreal.MaterialProperty.MP_EMISSIVE_COLOR)
finish(m, "M_VR_Gloom forged (the under-dark)")

# --------------------------------------------------------- M_VR_VioletSeep
m = new_mat("M_VR_VioletSeep")
set_translucent_unlit(m)
uv = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -900, 0)
v_mask = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -760, 0)
v_mask.set_editor_property("r", False)
v_mask.set_editor_property("g", True)
v_mask.set_editor_property("b", False)
v_mask.set_editor_property("a", False)
MEL.connect_material_expressions(uv, "", v_mask, "")
inv = MEL.create_material_expression(m, unreal.MaterialExpressionOneMinus, -640, 0)
MEL.connect_material_expressions(v_mask, "", inv, "")
MEL.connect_material_property(mul(m, inv, const3(m, 1.5, 0.45, 2.4, -640, 200), -480, 60),
                              "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.connect_material_property(mul(m, inv, const(m, 0.55, -640, 360), -480, 280), "",
                              unreal.MaterialProperty.MP_OPACITY)
finish(m, "M_VR_VioletSeep forged (the only violet)")

# ------------------------------------------------------------ M_VR_SapVein
m = new_mat("M_VR_SapVein")
MEL.connect_material_property(const3(m, 0.06, 0.04, 0.02, -500, -120), "",
                              unreal.MaterialProperty.MP_BASE_COLOR)
awake = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -500, 120)
awake.set_editor_property("parameter_name", "VeinAwake")
awake.set_editor_property("default_value", 0.05)
MEL.connect_material_property(mul(m, const3(m, 3.2, 1.6, 0.5, -500, 280), awake, -340, 180),
                              "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
finish(m, "M_VR_SapVein forged (dormant until C3)")

# -------------------------------------------------------- M_VR_BlossomStub
m = new_mat("M_VR_BlossomStub")
MEL.connect_material_property(const3(m, 0.30, 0.12, 0.03, -600, -140), "",
                              unreal.MaterialProperty.MP_BASE_COLOR)
pulse = add(m, const(m, 0.8, -600, 120), mul(m, breath_node(m, -600, 200),
            const(m, 0.5, -600, 280), -480, 220), -360, 160)
MEL.connect_material_property(mul(m, const3(m, 3.4, 1.55, 0.42, -360, 20), pulse, -220, 80),
                              "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
finish(m, "M_VR_BlossomStub forged (the swing grammar)")

# ----------------------------------------------------------- M_VR_EdgeGlow
m = new_mat("M_VR_EdgeGlow")
MEL.connect_material_property(const3(m, 0.05, 0.03, 0.01, -600, -140), "",
                              unreal.MaterialProperty.MP_BASE_COLOR)
fres = MEL.create_material_expression(m, unreal.MaterialExpressionFresnel, -600, 100)
fres.set_editor_property("exponent", 2.6)
fres.set_editor_property("base_reflect_fraction", 0.04)
MEL.connect_material_property(mul(m, fres, const3(m, 2.4, 1.2, 0.32, -600, 260), -440, 160),
                              "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
finish(m, "M_VR_EdgeGlow forged (amber rims)")

# --------------------------------------------------------- M_VR_Silhouette
m = new_mat("M_VR_Silhouette")
MEL.connect_material_property(const3(m, 0.16, 0.20, 0.14, -450, -60), "",
                              unreal.MaterialProperty.MP_BASE_COLOR)
MEL.connect_material_property(const(m, 1.0, -450, 160), "",
                              unreal.MaterialProperty.MP_ROUGHNESS)
finish(m, "M_VR_Silhouette forged")

# -------------------------------------------------------- M_VR_VillageLight
m = new_mat("M_VR_VillageLight")
MEL.connect_material_property(const3(m, 0.25, 0.15, 0.06, -450, -140), "",
                              unreal.MaterialProperty.MP_BASE_COLOR)
MEL.connect_material_property(const3(m, 4.0, 2.1, 0.8, -450, 100), "",
                              unreal.MaterialProperty.MP_EMISSIVE_COLOR)
finish(m, "M_VR_VillageLight forged")

# ------------------------------------------- assign kit-mesh default materials
ASSIGN = {
    "heartwood_trunk": "M_VR_Bark", "root_floor": "M_VR_GroundMoss",
    "branch_b1": "M_VR_Bark", "branch_b2": "M_VR_Bark",
    "branch_b3": "M_VR_Bark", "branch_b4": "M_VR_Bark",
    "canopy_blob_a": "M_VR_Canopy", "canopy_blob_b": "M_VR_Canopy",
    "canopy_blob_c": "M_VR_Canopy", "canopy_below": "M_VR_Canopy",
    "cloud_puff": "M_VR_Cloud", "gloom_ring": "M_VR_Gloom",
    "gloom_disc": "M_VR_Gloom", "seep_card": "M_VR_VioletSeep",
    "water_sheet": "M_VR_WaterSheet", "pool_disc": "M_VR_Pool",
}
assigned = 0
for mesh_name, mat_name in ASSIGN.items():
    mesh = EAL.load_asset(f"{DEST}/{mesh_name}")
    mat = EAL.load_asset(f"{DEST}/{mat_name}")
    if mesh and mat:
        mesh.set_material(0, mat)
        EAL.save_loaded_asset(mesh)
        assigned += 1
    else:
        print(f"REACH_WARN: assign {mesh_name} <- {mat_name} skipped (missing)")
print(f"REACH_MARKER: {assigned}/{len(ASSIGN)} kit meshes wearing Verdant materials")
print("VERDANT_MATERIALS_DONE")
