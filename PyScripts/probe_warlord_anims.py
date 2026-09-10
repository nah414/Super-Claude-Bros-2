"""Diagnostic: the Glade Prowler glides with dead legs (Adam, July 23 — "a problem
since we first built this character", i.e. since the Warlord's own import). Do the
Warlord clips contain animation, and do they target the SAME skeleton object the
mesh uses? Compare against the Bramblehulk (whose walk visibly works) as control."""
import unreal

print("=== WARLORD (the Prowler's rig) ===")
DEST = "/Game/Art/WarlordSkelV1"
mesh = unreal.load_asset(f"{DEST}/SCB2Warlord")
mesh_skel = mesh.get_editor_property("skeleton") if mesh else None
print(f"MESH: {type(mesh).__name__ if mesh else 'MISSING'}, "
      f"skeleton={mesh_skel.get_path_name() if mesh_skel else 'NONE'}")

for clip in ["Idle", "Walk", "Swing", "Chop", "Sweep", "Vent", "HitReact", "Stagger", "Defeat"]:
    a = unreal.load_asset(f"{DEST}/A_Warlord_{clip}_Anim")
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
    print(f"CLIP {clip}: len={length:.3f}s frames={frames} "
          f"skeleton={skel.get_name() if skel else 'NONE'} matches_mesh={same}")

print("=== BRAMBLEHULK (control: his walk works) ===")
for root in ("/Game/Art/BrambleSkelV1", "/Game/Art/BrambleSkelV2"):
    hm = unreal.load_asset(f"{root}/SCB2Bramble")
    if not hm:
        continue
    hs = hm.get_editor_property("skeleton")
    print(f"MESH {root}: skeleton={hs.get_path_name() if hs else 'NONE'}")
    for clip in ["Dormant", "Walk"]:
        a = unreal.load_asset(f"{root}/A_Bramble_{clip}_Anim")
        if a:
            sk = a.get_editor_property("skeleton")
            print(f"  CLIP {clip}: skeleton={sk.get_name() if sk else 'NONE'} matches={sk == hs}")
print("WARLORD_PROBE_DONE")
