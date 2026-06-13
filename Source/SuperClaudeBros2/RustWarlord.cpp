// The Rust Warlord — proof that the duel framework now lives in ASparkRivalBase.
// Everything below is JUST his soul: four heavy moves and the furnace. The state
// machine, the meter, the walk-away, the solid-body push — all inherited.

#include "RustWarlord.h"

#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "SparkHeroCharacter.h"
#include "SparkImpactBurst.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	const FLinearColor WarlordRust(2.6f, 1.1f, 0.25f);    // molten industrial orange
	const FLinearColor WarlordVent(2.2f, 0.5f, 2.6f);     // the furnace's violet heat
}

ARustWarlord::ARustWarlord()
{
	// The foundry brute: the tallest rival (below the Bramblehulk colossus),
	// wide and slow. Capsule half-height ~ the 0.8-family mesh extent (~78).
	GetCapsuleComponent()->SetCapsuleSize(58.f, 80.f);
	RivalDisplayName = TEXT("THE RUST WARLORD");
	GetCharacterMovement()->MaxWalkSpeed = 0.f;   // set from ApproachSpeed below

	// --- pacing: heavy and deliberate ---
	ApproachSpeed = 520.f;
	TurnRate = 5.f;
	IntroSeconds = 1.6f;
	ApproachAnimRate = 0.95f;
	TelegraphPulseHz = 16.f;
	TelegraphPulseIntensity = 6800.f;
	PhaseRoarSeconds = 1.2f;
	FlinchSeconds = 0.5f;
	StaggerSeconds = 2.2f;
	KnockbackForce = 1000.f;
	KnockbackLift = 440.f;
	GetCharacterMovement()->MaxWalkSpeed = ApproachSpeed;

	// --- scanned attack windows (recipe 7.5; RightHand Z/reach peaks) ---
	// Rate = (impact - start) * clipLen / Tell, so each strike lands as Active opens.
	SwingClipStart = 0.45f; SwingClipRate = 0.85f;   // hammer down-strike (impact ~0.78 of 1.83s)
	ChopClipStart  = 0.42f; ChopClipRate  = 1.50f;   // overhead chop windowed out of a 7.67s routine
	SweepClipStart = 0.15f; SweepClipRate = 1.05f;   // the spin extension fills the active window
	VentClipStart  = 0.15f; VentClipRate  = 0.60f;   // lingers on the chest-forward furnace brace

	// --- his colors ---
	HitBurstColor = FLinearColor(3.4f, 1.4f, 0.35f);
	HitBurstScale = 1.3f;
	HitBurstLight = 5400.f;
	DefeatBurstColor = FLinearColor(5.f, 2.2f, 0.7f);   // the furnace overloads
	DefeatBurstScale = 2.2f;
	DefeatBurstLight = 8200.f;
	if (TelegraphLight) { TelegraphLight->SetLightColor(WarlordRust); }

	// --- assets (resolve once the stage-29 clips import; clipless until then) ---
	static ConstructorHelpers::FObjectFinder<USkeletalMesh> Model(TEXT("/Game/Art/WarlordSkelV1/SCB2Warlord.SCB2Warlord"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FIdle(TEXT("/Game/Art/WarlordSkelV1/A_Warlord_Idle_Anim.A_Warlord_Idle_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FWalk(TEXT("/Game/Art/WarlordSkelV1/A_Warlord_Walk_Anim.A_Warlord_Walk_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FSwing(TEXT("/Game/Art/WarlordSkelV1/A_Warlord_Swing_Anim.A_Warlord_Swing_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FChop(TEXT("/Game/Art/WarlordSkelV1/A_Warlord_Chop_Anim.A_Warlord_Chop_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FSweep(TEXT("/Game/Art/WarlordSkelV1/A_Warlord_Sweep_Anim.A_Warlord_Sweep_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FVent(TEXT("/Game/Art/WarlordSkelV1/A_Warlord_Vent_Anim.A_Warlord_Vent_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FHit(TEXT("/Game/Art/WarlordSkelV1/A_Warlord_HitReact_Anim.A_Warlord_HitReact_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FStagger(TEXT("/Game/Art/WarlordSkelV1/A_Warlord_Stagger_Anim.A_Warlord_Stagger_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FDefeat(TEXT("/Game/Art/WarlordSkelV1/A_Warlord_Defeat_Anim.A_Warlord_Defeat_Anim"));

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
			PlaceholderBody->SetRelativeScale3D(FVector(1.5f, 1.5f, 2.9f));
		}
	}
	IdleAnim = LoadRivalClip(FIdle);
	MoveAnim = LoadRivalClip(FWalk);
	SwingAnim = LoadRivalClip(FSwing);
	ChopAnim = LoadRivalClip(FChop);
	SweepAnim = LoadRivalClip(FSweep);
	VentAnim = LoadRivalClip(FVent);
	HitReactAnim = LoadRivalClip(FHit);
	StaggerAnim = LoadRivalClip(FStagger);
	DefeatAnim = LoadRivalClip(FDefeat);
}

void ARustWarlord::NotifyRivalPhaseChanged(int32 NewPhase)
{
	// Armor break: the next move he makes is the furnace vent (the wound bites back).
	bVentPending = true;
	OnWarlordPhaseChanged(NewPhase);
}

void ARustWarlord::SelectMove(float DistToHero)
{
	if (bVentPending)
	{
		bVentPending = false;
		Move = EWarlordMove::FurnaceVent;
		return;
	}
	TArray<EWarlordMove> Pool = { EWarlordMove::HeavySwing, EWarlordMove::AxeChop };
	if (Phase >= 2) { Pool.Add(EWarlordMove::SpinSweep); }
	if (Phase >= 3) { Pool.Add(EWarlordMove::AxeChop); }   // heavier pressure late
	EWarlordMove Picked = Pool[FMath::RandRange(0, Pool.Num() - 1)];
	if (Picked == Move && Pool.Num() > 1)
	{
		Picked = Pool[(Pool.Find(Picked) + 1) % Pool.Num()];   // never the same twice
	}
	Move = Picked;
}

void ARustWarlord::StartTelegraph()
{
	bHitThisAttack = false;
	NextVentTick = 0.f;
	GetCharacterMovement()->StopMovementImmediately();

	float Tell = SwingTell;
	switch (Move)
	{
	case EWarlordMove::AxeChop:     Tell = ChopTell; break;
	case EWarlordMove::SpinSweep:   Tell = SweepTell; break;
	case EWarlordMove::FurnaceVent: Tell = VentTell; break;
	default: break;
	}
	Tell *= TellScale();

	// The furnace tell glows violet; honest steel glows molten orange.
	if (TelegraphLight)
	{
		TelegraphLight->SetLightColor(Move == EWarlordMove::FurnaceVent ? WarlordVent : WarlordRust);
	}

	switch (Move)
	{
	case EWarlordMove::HeavySwing:
		PlayOneShot(SwingAnim, Tell + SwingActive + SwingRecover * 0.4f, SwingClipStart, SwingClipRate);
		break;
	case EWarlordMove::AxeChop:
		PlayOneShot(ChopAnim, Tell + ChopActive + ChopRecover * 0.4f, ChopClipStart, ChopClipRate);
		break;
	case EWarlordMove::SpinSweep:
		PlayOneShot(SweepAnim, Tell + SweepActive + SweepRecover * 0.4f, SweepClipStart, SweepClipRate);
		break;
	case EWarlordMove::FurnaceVent:
		PlayOneShot(VentAnim, Tell + VentActive * 0.5f, VentClipStart, VentClipRate);
		break;
	default: break;
	}
	EnterState(ERivalState::Telegraph, Tell);
}

void ARustWarlord::StartAttack()
{
	if (TelegraphLight) { TelegraphLight->SetIntensity(0.f); }
	const bool bVent = (Move == EWarlordMove::FurnaceVent);
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 40.f),
		(bVent ? WarlordVent : WarlordRust) * 2.4f, 1.3f, 4600.f, 0.22f);

	switch (Move)
	{
	case EWarlordMove::HeavySwing:
		EnterState(ERivalState::Attack, SwingActive);
		break;
	case EWarlordMove::AxeChop:
		EnterState(ERivalState::Attack, ChopActive);
		break;
	case EWarlordMove::SpinSweep:
		EnterState(ERivalState::Attack, SweepActive);
		break;
	case EWarlordMove::FurnaceVent:
		NextVentTick = Now();   // the cone starts roaring this frame
		EnterState(ERivalState::Attack, VentActive);
		break;
	default:
		FinishAttack(SwingRecover);
		break;
	}
}

void ARustWarlord::TickAttack(float DeltaTime, ASparkHeroCharacter* Hero)
{
	switch (Move)
	{
	case EWarlordMove::HeavySwing:
		if (Hero && !bHitThisAttack)
		{
			const FVector To = Hero->GetActorLocation() - GetActorLocation();
			if (FVector::DotProduct(To.GetSafeNormal2D(), GetActorForwardVector()) > 0.2f
				&& To.Size() <= SwingReach)
			{
				bHitThisAttack = true;
				LandDuelHit(Hero, DuelHitEmbers);
			}
		}
		break;

	case EWarlordMove::AxeChop:
		if (Hero && !bHitThisAttack)
		{
			const FVector To = Hero->GetActorLocation() - GetActorLocation();
			if (FVector::DotProduct(To.GetSafeNormal2D(), GetActorForwardVector()) > 0.25f
				&& To.Size() <= ChopReach)
			{
				bHitThisAttack = true;
				LandDuelHit(Hero, DuelHitEmbers * 1.3f);   // the overhead bites deepest
			}
		}
		break;

	case EWarlordMove::SpinSweep:
		// A wide low ring — grounded heroes are swept; back off or JUMP it.
		if (Hero && !bHitThisAttack
			&& Hero->GetCharacterMovement()->IsMovingOnGround()
			&& FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= SweepRadius)
		{
			bHitThisAttack = true;
			LandDuelHit(Hero, DuelHitEmbers);
		}
		break;

	case EWarlordMove::FurnaceVent:
		// FURNACE VENT: rooted, the chest roars a violet heat-cone. Standing in it
		// chips embers on a cadence; DASH THROUGH to pass (the codex's escape).
		if (Now() >= NextVentTick)
		{
			NextVentTick = Now() + VentTickInterval;
			const FVector Mouth = GetActorLocation()
				+ GetActorForwardVector() * (VentConeReach * 0.45f) + FVector(0.f, 0.f, 35.f);
			ASparkImpactBurst::Burst(this, Mouth, WarlordVent * 2.2f, VentConeReach / 150.f, 4200.f, 0.3f);
			if (Hero && !Hero->IsDashing())
			{
				const FVector To = Hero->GetActorLocation() - GetActorLocation();
				const float Cos = FVector::DotProduct(To.GetSafeNormal2D(), GetActorForwardVector());
				if (Cos > FMath::Cos(FMath::DegreesToRadians(VentConeHalfAngleDeg))
					&& To.Size() <= VentConeReach)
				{
					Hero->TakeEmberHit(VentTickEmbers);   // chip; area denial, not a slam
				}
			}
		}
		break;

	default: break;
	}
}

void ARustWarlord::HandleAttackExpired(ASparkHeroCharacter* Hero)
{
	float Recover = SwingRecover;
	switch (Move)
	{
	case EWarlordMove::AxeChop:     Recover = ChopRecover; break;
	case EWarlordMove::SpinSweep:   Recover = SweepRecover; break;
	case EWarlordMove::FurnaceVent: Recover = VentRecover; break;
	default: break;
	}
	FinishAttack(Recover);
}

float ARustWarlord::GetTriggerRange() const
{
	switch (Move)
	{
	case EWarlordMove::AxeChop:     return ChopReach * 0.85f;
	case EWarlordMove::SpinSweep:   return SweepRadius * 0.8f;
	case EWarlordMove::FurnaceVent: return 600.f;   // he plants and vents from range
	default:                        return SwingReach * 0.85f;
	}
}
