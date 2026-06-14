// ASparkRivalBase — the duel framework, factored out of the three proven voices.
// Every line here was identical (or trivially reconciled) across the Iron Kraken,
// the Ember Reaver, and the Void Stalker. The per-rival soul lives in the seams.

#include "SparkRivalBase.h"

#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "EmberMeterComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "SparkAnimPerf.h"
#include "SparkHeroCharacter.h"
#include "SparkImpactBurst.h"

ASparkRivalBase::ASparkRivalBase()
{
	PrimaryActorTick.bCanEverTick = true;

	// A neutral default; each rival sizes its own capsule to its visual bulk
	// (solid-body law) after Super() runs.
	GetCapsuleComponent()->SetCapsuleSize(40.f, 72.f);
	// The hero must never wall-climb a rival; Glimmer sense traces pass through.
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);

	GetCharacterMovement()->bOrientRotationToMovement = false;   // FaceHero owns the yaw
	GetCharacterMovement()->MaxWalkSpeed = ApproachSpeed;
	GetCharacterMovement()->GravityScale = 1.9f;                 // the world's feel
	AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;

	VisualRoot = CreateDefaultSubobject<USceneComponent>(TEXT("VisualRoot"));
	VisualRoot->SetupAttachment(RootComponent);

	RivalBody = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("RivalBody"));
	RivalBody->SetupAttachment(VisualRoot);
	RivalBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	RivalBody->SetAnimationMode(EAnimationMode::AnimationSingleNode);
	RivalBody->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;   // LOAD LAW (distance pose-LOD throttles this for FAR rivals at runtime)
	RivalBody->bEnableUpdateRateOptimizations = true;   // PERF: distant/off-centre rivals evaluate their pose less often (interpolated — never freezes)
	RivalBody->SetBoundsScale(1.8f);   // the cull-freeze insurance: the widest animated pose can never leave its bounds (1.8 covers the big-capsule + 1.4x-scaled giants: Dragonlord/Unlight/FoundryKing)

	PlaceholderBody = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PlaceholderBody"));
	PlaceholderBody->SetupAttachment(VisualRoot);
	PlaceholderBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	DuelMeter = CreateDefaultSubobject<UEmberMeterComponent>(TEXT("DuelMeter"));
	// Every combo beat must count: the hero's hits land ~0.3s apart, so the
	// meter's anti-double-dip grace shrinks to a heartbeat for the duel role.
	DuelMeter->GraceDuration = 0.05f;

	TelegraphLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("TelegraphLight"));
	TelegraphLight->SetupAttachment(VisualRoot);
	TelegraphLight->SetRelativeLocation(FVector(0.f, 0.f, 48.f));
	TelegraphLight->SetAttenuationRadius(640.f);
	TelegraphLight->SetCastShadows(false);
	TelegraphLight->SetIntensity(0.f);

	ContactProfile.MassClass = EMassClass::Champion;
	ContactProfile.bStompImmune = true;
	ContactProfile.bDashImmune = true;
	ContactProfile.ContactDamageEmbers = 20.f;
}

void ASparkRivalBase::BeginPlay()
{
	Super::BeginPlay();
	if (bHasSkeletalModel)
	{
		RivalBody->SetRelativeLocation(FVector(0.f, 0.f, -GetCapsuleComponent()->GetScaledCapsuleHalfHeight()));
		RivalBody->SetRelativeRotation(FRotator(0.f, SkelMeshYaw, 0.f));
		RivalBody->SetRelativeScale3D(FVector(SkelMeshScale));
	}
	if (DuelMeter)
	{
		DuelMeter->OnFlameOut.AddDynamic(this, &ASparkRivalBase::HandleDuelMeterEmpty);
	}
	PostRivalBeginPlay();   // per-rival tail (Kraken tether MID, etc.)
	PlayLoop(IdleAnim);
}

