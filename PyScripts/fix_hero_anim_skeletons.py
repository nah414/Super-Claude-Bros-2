"""THE FROZEN-HERO FIX: every hero AnimSequence lost its skeleton reference
(probe showed skeleton=NONE on all nine — orphaned anims play on nothing).
Rebind each to SCB2Hero_Skeleton (same rig, identical bone tree) and resave."""
import unreal

DEST = "/Game/Art/HeroSkel"
CLIPS = ["Idle", "Walk", "Run", "Jump", "Strike1", "Strike2", "Haymaker", "HitReact", "Relight"]

skel = unreal.load_asset(f"{DEST}/SCB2Hero_Skeleton")
if not isinstance(skel, unreal.Skeleton):
    raise SystemExit("NO_SKELETON")
print(f"TARGET SKELETON: {skel.get_name()}")

fixed = 0
for clip in CLIPS:
    path = f"{DEST}/A_Hero_{clip}"
    a = unreal.load_asset(path)
    if not isinstance(a, unreal.AnimSequence):
        print(f"SKIP {clip}: not an AnimSequence")
        continue
    a.set_editor_property("skeleton", skel)
    unreal.EditorAssetLibrary.save_loaded_asset(a)
    chk = unreal.load_asset(path).get_editor_property("skeleton")
    ok = (chk == skel)
    fixed += int(ok)
    print(f"REBIND {clip}: skeleton={chk.get_name() if chk else 'NONE'} {'OK' if ok else 'FAILED'}")

print(f"FIX_{'DONE' if fixed == len(CLIPS) else 'INCOMPLETE'}: {fixed}/{len(CLIPS)} rebound")
