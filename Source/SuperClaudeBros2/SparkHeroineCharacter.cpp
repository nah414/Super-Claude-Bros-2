#include "SparkHeroineCharacter.h"

#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/AnimSequence.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	UAnimSequence* Pick(const ConstructorHelpers::FObjectFinder<UAnimSequence>& Finder,
	                    UAnimSequence* Fallback)
	{
		return Finder.Succeeded() ? Finder.Object.Get() : Fallback;
	}
}

ASparkHeroineCharacter::ASparkHeroineCharacter()
{
	// Sonnet's body and clips replace Claude's; everything else is inherited.
	// Missing clips fall back to his (parity never breaks while hers import).
	static ConstructorHelpers::FObjectFinder<USkeletalMesh> HerModel(TEXT("/Game/Art/HeroineSkelV2/SCB2Heroine.SCB2Heroine"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> HerIdle(TEXT("/Game/Art/HeroineSkelV2/A_Heroine_Idle_Anim.A_Heroine_Idle_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> HerWalk(TEXT("/Game/Art/HeroineSkelV2/A_Heroine_Walk_Anim.A_Heroine_Walk_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> HerRun(TEXT("/Game/Art/HeroineSkelV2/A_Heroine_Run_Anim.A_Heroine_Run_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> HerJump(TEXT("/Game/Art/HeroineSkelV2/A_Heroine_Jump_Anim.A_Heroine_Jump_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> HerStrike1(TEXT("/Game/Art/HeroineSkelV2/A_Heroine_Strike1_Anim.A_Heroine_Strike1_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> HerStrike2(TEXT("/Game/Art/HeroineSkelV2/A_Heroine_Strike2_Anim.A_Heroine_Strike2_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> HerHaymaker(TEXT("/Game/Art/HeroineSkelV2/A_Heroine_Haymaker_Anim.A_Heroine_Haymaker_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> HerHitReact(TEXT("/Game/Art/HeroineSkelV2/A_Heroine_HitReact_Anim.A_Heroine_HitReact_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> HerRelight(TEXT("/Game/Art/HeroineSkelV2/A_Heroine_Relight_Anim.A_Heroine_Relight_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> HerCrouch(TEXT("/Game/Art/HeroineSkelV2/A_Heroine_CrouchWalk_Anim.A_Heroine_CrouchWalk_Anim"));

	if (HerModel.Succeeded() && SkelBody)
	{
		SkelBody->SetSkeletalMesh(HerModel.Object);
		bHasSkeletalModel = true;
	}
	IdleAnim = Pick(HerIdle, IdleAnim);
	WalkAnim = Pick(HerWalk, WalkAnim);
	RunAnim = Pick(HerRun, RunAnim);
	JumpAnim = Pick(HerJump, JumpAnim);
	Strike1Anim = Pick(HerStrike1, Strike1Anim);
	Strike2Anim = Pick(HerStrike2, Strike2Anim);
	HaymakerAnim = Pick(HerHaymaker, HaymakerAnim);
	HitReactAnim = Pick(HerHitReact, HitReactAnim);
	RelightAnim = Pick(HerRelight, RelightAnim);
	CrouchAnim = Pick(HerCrouch, CrouchAnim);
}
