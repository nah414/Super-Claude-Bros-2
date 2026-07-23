"""Import the Blender-sculpted World Stage terrain with WALKABLE collision.

The July 22 ghost-hills lesson: non-uniformly scaled sphere COLLISION primitives
degenerate — render stretched, physics didn't, the hero ran straight through.
The terrain mesh instead carries CTF_USE_COMPLEX_AS_SIMPLE: traces and feet hit
the actual sculpted triangles. Nanite stays OFF here (Nanite would swap collision
to its coarse fallback; 68k raster tris are cheap).
"""
import os

import unreal

SRC = r"C:\Users\Atomn\mario2\_prep\stage_terrain.fbx"
DEST = "/Game/Art/Moonworks"
SPAN_X = 28000.0

assert os.path.isfile(SRC), "TERRAIN_FBX_MISSING"
unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
tools = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary

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
sd.set_editor_property("auto_generate_collision", False)   # complex IS the collision

task = unreal.AssetImportTask()
task.filename = SRC
task.destination_path = DEST
task.destination_name = "stage_terrain"
task.automated = True
task.save = True
task.replace_existing = True
task.options = ui
tools.import_asset_tasks([task])
paths = list(task.get_editor_property("imported_object_paths") or [])
mesh = unreal.load_asset(paths[0]) if paths else None
assert isinstance(mesh, unreal.StaticMesh), "TERRAIN_IMPORT_FAILED"

# Probe-and-correct to exactly 28000uu across (the only scale truth we trust).
b = mesh.get_bounding_box()
span = b.max.x - b.min.x
if span > 1.0 and abs(1.0 - SPAN_X / span) > 0.01:
    s = SPAN_X / span
    sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    bs = sms.get_lod_build_settings(mesh, 0)
    bs.build_scale3d = unreal.Vector(s, s, s)
    sms.set_lod_build_settings(mesh, 0, bs)
    print(f"TERRAIN_SCALE: span {span:.0f} -> x{s:.3f}")

# THE WALKABLE LAYER: queries collide with the sculpted triangles themselves.
body = mesh.get_editor_property("body_setup")
body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
mesh.set_editor_property("body_setup", body)

basic = unreal.load_asset("/Engine/BasicShapes/BasicShapeMaterial")
if basic:
    mesh.set_material(0, basic)

EAL.save_loaded_asset(mesh)
b2 = mesh.get_bounding_box()
print(f"TERRAIN_OK: {b2.max.x - b2.min.x:.0f} x {b2.max.y - b2.min.y:.0f} uu, peak {b2.max.z:.0f}uu")
print("TERRAIN_IMPORT_DONE")
