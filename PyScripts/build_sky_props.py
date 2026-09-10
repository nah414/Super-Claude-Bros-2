"""WORLD-1 SKY BODIES: the Meshy celestial meshes (large red moon + ring-less pale companion + a gas
giant planet) placed as 3D bodies INSIDE the star dome, so the textured all-sky map (T_StarMap on the
dome) is the farthest backdrop and these read as nearer objects (Adam's "space dimensioning"). Replaces
the old engine-sphere emissive moons. Each body's self-lit material (M_*_lit) is already on its mesh.

Dome center (6000,0,2000), radius ~26000. Moons sit at r~20000, planet at r~15000 — all INSIDE the dome
so it never occludes them (the old bug). Idempotent: clears prior MoonLarge/MoonSmall/MoonRing/Planet.
Run with rendering (map save):
  UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/build_sky_props.py
      -unattended -nosplash -RenderOffscreen -nopause
"""
import math
import unreal

EAL = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

assert unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity"), "LOAD_NEONCITY_FAILED"
CX, CY, CZ = 6000.0, 0.0, 2000.0     # dome center

# label, mesh path, direction (will be normalized), radius from center, scale
#   moons hang in the WESTERN sky (look-back from the +X-facing spawn): large high, pale companion
#   lower-left. The planet sits forward+up in a different region so it reads as its own world.
# Moons get DEPTH separation (Adam: not smushed; one in front of the other): the LIGHT large moon sits
# farther + high; the DARK small moon sits at half the radius on a slightly-offset heading, so it reads
# as a distinct body IN FRONT of the large one (closer = drawn in front), not merged side-by-side.
BODIES = [
    ("MoonLarge", "/Game/Art/Celestial/moon_large_red/SM_moon_large_red",
     (-0.82, 0.00, 0.52), 24000.0, 30.0),     # light, FAR, high in the west
    ("MoonSmall", "/Game/Art/Celestial/moon_small_pale/SM_moon_small_pale",
     (-0.84, 0.10, 0.46), 12000.0, 12.0),     # dark, NEAR (in front), slightly off the large's heading
    ("Planet", "/Game/Art/Celestial/planet_gasgiant/SM_planet_gasgiant",
     (0.62, 0.22, 0.52), 15000.0, 22.0),
]

# clear any prior sky bodies (old engine-sphere moons + ring + any earlier placement)
removed = 0
for a in list(eas.get_all_level_actors()):
    try:
        if a.get_actor_label() in ("MoonLarge", "MoonSmall", "MoonRing", "Planet", "Nebula"):
            eas.destroy_actor(a)
            removed += 1
    except Exception:
        pass

def sky_flags(smc):
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    for p, v in (("visible_in_ray_tracing", False), ("cast_shadow", False),
                 ("ld_max_draw_distance", 0.0)):
        try:
            smc.set_editor_property(p, v)
        except Exception:
            pass


placed = 0
moonlarge_loc = None
for label, path, d, radius, scale in BODIES:
    sm = EAL.load_asset(path)
    if not sm:
        print(f"BODY_SKIP {label}: mesh missing {path}")
        continue
    n = math.sqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2])
    loc = unreal.Vector(CX + d[0] / n * radius, CY + d[1] / n * radius, CZ + d[2] / n * radius)
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, loc)
    smc = a.static_mesh_component
    smc.set_static_mesh(sm)              # the SM already carries its M_*_lit emissive material
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    sky_flags(smc)
    a.set_actor_label(label)
    if label == "MoonLarge":
        moonlarge_loc = loc
    placed += 1
    print(f"BODY_PLACED {label}: scale {scale} @ ({loc.x:.0f},{loc.y:.0f},{loc.z:.0f}) r{radius:.0f}")

# orbital RING around the large moon (Adam: add the ring back). M_MoonRing annulus = 0.35..0.47 of the
# plane, so scale ~96 gives a ring radius (~3360-4500uu) just outside the moon (~2850uu radius @ scale 30).
RING_SCALE, RING_ROT = 96.0, (16.0, 0.0, 12.0)   # (pitch, yaw, roll) — tilt so it reads as an open ellipse
ring_mat = EAL.load_asset("/Game/Art/CityMat/M_MoonRing")
plane = unreal.load_asset("/Engine/BasicShapes/Plane")
if moonlarge_loc and ring_mat and plane:
    r = eas.spawn_actor_from_class(unreal.StaticMeshActor, moonlarge_loc)
    rsmc = r.static_mesh_component
    rsmc.set_static_mesh(plane)
    r.set_actor_scale3d(unreal.Vector(RING_SCALE, RING_SCALE, RING_SCALE))
    r.set_actor_rotation(unreal.Rotator(RING_ROT[0], RING_ROT[1], RING_ROT[2]), False)
    rsmc.set_material(0, ring_mat)
    sky_flags(rsmc)
    r.set_actor_label("MoonRing")
    placed += 1
    print(f"BODY_PLACED MoonRing: scale {RING_SCALE} @ large moon")
else:
    print(f"RING_SKIP: moonloc={moonlarge_loc is not None} mat={ring_mat is not None} plane={plane is not None}")

print(f"SKY_BODIES: cleared {removed}, placed {placed}")
saved = les.save_current_level()
print(f"SKY_BODIES_SAVED: {saved}")
print("SKY_PROPS_DONE")
