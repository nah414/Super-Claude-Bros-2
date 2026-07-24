"""Forge the VERDANT REACH material family + MPC_VerdantBreath.

One collection scalar ("Breath", driven 10Hz by AVerdantBreath) makes the whole
world inhale: canopy WPO sway, moss-band glow, waterfall shimmer, blossom pulse.
Palette law in material form: greens + sun-gold + bronze everywhere; violet
exists ONLY in the under-dark pair (Gloom/Seep); amber is the safety grammar
(MossBand, BlossomStub, EdgeGlow). Emissives stay damped — the Brightness War
stays won. Rerun-safe: materials are deleted + reforged, the MPC is updated.
"""
import json

import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
DEST = "/Game/Art/Verdant"

# v3: the pool's impact point feeds the ripple WPO — read from the field truth.
with open(r"C:\Users\Atomn\mario2\_prep\verdant_heartwood.json") as _f:
    FIELD = json.load(_f)
IMPACT = FIELD["pool"].get("impact", FIELD["pool"]["center"])

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
# v3: HeroPos — the parting brush reads where the hero stands (default is a
# kilometer underground so untouched worlds never part).
vp = unreal.CollectionVectorParameter()
vp.set_editor_property("parameter_name", "HeroPos")
vp.set_editor_property("default_value", unreal.LinearColor(0.0, 0.0, -100000.0, 1.0))
mpc.set_editor_property("vector_parameters", [vp])
EAL.save_loaded_asset(mpc)
print("REACH_MARKER: MPC_VerdantBreath ready (Breath, Gust, HeroPos)")


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
pan.set_editor_property("speed_y", 0.9)     # v4 flow law: the curtain keeps pace
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
pan.set_editor_property("speed_y", 0.5)     # v4: 400uu/s downstream
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
# v3: the VERTEX-COLOR foam mask (V-wakes behind rapids + bank foam, baked in
# Blender) drives real white water riding a slow foam-texture panner.
vc = MEL.create_material_expression(m, unreal.MaterialExpressionVertexColor, -880, 620)
pan_vf = MEL.create_material_expression(m, unreal.MaterialExpressionPanner, -1050, 700)
# v4 flow law: the white water RIDES DOWNSTREAM (V = along the flow). The old
# 0.06 cross-stream drift was the frozen-foam bug Adam filmed.
pan_vf.set_editor_property("speed_x", 0.0)
pan_vf.set_editor_property("speed_y", 0.55)
ftex = sample(m, tex("foam"), -880, 700, linear=True)
MEL.connect_material_expressions(pan_vf, "", ftex, "Coordinates")
white = mul(m, mul(m, ftex, vc, -740, 660, a_out="R", b_out="R"),
            const3(m, 0.9, 0.93, 0.9, -740, 780), -620, 700)
