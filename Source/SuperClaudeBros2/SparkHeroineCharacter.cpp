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
	// Her SIGNATURE combo (Adam's custom-moves law: jabs read as hand-waving on
	// her frame): left hook / rising upper-hook / both-fists drive.
	static ConstructorHelpers::FObjectFinder<UAnimSequence> HerCombo1(TEXT("/Game/Art/HeroineSkelV2/A_Heroine_Combo1_Anim.A_Heroine_Combo1_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> HerCombo2(TEXT("/Game/Art/HeroineSkelV2/A_Heroine_Combo2_Anim.A_Heroine_Combo2_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> HerCombo3(TEXT("/Game/Art/HeroineSkelV2/A_Heroine_Combo3_Anim.A_Heroine_Combo3_Anim"));

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

	// Signature combo wins over the jab scaffolding; windows are data-scanned
	// (hand-extension peaks: hook impact frac 0.725, upper-hook 0.475, double
	// drive 0.20) so the PUNCH plays inside the beat, not the wind-up.
	if (HerCombo1.Succeeded())
	{
		Strike1Anim = HerCombo1.Object.Get();
		Strike1ClipStartFraction = 0.40f;
		Strike1ClipRate = 2.2f;
	}
	if (HerCombo2.Succeeded())
	{
		Strike2Anim = HerCombo2.Object.Get();
		Strike2ClipStartFraction = 0.33f;
		Strike2ClipRate = 1.8f;
	}
	if (HerCombo3.Succeeded())
	{
		HaymakerAnim = HerCombo3.Object.Get();
		HaymakerClipStartFraction = 0.12f;
		HaymakerClipRate = 1.4f;
	}
}
