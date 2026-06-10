using UnrealBuildTool;

public class SuperClaudeBros2 : ModuleRules
{
	public SuperClaudeBros2(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"EngineCameras"   // PerlinNoiseCameraShakePattern (UE 5.7: lives in the EngineCameras plugin)
		});
	}
}