MEL.connect_material_property(add(m, add(m, body, foam, -300, 200), white, -200, 260),
                              "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
op_deep = MEL.create_material_expression(m, unreal.MaterialExpressionOneMinus, -560, 640)
MEL.connect_material_expressions(depth_fade(m, -700, 660, 400.0), "", op_deep, "")
MEL.connect_material_property(add(m, add(m, const(m, 0.5, -560, 580), mul(
    m, op_deep, const(m, 0.25, -560, 720), -440, 660), -320, 620),
    mul(m, vc, const(m, 0.3, -440, 780), -320, 740, a_out="R"), -220, 680), "",
    unreal.MaterialProperty.MP_OPACITY)
finish(m, "M_VR_WaterFlow forged (v3: the river carries real white water)")

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
MEL.connect_material_expressions(mul(m, const3(m, 0.22, 0.55, 0.58, -640, 380),
                                     add(m, const(m, 0.55, -640, 500), shimmer, -520, 460),
                                     -460, 400), "", body, "B")
MEL.connect_material_expressions(shallow, "", body, "Alpha")
foam_edge = MEL.create_material_expression(m, unreal.MaterialExpressionOneMinus, -640, 620)
MEL.connect_material_expressions(depth_fade(m, -820, 640, 120.0), "", foam_edge, "")
# v3: caustic sparkle layer + shore-foam vertex color.
pan_c = MEL.create_material_expression(m, unreal.MaterialExpressionPanner, -1050, 700)
pan_c.set_editor_property("speed_x", 0.05)
pan_c.set_editor_property("speed_y", 0.03)
caus = sample(m, tex("caustic"), -880, 700, linear=True)
MEL.connect_material_expressions(pan_c, "", caus, "Coordinates")
vc_p = MEL.create_material_expression(m, unreal.MaterialExpressionVertexColor, -880, 860)
sparkle = mul(m, caus, const3(m, 0.35, 0.42, 0.42, -740, 720), -640, 740, a_out="R")
shore = mul(m, vc_p, const3(m, 0.55, 0.57, 0.55, -740, 900), -640, 880, a_out="R")
# foam + sparkle gated by the SHALLOW mask: OneMinus(DepthFade) floods to 1
# at grazing angles and used to blanket the whole pool white — gating lets
# the grazing view fall through to the teal body (the depth Adam must SEE).
MEL.connect_material_property(add(m, add(m, add(m, body, mul(m, mul(m, foam_edge,
                                  const3(m, 0.5, 0.52, 0.5, -640, 620), -520, 660),
                                  shallow, -440, 690), -260, 240), mul(m, sparkle,
                                  shallow, -180, 260), -180, 300), mul(m, shore,
                                  const(m, 0.8, -100, 420), -100, 400), -100, 360), "",
                              unreal.MaterialProperty.MP_EMISSIVE_COLOR)
op_deep = MEL.create_material_expression(m, unreal.MaterialExpressionOneMinus, -520, 840)
MEL.connect_material_expressions(depth_fade(m, -660, 860, 420.0), "", op_deep, "")
MEL.connect_material_property(add(m, const(m, 0.48, -520, 780), mul(
    m, op_deep, const(m, 0.3, -520, 920), -400, 860), -280, 820), "",
    unreal.MaterialProperty.MP_OPACITY)
# v3: the IMPACT RIPPLE — rings travel outward from where the sky-fall lands.
wp_p = MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -1250, 1050)
wpRG = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -1130, 1050)
wpRG.set_editor_property("r", True)
wpRG.set_editor_property("g", True)
wpRG.set_editor_property("b", False)
wpRG.set_editor_property("a", False)
MEL.connect_material_expressions(wp_p, "", wpRG, "")
impRG = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -1130, 1170)
impRG.set_editor_property("r", True)
impRG.set_editor_property("g", True)
impRG.set_editor_property("b", False)
impRG.set_editor_property("a", False)
MEL.connect_material_expressions(const3(m, IMPACT[0], IMPACT[1], 0.0, -1250, 1170), "", impRG, "")
dist_p = MEL.create_material_expression(m, unreal.MaterialExpressionDistance, -1010, 1100)
MEL.connect_material_expressions(wpRG, "", dist_p, "A")
MEL.connect_material_expressions(impRG, "", dist_p, "B")
t_p = MEL.create_material_expression(m, unreal.MaterialExpressionTime, -1010, 1220)
phase_p = add(m, mul(m, dist_p, const(m, 0.011, -890, 1080), -790, 1100),
              mul(m, t_p, const(m, -4.2, -890, 1240), -790, 1220), -690, 1160)
