"""Aurora borealis for World 1 (Adam): an animated green->teal curtain band low across the sky.
Builds M_Aurora (additive, unlit, two-sided, time-animated vertical curtains that shimmer + drift) and
places it on a big inverted CYLINDER ring low above the horizon, inside the star dome. Additive so it
glows over the stars and never occludes them. Idempotent (clears prior AuroraRing). Run with rendering:
  UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/build_aurora.py
      -unattended -nosplash -RenderOffscreen -nopause
"""
import unreal

MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
MAT_DEST = "/Game/Art/CityMat"


def X(mat, cls, x, y):
    return MEL.create_material_expression(mat, cls, x, y)


def C(mat, v, x, y):
    e = X(mat, unreal.MaterialExpressionConstant, x, y)
    e.set_editor_property("r", v)
    return e


def RGB(mat, rgb, x, y):
    e = X(mat, unreal.MaterialExpressionConstant3Vector, x, y)
    e.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    return e


def MUL(mat, a, b, x, y):
    m = X(mat, unreal.MaterialExpressionMultiply, x, y)
    MEL.connect_material_expressions(a, "", m, "A")
    MEL.connect_material_expressions(b, "", m, "B")
    return m


def ADD(mat, a, b, x, y):
    m = X(mat, unreal.MaterialExpressionAdd, x, y)
    MEL.connect_material_expressions(a, "", m, "A")
    MEL.connect_material_expressions(b, "", m, "B")
    return m


# ---- M_Aurora ----
path = f"{MAT_DEST}/M_Aurora"
if EAL.does_asset_exist(path):
    EAL.delete_asset(path)
mat = TOOLS.create_asset("M_Aurora", MAT_DEST, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
mat.set_editor_property("two_sided", True)

uv = X(mat, unreal.MaterialExpressionTextureCoordinate, -1300, 0)
um = X(mat, unreal.MaterialExpressionComponentMask, -1140, -80)
um.set_editor_property("r", True); um.set_editor_property("g", False)
um.set_editor_property("b", False); um.set_editor_property("a", False)
vm = X(mat, unreal.MaterialExpressionComponentMask, -1140, 120)
vm.set_editor_property("r", False); vm.set_editor_property("g", True)
vm.set_editor_property("b", False); vm.set_editor_property("a", False)
MEL.connect_material_expressions(uv, "", um, "")
MEL.connect_material_expressions(uv, "", vm, "")
time = X(mat, unreal.MaterialExpressionTime, -1140, -260)

# two drifting sine curtains -> multiply for shimmering vertical bands (0..1)
a1 = ADD(mat, MUL(mat, um, C(mat, 26.0, -1000, -160), -860, -120), MUL(mat, time, C(mat, 0.18, -1000, -300), -860, -260), -700, -160)
s1 = X(mat, unreal.MaterialExpressionSine, -560, -160)
MEL.connect_material_expressions(a1, "", s1, "")
a2 = ADD(mat, MUL(mat, um, C(mat, 11.0, -1000, 40), -860, 40), MUL(mat, time, C(mat, -0.11, -1000, -40), -860, -40), -700, 20)
s2 = X(mat, unreal.MaterialExpressionSine, -560, 20)
MEL.connect_material_expressions(a2, "", s2, "")
streaks = X(mat, unreal.MaterialExpressionClamp, -380, -60)
MEL.connect_material_expressions(MUL(mat, s1, s2, -480, -60), "", streaks, "")

# curtains hang from the horizon: bright at the bottom (V=0), fading up -> squared
vinv = X(mat, unreal.MaterialExpressionOneMinus, -380, 160)
MEL.connect_material_expressions(vm, "", vinv, "")
hf = MUL(mat, vinv, vinv, -240, 160)

opacity = MUL(mat, streaks, hf, -80, 40)
# green at the base -> teal/cyan higher
col = X(mat, unreal.MaterialExpressionLinearInterpolate, -240, 320)
MEL.connect_material_expressions(RGB(mat, (0.10, 1.00, 0.45), -440, 300), "", col, "A")
MEL.connect_material_expressions(RGB(mat, (0.25, 0.70, 1.00), -440, 420), "", col, "B")
MEL.connect_material_expressions(vm, "", col, "Alpha")
emis = MUL(mat, col, C(mat, 2.6, -80, 360), 80, 320)

MEL.connect_material_property(emis, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)
MEL.recompile_material(mat)
EAL.save_loaded_asset(mat)
print("AURORA_MAT_OK: M_Aurora")

# ---- place the aurora ring low across the sky ----
assert unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity"), "LOAD_NEONCITY_FAILED"
for a in list(eas.get_all_level_actors()):
    try:
        if a.get_actor_label() == "AuroraRing":
            eas.destroy_actor(a)
    except Exception:
        pass
cyl = unreal.load_asset("/Engine/BasicShapes/Cylinder")
ring = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(6000.0, 0.0, 5200.0))
smc = ring.static_mesh_component
smc.set_static_mesh(cyl)
ring.set_actor_scale3d(unreal.Vector(340.0, 340.0, 52.0))    # ~17000uu radius, ~5200uu tall band
smc.set_material(0, mat)
smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
for p, v in (("visible_in_ray_tracing", False), ("cast_shadow", False), ("ld_max_draw_distance", 0.0)):
    try:
        smc.set_editor_property(p, v)
    except Exception:
        pass
ring.set_actor_label("AuroraRing")
print("AURORA_RING_PLACED @ (6000,0,5200) r17000")
saved = les.save_current_level()
print(f"AURORA_SAVED: {saved}")
print("AURORA_DONE")
