"""Restore the river after the DepthFade instrument shot."""
import unreal

EAL = unreal.EditorAssetLibrary
DEST = "/Game/Art/Verdant"
mesh = EAL.load_asset(f"{DEST}/river_surface")
mat = EAL.load_asset(f"{DEST}/M_VR_WaterFlow")
mesh.set_material(0, mat)
EAL.save_loaded_asset(mesh)
if EAL.does_asset_exist(f"{DEST}/M_ZZ_DepthDebug"):
    EAL.delete_asset(f"{DEST}/M_ZZ_DepthDebug")
    print("RESTORE: debug material deleted")
print("RESTORE: river wears M_VR_WaterFlow again")
print("RESTORE_DONE")