sin_p = MEL.create_material_expression(m, unreal.MaterialExpressionSine, -590, 1160)
MEL.connect_material_expressions(phase_p, "", sin_p, "")
div_p = MEL.create_material_expression(m, unreal.MaterialExpressionDivide, -890, 1330)
MEL.connect_material_expressions(dist_p, "", div_p, "A")
MEL.connect_material_expressions(const(m, 1400.0, -1010, 1360), "", div_p, "B")
inv_p = MEL.create_material_expression(m, unreal.MaterialExpressionOneMinus, -790, 1330)
MEL.connect_material_expressions(div_p, "", inv_p, "")
sat_p = MEL.create_material_expression(m, unreal.MaterialExpressionSaturate, -690, 1330)
MEL.connect_material_expressions(inv_p, "", sat_p, "")
zrip = mul(m, mul(m, sin_p, sat_p, -490, 1240), const(m, 11.0, -490, 1330), -390, 1270)
ap0 = MEL.create_material_expression(m, unreal.MaterialExpressionAppendVector, -290, 1240)
MEL.connect_material_expressions(const(m, 0.0, -390, 1170), "", ap0, "A")
MEL.connect_material_expressions(const(m, 0.0, -390, 1200), "", ap0, "B")
apZ = MEL.create_material_expression(m, unreal.MaterialExpressionAppendVector, -190, 1260)
MEL.connect_material_expressions(ap0, "", apZ, "A")
MEL.connect_material_expressions(zrip, "", apZ, "B")
MEL.connect_material_property(apZ, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
finish(m, "M_VR_WaterDeep forged (v3: dome, sparkle, and the impact ripple)")

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

# ------------------------------------------------------------ the FROND family
# v3: one helper, four tints — and every frond learns THE PARTING BRUSH:
# plants bend away (and duck) within 220uu of HeroPos, roots staying planted
# (UV.y is the height mask). Springback rides the Breath sway for free.
def forge_frond(name, tr, tg, tb):
    m = new_mat(name)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    m.set_editor_property("two_sided", True)
    MEL.connect_material_property(mul(m, sample(m, tex("canopy_top"), -900, -200),
                                      const3(m, tr, tg, tb, -900, -20), -720, -120),
                                  "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(const(m, 0.85, -900, 120), "",
                                  unreal.MaterialProperty.MP_ROUGHNESS)
    fmask = sample(m, tex("moss_mask"), -900, 260, linear=True)
    MEL.connect_material_property(add(m, fmask, const(m, 0.35, -760, 380), -640, 320,
                                      a_out="R"), "",
                                  unreal.MaterialProperty.MP_OPACITY_MASK)
    # --- the breath sway (round-2 graph) ---
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
    # --- the parting brush ---
    hero = MEL.create_material_expression(m, unreal.MaterialExpressionCollectionParameter, -1300, 950)
    hero.set_editor_property("collection", mpc)
    hero.set_editor_property("parameter_name", "HeroPos")
    # MPC vector params are float4 — mask to RGB or the whole material fails
    # to compile (float3-vs-float4 in Distance/Subtract; the grey-frond bug).
    heroM = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -1160, 950)
    heroM.set_editor_property("r", True)
    heroM.set_editor_property("g", True)
    heroM.set_editor_property("b", True)
    heroM.set_editor_property("a", False)
    MEL.connect_material_expressions(hero, "", heroM, "")
    dist = MEL.create_material_expression(m, unreal.MaterialExpressionDistance, -1040, 950)
    MEL.connect_material_expressions(wp, "", dist, "A")
    MEL.connect_material_expressions(heroM, "", dist, "B")
    div = MEL.create_material_expression(m, unreal.MaterialExpressionDivide, -920, 950)
    MEL.connect_material_expressions(dist, "", div, "A")
    MEL.connect_material_expressions(const(m, 220.0, -1040, 1050), "", div, "B")
    inv = MEL.create_material_expression(m, unreal.MaterialExpressionOneMinus, -800, 950)
    MEL.connect_material_expressions(div, "", inv, "")
    sat = MEL.create_material_expression(m, unreal.MaterialExpressionSaturate, -700, 950)
    MEL.connect_material_expressions(inv, "", sat, "")
    fall2 = mul(m, sat, sat, -600, 950)
    subv = MEL.create_material_expression(m, unreal.MaterialExpressionSubtract, -1040, 1120)
    MEL.connect_material_expressions(wp, "", subv, "A")
    MEL.connect_material_expressions(heroM, "", subv, "B")
    subRG = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -920, 1120)
    subRG.set_editor_property("r", True)
    subRG.set_editor_property("g", True)
    subRG.set_editor_property("b", False)
    subRG.set_editor_property("a", False)
    MEL.connect_material_expressions(subv, "", subRG, "")
    ndir = MEL.create_material_expression(m, unreal.MaterialExpressionNormalize, -800, 1120)
    MEL.connect_material_expressions(subRG, "", ndir, "")
    pushxy = mul(m, ndir, mul(m, fall2, const(m, 90.0, -600, 1050), -500, 1000), -420, 1080)
    push3 = MEL.create_material_expression(m, unreal.MaterialExpressionAppendVector, -320, 1100)
    MEL.connect_material_expressions(pushxy, "", push3, "A")
    MEL.connect_material_expressions(mul(m, fall2, const(m, -31.0, -500, 1180), -420, 1180), "", push3, "B")
    uvroot = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -500, 1280)
    uvG = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -420, 1280)
    uvG.set_editor_property("r", False)
    uvG.set_editor_property("g", True)
    uvG.set_editor_property("b", False)
    uvG.set_editor_property("a", False)
    MEL.connect_material_expressions(uvroot, "", uvG, "")
    push_final = mul(m, push3, uvG, -240, 1150)
    MEL.connect_material_property(add(m, ap2, push_final, -140, 800), "",
                                  unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    finish(m, f"{name} forged (breathing + parting)")


forge_frond("M_VR_Frond", 1.0, 1.5, 0.7)
forge_frond("M_VR_FrondTeal", 0.5, 1.35, 1.2)
forge_frond("M_VR_FrondGold", 1.5, 1.2, 0.5)
forge_frond("M_VR_FrondCream", 1.35, 1.3, 1.05)

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

# ------------------------------------------------------------ M_VR_Torrent
# The falls become WATER: fast streaks + slow foam riding sculpted crescents,
# fresnel-bright edges, a downward-traveling WPO bulge phased by WorldZ (seam-
# proof across stacked segments by construction).
m = new_mat("M_VR_Torrent")
set_translucent_unlit(m, two_sided=False)
# v4 THE FLOW LAW: the DOMINANT layer is fast vertically-stretched rope noise
# (Adam's video: round cells at slow speed read as a static lace curtain).
tc_f = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -1400, -80)
tc_f.set_editor_property("u_tiling", 3.0)
pan_f = MEL.create_material_expression(m, unreal.MaterialExpressionPanner, -1250, -80)
pan_f.set_editor_property("speed_y", 1.5)
MEL.connect_material_expressions(tc_f, "", pan_f, "Coordinate")
streak = sample(m, tex("fall_rope"), -1050, -80, linear=True)
MEL.connect_material_expressions(pan_f, "", streak, "Coordinates")
pan_s = MEL.create_material_expression(m, unreal.MaterialExpressionPanner, -1250, 140)
pan_s.set_editor_property("speed_y", 0.9)
foam = sample(m, tex("foam"), -1050, 140, linear=True)
MEL.connect_material_expressions(pan_s, "", foam, "Coordinates")
body = add(m, mul(m, streak, const3(m, 0.85, 1.0, 1.15, -880, -140), -760, -100, a_out="R"),
           mul(m, foam, const3(m, 0.5, 0.52, 0.5, -880, 100), -760, 120, a_out="R"),
           -640, 0)
