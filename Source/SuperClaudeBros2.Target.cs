using UnrealBuildTool;
using System.Collections.Generic;

public class SuperClaudeBros2Target : TargetRules
{
	public SuperClaudeBros2Target(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("SuperClaudeBros2");
	}
}
