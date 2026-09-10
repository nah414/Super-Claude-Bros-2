"""Remove the round-5 MPC scratch-test assets."""
import unreal

EAL = unreal.EditorAssetLibrary
for n in ("M_ZZ_MPCTestA", "M_ZZ_MPCTestB", "M_ZZ_MPCTestC",
          "M_ZZ_DepthDebug", "M_ZZ_VCDebug", "M_ZZ_UVDebug",
          "M_ZZ_DepthTermDebug", "M_ZZ_AtomDebug", "M_ZZ_NodeCheck"):
    p = f"/Game/Art/Verdant/{n}"
    if EAL.does_asset_exist(p):
        EAL.delete_asset(p)
        print(f"CLEANUP: {n} deleted")
print("CLEANUP_DONE")