fres = MEL.create_material_expression(m, unreal.MaterialExpressionFresnel, -880, 280)
fres.set_editor_property("exponent", 2.2)
fres.set_editor_property("base_reflect_fraction", 0.04)
edge = mul(m, fres, const3(m, 0.4, 0.5, 0.55, -880, 420), -740, 320)
bright = add(m, const(m, 0.7, -640, 220), mul(m, breath_node(m, -640, 300),
             const(m, 0.5, -640, 380), -540, 320), -440, 260)
MEL.connect_material_property(add(m, mul(m, body, bright, -520, 60), edge, -380, 120),
                              "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.connect_material_property(add(m, add(m, mul(m, streak, const(m, 0.55, -640, 500),
                                  -540, 460, a_out="R"), mul(m, foam, const(m, 0.45, -640, 580),
                                  -540, 560, a_out="R"), -440, 500), const(m, 0.22, -440, 620),
                                  -340, 540), "", unreal.MaterialProperty.MP_OPACITY)
wpT = MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -1250, 700)
wpB = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -1130, 700)
wpB.set_editor_property("r", False)
wpB.set_editor_property("g", False)
wpB.set_editor_property("b", True)
wpB.set_editor_property("a", False)
MEL.connect_material_expressions(wpT, "", wpB, "")
t_t = MEL.create_material_expression(m, unreal.MaterialExpressionTime, -1250, 830)
phase_t = add(m, mul(m, wpB, const(m, 0.004, -1130, 780), -1010, 740),
              mul(m, t_t, const(m, 3.5, -1130, 900), -1010, 860), -890, 800)
