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
MEL.connect_material_property(mul(m, mul(m, streak, const3(m, 1.6, 1.9, 2.2, -520, 60),
                                         -400, 0, a_out="R"), bright, -280, 40), "",
                              unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.connect_material_property(mul(m, streak, const(m, 0.62, -520, 420), -400, 380, a_out="R"),
                              "", unreal.MaterialProperty.MP_OPACITY)
finish(m, "M_VR_WaterSheet forged (falling panner, v2 loud)")

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
MEL.connect_material_property(mul(m, inv, const3(m, 0.50, 0.12, 1.15, -640, 200), -480, 60),
                              "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.connect_material_property(mul(m, inv, const(m, 0.38, -640, 360), -480, 280), "",
                              unreal.MaterialProperty.MP_OPACITY)
finish(m, "M_VR_VioletSeep forged (DEEP violet — daylight turned it pink once)")

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

# ======================= v2 (Round 2) forges =======================
def depth_fade(mat, x, y, dist):
    n = MEL.create_material_expression(mat, unreal.MaterialExpressionDepthFade, x, y)
    n.set_editor_property("fade_distance_default", dist)
    return n


# --------------------------------------------------------- M_VR_WaterFlow
# The river: streaks pan ALONG the flow (V), DepthFade darkens the deeps and
# foams the banks — true depth cueing at unlit-translucent cost.
m = new_mat("M_VR_WaterFlow")
set_translucent_unlit(m)
pan = MEL.create_material_expression(m, unreal.MaterialExpressionPanner, -1050, -60)
pan.set_editor_property("speed_y", 0.35)
streak = sample(m, tex("water_streak"), -880, -60, linear=True)
MEL.connect_material_expressions(pan, "", streak, "Coordinates")
shallow = depth_fade(m, -880, 200, 400.0)
deep_col = const3(m, 0.02, 0.10, 0.12, -880, 340)
base_col = mul(m, const3(m, 0.35, 0.75, 0.75, -700, -160), add(
    m, const(m, 0.7, -700, 40), mul(m, breath_node(m, -700, 120),
    const(m, 0.4, -700, 200), -580, 140), -460, 80), -520, -100)
body = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -420, 100)
MEL.connect_material_expressions(deep_col, "", body, "A")
MEL.connect_material_expressions(mul(m, streak, base_col, -520, -20, a_out="R"), "", body, "B")
MEL.connect_material_expressions(shallow, "", body, "Alpha")
foam_edge = MEL.create_material_expression(m, unreal.MaterialExpressionOneMinus, -700, 420)
MEL.connect_material_expressions(depth_fade(m, -880, 440, 110.0), "", foam_edge, "")
foam = mul(m, foam_edge, const3(m, 1.3, 1.35, 1.3, -700, 540), -560, 460)
MEL.connect_material_property(add(m, body, foam, -300, 200), "",
                              unreal.MaterialProperty.MP_EMISSIVE_COLOR)
op_deep = MEL.create_material_expression(m, unreal.MaterialExpressionOneMinus, -560, 640)
MEL.connect_material_expressions(depth_fade(m, -700, 660, 400.0), "", op_deep, "")
MEL.connect_material_property(add(m, const(m, 0.5, -560, 580), mul(
    m, op_deep, const(m, 0.25, -560, 720), -440, 660), -320, 620), "",
    unreal.MaterialProperty.MP_OPACITY)
finish(m, "M_VR_WaterFlow forged (the river knows its depth)")

# --------------------------------------------------------- M_VR_WaterDeep
# The pool: no directional flow — two slow counter-panners shimmer; the same
# DepthFade depth cue + foam rim. Retires the round-1 pancake (M_VR_Pool).
m = new_mat("M_VR_WaterDeep")
set_translucent_unlit(m, two_sided=False)
p1 = MEL.create_material_expression(m, unreal.MaterialExpressionPanner, -1050, -80)
p1.set_editor_property("speed_x", 0.05)
s1 = sample(m, tex("water_streak"), -880, -80, linear=True)
MEL.connect_material_expressions(p1, "", s1, "Coordinates")
p2 = MEL.create_material_expression(m, unreal.MaterialExpressionPanner, -1050, 120)
p2.set_editor_property("speed_x", -0.035)
s2 = sample(m, tex("water_streak"), -880, 120, linear=True)
MEL.connect_material_expressions(p2, "", s2, "Coordinates")
shimmer = add(m, mul(m, s1, const(m, 0.4, -700, -40), -640, -60, a_out="R"),
              mul(m, s2, const(m, 0.4, -700, 160), -640, 140, a_out="R"), -520, 40)
