// The Hollow Warden — a knight who eats the light. The duel framework is all
// inherited; what lives here is the sword, the dark, and how the two feed.

#include "HollowWarden.h"

#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "SparkHeroCharacter.h"
#include "SparkImpactBurst.h"
#include "UObject/ConstructorHelpers.h"
#include "UObject/UObjectIterator.h"

namespace
{
	const FLinearColor WardenVoid(0.5f, 0.15f, 1.1f);    // the dark energy he wears
	const FLinearColor WardenGold(2.4f, 1.6f, 0.45f);    // the corrupted trim
}

AHollowWarden::AHollowWarden()
{
	GetCapsuleComponent()->SetCapsuleSize(52.f, 78.f);   // a tall knight

	ApproachSpeed = 600.f;
	TurnRate = 6.f;
	IntroSeconds = 1.6f;
	ApproachAnimRate = 1.0f;
	TelegraphPulseHz = 18.f;
	TelegraphPulseIntensity = 6200.f;
	PhaseRoarSeconds = 1.1f;
	FlinchSeconds = 0.45f;
	StaggerSeconds = 2.0f;
	KnockbackForce = 900.f;
	KnockbackLift = 400.f;
	GetCharacterMovement()->MaxWalkSpeed = ApproachSpeed;

	HitBurstColor = FLinearColor(2.2f, 0.9f, 2.6f);   // a violet-gold cut
	HitBurstScale = 1.2f;
	HitBurstLight = 5000.f;
	DefeatBurstColor = FLinearColor(3.f, 2.f, 3.6f);
	DefeatBurstScale = 2.1f;
	DefeatBurstLight = 7600.f;
	if (TelegraphLight) { TelegraphLight->SetLightColor(WardenVoid); }

	static ConstructorHelpers::FObjectFinder<USkeletalMesh> Model(TEXT("/Game/Art/WardenSkelV1/SCB2Warden.SCB2Warden"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FIdle(TEXT("/Game/Art/WardenSkelV1/A_Warden_Idle_Anim.A_Warden_Idle_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FWalk(TEXT("/Game/Art/WardenSkelV1/A_Warden_Walk_Anim.A_Warden_Walk_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FSlash(TEXT("/Game/Art/WardenSkelV1/A_Warden_Slash_Anim.A_Warden_Slash_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FJudg(TEXT("/Game/Art/WardenSkelV1/A_Warden_Judgment_Anim.A_Warden_Judgment_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FCharged(TEXT("/Game/Art/WardenSkelV1/A_Warden_Charged_Anim.A_Warden_Charged_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FVoid(TEXT("/Game/Art/WardenSkelV1/A_Warden_Voidcast_Anim.A_Warden_Voidcast_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FHit(TEXT("/Game/Art/WardenSkelV1/A_Warden_HitReact_Anim.A_Warden_HitReact_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FStagger(TEXT("/Game/Art/WardenSkelV1/A_Warden_Stagger_Anim.A_Warden_Stagger_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FDefeat(TEXT("/Game/Art/WardenSkelV1/A_Warden_Defeat_Anim.A_Warden_Defeat_Anim"));

	if (Model.Succeeded())
	{
		RivalBody->SetSkeletalMesh(Model.Object);
		bHasSkeletalModel = true;
		PlaceholderBody->SetVisibility(false);
	}
	else
	{
		static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
		if (Sphere.Succeeded())
		{
			PlaceholderBody->SetStaticMesh(Sphere.Object);
			PlaceholderBody->SetRelativeScale3D(FVector(1.2f, 1.2f, 2.7f));
		}
	}
	IdleAnim = LoadRivalClip(FIdle);
	MoveAnim = LoadRivalClip(FWalk);
	SlashAnim = LoadRivalClip(FSlash);
	JudgmentAnim = LoadRivalClip(FJudg);
	ChargedAnim = LoadRivalClip(FCharged);
	VoidAnim = LoadRivalClip(FVoid);
	HitReactAnim = LoadRivalClip(FHit);
	StaggerAnim = LoadRivalClip(FStagger);
	DefeatAnim = LoadRivalClip(FDefeat);

	// scanned attack windows (recipe 7.5; RightHand Z/reach peaks).
	SlashClipStart = 0.25f; SlashClipRate = 1.27f;   // horizontal cut (impact ~0.45 of 3.17s)
	JudgClipStart  = 0.12f; JudgClipRate  = 1.18f;   // overhead, windowed from a 4.37s routine
	LampClipStart  = 0.35f; LampClipRate  = 0.70f;   // the wide Lamp-Eater arc (sweep ~0.575)
	VoidClipStart  = 0.30f; VoidClipRate  = 1.00f;   // the cast climax aligns to the spill
}

float AHollowWarden::DarknessTellMult() const
{
	return 1.f - FMath::Min(DarkStacks, MaxDarkStacks) * DarkTellPerStack;
}

void AHollowWarden::EatNearbyLights()
{
	const FVector C = GetActorLocation();
	APawn* HeroPawn = UGameplayStatics::GetPlayerPawn(this, 0);
	int32 eaten = 0;
	for (TObjectIterator<UPointLightComponent> It; It; ++It)
	{
		if (eaten >= MaxLightsEaten) { break; }
		UPointLightComponent* L = *It;
		if (!L || L->GetWorld() != GetWorld() || L == TelegraphLight) { continue; }
		AActor* LightOwner = L->GetOwner();
		if (LightOwner == this || (HeroPawn && LightOwner == HeroPawn)) { continue; }   // never eat the hero's own glow
		const float Cur = L->Intensity;
		if (Cur <= 1.f) { continue; }   // already dark
		if (FVector::Dist(L->GetComponentLocation(), C) > LampSnuffRadius) { continue; }
		EatenLights.Add(L);
		EatenOrig.Add(Cur);
		L->SetIntensity(Cur * LampDimFactor);
		++eaten;
	}
	if (eaten > 0)
	{
		RestoreLightsTime = Now() + LampDarkSeconds;
		DarkStacks = FMath::Min(DarkStacks + 1, MaxDarkStacks);   // the dark feeds him
		DarkStackFadeTime = Now() + DarkStackSeconds;
	}
}

void AHollowWarden::RestoreEatenLights()
{
	for (int32 i = 0; i < EatenLights.Num(); ++i)
	{
		if (UPointLightComponent* L = EatenLights[i].Get())
		{
			if (i < EatenOrig.Num()) { L->SetIntensity(EatenOrig[i]); }
		}
	}
	EatenLights.Reset();
	EatenOrig.Reset();
	RestoreLightsTime = 0.f;
}

void AHollowWarden::ClearActiveMoveState()
{
	// Interrupted mid-arc: the dark he was holding releases, the lamps relight.
	RestoreEatenLights();
}

void AHollowWarden::NotifyRivalPhaseChanged(int32 NewPhase)
{
	if (NewPhase >= 3) { bVoidPending = true; }   // phase 3: the absence spills
	OnWardenPhaseChanged(NewPhase);
}

void AHollowWarden::NotifyRivalDefeated()
{
	RestoreEatenLights();   // the light returns when he falls
	OnWardenDefeated();
}

void AHollowWarden::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
	if (RestoreLightsTime > 0.f && Now() >= RestoreLightsTime) { RestoreEatenLights(); }
	if (DarkStacks > 0 && Now() >= DarkStackFadeTime) { DarkStacks = 0; }
}

void AHollowWarden::SelectMove(float DistToHero)
{
	if (bVoidPending)
	{
		bVoidPending = false;
		Move = EWardenMove::VoidSpill;
		return;
	}
	// Villains own their kit from the first bell: the Lamp-Eater arc debuts in P1.
	TArray<EWardenMove> Pool = { EWardenMove::Slash, EWardenMove::Judgment, EWardenMove::LampArc };
	if (Phase >= 3) { Pool.Add(EWardenMove::LampArc); }   // the dark grows late
	EWardenMove Picked = Pool[FMath::RandRange(0, Pool.Num() - 1)];
	if (Picked == Move && Pool.Num() > 1)
	{
		Picked = Pool[(Pool.Find(Picked) + 1) % Pool.Num()];
	}
	Move = Picked;
}

void AHollowWarden::StartTelegraph()
{
	bHitThisAttack = false;
	bVoidStruck = false;
	GetCharacterMovement()->StopMovementImmediately();

	float Tell = SlashTell;
	switch (Move)
	{
	case EWardenMove::Judgment:  Tell = JudgTell; break;
	case EWardenMove::LampArc:   Tell = LampTell; break;
	case EWardenMove::VoidSpill: Tell = VoidTell; break;
	default: break;
	}
	Tell *= TellScale() * DarknessTellMult();   // the darker it is, the faster he is

	if (TelegraphLight)
	{
		// Deeper violet the more light he has eaten.
		const float Deep = 1.f + 0.4f * FMath::Min(DarkStacks, MaxDarkStacks);
		TelegraphLight->SetLightColor(WardenVoid * Deep);
	}

	switch (Move)
	{
	case EWardenMove::Slash:
		PlayOneShot(SlashAnim, Tell + SlashActive + SlashRecover * 0.4f, SlashClipStart, SlashClipRate);
		break;
	case EWardenMove::Judgment:
		PlayOneShot(JudgmentAnim, Tell + JudgActive + JudgRecover * 0.4f, JudgClipStart, JudgClipRate);
		break;
	case EWardenMove::LampArc:
		PlayOneShot(ChargedAnim, Tell + LampActive + LampRecover * 0.4f, LampClipStart, LampClipRate);
		break;
	case EWardenMove::VoidSpill:
		PlayOneShot(VoidAnim, Tell + VoidActive + 0.3f, VoidClipStart, VoidClipRate);
		break;
	default: break;
	}
	EnterState(ERivalState::Telegraph, Tell);
}

void AHollowWarden::StartAttack()
{
	if (TelegraphLight) { TelegraphLight->SetIntensity(0.f); }
	const bool bDark = (Move == EWardenMove::LampArc || Move == EWardenMove::VoidSpill);
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 40.f),
		(bDark ? WardenVoid * 2.6f : WardenGold * 2.2f), 1.2f, 4400.f, 0.2f);

	switch (Move)
	{
	case EWardenMove::Slash:
		EnterState(ERivalState::Attack, SlashActive);
		break;
	case EWardenMove::Judgment:
		EnterState(ERivalState::Attack, JudgActive);
		break;
	case EWardenMove::LampArc:
		// THE LAMP-EATER: the wide arc swallows the light around him.
		EatNearbyLights();
		ASparkImpactBurst::Burst(this, GetActorLocation()
			+ GetActorForwardVector() * (LampArcReach * 0.5f) + FVector(0.f, 0.f, 45.f),
			WardenVoid * 3.f, LampArcReach / 130.f, 5200.f, 0.3f);
		EnterState(ERivalState::Attack, LampActive);
		break;
	case EWardenMove::VoidSpill:
		EnterState(ERivalState::Attack, VoidActive);
		break;
	default:
		FinishAttack(SlashRecover);
		break;
	}
}

void AHollowWarden::TickAttack(float DeltaTime, ASparkHeroCharacter* Hero)
{
	switch (Move)
	{
	case EWardenMove::Slash:
		if (Hero && !bHitThisAttack)
		{
			const FVector To = Hero->GetActorLocation() - GetActorLocation();
			if (FVector::DotProduct(To.GetSafeNormal2D(), GetActorForwardVector()) > 0.2f
				&& To.Size() <= SlashReach)
			{
				bHitThisAttack = true;
				LandDuelHit(Hero, DuelHitEmbers);
			}
		}
		break;

	case EWardenMove::Judgment:
		if (Hero && !bHitThisAttack)
		{
			const FVector To = Hero->GetActorLocation() - GetActorLocation();
			if (FVector::DotProduct(To.GetSafeNormal2D(), GetActorForwardVector()) > 0.25f
				&& To.Size() <= JudgReach)
			{
				bHitThisAttack = true;
				LandDuelHit(Hero, DuelHitEmbers * 1.3f);
			}
		}
		break;

	case EWardenMove::LampArc:
		// A WIDE arc — anything in the broad front cone is cut.
		if (Hero && !bHitThisAttack)
		{
			const FVector To = Hero->GetActorLocation() - GetActorLocation();
			const float Cos = FVector::DotProduct(To.GetSafeNormal2D(), GetActorForwardVector());
			if (Cos > FMath::Cos(FMath::DegreesToRadians(LampArcHalfAngleDeg))
				&& To.Size() <= LampArcReach)
			{
				bHitThisAttack = true;
				LandDuelHit(Hero, DuelHitEmbers);
			}
		}
		break;

	case EWardenMove::VoidSpill:
		// The absence floods the ground: a dark ring detonates around him.
		if (!bVoidStruck)
		{
			const float Elapsed = VoidActive - (StateUntil - Now());
			if (Elapsed >= VoidActive * 0.5f)
			{
				bVoidStruck = true;
				ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 30.f),
					WardenVoid * 2.8f, VoidRadius / 110.f, 6000.f, 0.32f);
				if (Hero && FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= VoidRadius)
				{
					LandDuelHit(Hero, DuelHitEmbers);
				}
			}
		}
		break;

	default: break;
	}
}

void AHollowWarden::HandleAttackExpired(ASparkHeroCharacter* Hero)
{
	float Recover = SlashRecover;
	switch (Move)
	{
	case EWardenMove::Judgment:  Recover = JudgRecover; break;
	case EWardenMove::LampArc:   Recover = LampRecover; break;
	case EWardenMove::VoidSpill: Recover = VoidRecover; break;
	default: break;
	}
	FinishAttack(Recover);
}

float AHollowWarden::GetTriggerRange() const
{
	switch (Move)
	{
	case EWardenMove::Judgment:  return JudgReach * 0.85f;
	case EWardenMove::LampArc:   return LampArcReach * 0.8f;
	case EWardenMove::VoidSpill: return 500.f;   // he casts the spill from range
	default:                     return SlashReach * 0.85f;
	}
}
