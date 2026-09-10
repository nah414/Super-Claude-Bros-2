# ============================================================================
# import_art.py -- Super Claude Bros 2 asset import pipeline (UE 5.7 editor)
# ----------------------------------------------------------------------------
# Run INSIDE the Unreal Editor's Python environment, e.g.:
#   UnrealEditor-Cmd.exe <proj>.uproject -run=pythonscript -script="PyScripts/import_art.py"
# or from the editor's Output Log:  py "C:/Users/Atomn/mario2/SuperClaudeBros2/PyScripts/import_art.py"
#
# What it does (idempotently -- safe to re-run; existing TARGET assets are
# deleted first; these are mesh/audio/material assets, never levels):
#   1. Import every ArtSource/kit/*.glb        -> /Game/Art/Kit
#   2. Import ArtSource/hero/SparkHero.glb     -> /Game/Art/Hero
#   3. Import every ArtSource/audio/*.wav      -> /Game/Art/Audio
#      (files named *_loop.wav get SoundWave.looping = True)
#   4. Build two master materials from code:
#        /Game/Art/M_VertexLit         (vertex color -> BaseColor, 0.7 rough)
#        /Game/Art/M_VertexLitEmissive (same + vertexcolor*8 -> Emissive)
#      glTF vertex colors do NOT show up automatically in UE -- meshes need a
#      material that actually samples the VertexColor node. That is the whole
#      reason these materials exist.
#   5. Assign M_VertexLit to every material slot of every imported static
#      mesh; assets whose name contains 'Crystal' or 'Monument' get the
#      emissive variant instead (crystals / monument glow).
#   6. Print a manifest: IMPORTED counts + IMPORT_FAIL lines for anything
#      that went wrong. Every per-asset step is wrapped in try/except so a
#      single bad file never aborts the whole run.
# ============================================================================

import os
import traceback

import unreal

# ----------------------------------------------------------------------------
# Constants / paths
# ----------------------------------------------------------------------------

# Absolute on-disk project dir, e.g. C:/Users/Atomn/mario2/SuperClaudeBros2/
PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())

ART_SOURCE_DIR = os.path.join(PROJECT_DIR, "ArtSource")
KIT_SRC_DIR    = os.path.join(ART_SOURCE_DIR, "kit")
HERO_SRC_FILE  = os.path.join(ART_SOURCE_DIR, "hero", "SparkHero.glb")
AUDIO_SRC_DIR  = os.path.join(ART_SOURCE_DIR, "audio")

KIT_DEST   = "/Game/Art/Kit"
HERO_DEST  = "/Game/Art/Hero"
AUDIO_DEST = "/Game/Art/Audio"
MAT_DEST   = "/Game/Art"

MAT_LIT_NAME      = "M_VertexLit"
MAT_EMISSIVE_NAME = "M_VertexLitEmissive"
MAT_LIT_PATH      = MAT_DEST + "/" + MAT_LIT_NAME
MAT_EMISSIVE_PATH = MAT_DEST + "/" + MAT_EMISSIVE_NAME

# Subsystem / helper singletons.
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
eal         = unreal.EditorAssetLibrary
mel         = unreal.MaterialEditingLibrary

# Bookkeeping for the final manifest.
imported_mesh_paths  = []   # '/Game/Art/Kit/Foo' style object paths of StaticMeshes
imported_sound_paths = []   # SoundWave object paths
failures             = []   # human-readable 'IMPORT_FAIL: ...' strings


def log(msg):
    """Single funnel for output so it shows both in stdout and the UE log."""
    print("[import_art] {}".format(msg))
    try:
        unreal.log("[import_art] {}".format(msg))
    except Exception:
        pass  # unreal.log should always work in-editor, but never let logging kill us


def fail(name, why):
    """Record a failure without raising -- one bad asset must not abort the run."""
    entry = "IMPORT_FAIL: {} ({})".format(name, why)
    failures.append(entry)
    log(entry)


# ----------------------------------------------------------------------------
# Idempotency helper: delete an existing asset at a /Game/... path.
# These are mesh/audio/material assets, NOT levels, so direct delete is fine.
# ----------------------------------------------------------------------------

