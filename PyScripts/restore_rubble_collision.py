"""RESTORE collision on the seam rubble meshes so the pile is SOLID + CLIMBABLE (Adam: climb OVER
it). clear_gate_collision.py had stripped them; this is the inverse. BOX collision = clean VERTICAL
faces the climb trace needs (the gate rejects |normal.Z|>0.55). Component flags don't persist — only
this ASSET-level collision does. Run -RenderOffscreen (mesh edit needs the build context)."""
import unreal

EAL = unreal.EditorAssetLibrary
SMES = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)

RUBBLE = ("/Game/Art/CityTowerKit/rubble_pile/SM_rubble_pile",
          "/Game/Art/CityTowerKit/debris_chunks/SM_debris_chunks")

# Resolve the BOX shape enum across UE naming variants.
SHAPE_BOX = None
for en in ("ScriptCollisionShapeType", "ScriptingCollisionShapeType"):
    e = getattr(unreal, en, None)
    if e is not None and hasattr(e, "BOX"):
        SHAPE_BOX = e.BOX
        print(f"SHAPE_ENUM: {en}.BOX")
        break
print(f"SMES collision methods: {[m for m in dir(SMES) if 'colli' in m.lower()]}")

for path in RUBBLE:
    sm = EAL.load_asset(path)
    if not sm:
        unreal.log_warning(f"RUBBLE_MISSING: {path}")
        continue
    SMES.remove_collisions(sm)
    ok = False
    if SHAPE_BOX is not None:
        try:
            idx = SMES.add_simple_collisions(sm, SHAPE_BOX)
            ok = True
            print(f"add_simple_collisions({path.split('/')[-1]}) -> {idx}")
        except Exception as e:
            print(f"add_simple_collisions failed: {e}")
    if not ok or SMES.get_simple_collision_count(sm) < 1:
        try:
            r = SMES.set_convex_decomposition_collisions(sm, 8, 16, 100000)
            print(f"convex fallback -> {r}")
        except Exception as e:
            print(f"convex fallback failed: {e}")
    bs = sm.get_editor_property("body_setup")
    if bs:
        bs.set_editor_property("collision_trace_flag",
                               unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AND_COMPLEX)
    EAL.save_asset(path)
    print(f"RUBBLE_SOLID: {path.split('/')[-1]} simple_collision={SMES.get_simple_collision_count(sm)}")

print("RESTORE_RUBBLE_COLLISION_DONE")