UAnimSequence* ASparkRivalBase::LoadRivalClip(const ConstructorHelpers::FObjectFinder<UAnimSequence>& Finder)
{
	return Finder.Succeeded() ? Finder.Object.Get() : nullptr;
}

ASparkHeroCharacter* ASparkRivalBase::ResolveHero() const
{
	// NEVER cache: P swaps hero pawns mid-level (the stale-pointer lesson).
	return Cast<ASparkHeroCharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
}

float ASparkRivalBase::Now() const
{
	return GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
}

void ASparkRivalBase::PlayLoop(UAnimSequence* Clip, float Rate)
{
	if (!bHasSkeletalModel || !Clip || !RivalBody) { return; }
	if (CurrentLoop == Clip) { RivalBody->SetPlayRate(Rate); return; }
	CurrentLoop = Clip;
	RivalBody->PlayAnimation(Clip, true);
	RivalBody->SetPlayRate(Rate);
}

void ASparkRivalBase::PlayOneShot(UAnimSequence* Clip, float FitSeconds, float StartFraction, float OverrideRate)
{
	if (!bHasSkeletalModel || !Clip || !RivalBody) { return; }
	CurrentLoop = nullptr;
	RivalBody->PlayAnimation(Clip, false);
	const float Rate = (OverrideRate > 0.f)
		? OverrideRate
		: Clip->GetPlayLength() * (1.f - StartFraction) / FMath::Max(FitSeconds, 0.05f);
	RivalBody->SetPlayRate(FMath::Clamp(Rate, 0.3f, 5.f));   // original known-good (the 0.25-6 widen caused slow/blur regressions)
	if (StartFraction > 0.f)
	{
		RivalBody->SetPosition(Clip->GetPlayLength() * StartFraction, false);
	}
}

void ASparkRivalBase::EnterState(ERivalState NewState, float Duration)
{
	State = NewState;
	StateUntil = Now() + Duration;
}

void ASparkRivalBase::FaceHero(const ASparkHeroCharacter* Hero, float DeltaTime)
{
	if (!Hero) { return; }
	const FVector To = Hero->GetActorLocation() - GetActorLocation();
	const FRotator Want(0.f, To.Rotation().Yaw, 0.f);
	SetActorRotation(FMath::RInterpTo(GetActorRotation(), Want, DeltaTime, TurnRate));
}

void ASparkRivalBase::FinishAttack(float RecoverSeconds)
{
	GetCharacterMovement()->StopMovementImmediately();
	SetActorHiddenInGame(false);   // never recover invisible (the Stalker's rule, harmless for the rest)
	if (TelegraphLight) { TelegraphLight->SetIntensity(0.f); }
	ClearActiveMoveState();        // purge any per-move physics (Kraken grip/tether)
	EnterState(ERivalState::Recover, RecoverSeconds);
}

void ASparkRivalBase::LandDuelHit(ASparkHeroCharacter* Hero, float Embers)
{
	if (!Hero) { return; }
	// The knockback law: shove first (always), fire second (grace may eat it).
	// NOTE: callers own bHitThisAttack — moves that hit twice (flurry/cut) rely on it.
	FVector Away = Hero->GetActorLocation() - GetActorLocation();
	Away.Z = 0.f;
	Away = Away.IsNearlyZero() ? GetActorForwardVector() : Away.GetSafeNormal();
	Hero->LaunchCharacter(Away * KnockbackForce + FVector(0.f, 0.f, KnockbackLift), true, true);
	Hero->TakeEmberHit(Embers);
	ASparkImpactBurst::Burst(this,
		(Hero->GetActorLocation() + GetActorLocation()) * 0.5f + FVector(0.f, 0.f, 40.f),
		HitBurstColor, HitBurstScale, HitBurstLight);
}

