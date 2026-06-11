#include "FixHeroAnimsCommandlet.h"

#include "Animation/AnimSequence.h"
#include "Animation/Skeleton.h"
#include "Misc/PackageName.h"
#include "UObject/Package.h"
#include "UObject/SavePackage.h"

int32 UFixHeroAnimsCommandlet::Main(const FString& Params)
{
	USkeleton* Skel = LoadObject<USkeleton>(nullptr,
		TEXT("/Game/Art/HeroSkel/SCB2Hero_Skeleton.SCB2Hero_Skeleton"));
	if (!Skel)
	{
		UE_LOG(LogTemp, Error, TEXT("FIXANIM: skeleton not found"));
		return 1;
	}

	const TCHAR* Clips[] = { TEXT("Idle"), TEXT("Walk"), TEXT("Run"), TEXT("Jump"),
	                         TEXT("Strike1"), TEXT("Strike2"), TEXT("Haymaker"),
	                         TEXT("HitReact"), TEXT("Relight") };
	int32 Fixed = 0;
	for (const TCHAR* Clip : Clips)
	{
		const FString Path = FString::Printf(
			TEXT("/Game/Art/HeroSkel/A_Hero_%s.A_Hero_%s"), Clip, Clip);
		UAnimSequence* Anim = LoadObject<UAnimSequence>(nullptr, *Path);
		if (!Anim)
		{
			UE_LOG(LogTemp, Error, TEXT("FIXANIM: missing %s"), *Path);
			continue;
		}

		Anim->SetSkeleton(Skel);
#if WITH_EDITOR
		Anim->PostEditChange();   // kick compression now that a skeleton exists
#endif
		Anim->MarkPackageDirty();

		UPackage* Pkg = Anim->GetOutermost();
		const FString FileName = FPackageName::LongPackageNameToFilename(
			Pkg->GetName(), FPackageName::GetAssetPackageExtension());
		FSavePackageArgs SaveArgs;
		SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
		const bool bSaved = UPackage::SavePackage(Pkg, nullptr, *FileName, SaveArgs);

		const USkeleton* Check = Anim->GetSkeleton();
		UE_LOG(LogTemp, Display, TEXT("FIXANIM %s: skeleton=%s saved=%d"),
			Clip, Check ? *Check->GetName() : TEXT("NONE"), bSaved ? 1 : 0);
		Fixed += (Check == Skel && bSaved) ? 1 : 0;
	}

	UE_LOG(LogTemp, Display, TEXT("FIXANIM_DONE: %d/%d bound+saved"), Fixed, 9);
	return (Fixed == 9) ? 0 : 1;
}