def delete_if_exists(asset_path):
    """Delete the asset at asset_path if it exists. Returns True on 'gone'."""
    try:
        if eal.does_asset_exist(asset_path):
            ok = eal.delete_asset(asset_path)
            if not ok:
                # Deletion can fail if something holds a hard reference; we
                # still try the import with replace_existing=True afterwards.
                log("WARNING: could not delete existing asset {} "
                    "(import will try replace_existing instead)".format(asset_path))
            return ok
        return True
    except Exception as e:
        log("WARNING: exception deleting {}: {}".format(asset_path, e))
        return False


# ----------------------------------------------------------------------------
# Generic file import via AssetImportTask.
#
# UE 5.7 routes .glb files through Interchange by default; with automated=True
# and options=None the default Interchange pipeline runs without any dialogs.
# .wav files go through the classic sound factory and become SoundWave assets.
#
# UNCERTAINTY NOTE: with Interchange, task.imported_object_paths is sometimes
# empty even on success (long-standing quirk), so after the task runs we ALSO
# probe the expected destination path with does_asset_exist as a fallback.
# ----------------------------------------------------------------------------

def run_import_task(src_file, dest_path, dest_name):
    """Import one file. Returns the imported main object path or None."""
    task = unreal.AssetImportTask()
    task.set_editor_property("automated", True)          # no UI dialogs
    task.set_editor_property("filename", src_file)       # absolute source path
    task.set_editor_property("destination_path", dest_path)
    task.set_editor_property("destination_name", dest_name)  # force asset name = file stem
    task.set_editor_property("replace_existing", True)   # belt & braces on top of delete
    task.set_editor_property("save", True)               # save imported packages to disk
    # options=None lets the importer pick its defaults. For glTF/GLB in 5.7
    # that means the default Interchange pipeline (handles meshes + vertex
    # colors); for wav it means the standard SoundWave factory.
    task.set_editor_property("options", None)

    asset_tools.import_asset_tasks([task])

    # --- Primary result channel: the task's reported object paths ----------
    try:
        reported = list(task.get_editor_property("imported_object_paths"))
    except Exception:
        reported = []
    if reported:
        # Object paths look like '/Game/Art/Kit/Foo.Foo'; normalize to the
        # package-style path '/Game/Art/Kit/Foo' that EditorAssetLibrary likes.
        main = str(reported[0]).split(".")[0]
        return main

    # --- Fallback: probe the expected location ------------------------------
    expected = dest_path + "/" + dest_name
    if eal.does_asset_exist(expected):
        return expected

    # --- Last resort: scan the destination folder for a freshly created -----
    # asset whose name matches (Interchange occasionally renames the asset
    # after the internal mesh node instead of the file stem).
    try:
        for p in eal.list_assets(dest_path, recursive=False, include_folder=False):
            pkg = str(p).split(".")[0]
            if pkg.rsplit("/", 1)[-1].lower() == dest_name.lower():
                return pkg
    except Exception:
        pass
    return None


def import_glb(src_file, dest_path):
    """Import one .glb as a StaticMesh; record success/failure."""
    stem = os.path.splitext(os.path.basename(src_file))[0]
    target = dest_path + "/" + stem
    try:
        delete_if_exists(target)  # idempotency: nuke previous import first
        result = run_import_task(src_file, dest_path, stem)
        if result is None:
            fail(stem, "no asset found at {} after import".format(target))
            return
        # Verify it is actually a StaticMesh before we count it -- Interchange
        # also spawns sibling material/texture assets we don't track here.
        loaded = eal.load_asset(result)
        if isinstance(loaded, unreal.StaticMesh):
            imported_mesh_paths.append(result)
            log("imported mesh: {}".format(result))
        else:
            # The main reported asset wasn't the mesh (can happen if a glTF
            # scene reports its material first). Scan the folder for the mesh.
            found = False
            for p in eal.list_assets(dest_path, recursive=False, include_folder=False):
                pkg = str(p).split(".")[0]
                if pkg.rsplit("/", 1)[-1].lower() != stem.lower():
                    continue
                obj = eal.load_asset(pkg)
                if isinstance(obj, unreal.StaticMesh):
                    imported_mesh_paths.append(pkg)
                    log("imported mesh (via folder scan): {}".format(pkg))
                    found = True
                    break
            if not found:
                fail(stem, "import produced no StaticMesh named '{}'".format(stem))
    except Exception as e:
        fail(stem, "exception: {}".format(e))
        traceback.print_exc()


