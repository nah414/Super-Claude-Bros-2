"""Control group: do the heroine's June-10 AnimSequences (untouched today) have
skeleton bindings? Decides whether the import recipe was ever producing playable
clips, or the frozen hero has been frozen since day one."""
import unreal

DEST = "/Game/Art/HeroineSkel"
mesh = unreal.load_asset(f"{DEST}/SCB2Heroine")
skel = mesh.get_editor_property("skeleton") if mesh else None
print(f"HEROINE MESH: {type(mesh).__name__ if mesh else 'MISSING'}, skeleton={skel.get_name() if skel else 'NONE'}")

for clip in ["Idle", "Walk", "Run", "Jump"]:
    a = unreal.load_asset(f"{DEST}/A_Heroine_{clip}")
    if not a:
        print(f"HEROINE CLIP {clip}: MISSING")
        continue
    s = a.get_editor_property("skeleton")
    print(f"HEROINE CLIP {clip}: {type(a).__name__} len={a.get_play_length():.3f}s "
          f"skeleton={s.get_name() if s else 'NONE'}")
print("HEROINE_PROBE_DONE")
