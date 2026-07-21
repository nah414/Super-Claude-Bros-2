"""Verification capture for the Neon District sky fix — renders the LOOK-BACK view (hero at the
spawn turned to face WEST), where the moons now hang, plus a high east-facing shot to gauge star
density. Writes PNGs to _prep\neon_shots. Run WITH a real offscreen RHI (the export needs a real
render; a plain -nullrhi/commandlet returns an unrendered/black target):
  UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/capture_neon_lookback.py
      -unattended -nosplash -RenderOffscreen -nopause
"""
import math
import unreal

RL = unreal.RenderingLibrary
OUTDIR = r"C:\Users\Atomn\mario2\_prep\neon_shots"
MAP = "/Game/Maps/NeonCity"

# PlayerStart ~ (-4500, 0, 120) faces EAST (+X). Looking BACK = WEST (-X), where the moons now sit.
SHOTS = [
    ("lookback_moons", (-4200.0, 0.0, 320.0),  (-40000.0, -5000.0, 16000.0)),  # turned west, up at the moons
    ("lookback_wide",  (-4200.0, 0.0, 500.0),  (-40000.0, 0.0, 10000.0)),      # wide west sky (star density)
    ("spawn_forward",  (-4400.0, 0.0, 300.0),  (10000.0, 0.0, 4000.0)),        # default east view (star density)
]


def look_rot(loc, tgt):
    d = unreal.Vector(tgt[0] - loc[0], tgt[1] - loc[1], tgt[2] - loc[2])
    yaw = math.degrees(math.atan2(d.y, d.x))
    pitch = math.degrees(math.atan2(d.z, math.sqrt(d.x * d.x + d.y * d.y)))
    return unreal.Rotator(0.0, pitch, yaw)


assert unreal.EditorLoadingAndSavingUtils.load_map(MAP), "LOAD_NEONCITY_FAILED"
world = unreal.EditorLevelLibrary.get_editor_world()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rt = RL.create_render_target2d(world, 1600, 900, unreal.TextureRenderTargetFormat.RTF_RGBA8)

done = 0
for name, loc, tgt in SHOTS:
    cap = eas.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(*loc), look_rot(loc, tgt))
    comp = cap.capture_component2d
    comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    comp.set_editor_property("texture_target", rt)
    comp.set_editor_property("fov_angle", 95.0)              # wide so both moons frame in the look-back
    comp.set_editor_property("capture_every_frame", False)
    comp.set_editor_property("capture_on_movement", False)
    pp = comp.get_editor_property("post_process_settings")
    pp.set_editor_property("override_auto_exposure_method", True)
    pp.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    pp.set_editor_property("override_auto_exposure_bias", True)
    pp.set_editor_property("auto_exposure_bias", 10.0)
    comp.set_editor_property("post_process_settings", pp)
    comp.capture_scene()
    comp.capture_scene()   # twice — first warms streaming/shaders, second is clean
    ok = RL.export_render_target(world, rt, OUTDIR, f"{name}.png")
    eas.destroy_actor(cap)
    done += 1
    print(f"NEONSHOT {name}: export={ok} @ {loc}")

print(f"NEON_LOOKBACK_DONE: {done}/{len(SHOTS)} shots -> {OUTDIR}")
