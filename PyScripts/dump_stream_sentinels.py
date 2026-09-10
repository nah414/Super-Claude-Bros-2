"""Global-stream regression sentinels: transforms of seeded actors placed by
the GLOBAL random stream. Byte-equal before/after a builder change proves the
stream never shifted (the round-4 audit's definitive test)."""
import unreal

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert les.load_level("/Game/Maps/WorldStageTesting"), "LOAD_STAGE_FAILED"
for want in ("VR_Knot_0", "VR_Cloud_0", "VR_Roly_0", "VR_Moss_FIN_25",
             "VR_Fall_sky_fall_t5", "VR_Village_3"):
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == want:
            l = a.get_actor_location()
            r = a.get_actor_rotation()
            s = a.get_actor_scale3d()
            print(f"SENTINEL: {want} loc {l.x:.2f},{l.y:.2f},{l.z:.2f} "
                  f"rot {r.pitch:.3f},{r.yaw:.3f},{r.roll:.3f} "
                  f"scl {s.x:.4f},{s.y:.4f},{s.z:.4f}")
            break
print("SENTINELS_DONE")
