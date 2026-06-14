"""Import GUARDIAN(s) as full characters — mesh + 9 clips + material, one session.
V4 native pipeline into virgin /Game/Art/<Camel>SkelV1. Run:
    UnrealEditor-Cmd ... -ExecutePythonScript=import_guardian_native.py
    SCB2_GUARDIAN env: a single name, a comma-list, or "all" (default) — all four.
"""
import os
import unreal

GUARDIANS = {
    "sleek_knight":  {"camel": "SleekKnight",  "mesh": "SCB2SleekKnight",  "target": 71.0,
                      "clips": ["Idle", "Walk", "Slash1", "Slash2", "Spin", "Dodge", "HitReact", "Stagger", "Defeat"],
                      "slots": ["idle", "walk", "slash1", "slash2", "spin", "dodge", "hitreact", "stagger", "defeat"]},
    "heroic_tank":   {"camel": "HeroicTank",   "mesh": "SCB2HeroicTank",   "target": 82.0,
                      "clips": ["Idle", "Walk", "Swing", "Push", "Charge", "Block", "HitReact", "Stagger", "Defeat"],
                      "slots": ["idle", "walk", "swing", "push", "charge", "block", "hitreact", "stagger", "defeat"]},
    "powerhouse":    {"camel": "Powerhouse",   "mesh": "SCB2Powerhouse",   "target": 75.0,
                      "clips": ["Idle", "Walk", "Jab", "Hook", "BothFists", "Combo", "HitReact", "Stagger", "Defeat"],
                      "slots": ["idle", "walk", "jab", "hook", "bothfists", "combo", "hitreact", "stagger", "defeat"]},
    "classic_spark": {"camel": "ClassicSpark", "mesh": "SCB2ClassicSpark", "target": 68.0,
                      "clips": ["Idle", "Walk", "Jab", "Uppercut", "Counter", "Combo", "HitReact", "Stagger", "Defeat"],
                      "slots": ["idle", "walk", "jab", "uppercut", "counter", "combo", "hitreact", "stagger", "defeat"]},
}

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()


def import_skeletal(fbx, dest, name, scale, skel=None):
    ui = unreal.FbxImportUI()
    if skel is None:
        ui.import_mesh = True
        ui.import_as_skeletal = True
        ui.import_animations = False
        ui.import_materials = True
        ui.import_textures = True
        ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
        ui.skeletal_mesh_import_data.set_editor_property("import_uniform_scale", scale)
        ui.skeletal_mesh_import_data.set_editor_property("convert_scene", True)
    else:
        ui.import_mesh = False
        ui.import_as_skeletal = False
        ui.import_animations = True
        ui.import_materials = False
        ui.import_textures = False
        ui.skeleton = skel
        ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION
        ui.anim_sequence_import_data.set_editor_property("import_uniform_scale", scale)
        ui.anim_sequence_import_data.set_editor_property("snap_to_closest_frame_boundary", True)
        ui.anim_sequence_import_data.set_editor_property("convert_scene", True)
    t = unreal.AssetImportTask()
    t.filename = fbx
    t.destination_path = dest
    t.destination_name = name
    t.automated = True
    t.save = True
    t.replace_existing = False
    t.options = ui
    tools.import_asset_tasks([t])
    # FBXIT_ANIMATION also materializes a redundant full SkeletalMesh + PhysicsAsset next to
    # the AnimSequence; purge them so the repo never re-bloats (game loads only SCB2<Char> + *_Anim).
    if skel is not None:
        for dup in (f"{dest}/{name}", f"{dest}/{name}_PhysicsAsset"):
            if EAL.does_asset_exist(dup) and not isinstance(unreal.load_asset(dup), unreal.AnimSequence):
                EAL.delete_asset(dup)
                print(f"PURGE_DUP: {dup}")


