// The Unlight — the Dragonlord's shape, worn by the dark. It borrows his clips
// and his body; only the violet skin, the hostile soul, and the spreading void
// that eats the lanterns are its own.

#include "Unlight.h"

#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Lantern.h"
#include "Materials/MaterialInterface.h"
#include "SparkHeroCharacter.h"
#include "SparkImpactBurst.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	const FLinearColor UnlightViolet(0.9f, 0.2f, 1.6f);   // burning violet where a face should be
}

AUnlight::AUnlight()
{
	GetCapsuleComponent()->SetCapsuleSize(72.f, 118.f);   // the Dragon's frame, worn by the dark
	RivalDisplayName = TEXT("THE UNLIGHT");

	ApproachSpeed = 540.f;   // faster than the kind Dragon — it comes for you
	TurnRate = 5.f;
	IntroSeconds = 1.8f;
	ApproachAnimRate = 0.95f;
	TelegraphPulseHz = 16.f;
	TelegraphPulseIntensity = 7200.f;
	PhaseRoarSeconds = 1.3f;
	FlinchSeconds = 0.5f;
	StaggerSeconds = 2.4f;
	KnockbackForce = 1100.f;
	KnockbackLift = 440.f;
	GetCharacterMovement()->MaxWalkSpeed = ApproachSpeed;

	HitBurstColor = FLinearColor(2.6f, 0.7f, 3.4f);
	HitBurstScale = 1.4f;
	HitBurstLight = 5400.f;
	DefeatBurstColor = FLinearColor(3.4f, 1.0f, 4.2f);
	DefeatBurstScale = 2.6f;
	DefeatBurstLight = 8400.f;
	if (TelegraphLight) { TelegraphLight->SetLightColor(UnlightViolet); }

	ContactProfile.MassClass = EMassClass::Mythic;
	ContactProfile.bStompImmune = true;
	ContactProfile.bDashImmune = true;

	// BORROWED SHAPE: it wears the Dragonlord's mesh and clips entire.
	static ConstructorHelpers::FObjectFinder<USkeletalMesh> Model(TEXT("/Game/Art/DragonSkelV1/SCB2Dragon.SCB2Dragon"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FIdle(TEXT("/Game/Art/DragonSkelV1/A_Dragon_Idle_Anim.A_Dragon_Idle_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FWalk(TEXT("/Game/Art/DragonSkelV1/A_Dragon_Walk_Anim.A_Dragon_Walk_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FSweep(TEXT("/Game/Art/DragonSkelV1/A_Dragon_WingSweep_Anim.A_Dragon_WingSweep_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FCast(TEXT("/Game/Art/DragonSkelV1/A_Dragon_Sanctuary_Anim.A_Dragon_Sanctuary_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FShove(TEXT("/Game/Art/DragonSkelV1/A_Dragon_WingShove_Anim.A_Dragon_WingShove_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FHit(TEXT("/Game/Art/DragonSkelV1/A_Dragon_HitReact_Anim.A_Dragon_HitReact_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FStagger(TEXT("/Game/Art/DragonSkelV1/A_Dragon_Stagger_Anim.A_Dragon_Stagger_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FDefeat(TEXT("/Game/Art/DragonSkelV1/A_Dragon_Defeat_Anim.A_Dragon_Defeat_Anim"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> FUnlightMat(TEXT("/Game/Art/DragonSkelV1/M_UnlightPBR.M_UnlightPBR"));

	if (Model.Succeeded())
	{
		RivalBody->SetSkeletalMesh(Model.Object);
		if (FUnlightMat.Succeeded()) { RivalBody->SetMaterial(0, FUnlightMat.Object); }   // ink-black + violet
		bHasSkeletalModel = true;
		PlaceholderBody->SetVisibility(false);
	}
	else
	{
		static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
		if (Sphere.Succeeded())
		{
			PlaceholderBody->SetStaticMesh(Sphere.Object);
			PlaceholderBody->SetRelativeScale3D(FVector(1.7f, 1.7f, 3.4f));
		}
	}
	IdleAnim = LoadRivalClip(FIdle);
	MoveAnim = LoadRivalClip(FWalk);
	SweepAnim = LoadRivalClip(FSweep);
	ExtinguishAnim = LoadRivalClip(FCast);
	LungeAnim = LoadRivalClip(FShove);
	HitReactAnim = LoadRivalClip(FHit);
	StaggerAnim = LoadRivalClip(FStagger);
	DefeatAnim = LoadRivalClip(FDefeat);
}

void AUnlight::SelectMove(float DistToHero)
{
	// Extinguish is its signature — it reaches for the lanterns often.
	TArray<EUnlightMove> Pool = { EUnlightMove::VoidSweep, EUnlightMove::Extinguish,
	                              EUnlightMove::VoidLunge, EUnlightMove::Extinguish };
	EUnlightMove Picked = Pool[FMath::RandRange(0, Pool.Num() - 1)];
	if (Picked == Move)
	{
		Picked = Pool[(Pool.Find(Picked) + 1) % Pool.Num()];
	}
	Move = Picked;
}

void AUnlight::StartTelegraph()
{
	bHitThisAttack = false;
	bHitThisLunge = false;
	GetCharacterMovement()->StopMovementImmediately();

	float Tell = SweepTell;
	switch (Move)
	{
	case EUnlightMove::Extinguish: Tell = ExtinguishTell; break;
	case EUnlightMove::VoidLunge:  Tell = LungeTell; break;
	default: break;
	}
	Tell *= TellScale();

	if (TelegraphLight) { TelegraphLight->SetLightColor(UnlightViolet); }

	switch (Move)
	{
	case EUnlightMove::VoidSweep:
		PlayOneShot(SweepAnim, Tell + SweepActive + SweepRecover * 0.4f, SweepClipStart, SweepClipRate);
		break;
	case EUnlightMove::Extinguish:
		PlayOneShot(ExtinguishAnim, Tell + ExtinguishActive + 0.3f, ExtinguishClipStart, ExtinguishClipRate);
		break;
	case EUnlightMove::VoidLunge:
		PlayOneShot(LungeAnim, Tell + LungeActive + 0.3f, LungeClipStart, LungeClipRate);
		break;
	default: break;
	}
	EnterState(ERivalState::Telegraph, Tell);
}

void AUnlight::StartAttack()
{
	if (TelegraphLight) { TelegraphLight->SetIntensity(0.f); }
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 60.f),
		UnlightViolet * 2.6f, 1.5f, 5400.f, 0.24f);

	ASparkHeroCharacter* Hero = ResolveHero();
	switch (Move)
	{
	case EUnlightMove::VoidSweep:
		EnterState(ERivalState::Attack, SweepActive);
		break;
	case EUnlightMove::Extinguish:
		Extinguish();
		EnterState(ERivalState::Attack, ExtinguishActive);
		break;
	case EUnlightMove::VoidLunge:
		LungeDir = Hero ? (Hero->GetActorLocation() - GetActorLocation()).GetSafeNormal2D()
		                : GetActorForwardVector();
		EnterState(ERivalState::Attack, LungeActive);
		break;
	default:
		FinishAttack(SweepRecover);
		break;
	}
}

void AUnlight::Extinguish()
{
	// The lanterns die, and from each death the killing dark spreads.
	const FVector C = GetActorLocation();
	int32 added = 0;
	for (TActorIterator<ALantern> It(GetWorld()); It; ++It)
	{
		if (VoidSpots.Num() >= MaxVoidSpots) { break; }
		ALantern* Lan = *It;
		if (Lan && Lan->IsLit() && FVector::Dist(Lan->GetActorLocation(), C) <= SnuffRadius)
		{
			Lan->Snuff();
			VoidSpots.Add(Lan->GetActorLocation());
			VoidSpotUntil.Add(Now() + VoidSpotSeconds);
			++added;
		}
	}
	// If there were no lanterns to kill, the dark simply finds you where you stand.
	if (added == 0 && VoidSpots.Num() < MaxVoidSpots)
	{
		if (ASparkHeroCharacter* Hero = ResolveHero())
		{
			VoidSpots.Add(Hero->GetActorLocation());
			VoidSpotUntil.Add(Now() + VoidSpotSeconds);
		}
	}
	NextVoidChip = Now();
	NextVoidFx = Now();
}

void AUnlight::TickAttack(float DeltaTime, ASparkHeroCharacter* Hero)
{
	switch (Move)
	{
	case EUnlightMove::VoidSweep:
		if (Hero && !bHitThisAttack
			&& FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= SweepRadius)
		{
			bHitThisAttack = true;
			LandDuelHit(Hero, DuelHitEmbers);
		}
		break;

	case EUnlightMove::VoidLunge:
		GetCharacterMovement()->Velocity =
			FVector(LungeDir.X, LungeDir.Y, 0.f) * LungeSpeed
			+ FVector(0.f, 0.f, GetCharacterMovement()->Velocity.Z);
		if (Hero && !bHitThisLunge
			&& FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= LungeReach)
		{
			bHitThisLunge = true;
			LandDuelHit(Hero, DuelHitEmbers);
		}
		break;

	case EUnlightMove::Extinguish:
	default:
		break;   // the void floor does its work in the main Tick
	}
}

void AUnlight::HandleAttackExpired(ASparkHeroCharacter* Hero)
{
	float Recover = SweepRecover;
	switch (Move)
	{
	case EUnlightMove::Extinguish: Recover = ExtinguishRecover; break;
	case EUnlightMove::VoidLunge:  Recover = LungeRecover; break;
	default: break;
	}
	FinishAttack(Recover);
}

float AUnlight::GetTriggerRange() const
{
	switch (Move)
	{
	case EUnlightMove::Extinguish: return 820.f;   // it reaches for the lanterns from afar
	case EUnlightMove::VoidLunge:  return 640.f;
	default:                       return SweepRadius * 0.8f;
	}
}

void AUnlight::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	// Expire void spots that have run their course (the dark recedes... slowly).
	for (int32 i = VoidSpotUntil.Num() - 1; i >= 0; --i)
	{
		if (Now() >= VoidSpotUntil[i])
		{
			VoidSpots.RemoveAt(i);
			VoidSpotUntil.RemoveAt(i);
		}
	}
	if (VoidSpots.Num() == 0) { return; }

	// The void floor SHOWS: a dark violet pulse over each killed lantern.
	if (Now() >= NextVoidFx)
	{
		NextVoidFx = Now() + 0.45f;
		for (const FVector& S : VoidSpots)
		{
			ASparkImpactBurst::Burst(this, S + FVector(0.f, 0.f, 8.f),
			                         UnlightViolet * 1.9f, VoidSpotRadius / 130.f, 2600.f, 0.34f);
		}
	}
	// Standing in the void costs you light.
	if (Now() >= NextVoidChip)
	{
		NextVoidChip = Now() + VoidChipInterval;
		if (ASparkHeroCharacter* Hero = ResolveHero())
		{
			for (const FVector& S : VoidSpots)
			{
				if (FVector::Dist2D(Hero->GetActorLocation(), S) <= VoidSpotRadius)
				{
					Hero->TakeEmberHit(VoidChipEmbers);
					break;   // one chip per interval, however many spots overlap
				}
			}
		}
	}
}