def import_wav(src_file, dest_path):
    """Import one .wav as a SoundWave; set looping for *_loop files."""
    stem = os.path.splitext(os.path.basename(src_file))[0]
    target = dest_path + "/" + stem
    try:
        delete_if_exists(target)  # idempotency
        result = run_import_task(src_file, dest_path, stem)
        if result is None:
            fail(stem, "no asset found at {} after import".format(target))
            return
        sound = eal.load_asset(result)
        if not isinstance(sound, unreal.SoundWave):
            fail(stem, "imported asset is not a SoundWave ({})".format(type(sound).__name__))
            return
        # Music/ambience loops must actually loop. The C++ property is
        # bLooping; the Python editor-property name is 'looping'. Match "loop"
        # ANYWHERE in the stem (not just a trailing _loop) so versioned tracks
        # like music_city_loop_v2 also loop on a full-pipeline re-import.
        if "loop" in stem.lower():
            sound.set_editor_property("looping", True)
            eal.save_loaded_asset(sound)
            log("imported sound (LOOPING): {}".format(result))
        else:
            log("imported sound: {}".format(result))
        imported_sound_paths.append(result)
    except Exception as e:
        fail(stem, "exception: {}".format(e))
        traceback.print_exc()


# ----------------------------------------------------------------------------
# Step 1+2: meshes (kit + hero)
# ----------------------------------------------------------------------------

def import_all_meshes():
    eal.make_directory(KIT_DEST)
    eal.make_directory(HERO_DEST)

    # --- Kit pieces ---------------------------------------------------------
    if os.path.isdir(KIT_SRC_DIR):
        glbs = sorted(f for f in os.listdir(KIT_SRC_DIR) if f.lower().endswith(".glb"))
        if not glbs:
            log("WARNING: no .glb files found in {}".format(KIT_SRC_DIR))
        for fname in glbs:
            import_glb(os.path.join(KIT_SRC_DIR, fname), KIT_DEST)
    else:
        fail("kit", "source dir missing: {}".format(KIT_SRC_DIR))

    # --- Hero ----------------------------------------------------------------
    if os.path.isfile(HERO_SRC_FILE):
        import_glb(HERO_SRC_FILE, HERO_DEST)
    else:
        fail("SparkHero", "source file missing: {}".format(HERO_SRC_FILE))


# ----------------------------------------------------------------------------
# Step 3: audio
# ----------------------------------------------------------------------------

def import_all_audio():
    eal.make_directory(AUDIO_DEST)
    if os.path.isdir(AUDIO_SRC_DIR):
        wavs = sorted(f for f in os.listdir(AUDIO_SRC_DIR) if f.lower().endswith(".wav"))
        if not wavs:
            log("WARNING: no .wav files found in {}".format(AUDIO_SRC_DIR))
        for fname in wavs:
            import_wav(os.path.join(AUDIO_SRC_DIR, fname), AUDIO_DEST)
    else:
        fail("audio", "source dir missing: {}".format(AUDIO_SRC_DIR))


# ----------------------------------------------------------------------------
# Step 4: master materials built entirely from code.
#
# glTF vertex colors are imported onto the mesh but UE materials ignore them
# unless a VertexColor expression is wired in -- so we author two tiny master
# materials here and assign them to every mesh in step 5.
# ----------------------------------------------------------------------------

def build_material(name, emissive):
    """Create one vertex-color master material. Returns the Material or None."""
    path = MAT_DEST + "/" + name
    try:
        delete_if_exists(path)  # idempotency: rebuild from scratch every run

        mat = asset_tools.create_asset(name, MAT_DEST, unreal.Material,
                                       unreal.MaterialFactoryNew())
        if mat is None:
            fail(name, "create_asset returned None")
            return None

        # VertexColor -> BaseColor. (Node positions are just for tidy graphs.)
        vcol = mel.create_material_expression(
            mat, unreal.MaterialExpressionVertexColor, -500, -100)
        mel.connect_material_property(vcol, "", unreal.MaterialProperty.MP_BASE_COLOR)

        # Constant 0.7 -> Roughness: soft, friendly, stylized non-shiny look.
        rough = mel.create_material_expression(
            mat, unreal.MaterialExpressionConstant, -500, 150)
        rough.set_editor_property("r", 0.7)
        mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

        if emissive:
            # VertexColor * 8.0 -> EmissiveColor, so crystals / the monument
            # actually GLOW in the moonlit night scenes (also feeds bloom).
            vcol2 = mel.create_material_expression(
                mat, unreal.MaterialExpressionVertexColor, -700, 350)
            strength = mel.create_material_expression(
                mat, unreal.MaterialExpressionConstant, -700, 500)
            strength.set_editor_property("r", 8.0)
            mul = mel.create_material_expression(
                mat, unreal.MaterialExpressionMultiply, -450, 400)
            # connect_material_expressions(from_expr, from_output, to_expr, to_input)
            mel.connect_material_expressions(vcol2, "", mul, "A")
            mel.connect_material_expressions(strength, "", mul, "B")
            mel.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

        mel.recompile_material(mat)
        eal.save_loaded_asset(mat)
        log("built material: {}".format(path))
        return mat
    except Exception as e:
        fail(name, "exception building material: {}".format(e))
        traceback.print_exc()
        return None