def run(NAME):
    CFG = GUARDIANS[NAME]
    DROPS = rf"C:\Users\Atomn\mario2\_prep\meshy_api_drops\{NAME}_full"
    MESH_FBX = os.path.join(DROPS, "rig", f"{NAME}_rig_rigged_character_fbx_url.fbx")
    CAMEL = CFG["camel"]
    PROBE = f"/Game/_Probe{CAMEL}"
    DEST = f"/Game/Art/{CAMEL}SkelV1"
    NAMEM = CFG["mesh"]
    TARGET = CFG["target"]

    if not os.path.isfile(MESH_FBX):
        print(f"GRD_{CAMEL}_SKIP: no rig fbx on disk")
        return

    if EAL.does_directory_exist(PROBE):
        EAL.delete_directory(PROBE)
    import_skeletal(MESH_FBX, PROBE, "ProbeMesh", 1.0)
    probe = unreal.load_asset(f"{PROBE}/ProbeMesh")
    z = probe.get_bounds().box_extent.z
    scale = TARGET / max(z, 0.001)
    print(f"GRD_{CAMEL}_PROBE: native z={z:.1f} -> scale {scale:.4f}")
    EAL.delete_directory(PROBE)

    if EAL.does_directory_exist(DEST):
        if not EAL.delete_directory(DEST):
            raise SystemExit(f"GRD_WIPE_FAILED {CAMEL}")
    import_skeletal(MESH_FBX, DEST, NAMEM, scale)
    mesh = unreal.load_asset(f"{DEST}/{NAMEM}")
    skeleton = unreal.load_asset(f"{DEST}/{NAMEM}_Skeleton")
    print(f"GRD_{CAMEL}_MESH: extent z={mesh.get_bounds().box_extent.z:.1f} (target {TARGET})")

    bound = 0
    for clip, slot in zip(CFG["clips"], CFG["slots"]):
        fbx = os.path.join(DROPS, f"anim_{slot}", f"{NAME}_{slot}_animation_fbx_url.fbx")
        import_skeletal(fbx, DEST, f"A_{CAMEL}_{clip}", scale, skel=skeleton)
        a = unreal.load_asset(f"{DEST}/A_{CAMEL}_{clip}_Anim")
        if isinstance(a, unreal.AnimSequence):
            ok = a.get_editor_property("skeleton") == skeleton
            bound += int(ok)
            print(f"GRD {CAMEL} {clip}: len={a.get_play_length():.2f}s {'BOUND' if ok else 'ORPHANED'}")
        else:
            print(f"GRD {CAMEL} {clip}: NO_ANIMSEQUENCE")

    base_tex = unreal.load_asset(f"{DEST}/texture_0")
    mat = tools.create_asset(f"M_{CAMEL}PBR", DEST, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("used_with_skeletal_mesh", True)
    ts = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -500, -100)
    ts.texture = base_tex
    ok_base = MEL.connect_material_property(ts, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -500, 150)
    rough.set_editor_property("r", 0.5)
    MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    mats = mesh.get_editor_property("materials")
    mesh.set_editor_property("materials", [
        unreal.SkeletalMaterial(material_interface=mat, material_slot_name=m.get_editor_property("material_slot_name"))
        for m in mats])
    EAL.save_loaded_asset(mesh)

    EAL.save_directory(DEST, recursive=True)
    print(f"GRD_{CAMEL}_{'SUCCESS' if bound == len(CFG['clips']) else 'PARTIAL'}: {bound}/{len(CFG['clips'])} bound, scale={scale:.4f}, matbase={ok_base}")


WANT = os.environ.get("SCB2_GUARDIAN", "all").strip().lower()
TARGETS = list(GUARDIANS.keys()) if WANT == "all" else [g.strip() for g in WANT.split(",")]
for g in TARGETS:
    if g in GUARDIANS:
        run(g)
    else:
        print(f"GRD_UNKNOWN: {g}")
print("GUARDIAN_IMPORT_ALL_DONE")
