// The Powerhouse — the grounded bruiser. Fast jabs, a hook, a two-beat combo, and a
// both-fists overhead that drops on the phase break. The shared engine, hammer-tuned.

#include "Powerhouse.h"

#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "UObject/ConstructorHelpers.h"

APowerhouse::APowerhouse()
{
	GetCapsuleComponent()->SetCapsuleSize(48.f, 75.f);   // stocky, ~1.50m 0.8-family
	RivalDisplayName = TEXT("THE POWERHOUSE");
	ApproachSpeed = 560.f;
	TurnRate = 6.f;
	IntroSeconds = 1.4f;
	StaggerSeconds = 1.9f;
	KnockbackForce = 980.f;
	KnockbackLift = 360.f;
	DuelHitEmbers = 18.f;
	GetCharacterMovement()->MaxWalkSpeed = ApproachSpeed;

	SignatureColor = FLinearColor(2.9f, 0.9f, 0.4f);   // forge orange
	BodyGlowColor  = FLinearColor(1.9f, 1.0f, 0.5f);
	HitBurstColor  = FLinearColor(3.0f, 1.3f, 0.45f);
	HitBurstScale = 1.3f;
	DefeatBurstColor = FLinearColor(3.2f, 1.5f, 0.6f);
	if (TelegraphLight) { TelegraphLight->SetLightColor(BodyGlowColor); }

	static ConstructorHelpers::FObjectFinder<USkeletalMesh> Model(TEXT("/Game/Art/PowerhouseSkelV1/SCB2Powerhouse.SCB2Powerhouse"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FIdle(TEXT("/Game/Art/PowerhouseSkelV1/A_Powerhouse_Idle_Anim.A_Powerhouse_Idle_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FWalk(TEXT("/Game/Art/PowerhouseSkelV1/A_Powerhouse_Walk_Anim.A_Powerhouse_Walk_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FJab(TEXT("/Game/Art/PowerhouseSkelV1/A_Powerhouse_Jab_Anim.A_Powerhouse_Jab_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FHook(TEXT("/Game/Art/PowerhouseSkelV1/A_Powerhouse_Hook_Anim.A_Powerhouse_Hook_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FBoth(TEXT("/Game/Art/PowerhouseSkelV1/A_Powerhouse_BothFists_Anim.A_Powerhouse_BothFists_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FCombo(TEXT("/Game/Art/PowerhouseSkelV1/A_Powerhouse_Combo_Anim.A_Powerhouse_Combo_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FHit(TEXT("/Game/Art/PowerhouseSkelV1/A_Powerhouse_HitReact_Anim.A_Powerhouse_HitReact_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FStagger(TEXT("/Game/Art/PowerhouseSkelV1/A_Powerhouse_Stagger_Anim.A_Powerhouse_Stagger_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FDefeat(TEXT("/Game/Art/PowerhouseSkelV1/A_Powerhouse_Defeat_Anim.A_Powerhouse_Defeat_Anim"));

	if (Model.Succeeded())
	{
		RivalBody->SetSkeletalMesh(Model.Object);
		bHasSkeletalModel = true;
		PlaceholderBody->SetVisibility(false);
	}
	else
	{
		static ConstructorHelpers::FObjectFinder<UStaticMesh> Box(TEXT("/Engine/BasicShapes/Cube.Cube"));
		if (Box.Succeeded()) { PlaceholderBody->SetStaticMesh(Box.Object); PlaceholderBody->SetRelativeScale3D(FVector(1.0f, 1.0f, 1.5f)); }
	}
	IdleAnim = LoadRivalClip(FIdle);
	MoveAnim = LoadRivalClip(FWalk);
	HitReactAnim = LoadRivalClip(FHit);
	StaggerAnim = LoadRivalClip(FStagger);
	DefeatAnim = LoadRivalClip(FDefeat);

	FGuardianMove Jab;
	Jab.Name = TEXT("Jab");
	Jab.Clip = LoadRivalClip(FJab);
	Jab.Kind = EGuardianMoveKind::Cone;
	Jab.Tell = 0.35f; Jab.Active = 0.25f; Jab.Recover = 0.6f; Jab.Reach = 210.f; Jab.EmberMul = 0.7f;
	AddMove(Jab);

	FGuardianMove Hook;
	Hook.Name = TEXT("Hook");
	Hook.Clip = LoadRivalClip(FHook);
	Hook.Kind = EGuardianMoveKind::Cone;
	Hook.Tell = 0.50f; Hook.Active = 0.30f; Hook.Recover = 0.85f; Hook.Reach = 230.f; Hook.EmberMul = 1.0f;
	AddMove(Hook);

	FGuardianMove Combo;
	Combo.Name = TEXT("Combo");
	Combo.Clip = LoadRivalClip(FCombo);
	Combo.Kind = EGuardianMoveKind::ConeTwice;
	Combo.Tell = 0.55f; Combo.Active = 0.50f; Combo.Recover = 0.95f; Combo.Reach = 230.f; Combo.EmberMul = 0.8f;
	AddMove(Combo);

	FGuardianMove Both;
	Both.Name = TEXT("Hammer Blow");
	Both.Clip = LoadRivalClip(FBoth);
	Both.Kind = EGuardianMoveKind::Cone;
	Both.Tell = 0.65f; Both.Active = 0.40f; Both.Recover = 1.1f; Both.Reach = 240.f; Both.EmberMul = 1.5f;
	Both.MinPhase = 2; Both.bSignature = true;
	SignatureIdx = AddMove(Both);
}
