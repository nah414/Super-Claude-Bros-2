import unreal
skel = unreal.load_asset("/Game/Art/HeroSkel/SCB2Hero_Skeleton")
ok = 0
clips = ["Idle", "Walk", "Run", "Jump", "Strike1", "Strike2", "Haymaker", "HitReact", "Relight"]
for clip in clips:
    a = unreal.load_asset(f"/Game/Art/HeroSkel/A_Hero_{clip}_Anim")
    s = a.get_editor_property("skeleton") if a else None
    bound = (s == skel and isinstance(a, unreal.AnimSequence))
    ok += int(bound)
    print(f"FINAL {clip}_Anim: {type(a).__name__ if a else 'MISSING'} skeleton={s.get_name() if s else 'NONE'}")
print(f"FINAL_{'ALL_BOUND' if ok == len(clips) else 'BROKEN'}: {ok}/{len(clips)}")
