"""Headless in-engine Hall capture — no game window (the -game/-SCB2Shot path is
flaky in dispatch mode). Loads RosterHall, drops a SceneCapture2D at chosen poses,
renders FINAL_COLOR_LDR to a render target, exports each to PNG. Manual exposure so
headless frames never come back black. Run:
  UnrealEditor-Cmd <uproject> -run=pythonscript -script=PyScripts/capture_hall_headless.py -unattended -nosplash -nopause
"""
import unreal
import math

RL = unreal.RenderingLibrary
OUTDIR = r"C:\Users\Atomn\mario2\_prep\hall_shots"
MAP = "/Game/Maps/RosterHall"

# (name, camera_location, look_at_location)  — PlayerStart is (0,-700) looking +y.
SHOTS = [
    ("v2_hall_overview", (0.0, -1100.0, 320.0), (0.0, 4900.0, 160.0)),     # whole range, dark knight dead-center
    ("v2_darkknight",    (0.0, 2400.0, 230.0), (0.0, 4900.0, 170.0)),      # close on the Hollow Warden (back-center)
    ("v2_dragonlord",    (5400.0, 2600.0, 250.0), (5400.0, 4900.0, 200.0)), # the new V2 Dragonlord station
]


def look_rot(loc, tgt):
    d = unreal.Vector(tgt[0] - loc[0], tgt[1] - loc[1], tgt[2] - loc[2])
    yaw = math.degrees(math.atan2(d.y, d.x))
    pitch = math.degrees(math.atan2(d.z, math.sqrt(d.x * d.x + d.y * d.y)))
    return unreal.Rotator(0.0, pitch, yaw)


unreal.EditorLoadingAndSavingUtils.load_map(MAP)
world = unreal.EditorLevelLibrary.get_editor_world()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

rt = RL.create_render_target2d(world, 1600, 900, unreal.TextureRenderTargetFormat.RTF_RGBA8)

done = 0
for name, loc, tgt in SHOTS:
    cap = eas.spawn_actor_from_class(unreal.SceneCapture2D,
                                     unreal.Vector(loc[0], loc[1], loc[2]),
                                     look_rot(loc, tgt))
    comp = cap.capture_component2d
    comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    comp.set_editor_property("texture_target", rt)
    comp.set_editor_property("fov_angle", 70.0)
    comp.set_editor_property("capture_every_frame", False)
    comp.set_editor_property("capture_on_movement", False)
    # manual exposure so headless frames are correctly lit (no black auto-exposure frame)
    pp = comp.get_editor_property("post_process_settings")
    pp.set_editor_property("override_auto_exposure_method", True)
    pp.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    pp.set_editor_property("override_auto_exposure_bias", True)
    pp.set_editor_property("auto_exposure_bias", 11.0)
    comp.set_editor_property("post_process_settings", pp)
    comp.capture_scene()
    comp.capture_scene()   # twice — first warms streaming/shaders, second is clean
    ok = RL.export_render_target(world, rt, OUTDIR, f"{name}.png")
    eas.destroy_actor(cap)
    done += 1
    print(f"HALLSHOT {name}: export={ok} @ {loc}")

print(f"HALLCAP_DONE: {done}/{len(SHOTS)} shots")
