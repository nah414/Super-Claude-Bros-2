"""M0.6 cleanup: the reconverted clip FBXes embed the mesh, so each animation-only
import produced an unwanted 33MB SkeletalMesh copy (A_Hero_X) plus the real
AnimSequence (A_Hero_X_Anim). Delete the copies, rename _Anim -> canonical, so
the C++ FObjectFinder paths (/Game/Art/HeroSkel/A_Hero_X.A_Hero_X) load the
AnimSequences directly — zero churn for the original four clips.

Run: UnrealEditor-Cmd.exe <proj> -ExecutePythonScript=PyScripts/cleanup_hero_anim_packages.py -RenderOffscreen -unattended
"""
import unreal

DEST = "/Game/Art/HeroSkel"
CLIPS = ["Idle", "Walk", "Run", "Jump", "Strike1", "Strike2", "Haymaker", "HitReact", "Relight"]

eal = unreal.EditorAssetLibrary

for clip in CLIPS:
    base = f"{DEST}/A_Hero_{clip}"
    anim = f"{base}_Anim"
    phys = f"{base}_PhysicsAsset"

    a = unreal.load_asset(anim)
    if not isinstance(a, unreal.AnimSequence):
        print(f"SKIP {clip}: {anim} is {type(a).__name__ if a else 'missing'}")
        continue

    # 1) delete the unwanted mesh copy + its physics asset
    for junk in (base, phys):
        if eal.does_asset_exist(junk):
            ok = eal.delete_asset(junk)
            print(f"DELETE {junk}: {ok}")

    # 2) rename the AnimSequence to the canonical name
    ok = eal.rename_asset(anim, base)
    print(f"RENAME {anim} -> {base}: {ok}")

# Drop renamed-asset redirectors so FObjectFinder hits the real object.
unreal.SystemLibrary.execute_console_command(None, f"FixupRedirects {DEST}")
eal.save_directory(DEST, recursive=True)

# Verify: every canonical path must now be an AnimSequence.
all_ok = True
for clip in CLIPS:
    a = unreal.load_asset(f"{DEST}/A_Hero_{clip}")
    kind = type(a).__name__ if a else "MISSING"
    good = isinstance(a, unreal.AnimSequence)
    all_ok &= good
    print(f"VERIFY A_Hero_{clip}: {kind} {'OK' if good else 'BAD'}")
print("CLEANUP_DONE" if all_ok else "CLEANUP_INCOMPLETE")