sin_t = MEL.create_material_expression(m, unreal.MaterialExpressionSine, -780, 800)
MEL.connect_material_expressions(phase_t, "", sin_t, "")
vn = MEL.create_material_expression(m, unreal.MaterialExpressionVertexNormalWS, -780, 920)
MEL.connect_material_property(mul(m, vn, mul(m, sin_t, const(m, 14.0, -660, 860),
                                  -560, 830), -460, 880), "",
                              unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
finish(m, "M_VR_Torrent forged (the falls become water)")

# -------------------------------------------------------------- M_VR_Churn
m = new_mat("M_VR_Churn")
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
m.set_editor_property("two_sided", True)
pan_a = MEL.create_material_expression(m, unreal.MaterialExpressionPanner, -1050, -60)
pan_a.set_editor_property("speed_x", 0.25)
f_a = sample(m, tex("foam"), -880, -60, linear=True)
MEL.connect_material_expressions(pan_a, "", f_a, "Coordinates")
pan_b = MEL.create_material_expression(m, unreal.MaterialExpressionPanner, -1050, 160)
pan_b.set_editor_property("speed_x", -0.2)
f_b = sample(m, tex("foam"), -880, 160, linear=True)
MEL.connect_material_expressions(pan_b, "", f_b, "Coordinates")
gustn = MEL.create_material_expression(m, unreal.MaterialExpressionCollectionParameter, -880, 340)
gustn.set_editor_property("collection", mpc)
gustn.set_editor_property("parameter_name", "Gust")
swell = add(m, const(m, 1.0, -740, 320), mul(m, gustn, const(m, 0.4, -740, 400),
            -660, 360), -560, 340)
mix = add(m, mul(m, f_a, const(m, 0.5, -740, -20), -660, -40, a_out="R"),
          mul(m, f_b, const(m, 0.5, -740, 180), -660, 160, a_out="R"), -560, 60)
soft = depth_fade(m, -740, 480, 250.0)
MEL.connect_material_property(mul(m, mul(m, mul(m, mix, const3(m, 0.6, 0.63, 0.6, -560, 200),
                                  -460, 100), swell, -380, 160), soft, -280, 220), "",
                              unreal.MaterialProperty.MP_EMISSIVE_COLOR)
finish(m, "M_VR_Churn forged (white water, quieted)")

# ---------------------------------------------------------- M_VR_LightShaft
# The weenie's sky-drawing beam: quiet additive gold, fading with height.
m = new_mat("M_VR_LightShaft")
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
m.set_editor_property("two_sided", True)
uv_s = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -880, 0)
vfade = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -760, 0)
vfade.set_editor_property("r", False)
vfade.set_editor_property("g", True)
vfade.set_editor_property("b", False)
vfade.set_editor_property("a", False)
MEL.connect_material_expressions(uv_s, "", vfade, "")
inv_s = MEL.create_material_expression(m, unreal.MaterialExpressionOneMinus, -640, 0)
MEL.connect_material_expressions(vfade, "", inv_s, "")
soft_s = depth_fade(m, -640, 200, 400.0)
MEL.connect_material_property(mul(m, mul(m, mul(m, const3(m, 1.2, 1.0, 0.55, -640, 100),
                                  inv_s, -520, 40), const(m, 0.13, -520, 180), -420, 100),
                                  soft_s, -320, 160), "",
                              unreal.MaterialProperty.MP_EMISSIVE_COLOR)
finish(m, "M_VR_LightShaft forged (the weenie's beam)")