void ASparkRivalBase::TakeStrike(int32 InComboBeat, bool bCharged)
{
	if (State == ERivalState::Defeated || !DuelMeter) { return; }
	float Embers = (bCharged || InComboBeat >= 2) ? HeavyStrikeEmbers : LightStrikeEmbers;
	Embers = ModifyIncomingEmbers(Embers, InComboBeat, bCharged);   // Reaver blind-cone, etc.
	DuelMeter->ApplyEmberDamage(Embers);

	// Post-damage short-circuit: the Stalker's blink-feint break handles & returns.
	if (OnStruck(InComboBeat, bCharged)) { return; }

	// Phase check (spec: bosses teach a phase before they test it).
	const float Frac = DuelMeter->GetFraction();
	const int32 NewPhase = Frac <= Phase3Fraction ? 3 : (Frac <= Phase2Fraction ? 2 : 1);
	if (NewPhase > Phase)
	{
		Phase = NewPhase;
		NotifyRivalPhaseChanged(Phase);
		if (State != ERivalState::Staggered)
		{
			// The phase roar mid-attack must CLEAN UP the move it interrupts.
			ClearActiveMoveState();
			GetCharacterMovement()->StopMovementImmediately();
			PlayOneShot(TauntAnim ? TauntAnim : HitReactAnim, PhaseRoarSeconds);
			EnterState(ERivalState::Recover, PhaseRoarSeconds);   // the roar IS an opening
		}
	}
	else if (bCharged)
	{
		TakeStagger(StaggerSeconds);
	}
	else if (State == ERivalState::Waiting || State == ERivalState::Recover
	         || State == ERivalState::Approach)
	{
		PlayOneShot(HitReactAnim, FlinchSeconds);   // light hits flinch only off-attack
		if (State != ERivalState::Recover) { EnterState(ERivalState::Recover, FlinchSeconds); }
	}
}

void ASparkRivalBase::TakeStagger(float Seconds)
{
	if (State == ERivalState::Defeated) { return; }
	ClearActiveMoveState();
	SetActorHiddenInGame(false);
	if (TelegraphLight) { TelegraphLight->SetIntensity(0.f); }
	GetCharacterMovement()->StopMovementImmediately();
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 58.f),
	                         StaggerBurstColor, StaggerBurstScale, StaggerBurstLight);
	PlayOneShot(StaggerAnim ? StaggerAnim : HitReactAnim, Seconds);
	EnterState(ERivalState::Staggered, Seconds);
}

void ASparkRivalBase::HandleDuelMeterEmpty()
{
	if (State == ERivalState::Defeated) { return; }
	ClearActiveMoveState();
	SetActorHiddenInGame(false);
	if (TelegraphLight) { TelegraphLight->SetIntensity(0.f); }
	GetCharacterMovement()->StopMovementImmediately();
	GetCharacterMovement()->DisableMovement();
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
	if (DefeatAnim) { PlayOneShot(DefeatAnim, DefeatAnim->GetPlayLength()); }
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 50.f),
	                         DefeatBurstColor, DefeatBurstScale, DefeatBurstLight, 0.6f);
	EnterState(ERivalState::Defeated, 0.f);
	NotifyRivalDefeated();
}

float ASparkRivalBase::GetDuelFraction() const
{
	return DuelMeter ? DuelMeter->GetFraction() : 1.f;
}