# ----------------------------------------------------------------------------
# Step 5: assign the master materials to every imported static mesh.
# ----------------------------------------------------------------------------

def assign_materials(mat_lit, mat_emissive):
    if mat_lit is None:
        log("WARNING: M_VertexLit missing -- skipping material assignment entirely")
        return

    for mesh_path in imported_mesh_paths:
        try:
            mesh = eal.load_asset(mesh_path)
            if not isinstance(mesh, unreal.StaticMesh):
                fail(mesh_path, "expected StaticMesh during assignment")
                continue

            asset_name = mesh_path.rsplit("/", 1)[-1]
            # Crystals and the monument glow; everything else is plain lit.
            # Case-insensitive on purpose so 'crystal_small' also matches.
            lower = asset_name.lower()
            wants_glow = ("crystal" in lower) or ("monument" in lower)
            target_mat = mat_emissive if (wants_glow and mat_emissive is not None) else mat_lit

            slots = mesh.get_editor_property("static_materials")
            num_slots = len(slots)
            if num_slots == 0:
                # A mesh with zero slots is odd but not fatal; UE will use the
                # world default material. Flag it so we notice.
                log("WARNING: {} has 0 material slots".format(mesh_path))

            if hasattr(mesh, "set_material"):
                # Preferred path: StaticMesh.set_material(index, material) is
                # the official editor-scripting setter and keeps slot names.
                for i in range(num_slots):
                    mesh.set_material(i, target_mat)
            else:
                # Fallback: rebuild the StaticMaterial array by hand and push
                # it back. (set_material has existed for many versions, but if
                # 5.7 ever drops it this branch keeps the pipeline alive.)
                new_slots = []
                for slot in slots:
                    slot.set_editor_property("material_interface", target_mat)
                    new_slots.append(slot)
                mesh.set_editor_property("static_materials", new_slots)

            eal.save_loaded_asset(mesh)
            log("assigned {} -> {} ({} slot(s))".format(
                MAT_EMISSIVE_NAME if target_mat is mat_emissive else MAT_LIT_NAME,
                mesh_path, num_slots))
        except Exception as e:
            fail(mesh_path, "exception assigning material: {}".format(e))
            traceback.print_exc()


# ----------------------------------------------------------------------------
# Step 6: manifest
# ----------------------------------------------------------------------------

def print_manifest():
    log("=" * 60)
    log("IMPORTED: {} meshes, {} sounds".format(
        len(imported_mesh_paths), len(imported_sound_paths)))
    for p in imported_mesh_paths:
        log("  mesh : {}".format(p))
    for p in imported_sound_paths:
        log("  sound: {}".format(p))
    if failures:
        log("FAILURES ({}):".format(len(failures)))
        for f_line in failures:
            log("  {}".format(f_line))
    else:
        log("FAILURES: none")
    log("=" * 60)


# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------

def main():
    log("project dir: {}".format(PROJECT_DIR))
    log("art source : {}".format(ART_SOURCE_DIR))

    import_all_meshes()                                   # steps 1 + 2
    import_all_audio()                                    # step 3
    mat_lit      = build_material(MAT_LIT_NAME, emissive=False)       # step 4a
    mat_emissive = build_material(MAT_EMISSIVE_NAME, emissive=True)   # step 4b
    assign_materials(mat_lit, mat_emissive)               # step 5

    # Final save sweep: make sure every dirty package under /Game/Art hits
    # disk even if an individual save above was skipped.
    try:
        eal.save_directory("/Game/Art", only_if_is_dirty=True, recursive=True)
    except Exception as e:
        log("WARNING: save_directory sweep failed: {}".format(e))

    print_manifest()                                      # step 6


if __name__ == "__main__":
    main()
