"""Import the VERDANT REACH kit -> /Game/Art/Verdant + /Game/Audio/Verdant.

Manifest-driven (the Blender sculptor wrote _prep/verdant/manifest.json): every
mesh is probed against its authored span and build-scale-corrected (the only
scale truth we trust), walkables get CTF_USE_COMPLEX_AS_SIMPLE with Nanite OFF
(Nanite swaps collision to its coarse fallback), dressing gets Nanite ON.
Textures and the ambience WAVs ride the same pass. Rerun-safe: replace_existing.
"""
import json
import os

import unreal

PREP = r"C:\Users\Atomn\mario2\_prep\verdant"
TEX_DIR = r"C:\Users\Atomn\mario2\SuperClaudeBros2\ArtSource\textures_verdant"
AUD_DIR = r"C:\Users\Atomn\mario2\SuperClaudeBros2\ArtSource\audio_verdant"
DEST = "/Game/Art/Verdant"
AUD_DEST = "/Game/Audio/Verdant"

with open(os.path.join(PREP, "manifest.json")) as f:
    MANIFEST = json.load(f)

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
tools = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)


def import_task(path, dest, name, options=None):
    task = unreal.AssetImportTask()
    task.filename = path
    task.destination_path = dest
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = True
    if options:
        task.options = options
    tools.import_asset_tasks([task])
    paths = list(task.get_editor_property("imported_object_paths") or [])
    return unreal.load_asset(paths[0]) if paths else None


def mesh_ui():
    ui = unreal.FbxImportUI()
    ui.import_mesh = True
    ui.import_as_skeletal = False
    ui.import_animations = False
    ui.import_materials = False
    ui.import_textures = False
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    sd = ui.static_mesh_import_data
    sd.set_editor_property("import_uniform_scale", 1.0)
    sd.set_editor_property("combine_meshes", True)
    sd.set_editor_property("auto_generate_collision", False)
    try:
        sd.set_editor_property("vertex_color_import_option",
                               unreal.VertexColorImportOption.REPLACE)
    except Exception as e:
        print(f"REACH_WARN: vertex color import option: {e} — river foam mask may be lost")
    return ui


ok = fail = 0
for name, m in MANIFEST["meshes"].items():
    fbx = os.path.join(PREP, m["file"])
    if not os.path.isfile(fbx):
        print(f"REACH_FAIL: {name} fbx missing on disk")
        fail += 1
        continue
    mesh = import_task(fbx, DEST, name, mesh_ui())
    if not isinstance(mesh, unreal.StaticMesh):
        print(f"REACH_FAIL: {name} did not import as StaticMesh")
        fail += 1
        continue

    # Probe-and-correct to the authored span (X is nonzero on every kit mesh).
    b = mesh.get_bounding_box()
    span = b.max.x - b.min.x
    want = m["span_x"]
    if span > 1.0 and want > 1.0 and abs(1.0 - want / span) > 0.01:
        s = want / span
        bs = sms.get_lod_build_settings(mesh, 0)
        bs.build_scale3d = unreal.Vector(s, s, s)
        sms.set_lod_build_settings(mesh, 0, bs)
        print(f"REACH_MARKER: {name} scale-corrected x{s:.3f}")

    if m["collision"]:
        body = mesh.get_editor_property("body_setup")
        body.set_editor_property("collision_trace_flag",
                                 unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        mesh.set_editor_property("body_setup", body)

    # R6 THE LIGHT READS: walkables join the Nanite world WITHOUT touching the
    # climb collision that took four rounds to win — fallback_relative_error=0
    # makes the Nanite fallback mesh the FULL geometry, so complex-as-simple
    # collision stays vertex-exact (the old "Nanite swaps collision to its
    # coarse fallback" objection dissolves at zero fallback error).
    want_nanite = m["nanite"] or m["collision"]
    ns = mesh.get_editor_property("nanite_settings")
    ns_changed = False
    if ns.get_editor_property("enabled") != want_nanite:
        ns.set_editor_property("enabled", want_nanite)
        ns_changed = True
    if m["collision"] and want_nanite:
        try:
            if ns.get_editor_property("fallback_relative_error") != 0.0:
                ns.set_editor_property("fallback_relative_error", 0.0)
                ns_changed = True
        except Exception as e:
            print(f"REACH_WARN: nanite fallback error on {name}: {e} — "
                  f"keeping Nanite OFF for collision safety")
            ns.set_editor_property("enabled", False)
            ns_changed = True
    if ns_changed:
        mesh.set_editor_property("nanite_settings", ns)

    EAL.save_loaded_asset(mesh)
    b2 = mesh.get_bounding_box()
    print(f"REACH_MARKER: mesh {name} {b2.max.x - b2.min.x:.0f}x"
          f"{b2.max.y - b2.min.y:.0f}x{b2.max.z - b2.min.z:.0f}uu "
          f"col={'complex' if m['collision'] else 'none'} nanite={int(m['nanite'])}")
    ok += 1

TEXTURES = {           # name: srgb (masks stay linear)
    "bark": True, "ground_moss": True, "canopy_top": True,
    "moss_mask": False, "water_streak": False, "cloud_soft": False,
    "foam": False, "caustic": False, "fall_rope": False,
    # v5 Round 5 (A4): the ripple distortion field + the aniso river streaks
    "water_ripple": False, "streak_aniso": False,
}
for stem, srgb in TEXTURES.items():
    png = os.path.join(TEX_DIR, f"{stem}.png")
    tex = import_task(png, DEST, f"T_{stem}") if os.path.isfile(png) else None
    if tex:
        tex.set_editor_property("srgb", srgb)
        EAL.save_loaded_asset(tex)
        print(f"REACH_MARKER: texture T_{stem} srgb={int(srgb)}")
        ok += 1
    else:
        print(f"REACH_FAIL: texture {stem} missing")
        fail += 1

for wav in ("amb_wind_loop", "amb_gust_a", "amb_gust_b", "amb_gust_c"):
    path = os.path.join(AUD_DIR, f"{wav}.wav")
    snd = import_task(path, AUD_DEST, wav) if os.path.isfile(path) else None
    if snd:
        print(f"REACH_MARKER: audio {wav} imported")
        ok += 1
    else:
        print(f"REACH_FAIL: audio {wav} missing")
        fail += 1

# v3: the enclosed tunnel_helix retired — the Sapline Stair replaces it.
# v4: mouth_bore retired — the REAL mouth cut + verdant_gallery replace it.
for stale in ("tunnel_helix", "mouth_bore"):
    path = f"{DEST}/{stale}"
    if stale not in MANIFEST["meshes"] and EAL.does_asset_exist(path):
        EAL.delete_asset(path)
        print(f"REACH_MARKER: stale asset retired: {stale}")

EAL.save_directory(DEST, recursive=True)
EAL.save_directory(AUD_DEST, recursive=True)
print(f"REACH_MARKER: kit import {ok} ok / {fail} failed (field {MANIFEST['field_md5'][:8]})")
assert fail == 0, "VERDANT_IMPORT_INCOMPLETE"
print("VERDANT_IMPORT_DONE")
