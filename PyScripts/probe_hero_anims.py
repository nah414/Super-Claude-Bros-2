"""Diagnostic: do the hero's AnimSequences actually contain animation, and do
they target the same skeleton the mesh uses? (Adam reports a frozen hero.)"""
import unreal

DEST = "/Game/Art/HeroSkel"
CLIPS = ["Idle", "Walk", "Run", "Jump", "Strike1", "Strike2", "Haymaker", "HitReact", "Relight"]

mesh = unreal.load_asset(f"{DEST}/SCB2Hero")
mesh_skel = mesh.get_editor_property("skeleton") if mesh else None
print(f"MESH: {type(mesh).__name__}, skeleton={mesh_skel.get_name() if mesh_skel else 'NONE'}")

for clip in CLIPS:
    a = unreal.load_asset(f"{DEST}/A_Hero_{clip}")
    if not a:
        print(f"CLIP {clip}: MISSING")
        continue
    skel = a.get_editor_property("skeleton")
    same = (skel == mesh_skel)
    try:
        length = a.get_play_length()
    except Exception:
        length = -1.0
    try:
        frames = a.get_editor_property("number_of_sampled_frames")
    except Exception:
        frames = "?"
    print(f"CLIP {clip}: {type(a).__name__} len={length:.3f}s frames={frames} "
          f"skeleton={skel.get_name() if skel else 'NONE'} matches_mesh={same}")
print("PROBE_DONE")