shallow = depth_fade(m, -880, 320, 420.0)
body = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -400, 120)
MEL.connect_material_expressions(const3(m, 0.015, 0.09, 0.11, -640, 260), "", body, "A")
MEL.connect_material_expressions(mul(m, const3(m, 0.30, 0.72, 0.72, -640, 380),
                                     add(m, const(m, 0.55, -640, 500), shimmer, -520, 460),
                                     -460, 400), "", body, "B")
MEL.connect_material_expressions(shallow, "", body, "Alpha")
foam_edge = MEL.create_material_expression(m, unreal.MaterialExpressionOneMinus, -640, 620)
MEL.connect_material_expressions(depth_fade(m, -820, 640, 120.0), "", foam_edge, "")
MEL.connect_material_property(add(m, body, mul(m, foam_edge, const3(m, 1.25, 1.3, 1.25,
                                  -640, 740), -520, 660), -260, 240), "",
                              unreal.MaterialProperty.MP_EMISSIVE_COLOR)
op_deep = MEL.create_material_expression(m, unreal.MaterialExpressionOneMinus, -520, 840)
MEL.connect_material_expressions(depth_fade(m, -660, 860, 420.0), "", op_deep, "")
MEL.connect_material_property(add(m, const(m, 0.48, -520, 780), mul(
    m, op_deep, const(m, 0.3, -520, 920), -400, 860), -280, 820), "",
    unreal.MaterialProperty.MP_OPACITY)
finish(m, "M_VR_WaterDeep forged (the pool has a bottom now)")

# ------------------------------------------------------------- M_VR_Mist
m = new_mat("M_VR_Mist")
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
m.set_editor_property("two_sided", True)
c_mask = sample(m, tex("cloud_soft"), -700, -60, linear=True)
gust = MEL.create_material_expression(m, unreal.MaterialExpressionCollectionParameter, -700, 160)
gust.set_editor_property("collection", mpc)
gust.set_editor_property("parameter_name", "Gust")
strength = add(m, const(m, 1.0, -560, 140), mul(m, gust, const(m, 0.4, -560, 220),
               -470, 180), -380, 160)
soft = depth_fade(m, -700, 300, 300.0)
MEL.connect_material_property(mul(m, mul(m, mul(m, c_mask, const(m, 0.06, -560, -20),
                                  -470, -40, a_out="R"), strength, -330, 40), soft,
                                  -240, 100), "",
                              unreal.MaterialProperty.MP_EMISSIVE_COLOR)
finish(m, "M_VR_Mist forged (whisper, not saucer)")

# --------------------------------------------------------- M_VR_TunnelSap
# The Sapline Hollow burns awake — a DEDICATED material so M_VR_SapVein's C3
# dormancy (VeinAwake 0.05) stays law outside the tunnel.
m = new_mat("M_VR_TunnelSap")
MEL.connect_material_property(const3(m, 0.06, 0.04, 0.02, -500, -120), "",
                              unreal.MaterialProperty.MP_BASE_COLOR)
pulse = add(m, const(m, 1.0, -500, 120), mul(m, breath_node(m, -500, 200),
            const(m, 0.3, -500, 280), -400, 220), -300, 160)
MEL.connect_material_property(mul(m, const3(m, 3.0, 1.5, 0.45, -500, 20), pulse, -220, 80),
                              "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
finish(m, "M_VR_TunnelSap forged (the sapline wakes)")

# -------------------------------------------------------- M_VR_AlphaShell
# The boss wears his history: scar-dark bronze, amber scratch-glow at the rims.
m = new_mat("M_VR_AlphaShell")
MEL.connect_material_property(const3(m, 0.05, 0.035, 0.02, -700, -160), "",
                              unreal.MaterialProperty.MP_BASE_COLOR)
MEL.connect_material_property(const(m, 0.55, -700, 40), "",
                              unreal.MaterialProperty.MP_ROUGHNESS)
scr = sample(m, tex("bark"), -700, 180)
fres = MEL.create_material_expression(m, unreal.MaterialExpressionFresnel, -700, 420)
fres.set_editor_property("exponent", 3.0)
fres.set_editor_property("base_reflect_fraction", 0.03)
MEL.connect_material_property(mul(m, mul(m, mul(m, scr, const3(m, 2.0, 0.5, 0.15, -560, 260),
                                  -470, 220, a_out="R"), fres, -350, 280), const(
                                  m, 0.35, -350, 400), -240, 320), "",
                              unreal.MaterialProperty.MP_EMISSIVE_COLOR)
finish(m, "M_VR_AlphaShell forged (scarred bronze)")

# ------------------------------------------------------------ M_VR_Frond
m = new_mat("M_VR_Frond")
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
m.set_editor_property("two_sided", True)
MEL.connect_material_property(mul(m, sample(m, tex("canopy_top"), -900, -200),
                                  const3(m, 0.9, 1.15, 0.6, -900, -20), -720, -120),
                              "", unreal.MaterialProperty.MP_BASE_COLOR)
MEL.connect_material_property(const(m, 0.85, -900, 120), "",
                              unreal.MaterialProperty.MP_ROUGHNESS)
mask = sample(m, tex("moss_mask"), -900, 260, linear=True)
MEL.connect_material_property(add(m, mask, const(m, 0.35, -760, 380), -640, 320,
                                  a_out="R"), "", unreal.MaterialProperty.MP_OPACITY_MASK)
t_node = MEL.create_material_expression(m, unreal.MaterialExpressionTime, -1300, 500)
wp = MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -1300, 620)
wpx = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -1160, 620)
wpx.set_editor_property("r", True)
wpx.set_editor_property("g", False)
wpx.set_editor_property("b", False)
wpx.set_editor_property("a", False)
MEL.connect_material_expressions(wp, "", wpx, "")
phase = add(m, mul(m, t_node, const(m, 0.16, -1160, 500), -1040, 520),
            mul(m, wpx, const(m, 0.00013, -1160, 700), -1040, 640), -920, 560)
