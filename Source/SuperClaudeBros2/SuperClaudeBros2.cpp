#include "SuperClaudeBros2.h"
#include "Modules/ModuleManager.h"

IMPLEMENT_PRIMARY_GAME_MODULE(FDefaultGameModuleImpl, SuperClaudeBros2, "SuperClaudeBros2");

// --- Hybrid-laptop GPU selection -------------------------------------------------------------
// Force the discrete GPU (RTX 5070 Laptop, 8 GB) instead of the AMD Radeon 890M iGPU (512 MB).
// The mobile NVIDIA Optimus / AMD PowerXpress drivers read these exported symbols from the
// executable's export table at launch and bind the high-performance dGPU. UE happens to pick
// the dGPU today, but a driver/dock/power-profile change could reroute to the iGPU — on which
// this game OOMs instantly. Must live in the PRIMARY GAME MODULE cpp so the symbols land in the
// game/editor .exe export table. (Does NOT change CPU/GPU split — the game always runs on the GPU.)
#if PLATFORM_WINDOWS
extern "C"
{
	__declspec(dllexport) unsigned long NvOptimusEnablement = 0x00000001;          // prefer NVIDIA dGPU
	__declspec(dllexport) int AmdPowerXpressRequestHighPerformance = 0x00000001;   // prefer AMD dGPU
}
#endif
