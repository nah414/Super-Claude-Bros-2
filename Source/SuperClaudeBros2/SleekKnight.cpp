// The Sleek Knight — agile crystal duelist. Quick cuts, a defensive sidestep, and a
// crystal spin that crowns the phase break. All from the shared fighter engine.

#include "SleekKnight.h"

#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "UObject/ConstructorHelpers.h"

ASleekKnight::ASleekKnight()
{
	GetCapsuleComponent()->SetCapsuleSize(38.f, 71.f);   // slim, ~1.42m 0.8-family
	RivalDisplayName = TEXT("THE SLEEK KNIGHT");
	ApproachSpeed = 720.f;
	TurnRate = 9.f;
	IntroSeconds = 1.2f;
	StaggerSeconds = 1.6f;
	KnockbackForce = 780.f;
	KnockbackLift = 360.f;
	DuelHitEmbers = 16.f;
	GetCharacterMovement()->MaxWalkSpeed = ApproachSpeed;

	SignatureColor = FLinearColor(0.6f, 2.4f, 2.9f);   // crystal cyan
	BodyGlowColor  = FLinearColor(1.1f, 1.8f, 2.2f);
	HitBurstColor  = FLinearColor(1.4f, 2.4f, 2.9f);
	DefeatBurstColor = FLinearColor(1.6f, 2.6f, 3.0f);
	if (TelegraphLight) { TelegraphLight->SetLightColor(BodyGlowColor); }

	static ConstructorHelpers::FObjectFinder<USkeletalMesh> Model(TEXT("/Game/Art/SleekKnightSkelV1/SCB2SleekKnight.SCB2SleekKnight"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FIdle(TEXT("/Game/Art/SleekKnightSkelV1/A_SleekKnight_Idle_Anim.A_SleekKnight_Idle_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FWalk(TEXT("/Game/Art/SleekKnightSkelV1/A_SleekKnight_Walk_Anim.A_SleekKnight_Walk_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FSlash1(TEXT("/Game/Art/SleekKnightSkelV1/A_SleekKnight_Slash1_Anim.A_SleekKnight_Slash1_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FSlash2(TEXT("/Game/Art/SleekKnightSkelV1/A_SleekKnight_Slash2_Anim.A_SleekKnight_Slash2_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FSpin(TEXT("/Game/Art/SleekKnightSkelV1/A_SleekKnight_Spin_Anim.A_SleekKnight_Spin_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FDodge(TEXT("/Game/Art/SleekKnightSkelV1/A_SleekKnight_Dodge_Anim.A_SleekKnight_Dodge_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FHit(TEXT("/Game/Art/SleekKnightSkelV1/A_SleekKnight_HitReact_Anim.A_SleekKnight_HitReact_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FStagger(TEXT("/Game/Art/SleekKnightSkelV1/A_SleekKnight_Stagger_Anim.A_SleekKnight_Stagger_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FDefeat(TEXT("/Game/Art/SleekKnightSkelV1/A_SleekKnight_Defeat_Anim.A_SleekKnight_Defeat_Anim"));

	if (Model.Succeeded())
	{
		RivalBody->SetSkeletalMesh(Model.Object);
		bHasSkeletalModel = true;
		PlaceholderBody->SetVisibility(false);
	}
	else
	{
		static ConstructorHelpers::FObjectFinder<UStaticMesh> Capsule(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
		if (Capsule.Succeeded()) { PlaceholderBody->SetStaticMesh(Capsule.Object); PlaceholderBody->SetRelativeScale3D(FVector(0.7f, 0.7f, 1.5f)); }
	}
	IdleAnim = LoadRivalClip(FIdle);
	MoveAnim = LoadRivalClip(FWalk);
	HitReactAnim = LoadRivalClip(FHit);
	StaggerAnim = LoadRivalClip(FStagger);
	DefeatAnim = LoadRivalClip(FDefeat);

	FGuardianMove Slash1;
	Slash1.Name = TEXT("Crystal Cut");
	Slash1.Clip = LoadRivalClip(FSlash1);
	Slash1.Kind = EGuardianMoveKind::Cone;
	Slash1.Tell = 0.40f; Slash1.Active = 0.30f; Slash1.Recover = 0.70f; Slash1.Reach = 230.f; Slash1.EmberMul = 1.0f;
	AddMove(Slash1);

	FGuardianMove Slash2;
	Slash2.Name = TEXT("Twin Slash");
	Slash2.Clip = LoadRivalClip(FSlash2);
	Slash2.Kind = EGuardianMoveKind::ConeTwice;
	Slash2.Tell = 0.48f; Slash2.Active = 0.45f; Slash2.Recover = 0.78f; Slash2.Reach = 240.f; Slash2.EmberMul = 0.8f;
	AddMove(Slash2);

	FGuardianMove Dodge;
	Dodge.Name = TEXT("Sidestep");
	Dodge.Clip = LoadRivalClip(FDodge);
	Dodge.Kind = EGuardianMoveKind::Guard;
	Dodge.Tell = 0.40f; Dodge.Active = 0.45f; Dodge.Recover = 0.45f; Dodge.Reach = 260.f;   // tell >= his fastest strike (0.40) so the stance reads, not a feint
	AddMove(Dodge);

	FGuardianMove Spin;
	Spin.Name = TEXT("Crystal Spin");
	Spin.Clip = LoadRivalClip(FSpin);
	Spin.Kind = EGuardianMoveKind::Ring;
	Spin.Tell = 0.55f; Spin.Active = 0.40f; Spin.Recover = 1.0f; Spin.Reach = 300.f; Spin.EmberMul = 1.1f;
	Spin.MinPhase = 2; Spin.bSignature = true;
	SignatureIdx = AddMove(Spin);
}
