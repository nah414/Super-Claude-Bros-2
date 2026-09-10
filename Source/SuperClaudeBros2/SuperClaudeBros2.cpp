#include "SuperClaudeBros2.h"
#include "Modules/ModuleManager.h"

IMPLEMENT_PRIMARY_GAME_MODULE(FDefaultGameModuleImpl, SuperClaudeBros2, "SuperClaudeBros2");

// NOTE on discrete-GPU selection: do NOT export NvOptimusEnablement /
// AmdPowerXpressRequestHighPerformance here. The engine's Launch module (LaunchWindows.cpp) already
// exports them =1 (prefer the discrete NVIDIA/AMD GPU), so a duplicate definition in this module
// link-errors the MONOLITHIC packaged/cooked build (LNK2005 "already defined in Module.Launch.cpp.obj").
// The dGPU preference is already in effect from the engine; nothing to add. (The modular editor build
// tolerated the duplicate, which is why it only surfaced at cook time.)
