// The Iron Kraken — duel framework v1. Patterns proven elsewhere in the project:
// single-node clip state machine (hero), VisualRoot never touches the capsule
// (house law), FObjectFinder fallbacks (everywhere), EmberMeter reuse (its own
// header called this), knockback = LaunchCharacter (and a pull is a launch
// TOWARD). Extraction into ASparkRivalBase happens when the Reaver lands.

#include "KrakenBoss.h"

#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "EmberMeterComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "SparkHeroCharacter.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	UAnimSequence* PickClip(const ConstructorHelpers::FObjectFinder<UAnimSequence>& Finder)
	{
		return Finder.Succeeded() ? Finder.Object.Get() : nullptr;
	}

	// Approach classification for the pattern-punish buffer.
	enum : uint8 { AP_None = 0, AP_Ground, AP_Dash, AP_Air, AP_Strike };
}

AKrakenBoss::AKrakenBoss()
{
	PrimaryActorTick.bCanEverTick = true;

	GetCapsuleComponent()->SetCapsuleSize(38.f, 76.f);   // Champion ≈ 36x76 (spec §9)
	GetCapsuleComponent()->OnComponentHit.AddDynamic(this, &AKrakenBoss::HandleCapsuleHit);
	// The hero must never wall-climb the boss; Glimmer sense traces pass through too.
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);

	GetCharacterMovement()->bOrientRotationToMovement = false;  // FaceHero owns the yaw
	GetCharacterMovement()->MaxWalkSpeed = ApproachSpeed;
	GetCharacterMovement()->GravityScale = 1.9f;                // the world's feel
	AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;

	VisualRoot = CreateDefaultSubobject<USceneComponent>(TEXT("VisualRoot"));
	VisualRoot->SetupAttachment(RootComponent);

	KrakenBody = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("KrakenBody"));
	KrakenBody->SetupAttachment(VisualRoot);
	KrakenBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	KrakenBody->SetAnimationMode(EAnimationMode::AnimationSingleNode);

	PlaceholderBody = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PlaceholderBody"));
	PlaceholderBody->SetupAttachment(VisualRoot);
	PlaceholderBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	DuelMeter = CreateDefaultSubobject<UEmberMeterComponent>(TEXT("DuelMeter"));
	// Every combo beat must count: the hero's 3 hits land ~0.3s apart, so the
	// meter's anti-double-dip grace shrinks to a heartbeat for the duel role.
	DuelMeter->GraceDuration = 0.05f;

	ContactProfile.MassClass = EMassClass::Champion;
	ContactProfile.bStompImmune = true;
	ContactProfile.bDashImmune = true;
	ContactProfile.ContactDamageEmbers = 20.f;

	static ConstructorHelpers::FObjectFinder<USkeletalMesh> Model(TEXT("/Game/Art/KrakenSkelV1/SCB2Kraken.SCB2Kraken"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FIdle(TEXT("/Game/Art/KrakenSkelV1/A_Kraken_Idle_Anim.A_Kraken_Idle_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FWalk(TEXT("/Game/Art/KrakenSkelV1/A_Kraken_Walk_Anim.A_Kraken_Walk_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FCharge(TEXT("/Game/Art/KrakenSkelV1/A_Kraken_Charge_Anim.A_Kraken_Charge_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FSwing(TEXT("/Game/Art/KrakenSkelV1/A_Kraken_Swing_Anim.A_Kraken_Swing_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FSlam(TEXT("/Game/Art/KrakenSkelV1/A_Kraken_Slam_Anim.A_Kraken_Slam_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FGrip(TEXT("/Game/Art/KrakenSkelV1/A_Kraken_Grip_Anim.A_Kraken_Grip_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FStagger(TEXT("/Game/Art/KrakenSkelV1/A_Kraken_Stagger_Anim.A_Kraken_Stagger_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FHit(TEXT("/Game/Art/KrakenSkelV1/A_Kraken_HitReact_Anim.A_Kraken_HitReact_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FDefeat(TEXT("/Game/Art/KrakenSkelV1/A_Kraken_Defeat_Anim.A_Kraken_Defeat_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FTaunt(TEXT("/Game/Art/KrakenSkelV1/A_Kraken_Taunt_Anim.A_Kraken_Taunt_Anim"));

	if (Model.Succeeded())
	{
		KrakenBody->SetSkeletalMesh(Model.Object);
		bHasSkeletalModel = true;
		PlaceholderBody->SetVisibility(false);
	}
	else
	{
		// Clipless placeholder: a looming violet-less mass so duels test today.
		static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
		if (Sphere.Succeeded())
		{
			PlaceholderBody->SetStaticMesh(Sphere.Object);
			PlaceholderBody->SetRelativeScale3D(FVector(1.4f, 1.4f, 2.8f));
		}
	}
	IdleAnim = PickClip(FIdle);
	WalkAnim = PickClip(FWalk);
	ChargeAnim = PickClip(FCharge);
	SwingAnim = PickClip(FSwing);
	SlamAnim = PickClip(FSlam);
	GripAnim = PickClip(FGrip);
	StaggerAnim = PickClip(FStagger);
	HitReactAnim = PickClip(FHit);
	DefeatAnim = PickClip(FDefeat);
	TauntAnim = PickClip(FTaunt);
}

void AKrakenBoss::BeginPlay()
{
	Super::BeginPlay();
	if (bHasSkeletalModel)
	{
		KrakenBody->SetRelativeLocation(FVector(0.f, 0.f, -GetCapsuleComponent()->GetScaledCapsuleHalfHeight()));
		KrakenBody->SetRelativeRotation(FRotator(0.f, SkelMeshYaw, 0.f));
		KrakenBody->SetRelativeScale3D(FVector(SkelMeshScale));
	}
	if (DuelMeter)
	{
		DuelMeter->OnFlameOut.AddDynamic(this, &AKrakenBoss::HandleDuelMeterEmpty);
	}
	PlayLoop(IdleAnim);
}

ASparkHeroCharacter* AKrakenBoss::ResolveHero() const
{
	// NEVER cache: P swaps hero pawns mid-level (the stale-pointer lesson).
	return Cast<ASparkHeroCharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
}

float AKrakenBoss::Now() const
{
	return GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
}

void AKrakenBoss::PlayLoop(UAnimSequence* Clip, float Rate)
{
	if (!bHasSkeletalModel || !Clip || !KrakenBody) { return; }
	if (CurrentLoop == Clip) { KrakenBody->SetPlayRate(Rate); return; }
	CurrentLoop = Clip;
	KrakenBody->PlayAnimation(Clip, true);
	KrakenBody->SetPlayRate(Rate);
}

void AKrakenBoss::PlayOneShot(UAnimSequence* Clip, float FitSeconds, float StartFraction, float OverrideRate)
{
	if (!bHasSkeletalModel || !Clip || !KrakenBody) { return; }
	CurrentLoop = nullptr;
	KrakenBody->PlayAnimation(Clip, false);
	const float Rate = (OverrideRate > 0.f)
		? OverrideRate
		: Clip->GetPlayLength() * (1.f - StartFraction) / FMath::Max(FitSeconds, 0.05f);
	KrakenBody->SetPlayRate(FMath::Clamp(Rate, 0.3f, 5.f));
	if (StartFraction > 0.f)
	{
		KrakenBody->SetPosition(Clip->GetPlayLength() * StartFraction, false);
	}
}

void AKrakenBoss::EnterState(EKrakenState NewState, float Duration)
{
	State = NewState;
	StateUntil = Now() + Duration;
}

void AKrakenBoss::FaceHero(const ASparkHeroCharacter* Hero, float DeltaTime)
{
	if (!Hero) { return; }
	const FVector To = Hero->GetActorLocation() - GetActorLocation();
	const FRotator Want(0.f, To.Rotation().Yaw, 0.f);
	SetActorRotation(FMath::RInterpTo(GetActorRotation(), Want, DeltaTime, TurnRate));
}

void AKrakenBoss::RecordApproach(const ASparkHeroCharacter* Hero)
{
	uint8 Kind = AP_Ground;
	if (Hero->IsDashing()) { Kind = AP_Dash; }
	else if (!Hero->GetCharacterMovement()->IsMovingOnGround()) { Kind = AP_Air; }
	else if (Hero->IsStriking()) { Kind = AP_Strike; }
	ApproachHistory[ApproachWrites % 3] = Kind;
	++ApproachWrites;
}

bool AKrakenBoss::PatternDemandsGrip() const
{
	// The codex: he grabs the THIRD identical approach. Pride remembers.
	return ApproachWrites >= 3
		&& ApproachHistory[0] == ApproachHistory[1]
		&& ApproachHistory[1] == ApproachHistory[2]
		&& ApproachHistory[0] != AP_None;
}

void AKrakenBoss::SelectMove(float DistToHero)
{
	if (PatternDemandsGrip())
	{
		Move = EKrakenMove::IronGrip;
		return;
	}
	// Phase rotation (spec §6.3: new move per threshold; tells stay honest).
	TArray<EKrakenMove> Pool = { EKrakenMove::ShowSwing };
	if (DistToHero > 450.f || Phase >= 2) { Pool.Add(EKrakenMove::PauldronRush); }
	if (Phase >= 2) { Pool.Add(EKrakenMove::ChampionsSlam); }
	if (Phase >= 3) { Pool.Add(EKrakenMove::IronGrip); }
	EKrakenMove Picked = Pool[FMath::RandRange(0, Pool.Num() - 1)];
	if (Picked == Move && Pool.Num() > 1)
	{
		Picked = Pool[(Pool.Find(Picked) + 1) % Pool.Num()];   // never the same twice
	}
	Move = Picked;
}

void AKrakenBoss::StartTelegraph()
{
	ASparkHeroCharacter* Hero = ResolveHero();
	if (Hero) { RecordApproach(Hero); }
	bHitThisAttack = false;
	GetCharacterMovement()->StopMovementImmediately();

	float Tell = SwingTell;
	switch (Move)
	{
	case EKrakenMove::PauldronRush:  Tell = RushTell; break;
	case EKrakenMove::ChampionsSlam: Tell = SlamTell; break;
	case EKrakenMove::IronGrip:      Tell = GripTell; break;
	default: break;
	}
	Tell *= TellScale();

	// One clip carries tell + active: fit it across both, windowed by the scans.
	switch (Move)
	{
	case EKrakenMove::ShowSwing:
		PlayOneShot(SwingAnim, Tell + SwingActive + SwingRecover * 0.5f, SwingClipStart, SwingClipRate);
		break;
	case EKrakenMove::PauldronRush:
		PlayOneShot(ChargeAnim ? ChargeAnim : SwingAnim, Tell + RushActive, 0.f, 0.f);
		break;
	case EKrakenMove::ChampionsSlam:
		PlayOneShot(SlamAnim, Tell + 1.0f + SlamRecover * 0.5f, SlamClipStart, SlamClipRate);
		break;
	case EKrakenMove::IronGrip:
		PlayOneShot(GripAnim, Tell + GripHoldSeconds + 0.6f, GripClipStart, GripClipRate);
		break;
	default: break;
	}
	EnterState(EKrakenState::Telegraph, Tell);
}

void AKrakenBoss::StartAttack()
{
	ASparkHeroCharacter* Hero = ResolveHero();
	bGripHolding = false;
	bSlamAirborne = false;

	switch (Move)
	{
	case EKrakenMove::ShowSwing:
		EnterState(EKrakenState::Attack, SwingActive);
		break;

	case EKrakenMove::PauldronRush:
	{
		// Direction LOCKS at commit — sidestepping the line is the dodge.
		FVector Dir = Hero ? (Hero->GetActorLocation() - GetActorLocation()) : GetActorForwardVector();
		Dir.Z = 0.f;
		RushDirection = Dir.GetSafeNormal();
		EnterState(EKrakenState::Attack, RushActive);
		break;
	}

	case EKrakenMove::ChampionsSlam:
	{
		FVector To = Hero ? (Hero->GetActorLocation() - GetActorLocation()) : GetActorForwardVector() * 300.f;
		To.Z = 0.f;
		const FVector Leap = To.GetSafeNormal() * FMath::Min(To.Size(), 420.f) / 0.7f;
		LaunchCharacter(FVector(Leap.X, Leap.Y, SlamLeapLift), true, true);
		bSlamAirborne = true;
		EnterState(EKrakenState::Attack, 2.0f);   // Landed() ends it early
		break;
	}

	case EKrakenMove::IronGrip:
	{
		// Commit check: a hero mid-dash slips the grab — dash IS the dodge.
		if (Hero && !Hero->IsDashing()
			&& FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= GripRange)
		{
			const FVector Pull = (GetActorLocation() - Hero->GetActorLocation()).GetSafeNormal2D();
			Hero->LaunchCharacter(Pull * GripPullSpeed + FVector(0.f, 0.f, 120.f), true, true);
			bGripHolding = true;
			EnterState(EKrakenState::Attack, GripHoldSeconds);
		}
		else
		{
			// Whiffed grip: the biggest opening he ever gives.
			FinishAttack(GripRecover);
		}
		break;
	}
	default:
		FinishAttack(SwingRecover);
		break;
	}
}

void AKrakenBoss::FinishAttack(float RecoverSeconds)
{
	GetCharacterMovement()->StopMovementImmediately();
	bGripHolding = false;
	EnterState(EKrakenState::Recover, RecoverSeconds);
}

void AKrakenBoss::LandDuelHit(ASparkHeroCharacter* Hero, float Embers)
{
	if (!Hero || bHitThisAttack) { return; }
	bHitThisAttack = true;
	// The knockback law: shove first (always), fire second (grace may eat it).
	FVector Away = Hero->GetActorLocation() - GetActorLocation();
	Away.Z = 0.f;
	Away = Away.IsNearlyZero() ? GetActorForwardVector() : Away.GetSafeNormal();
	Hero->LaunchCharacter(Away * KnockbackForce + FVector(0.f, 0.f, KnockbackLift), true, true);
	Hero->TakeEmberHit(Embers);
}

void AKrakenBoss::TickAttack(float DeltaTime, ASparkHeroCharacter* Hero)
{
	switch (Move)
	{
	case EKrakenMove::ShowSwing:
		if (Hero && !bHitThisAttack)
		{
			const FVector To = Hero->GetActorLocation() - GetActorLocation();
			const bool bInFront = FVector::DotProduct(To.GetSafeNormal2D(), GetActorForwardVector()) > 0.17f;
			if (bInFront && To.Size() <= SwingReach)
			{
				LandDuelHit(Hero, DuelHitEmbers);
			}
		}
		break;

	case EKrakenMove::PauldronRush:
		GetCharacterMovement()->Velocity =
			FVector(RushDirection.X, RushDirection.Y, 0.f) * RushSpeed
			+ FVector(0.f, 0.f, GetCharacterMovement()->Velocity.Z);
		if (Hero && !bHitThisAttack
			&& FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= RushHitRange)
		{
			LandDuelHit(Hero, DuelHitEmbers);
			FinishAttack(RushRecover);
		}
		break;

	case EKrakenMove::ChampionsSlam:
		break;   // ballistic; Landed() delivers the ring shock

	case EKrakenMove::IronGrip:
		if (bGripHolding && Hero)
		{
			// The licensed rule-bend: 1s of held physics. A spring pins the hero
			// to the grip point; his inputs fire but the tentacle owns his body.
			const FVector HoldPoint = GetActorLocation()
				+ GetActorForwardVector() * 150.f + FVector(0.f, 0.f, 30.f);
			Hero->GetCharacterMovement()->Velocity =
				(HoldPoint - Hero->GetActorLocation()) * 9.f;
		}
		break;
	default: break;
	}
}

void AKrakenBoss::Landed(const FHitResult& Hit)
{
	Super::Landed(Hit);
	if (State == EKrakenState::Attack && Move == EKrakenMove::ChampionsSlam && bSlamAirborne)
	{
		bSlamAirborne = false;
		if (ASparkHeroCharacter* Hero = ResolveHero())
		{
			// Ring shock: grounded heroes inside the ring are hit. JUMP dodges —
			// the slam teaches the first verb (and the final blow is a jump).
			const bool bHeroGrounded = Hero->GetCharacterMovement()->IsMovingOnGround();
			if (bHeroGrounded
				&& FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= SlamRingRadius)
			{
				LandDuelHit(Hero, DuelHitEmbers);
			}
		}
		FinishAttack(SlamRecover);
	}
}

void AKrakenBoss::HandleCapsuleHit(UPrimitiveComponent*, AActor* OtherActor,
                                   UPrimitiveComponent*, FVector, const FHitResult&)
{
	// CLASH row: stomps and dashes never hurt a Champion — both bounce off.
	ASparkHeroCharacter* Hero = Cast<ASparkHeroCharacter>(OtherActor);
	if (!Hero || State == EKrakenState::Defeated) { return; }
	const bool bStompTry = Hero->GetActorLocation().Z
		> GetActorLocation().Z + GetCapsuleComponent()->GetScaledCapsuleHalfHeight() * 0.5f;
	if (bStompTry || Hero->IsDashing())
	{
		FVector Away = Hero->GetActorLocation() - GetActorLocation();
		Away.Z = 0.f;
		Away = Away.IsNearlyZero() ? -GetActorForwardVector() : Away.GetSafeNormal();
		Hero->LaunchCharacter(Away * 520.f + FVector(0.f, 0.f, bStompTry ? 480.f : 220.f), true, true);
	}
}

void AKrakenBoss::TakeStrike(int32 InComboBeat, bool bCharged)
{
	if (State == EKrakenState::Defeated || !DuelMeter) { return; }
	const float Embers = (bCharged || InComboBeat >= 2) ? HeavyStrikeEmbers : LightStrikeEmbers;
	DuelMeter->ApplyEmberDamage(Embers);

	// Phase check (spec: bosses teach a phase before they test it).
	const float Frac = DuelMeter->GetFraction();
	const int32 NewPhase = Frac <= Phase3Fraction ? 3 : (Frac <= Phase2Fraction ? 2 : 1);
	if (NewPhase > Phase)
	{
		Phase = NewPhase;
		OnKrakenPhaseChanged(Phase);
		if (State != EKrakenState::Staggered)
		{
			PlayOneShot(TauntAnim ? TauntAnim : HitReactAnim, 1.1f);
			EnterState(EKrakenState::Recover, 1.1f);   // the phase roar IS an opening
		}
	}
	else if (bCharged)
	{
		TakeStagger(StaggerSeconds);   // DoChargedStrike's old promise, kept
	}
	else if (State == EKrakenState::Waiting || State == EKrakenState::Recover
	         || State == EKrakenState::Approach)
	{
		PlayOneShot(HitReactAnim, 0.5f);   // light hits flinch him only off-attack
		if (State != EKrakenState::Recover) { EnterState(EKrakenState::Recover, 0.5f); }
	}
}

void AKrakenBoss::TakeStagger(float Seconds)
{
	if (State == EKrakenState::Defeated) { return; }
	bGripHolding = false;
	GetCharacterMovement()->StopMovementImmediately();
	PlayOneShot(StaggerAnim ? StaggerAnim : HitReactAnim, Seconds);
	EnterState(EKrakenState::Staggered, Seconds);
}

void AKrakenBoss::HandleDuelMeterEmpty()
{
	if (State == EKrakenState::Defeated) { return; }
	bGripHolding = false;
	GetCharacterMovement()->StopMovementImmediately();
	GetCharacterMovement()->DisableMovement();
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
	if (DefeatAnim) { PlayOneShot(DefeatAnim, DefeatAnim->GetPlayLength()); }
	EnterState(EKrakenState::Defeated, 0.f);
	OnKrakenDefeated();   // he tears the orange strip from his pauldron
}

void AKrakenBoss::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
	if (State == EKrakenState::Defeated) { return; }

	ASparkHeroCharacter* Hero = ResolveHero();
	const float Dist = Hero ? FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) : 1e9f;

	// Walk-away law (§6.1): past the disengage ring he stands down; the duel
	// meter refills for the rematch — the duelist never executes, never sulks.
	if (State != EKrakenState::Waiting && Dist > DisengageRadius)
	{
		DuelMeter->RefillFull();
		Phase = 1;
		GetCharacterMovement()->StopMovementImmediately();
		PlayLoop(IdleAnim);
		State = EKrakenState::Waiting;
		return;
	}

	switch (State)
	{
	case EKrakenState::Waiting:
		PlayLoop(IdleAnim);
		if (Hero) { FaceHero(Hero, DeltaTime * 0.5f); }
		if (Dist <= DuelStartRadius)
		{
			PlayOneShot(TauntAnim ? TauntAnim : IdleAnim, 1.4f);
			EnterState(EKrakenState::Intro, 1.4f);
		}
		break;

	case EKrakenState::Intro:
		if (Hero) { FaceHero(Hero, DeltaTime); }
		if (Now() >= StateUntil) { EnterState(EKrakenState::Approach, 0.f); }
		break;

	case EKrakenState::Approach:
	{
		if (!Hero) { break; }
		FaceHero(Hero, DeltaTime);
		PlayLoop(WalkAnim, 1.f);
		GetCharacterMovement()->MaxWalkSpeed = ApproachSpeed;
		AddMovementInput((Hero->GetActorLocation() - GetActorLocation()).GetSafeNormal2D());

		if (Move == EKrakenMove::None) { SelectMove(Dist); }
		const float TriggerRange =
			Move == EKrakenMove::PauldronRush ? 750.f :
			Move == EKrakenMove::ChampionsSlam ? 480.f :
			Move == EKrakenMove::IronGrip ? GripRange * 0.9f : SwingReach * 0.85f;
		if (Dist <= TriggerRange) { StartTelegraph(); }
		break;
	}

	case EKrakenState::Telegraph:
		if (Hero) { FaceHero(Hero, DeltaTime); }   // tells track — dodging is timing, not strafing
		if (Now() >= StateUntil) { StartAttack(); }
		break;

	case EKrakenState::Attack:
		TickAttack(DeltaTime, Hero);
		if (Now() >= StateUntil)
		{
			float Recover = SwingRecover;
			if (Move == EKrakenMove::PauldronRush) { Recover = RushRecover; }
			else if (Move == EKrakenMove::ChampionsSlam) { Recover = SlamRecover; }
			else if (Move == EKrakenMove::IronGrip)
			{
				if (bGripHolding && Hero)
				{
					// The slam that ends the hold.
					bGripHolding = false;
					bHitThisAttack = false;
					FVector Away = Hero->GetActorLocation() - GetActorLocation();
					Away.Z = 0.f;
					Away = Away.IsNearlyZero() ? GetActorForwardVector() : Away.GetSafeNormal();
					Hero->LaunchCharacter(Away * GripSlamForce + FVector(0.f, 0.f, 480.f), true, true);
					Hero->TakeEmberHit(DuelHitEmbers);
				}
				Recover = GripRecover;
			}
			FinishAttack(Recover);
		}
		break;

	case EKrakenState::Recover:
		if (Now() >= StateUntil)
		{
			Move = EKrakenMove::None;
			EnterState(EKrakenState::Approach, 0.f);
		}
		break;

	case EKrakenState::Staggered:
		if (Now() >= StateUntil)
		{
			Move = EKrakenMove::None;
			EnterState(EKrakenState::Approach, 0.f);
		}
		break;

	default:
		break;
	}
}