void ASparkRivalBase::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
	if (State == ERivalState::Defeated) { return; }

	ASparkHeroCharacter* Hero = ResolveHero();
	const float Dist = Hero ? FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) : 1e9f;

	// PERF: full always-tick pose only when the hero is near; far rivals cull off-screen.
	SCB2_TickPoseLOD(RivalBody, Dist, PoseLODRadius);

	// SOLID-BODY LAW: bodies never share the same ground tile — a hero inside the
	// rival's personal space is shouldered out, except where a power legally owns
	// him (Kraken grip) or he is mid-blink (Stalker Vanished).
	if (Hero && State != ERivalState::Vanished && AllowSeparationPush())
	{
		const float PersonalSpace = GetCapsuleComponent()->GetScaledCapsuleRadius()
			+ Hero->GetCapsuleComponent()->GetScaledCapsuleRadius() + 8.f;
		FVector Out = Hero->GetActorLocation() - GetActorLocation();
		Out.Z = 0.f;
		const float Dist2D = Out.Size();
		if (Dist2D < PersonalSpace)
		{
			Out = Dist2D > 1.f ? Out / Dist2D : -GetActorForwardVector();
			Hero->GetCharacterMovement()->Velocity +=
				Out * SeparationPush * DeltaTime * (1.f - Dist2D / PersonalSpace + 0.35f);
		}
	}

	// Walk-away law: past the disengage ring he stands down; the meter refills for
	// the rematch — the duelist never executes, never sulks.
	if (State != ERivalState::Waiting && Dist > DisengageRadius)
	{
		DuelMeter->RefillFull();
		Phase = 1;
		SetActorHiddenInGame(false);
		GetCharacterMovement()->StopMovementImmediately();
		// Walk-away is the FIFTH exit path — it must purge per-move state like the
		// other four (FinishAttack/phase-roar/stagger/flame-out), or a move
		// interrupted mid-flight leaks its latches into the next engagement (the
		// Guardian's bGuarding 0.4x soak; the Kraken's grip/tether).
		ClearActiveMoveState();
		ClearMove();
		PlayLoop(IdleAnim);
		State = ERivalState::Waiting;
		return;
	}

	switch (State)
	{
	case ERivalState::Waiting:
		PlayLoop(IdleAnim);
		if (Hero) { FaceHero(Hero, DeltaTime * 0.5f); }
		if (Dist <= DuelStartRadius)
		{
			PlayOneShot(TauntAnim ? TauntAnim : IdleAnim, IntroSeconds);
			EnterState(ERivalState::Intro, IntroSeconds);
		}
		break;

	case ERivalState::Intro:
		if (Hero) { FaceHero(Hero, DeltaTime); }
		if (Now() >= StateUntil) { EnterState(ERivalState::Approach, 0.f); }
		break;

	case ERivalState::Approach:
	{
		if (!Hero) { break; }
		FaceHero(Hero, DeltaTime);
		PlayLoop(MoveAnim ? MoveAnim : IdleAnim, ApproachAnimRate);
		GetCharacterMovement()->MaxWalkSpeed = ApproachSpeed;
		AddMovementInput((Hero->GetActorLocation() - GetActorLocation()).GetSafeNormal2D());

		if (!HasMoveSelected()) { SelectMove(Dist); }
		if (Dist <= GetTriggerRange()) { StartTelegraph(); }
		break;
	}

	case ERivalState::Telegraph:
		if (Hero) { FaceHero(Hero, DeltaTime); }   // tells track — dodging is timing, not strafing
		if (TelegraphLight)
		{
			const float Pulse = 0.55f + 0.45f * FMath::Sin(Now() * TelegraphPulseHz);
			TelegraphLight->SetIntensity(TelegraphPulseIntensity * Pulse);
		}
		if (Now() >= StateUntil) { StartAttack(); }
		break;

	case ERivalState::Attack:
		TickAttack(DeltaTime, Hero);
		// The subclass owns the expiry (chaining, side-effects, recover pick).
		if (State == ERivalState::Attack && Now() >= StateUntil)
		{
			HandleAttackExpired(Hero);
		}
		break;

	case ERivalState::Vanished:
		if (Now() >= StateUntil) { OnVanishedExpired(); }
		break;

	case ERivalState::Recover:
		if (Now() >= StateUntil)
		{
			ClearMove();
			EnterState(ERivalState::Approach, 0.f);
		}
		break;

	case ERivalState::Staggered:
		if (Now() >= StateUntil)
		{
			ClearMove();
			EnterState(ERivalState::Approach, 0.f);
		}
		break;

	default:
		break;
	}
}
