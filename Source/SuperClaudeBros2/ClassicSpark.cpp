// Classic Spark — the original boxer hero as a sparring duelist. Quick jabs, a
// launching uppercut, a counter-stance, and a flurry combo on the phase break.

#include "ClassicSpark.h"

#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "UObject/ConstructorHelpers.h"

AClassicSpark::AClassicSpark()
{
	GetCapsuleComponent()->SetCapsuleSize(38.f, 68.f);   // lean, ~1.36m 0.8-family
	RivalDisplayName = TEXT("CLASSIC SPARK");
	ApproachSpeed = 640.f;
	TurnRate = 8.f;
	IntroSeconds = 1.3f;
	StaggerSeconds = 1.7f;
	KnockbackForce = 840.f;
	KnockbackLift = 420.f;   // the uppercut sends heroes up
	DuelHitEmbers = 16.f;
	GetCharacterMovement()->MaxWalkSpeed = ApproachSpeed;

	SignatureColor = FLinearColor(2.6f, 1.9f, 0.6f);   // classic spark-gold
	BodyGlowColor  = FLinearColor(1.7f, 1.4f, 0.7f);
	HitBurstColor  = FLinearColor(2.8f, 1.8f, 0.6f);
	DefeatBurstColor = FLinearColor(3.0f, 2.0f, 0.7f);
	if (TelegraphLight) { TelegraphLight->SetLightColor(BodyGlowColor); }

	static ConstructorHelpers::FObjectFinder<USkeletalMesh> Model(TEXT("/Game/Art/ClassicSparkSkelV1/SCB2ClassicSpark.SCB2ClassicSpark"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FIdle(TEXT("/Game/Art/ClassicSparkSkelV1/A_ClassicSpark_Idle_Anim.A_ClassicSpark_Idle_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FWalk(TEXT("/Game/Art/ClassicSparkSkelV1/A_ClassicSpark_Walk_Anim.A_ClassicSpark_Walk_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FJab(TEXT("/Game/Art/ClassicSparkSkelV1/A_ClassicSpark_Jab_Anim.A_ClassicSpark_Jab_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FUpper(TEXT("/Game/Art/ClassicSparkSkelV1/A_ClassicSpark_Uppercut_Anim.A_ClassicSpark_Uppercut_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FCounter(TEXT("/Game/Art/ClassicSparkSkelV1/A_ClassicSpark_Counter_Anim.A_ClassicSpark_Counter_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FCombo(TEXT("/Game/Art/ClassicSparkSkelV1/A_ClassicSpark_Combo_Anim.A_ClassicSpark_Combo_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FHit(TEXT("/Game/Art/ClassicSparkSkelV1/A_ClassicSpark_HitReact_Anim.A_ClassicSpark_HitReact_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FStagger(TEXT("/Game/Art/ClassicSparkSkelV1/A_ClassicSpark_Stagger_Anim.A_ClassicSpark_Stagger_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FDefeat(TEXT("/Game/Art/ClassicSparkSkelV1/A_ClassicSpark_Defeat_Anim.A_ClassicSpark_Defeat_Anim"));

	if (Model.Succeeded())
	{
		RivalBody->SetSkeletalMesh(Model.Object);
		bHasSkeletalModel = true;
		PlaceholderBody->SetVisibility(false);
	}
	else
	{
		static ConstructorHelpers::FObjectFinder<UStaticMesh> Capsule(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
		if (Capsule.Succeeded()) { PlaceholderBody->SetStaticMesh(Capsule.Object); PlaceholderBody->SetRelativeScale3D(FVector(0.7f, 0.7f, 1.4f)); }
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
	Jab.Tell = 0.30f; Jab.Active = 0.22f; Jab.Recover = 0.55f; Jab.Reach = 200.f; Jab.EmberMul = 0.7f;
	Jab.ClipStart = 0.15f; Jab.ClipRate = 1.33f;   // scanned: extension @0.35 of 2.00s
	AddMove(Jab);

	FGuardianMove Upper;
	Upper.Name = TEXT("Uppercut");
	Upper.Clip = LoadRivalClip(FUpper);
	Upper.Kind = EGuardianMoveKind::Cone;
	Upper.Tell = 0.50f; Upper.Active = 0.30f; Upper.Recover = 0.9f; Upper.Reach = 210.f; Upper.EmberMul = 1.1f;
	Upper.ClipStart = 0.55f; Upper.ClipRate = 0.56f;   // scanned: rising-fist apex @0.823 of 1.03s
	AddMove(Upper);

	FGuardianMove Counter;
	Counter.Name = TEXT("Counter Stance");
	Counter.Clip = LoadRivalClip(FCounter);
	Counter.Kind = EGuardianMoveKind::Guard;
	Counter.Tell = 0.40f; Counter.Active = 0.55f; Counter.Recover = 0.5f; Counter.Reach = 220.f;   // tell >= his Jab (0.30) so the counter-stance reads as a guard
	AddMove(Counter);

	FGuardianMove Combo;
	Combo.Name = TEXT("One-Two Combo");
	Combo.Clip = LoadRivalClip(FCombo);
	Combo.Kind = EGuardianMoveKind::ConeTwice;
	Combo.Tell = 0.50f; Combo.Active = 0.45f; Combo.Recover = 0.85f; Combo.Reach = 210.f; Combo.EmberMul = 0.8f;
	Combo.ClipStart = 0.22f; Combo.ClipRate = 1.80f;   // scanned: first beat @~0.40 of 5.00s
	Combo.MinPhase = 2; Combo.bSignature = true;
	SignatureIdx = AddMove(Combo);
}
