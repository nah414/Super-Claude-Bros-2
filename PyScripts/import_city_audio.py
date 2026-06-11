"""Import ONLY the city audio loops (never rerun the full import_art.py — its glb
path would drag the kit back through Interchange roulette)."""
import os

import unreal

SRC = r"C:\Users\Atomn\mario2\SuperClaudeBros2\ArtSource\audio"
DEST = "/Game/Art/Audio"
tools = unreal.AssetToolsHelpers.get_asset_tools()

for name in ("amb_rain_loop", "music_city_loop"):
    task = unreal.AssetImportTask()
    task.filename = os.path.join(SRC, f"{name}.wav")
    task.destination_path = DEST
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = True
    tools.import_asset_tasks([task])
    snd = unreal.load_asset(f"{DEST}/{name}")
    if not snd:
        raise SystemExit(f"AUDIO_IMPORT_FAILED: {name}")
    snd.set_editor_property("looping", True)
    unreal.EditorAssetLibrary.save_loaded_asset(snd)
    print(f"AUDIO_OK: {name}")

print("CITY_AUDIO_IMPORT_DONE")
