using UnrealBuildTool;
using System.Collections.Generic;

public class SuperClaudeBros2EditorTarget : TargetRules
{
	public SuperClaudeBros2EditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("SuperClaudeBros2");
	}
}
