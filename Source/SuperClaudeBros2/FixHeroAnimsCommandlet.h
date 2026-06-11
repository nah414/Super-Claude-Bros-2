// One-shot repair tool: the headless FBX import pipeline produces AnimSequences
// with Skeleton == nullptr (python's set_editor_property is blocked: read-only).
// C++ isn't blocked — this commandlet binds every hero clip to SCB2Hero_Skeleton
// and saves. Run:  UnrealEditor-Cmd.exe <proj> -run=FixHeroAnims

#pragma once

#include "Commandlets/Commandlet.h"
#include "FixHeroAnimsCommandlet.generated.h"

UCLASS()
class UFixHeroAnimsCommandlet : public UCommandlet
{
	GENERATED_BODY()

public:
	virtual int32 Main(const FString& Params) override;
};
