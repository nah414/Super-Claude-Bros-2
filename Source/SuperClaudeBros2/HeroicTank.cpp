// The Heroic Tank — the heavy carrier. Slow, enormous knockback, a brace, and a
// shoulder charge that crosses the arena when the duel escalates.

#include "HeroicTank.h"

#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "UObject/ConstructorHelpers.h"

AHeroicTank::AHeroicTank()
{
	GetCapsuleComponent()->SetCapsuleSize(55.f, 82.f);   // broad, ~1.64m 0.8-family
	RivalDisplayName = TEXT("THE HEROIC TANK");
	ApproachSpeed = 470.f;
	TurnRate = 4.5f;
	IntroSeconds = 1.6f;
	StaggerSeconds = 2.2f;
	KnockbackForce = 1120.f;   // he hits like a truck
	KnockbackLift = 420.f;
	DuelHitEmbers = 20.f;
	LungeSpeed = 1950.f;       // the shoulder charge is fast once committed
	GetCharacterMovement()->MaxWalkSpeed = ApproachSpeed;

	SignatureColor = FLinearColor(2.8f, 1.9f, 0.7f);   // gilded amber
	BodyGlowColor  = FLinearColor(1.8f, 1.4f, 0.7f);
	HitBurstColor  = FLinearColor(3.0f, 1.7f, 0.6f);
	HitBurstScale = 1.35f;
	DefeatBurstColor = FLinearColor(3.2f, 2.0f, 0.8f);
	DefeatBurstScale = 2.1f;
	if (TelegraphLight) { TelegraphLight->SetLightColor(BodyGlowColor); }

	static ConstructorHelpers::FObjectFinder<USkeletalMesh> Model(TEXT("/Game/Art/HeroicTankSkelV1/SCB2HeroicTank.SCB2HeroicTank"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FIdle(TEXT("/Game/Art/HeroicTankSkelV1/A_HeroicTank_Idle_Anim.A_HeroicTank_Idle_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FWalk(TEXT("/Game/Art/HeroicTankSkelV1/A_HeroicTank_Walk_Anim.A_HeroicTank_Walk_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FSwing(TEXT("/Game/Art/HeroicTankSkelV1/A_HeroicTank_Swing_Anim.A_HeroicTank_Swing_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FPush(TEXT("/Game/Art/HeroicTankSkelV1/A_HeroicTank_Push_Anim.A_HeroicTank_Push_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FCharge(TEXT("/Game/Art/HeroicTankSkelV1/A_HeroicTank_Charge_Anim.A_HeroicTank_Charge_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FBlock(TEXT("/Game/Art/HeroicTankSkelV1/A_HeroicTank_Block_Anim.A_HeroicTank_Block_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FHit(TEXT("/Game/Art/HeroicTankSkelV1/A_HeroicTank_HitReact_Anim.A_HeroicTank_HitReact_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FStagger(TEXT("/Game/Art/HeroicTankSkelV1/A_HeroicTank_Stagger_Anim.A_HeroicTank_Stagger_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FDefeat(TEXT("/Game/Art/HeroicTankSkelV1/A_HeroicTank_Defeat_Anim.A_HeroicTank_Defeat_Anim"));

	if (Model.Succeeded())
	{
		RivalBody->SetSkeletalMesh(Model.Object);
		bHasSkeletalModel = true;
		PlaceholderBody->SetVisibility(false);
	}
	else
	{
		static ConstructorHelpers::FObjectFinder<UStaticMesh> Box(TEXT("/Engine/BasicShapes/Cube.Cube"));
		if (Box.Succeeded()) { PlaceholderBody->SetStaticMesh(Box.Object); PlaceholderBody->SetRelativeScale3D(FVector(1.2f, 1.2f, 1.7f)); }
	}
	IdleAnim = LoadRivalClip(FIdle);
	MoveAnim = LoadRivalClip(FWalk);
	HitReactAnim = LoadRivalClip(FHit);
	StaggerAnim = LoadRivalClip(FStagger);
	DefeatAnim = LoadRivalClip(FDefeat);

	FGuardianMove Swing;
	Swing.Name = TEXT("Heavy Swing");
	Swing.Clip = LoadRivalClip(FSwing);
	Swing.Kind = EGuardianMoveKind::Cone;
	Swing.Tell = 0.70f; Swing.Active = 0.40f; Swing.Recover = 1.1f; Swing.Reach = 280.f; Swing.EmberMul = 1.2f;
	Swing.ClipStart = 0.55f; Swing.ClipRate = 0.99f;   // scanned: full extension @0.93 of 1.83s
	AddMove(Swing);

	FGuardianMove Push;
	Push.Name = TEXT("Shield Shove");
	Push.Clip = LoadRivalClip(FPush);
	Push.Kind = EGuardianMoveKind::Cone;
	Push.Tell = 0.50f; Push.Active = 0.30f; Push.Recover = 0.9f; Push.Reach = 220.f; Push.EmberMul = 0.8f;
	Push.ClipStart = 0.40f; Push.ClipRate = 1.17f;   // scanned: shove @0.625 of 2.60s
	AddMove(Push);

	FGuardianMove Block;
	Block.Name = TEXT("Brace");
	Block.Clip = LoadRivalClip(FBlock);
	Block.Kind = EGuardianMoveKind::Guard;
	Block.Tell = 0.40f; Block.Active = 0.60f; Block.Recover = 0.6f; Block.Reach = 280.f;
	AddMove(Block);

	FGuardianMove Charge;
	Charge.Name = TEXT("Shoulder Charge");
	Charge.Clip = LoadRivalClip(FCharge);
	Charge.Kind = EGuardianMoveKind::Lunge;
	Charge.Tell = 0.80f; Charge.Active = 0.55f; Charge.Recover = 1.3f; Charge.Reach = 210.f; Charge.EmberMul = 1.4f;
	Charge.MinPhase = 2;       // a phase-break reveal like the other guardians' signatures
	Charge.bSignature = true;
	SignatureIdx = AddMove(Charge);
}
