"""Boot + load the heavy NeonCity with rendering (the exact path that device-removed this morning)
and confirm it now loads inside the 8 GB budget. Run with -RenderOffscreen (NOT -nullrhi — we WANT
the renderer + device profile + texture pool active). The engine logs the device-profile application
+ 'Texture pool size now N MB'; this script just forces the map load and prints a marker so the run
is unambiguous. A clean exit (no DXGI_ERROR_DEVICE_REMOVED in the log) is the pass signal."""
import unreal

print("RUNTIME_BUDGET_BOOT: loading /Game/Maps/NeonCity with rendering active...")
ok = unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/NeonCity")
print(f"RUNTIME_BUDGET_LOADED: {ok}")

# Count actors so the world is actually realized (not a lazy stub).
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
n = len(eas.get_all_level_actors())
print(f"RUNTIME_BUDGET_ACTORS: {n}")
print("RUNTIME_BUDGET_DONE")