# ------------------------------------------------------- M_VR_TorrentCore
# The falls grow a BODY: an opaque-masked churning core riding inside each
# translucent crescent. Masked costs zero translucency budget (Load Law) and
# holds the silhouette from EVERY angle — edge-on the fall stays a column,
# never a thread (Adam round 3: "the waterfall is still thin").
m = new_mat("M_VR_TorrentCore")
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
m.set_editor_property("two_sided", True)
# v4 flow law: the core's erosion mask rides the FAST rope layer — the falls'
# dominant feature now moves at fall speed (20% off the shell for parallax).
tc_cf = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -1400, -80)
tc_cf.set_editor_property("u_tiling", 3.0)
pan_cf = MEL.create_material_expression(m, unreal.MaterialExpressionPanner, -1250, -80)
pan_cf.set_editor_property("speed_y", 1.25)
MEL.connect_material_expressions(tc_cf, "", pan_cf, "Coordinate")
streak_c = sample(m, tex("fall_rope"), -1050, -80, linear=True)
MEL.connect_material_expressions(pan_cf, "", streak_c, "Coordinates")
pan_cs = MEL.create_material_expression(m, unreal.MaterialExpressionPanner, -1250, 140)
pan_cs.set_editor_property("speed_y", 1.0)
foam_c = sample(m, tex("foam"), -1050, 140, linear=True)
MEL.connect_material_expressions(pan_cs, "", foam_c, "Coordinates")
body_c = add(m, mul(m, streak_c, const3(m, 0.62, 0.74, 0.82, -880, -140), -760, -100, a_out="R"),
             mul(m, foam_c, const3(m, 0.42, 0.44, 0.42, -880, 100), -760, 120, a_out="R"),
             -640, 0)
MEL.connect_material_property(mul(m, body_c, const(m, 0.85, -520, 60), -420, 40), "",
                              unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mask_c = add(m, mul(m, streak_c, const(m, 1.1, -640, 300), -540, 260, a_out="R"),
             mul(m, foam_c, const(m, 0.5, -640, 380), -540, 360, a_out="R"), -440, 320)
MEL.connect_material_property(add(m, mask_c, const(m, 0.15, -440, 420), -340, 360), "",
                              unreal.MaterialProperty.MP_OPACITY_MASK)
wpTc = MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -1250, 700)
wpBc = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -1130, 700)
wpBc.set_editor_property("r", False)
wpBc.set_editor_property("g", False)
wpBc.set_editor_property("b", True)
wpBc.set_editor_property("a", False)
MEL.connect_material_expressions(wpTc, "", wpBc, "")
t_tc = MEL.create_material_expression(m, unreal.MaterialExpressionTime, -1250, 830)
phase_c = add(m, mul(m, wpBc, const(m, 0.0037, -1130, 780), -1010, 740),
              mul(m, t_tc, const(m, 3.1, -1130, 900), -1010, 860), -890, 800)
sin_c = MEL.create_material_expression(m, unreal.MaterialExpressionSine, -780, 800)
MEL.connect_material_expressions(phase_c, "", sin_c, "")
vnc = MEL.create_material_expression(m, unreal.MaterialExpressionVertexNormalWS, -780, 920)
MEL.connect_material_property(mul(m, vnc, mul(m, sin_c, const(m, 10.0, -660, 860),
                                  -560, 830), -460, 880), "",
                              unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
finish(m, "M_VR_TorrentCore forged (the falls grow a body)")

# ------------------------------------------------ M_VR_GrassBlade family (v4)
# The full-floor meadow: breath sway ONLY — no parting subgraph, no HeroPos
# read. Per the round-4 audit, per-vertex parting at 15k instances is the 8GB
# bottleneck; the tall understory keeps full parting where Adam walks.
def forge_sway(name, tr, tg, tb):
    m = new_mat(name)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    m.set_editor_property("two_sided", True)
    MEL.connect_material_property(mul(m, sample(m, tex("canopy_top"), -900, -200),
                                      const3(m, tr, tg, tb, -900, -20), -720, -120),
                                  "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(const(m, 0.85, -900, 120), "",
                                  unreal.MaterialProperty.MP_ROUGHNESS)
    gmask = sample(m, tex("moss_mask"), -900, 260, linear=True)
    MEL.connect_material_property(add(m, gmask, const(m, 0.35, -760, 380), -640, 320,
                                      a_out="R"), "",
                                  unreal.MaterialProperty.MP_OPACITY_MASK)
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
               const(m, 14.0, -680, 760), -560, 660)
    uvroot = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -680, 840)
    uvG = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -560, 840)
    uvG.set_editor_property("r", False)
    uvG.set_editor_property("g", True)
    uvG.set_editor_property("b", False)
    uvG.set_editor_property("a", False)
    MEL.connect_material_expressions(uvroot, "", uvG, "")
    sway_rooted = mul(m, sway, uvG, -460, 720)
    ap1 = MEL.create_material_expression(m, unreal.MaterialExpressionAppendVector, -360, 640)
    MEL.connect_material_expressions(sway_rooted, "", ap1, "A")
    MEL.connect_material_expressions(mul(m, sway_rooted, const(m, 0.6, -460, 820), -400, 780), "", ap1, "B")
    ap2 = MEL.create_material_expression(m, unreal.MaterialExpressionAppendVector, -260, 670)
    MEL.connect_material_expressions(ap1, "", ap2, "A")
    MEL.connect_material_expressions(const(m, 0.0, -360, 860), "", ap2, "B")
    MEL.connect_material_property(ap2, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    finish(m, f"{name} forged (sway only — the meadow law)")


forge_sway("M_VR_GrassBlade", 0.85, 1.35, 0.55)
forge_sway("M_VR_BloomPatch", 1.35, 1.28, 0.95)

# --------------------------------------------- M_VR_HeartwoodInner (v4 seal)
# The liner's face: dark warm heartwood with faint gold sap stripes and a flat
# 0.008 emissive floor — the interior is NEVER void-black at any exposure.
m = new_mat("M_VR_HeartwoodInner")
MEL.connect_material_property(const3(m, 0.045, 0.028, 0.018, -700, -120), "",
                              unreal.MaterialProperty.MP_BASE_COLOR)
MEL.connect_material_property(const(m, 0.9, -700, 60), "",
                              unreal.MaterialProperty.MP_ROUGHNESS)
wp_l = MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -1100, 240)
wpz_l = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -980, 240)
wpz_l.set_editor_property("r", False)
wpz_l.set_editor_property("g", False)
wpz_l.set_editor_property("b", True)
wpz_l.set_editor_property("a", False)
MEL.connect_material_expressions(wp_l, "", wpz_l, "")
sin_l = MEL.create_material_expression(m, unreal.MaterialExpressionSine, -760, 260)
MEL.connect_material_expressions(mul(m, wpz_l, const(m, 0.002, -980, 340), -860, 280),
                                 "", sin_l, "")
