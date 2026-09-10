"""Verify the 3 low-level enemy classes + the exact Python property names for the anti-lag config
(draw-distance cull on the mesh, shadow/attenuation on the Flit Moth light) before writing the spawn
code. Read-only-ish (spawns into a blank Entry map, never saves). Run -nullrhi."""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.EditorLoadingAndSavingUtils.load_map("/Engine/Maps/Entry")

PATHS = ("/Script/SuperClaudeBros2.GlimmerEnemy",
         "/Script/SuperClaudeBros2.RolyShellback",
         "/Script/SuperClaudeBros2.FlitMoth")

for path in PATHS:
    cls = unreal.load_class(None, path)
    print(f"CLASS {path}: {'OK' if cls else '*** MISSING ***'}")
    if not cls:
        continue
    a = eas.spawn_actor_from_class(cls, unreal.Vector(0, 0, 100))
    prims = a.get_components_by_class(unreal.PrimitiveComponent)
    lights = a.get_components_by_class(unreal.LightComponent)
    print(f"  prims={[p.get_class().get_name() for p in prims]} lights={[l.get_class().get_name() for l in lights]}")
    if prims:
        for prop in ("ld_max_draw_distance", "max_draw_distance", "cull_distance", "visible_in_ray_tracing"):
            try:
                prims[0].set_editor_property(prop, (False if prop == "visible_in_ray_tracing" else 9000.0))
                print(f"  PRIM_PROP_OK: {prop}")
            except Exception as e:
                print(f"  PRIM_PROP_FAIL: {prop}: {str(e)[:70]}")
        for meth in ("set_cull_distance",):
            fn = getattr(prims[0], meth, None)
            print(f"  prim method {meth}: {'present' if fn else 'absent'}")
    if lights:
        for prop in ("cast_shadows", "cast_dynamic_shadows", "attenuation_radius", "max_draw_distance",
                     "max_distance_fade_range"):
            try:
                val = False if "shadow" in prop else 1500.0
                lights[0].set_editor_property(prop, val)
                print(f"  LIGHT_PROP_OK: {prop}")
            except Exception as e:
                print(f"  LIGHT_PROP_FAIL: {prop}: {str(e)[:70]}")
    eas.destroy_actor(a)

print("INTROSPECT_ENEMIES_DONE")
