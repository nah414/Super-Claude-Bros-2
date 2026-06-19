"""WORLD-1 SKY PROPS (Adam): two moons in the night sky — a LARGE reddish moon with an orbital RING,
and a SMALLER pale-yellow moon. Placed as far, unlit-emissive meshes INSIDE the StarDome (radius
~60000 around world ~6000,0,2000), so they read as distant moons over the starfield.

Idempotent: clears any prior MoonLarge/MoonSmall/MoonRing, then re-adds + saves. Run -RenderOffscreen
(map save needs render). Standalone OR as a chain step after build_neon_city (which wipes + rebuilds
the map). All positions/sizes are constants below — easy to nudge from Adam's playtest feedback.

NOTE: these are world-fixed meshes (like the StarDome), so they parallax slightly as the hero crosses
the level. If they need to feel truly locked to the sky, the next step is a camera-following sky actor.
"""
import unreal

EAL = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity"), "LOAD_NEONCITY_FAILED"

SPHERE = unreal.load_asset("/Engine/BasicShapes/Sphere")     # 100uu dia -> 50uu radius at scale 1
PLANE = unreal.load_asset("/Engine/BasicShapes/Plane")       # 100uu square at scale 1
M_RED = EAL.load_asset("/Game/Art/CityMat/M_MoonRed")
M_YEL = EAL.load_asset("/Game/Art/CityMat/M_MoonYellow")
M_RING = EAL.load_asset("/Game/Art/CityMat/M_MoonRing")

# ---- tunables (world coords) -------------------------------------------------------------------
LARGE_POS,  LARGE_SCALE = (36000.0, -10000.0, 26000.0), 90.0   # reddish moon, radius ~4500uu, ~35deg up
SMALL_POS,  SMALL_SCALE = (-22000.0, 20000.0, 24000.0), 48.0   # pale-yellow moon, radius ~2400uu
RING_SCALE, RING_ROT    = 150.0, (14.0, 0.0, 10.0)            # ring just outside the large moon, tilted
# ------------------------------------------------------------------------------------------------

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label() in ("MoonLarge", "MoonSmall", "MoonRing"):
        eas.destroy_actor(a)


def sky_mesh(mesh, mat, loc, scale, label, rot=None):
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc))
    smc = a.static_mesh_component
    smc.set_static_mesh(mesh)
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    if rot:
        a.set_actor_rotation(unreal.Rotator(rot[0], rot[1], rot[2]), False)
    if mat:
        smc.set_material(0, mat)
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    for p, v in (("visible_in_ray_tracing", False), ("cast_shadow", False),
                 ("ld_max_draw_distance", 0.0)):   # 0 = never distance-cull (it IS the sky backdrop)
        try:
            smc.set_editor_property(p, v)
        except Exception:
            pass
    a.set_actor_label(label)
    return a


big = sky_mesh(SPHERE, M_RED, LARGE_POS, LARGE_SCALE, "MoonLarge")
ring = sky_mesh(PLANE, M_RING, LARGE_POS, RING_SCALE, "MoonRing", rot=RING_ROT)
small = sky_mesh(SPHERE, M_YEL, SMALL_POS, SMALL_SCALE, "MoonSmall")

ok = all(x is not None for x in (big, ring, small)) and all(m is not None for m in (M_RED, M_YEL, M_RING))
print(f"SKY_PROPS: MoonLarge+MoonRing+MoonSmall placed (mats_ok={M_RED is not None},"
      f"{M_YEL is not None},{M_RING is not None})")
saved = les.save_current_level()
print(f"SKY_PROPS_SAVED: {saved}  ok={ok}")
print("SKY_PROPS_DONE")