stripe = mul(m, add(m, sin_l, const(m, 1.0, -680, 340), -620, 300),
             const(m, 0.5, -680, 400), -540, 330)
sap = mul(m, mul(m, stripe, stripe, -460, 300), const3(m, 0.9, 0.55, 0.15, -460, 400),
          -380, 340)
MEL.connect_material_property(add(m, mul(m, sap, const(m, 0.10, -300, 360), -240, 330),
                                  const3(m, 0.02, 0.015, 0.01, -300, 440), -160, 380),
                              "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
finish(m, "M_VR_HeartwoodInner forged (the seal law's face)")

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
    "mist_puff": "M_VR_Mist",
    "knothole_arch": "M_VR_EdgeGlow", "arena_pad": "M_VR_Bark",
    "knot_boulder": "M_VR_Bark", "fern_clump": "M_VR_Frond",
    "vine_curtain": "M_VR_Frond", "flower_stalk": "M_VR_Frond",
    "fungus_shelf": "M_VR_Fungus",
    # v3: the 3D water family
    "falls_torrent": "M_VR_Torrent", "falls_lip": "M_VR_Torrent",
    "falls_churn": "M_VR_Churn", "churn_ring": "M_VR_Churn",
    "foam_patch": "M_VR_Churn",
    # v3: the Sapline Stair / v4: the Hybrid Climb
    "mouth_ring": "M_VR_TunnelSap", "stair_ramp": "M_VR_Bark",
    "verdant_gallery": "M_VR_TunnelSap", "trunk_liner": "M_VR_HeartwoodInner",
    # v4: the full-floor meadow + the ivy
    "meadow_grass": "M_VR_GrassBlade", "flower_patch": "M_VR_BloomPatch",
    "ivy_spiral_a": "M_VR_FrondTeal", "ivy_spiral_b": "M_VR_FrondTeal",
    "ivy_spiral_c": "M_VR_FrondTeal",
    # v3: the understory ladder (knee -> shoulder)
    "puffgrass_tuft": "M_VR_FrondGold", "star_rosette": "M_VR_FrondTeal",
    "paddle_broadleaf": "M_VR_Frond", "reed_cluster": "M_VR_FrondGold",
    "fiddlehead_curl": "M_VR_Frond", "seedpod_stalk": "M_VR_FrondGold",
    "bellflower_stalk": "M_VR_FrondCream",
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