sine = MEL.create_material_expression(m, unreal.MaterialExpressionSine, -800, 560)
MEL.connect_material_expressions(phase, "", sine, "")
sway = mul(m, mul(m, sine, breath_node(m, -800, 700), -680, 600),
           const(m, 18.0, -680, 760), -560, 660)
ap1 = MEL.create_material_expression(m, unreal.MaterialExpressionAppendVector, -440, 640)
MEL.connect_material_expressions(sway, "", ap1, "A")
MEL.connect_material_expressions(mul(m, sway, const(m, 0.6, -560, 820), -500, 760), "", ap1, "B")
ap2 = MEL.create_material_expression(m, unreal.MaterialExpressionAppendVector, -320, 670)
MEL.connect_material_expressions(ap1, "", ap2, "A")
MEL.connect_material_expressions(mul(m, sway, const(m, 0.25, -560, 880), -440, 820), "", ap2, "B")
MEL.connect_material_property(ap2, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
finish(m, "M_VR_Frond forged (breathing leaves)")

# ----------------------------------------------------------- M_VR_Fungus
m = new_mat("M_VR_Fungus")
MEL.connect_material_property(const3(m, 0.10, 0.055, 0.022, -500, -120), "",
                              unreal.MaterialProperty.MP_BASE_COLOR)
MEL.connect_material_property(const(m, 0.8, -500, 60), "",
                              unreal.MaterialProperty.MP_ROUGHNESS)
ffres = MEL.create_material_expression(m, unreal.MaterialExpressionFresnel, -500, 220)
ffres.set_editor_property("exponent", 3.2)
ffres.set_editor_property("base_reflect_fraction", 0.02)
MEL.connect_material_property(mul(m, ffres, const3(m, 0.28, 0.13, 0.035, -500, 380),
                                  -360, 280), "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
finish(m, "M_VR_Fungus forged (quiet bronze)")

# ------------------------------------------- assign kit-mesh default materials
ASSIGN = {
    "heartwood_trunk": "M_VR_Bark", "root_floor": "M_VR_GroundMoss",
    "branch_b1": "M_VR_Bark", "branch_b2": "M_VR_Bark",
    "branch_b3": "M_VR_Bark", "branch_b4": "M_VR_Bark",
    "canopy_blob_a": "M_VR_Canopy", "canopy_blob_b": "M_VR_Canopy",
    "canopy_blob_c": "M_VR_Canopy", "canopy_below": "M_VR_Canopy",
    "cloud_puff": "M_VR_Cloud", "gloom_ring": "M_VR_Gloom",
    "gloom_disc": "M_VR_Gloom", "seep_card": "M_VR_VioletSeep",
    "water_sheet": "M_VR_WaterSheet", "pool_disc": "M_VR_WaterDeep",
    "river_surface": "M_VR_WaterFlow", "pool_surface": "M_VR_WaterDeep",
    "mist_puff": "M_VR_Mist", "tunnel_helix": "M_VR_Bark",
    "knothole_arch": "M_VR_EdgeGlow", "arena_pad": "M_VR_Bark",
    "knot_boulder": "M_VR_Bark", "fern_clump": "M_VR_Frond",
    "vine_curtain": "M_VR_Frond", "flower_stalk": "M_VR_Frond",
    "fungus_shelf": "M_VR_Fungus",
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
