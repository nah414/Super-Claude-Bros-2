import unreal
for clip in ["Idle", "Walk", "Run", "Jump"]:
    a = unreal.load_asset(f"/Game/Art/HeroineSkel/A_Heroine_{clip}_Anim")
    if not a:
        print(f"CTRL {clip}: _Anim MISSING")
        continue
    s = a.get_editor_property("skeleton")
    print(f"CTRL {clip}_Anim: {type(a).__name__} skeleton={s.get_name() if s else 'NONE'}")
print("CTRL_DONE")
