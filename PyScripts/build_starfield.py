"""Finalize the NeonCity sky DOME: clear the old discrete star meshes (the real all-sky map texture
on the dome now IS the star field + Milky Way), and set the dome's scale + orientation so the galactic
band arcs nicely across the sky instead of lying flat at the horizon.

Run AFTER build_city_materials.py (which rebuilds M_StarNebula to sample T_StarMap). Map save needs a
render device:
  UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/build_starfield.py
      -unattended -nosplash -RenderOffscreen -nopause
"""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

DOME_SCALE = 520.0                       # ~26000uu radius
DOME_TILT = unreal.Rotator(0.0, 55.0, 25.0)   # (roll, pitch, yaw) — tilt the Milky Way band up across the sky (tunable)

assert unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity"), "LOAD_NEONCITY_FAILED"

# remove any prior discrete starfield meshes
removed = 0
for a in list(eas.get_all_level_actors()):
    try:
        if a.get_actor_label().startswith("Star_"):
            eas.destroy_actor(a)
            removed += 1
    except Exception:
        pass

# scale + orient the StarDome (the textured sky)
domes = 0
for a in eas.get_all_level_actors():
    try:
        if a.get_actor_label() == "StarDome":
            a.set_actor_scale3d(unreal.Vector(DOME_SCALE, DOME_SCALE, DOME_SCALE))
            a.set_actor_rotation(DOME_TILT, False)
            domes += 1
    except Exception:
        pass

print(f"SKY_FINALIZE: cleared {removed} old star meshes, oriented {domes} StarDome(s) "
      f"(scale {DOME_SCALE}, tilt {DOME_TILT})")
saved = les.save_current_level()
print(f"SKY_FINALIZE_SAVED: {saved}")
print("STARFIELD_DONE")
