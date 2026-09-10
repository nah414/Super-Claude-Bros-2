#include "GladeProwler.h"

#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "SparkHeroCharacter.h"
#include "SparkImpactBurst.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	// Moss over old steel: teal-green, the Glade's calm made menacing.
	const FLinearColor ProwlerMoss(0.75f, 2.3f, 1.05f);
}

AGladeProwler::AGladeProwler()
{
	RivalDisplayName = TEXT("THE GLADE PROWLER");

	// THE STEALTH CONTRACT: proximity never starts this fight — his eyes do.
	DuelStartRadius = -1.f;
	DisengageRadius = 2400.f;   // break his line long enough and he forgets you
	ApproachSpeed = 640.f;      // active and angry once he knows
	DuelHitEmbers = 12.f;       // a small battle, not the Bramblehulk
	IntroSeconds = 1.2f;
	GetCharacterMovement()->MaxWalkSpeed = ApproachSpeed;

	// THE STALE-POSE FIX (Adam's July 23 report: gliding legs, ghosting trails).
	// He patrols far beyond the base's 3500uu pose-LOD ring, where render-culled
	// pose evaluation froze his skeleton mid-glimpse — and TSR smeared the frozen
	// mesh into blur. A wanderer lives to be seen at distance: full pose, always
	// (Load Law: priced — one extra always-ticking body).
	PoseLODRadius = 100000.f;

	// THE DEEP CUT (Adam's second report — "a problem since we first built this
	// character"): the base ships bEnableUpdateRateOptimizations=true, and URO
	// throttles pose EVALUATION by screen size — a human-frame walker seen at
	// distance drops to a few pose updates a second, UN-interpolated by default.
	// Root glides, legs snap, TSR smears the snaps into trails. Independent of
	// VisibilityBasedAnimTickOption, which is why the pose-LOD fix alone failed.
	// The Prowler's whole job is being watched walking from afar: URO off.
	RivalBody->bEnableUpdateRateOptimizations = false;

	HitBurstColor = ProwlerMoss * 1.4f;
	HitBurstScale = 1.2f;
	DefeatBurstColor = FLinearColor(1.4f, 3.4f, 1.6f);   // the seep breaks; the moss keeps him
	DefeatBurstScale = 2.0f;
	if (TelegraphLight) { TelegraphLight->SetLightColor(ProwlerMoss); }

	// HIS OWN BODY (stage 31, July 23): the Warlord loan is repaid. Fresh gen,
	// fresh rig, fresh clips through the proven stage-26 chain — including a real
	// ROAR for the taunt slot. Cone placeholder until the import lands.
	static ConstructorHelpers::FObjectFinder<USkeletalMesh> Model(TEXT("/Game/Art/ProwlerSkelV1/SCB2Prowler.SCB2Prowler"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FIdle(TEXT("/Game/Art/ProwlerSkelV1/A_Prowler_Idle_Anim.A_Prowler_Idle_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FWalk(TEXT("/Game/Art/ProwlerSkelV1/A_Prowler_Walk_Anim.A_Prowler_Walk_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FSwing(TEXT("/Game/Art/ProwlerSkelV1/A_Prowler_Swing_Anim.A_Prowler_Swing_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FChop(TEXT("/Game/Art/ProwlerSkelV1/A_Prowler_Chop_Anim.A_Prowler_Chop_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FSweep(TEXT("/Game/Art/ProwlerSkelV1/A_Prowler_Sweep_Anim.A_Prowler_Sweep_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FHit(TEXT("/Game/Art/ProwlerSkelV1/A_Prowler_HitReact_Anim.A_Prowler_HitReact_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FStagger(TEXT("/Game/Art/ProwlerSkelV1/A_Prowler_Stagger_Anim.A_Prowler_Stagger_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FDefeat(TEXT("/Game/Art/ProwlerSkelV1/A_Prowler_Defeat_Anim.A_Prowler_Defeat_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FTaunt(TEXT("/Game/Art/ProwlerSkelV1/A_Prowler_Taunt_Anim.A_Prowler_Taunt_Anim"));

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
	HitReactAnim = LoadRivalClip(FHit);
	StaggerAnim = LoadRivalClip(FStagger);
	DefeatAnim = LoadRivalClip(FDefeat);
	TauntAnim = LoadRivalClip(FTaunt);   // the roar is finally his own voice

	// Fresh clips, unscanned: auto-fit windows until the AnimPose scan pass
	// (Articulation Checklist rule 1 — no clip wires without scan numbers; the
	// Warlord's scan values do not transfer to a new skeleton's routines).
	SwingClipStart = 0.f; SwingClipRate = 0.f;
	ChopClipStart = 0.f; ChopClipRate = 0.f;
	SweepClipStart = 0.f; SweepClipRate = 0.f;
	PatrolAnimRate = 1.0f;   // Monster_Walk is a heavy stalk; re-rate after the scan
}

void AGladeProwler::BeginPlay()
{
	Super::BeginPlay();
	PatrolCenter = GetActorLocation();
	HeadingYaw = GetActorRotation().Yaw;
	NextHeadingAt = Now() + FMath::FRandRange(WanderIntervalMin, WanderIntervalMax);
}


bool AGladeProwler::CanSeeHero(const ASparkHeroCharacter* Hero) const
{
	if (!Hero) { return false; }
	// Undergrowth is cover: a crouched hero halves the range his eyes reach.
	const float Range = SightRange
		* (Hero->GetCharacterMovement()->IsCrouching() ? CrouchSightScale : 1.f);
	const FVector To = Hero->GetActorLocation() - GetActorLocation();
	if (To.SizeSquared() > Range * Range) { return false; }
	const float Cos = FVector::DotProduct(To.GetSafeNormal2D(), GetActorForwardVector());
	if (Cos < FMath::Cos(FMath::DegreesToRadians(SightHalfAngleDeg))) { return false; }

	// The forest is real cover: the look must actually reach him.
	FHitResult Hit;
	FCollisionQueryParams Params(FName(TEXT("ProwlerEyes")), false, this);
	const FVector Eye = GetActorLocation() + FVector(0.f, 0.f, 120.f);
	const FVector Mark = Hero->GetActorLocation() + FVector(0.f, 0.f, 50.f);
	const bool bBlocked = GetWorld()->LineTraceSingleByChannel(Hit, Eye, Mark, ECC_Visibility, Params)
		&& Hit.GetActor() != Hero;
	return !bBlocked;
}

void AGladeProwler::PickNewHeading(bool bBlocked)
{
	const FVector Home = PatrolCenter - GetActorLocation();
	if (Home.SizeSquared2D() > LeashRadius * LeashRadius)
	{
		// Beyond the leash: bend the round back toward home soil, loosely.
		HeadingYaw = Home.Rotation().Yaw + FMath::FRandRange(-50.f, 50.f);
	}
	else
	{
		HeadingYaw = FMath::FRandRange(0.f, 360.f);
	}
	NextHeadingAt = Now() + (bBlocked ? 0.6f : FMath::FRandRange(WanderIntervalMin, WanderIntervalMax));
}

void AGladeProwler::TickWaiting(float DeltaTime, ASparkHeroCharacter* Hero, float Dist)
{
	// NO Super call, ever: the base's idle/face-hero would fight the patrol for
	// the skeleton and the yaw — the July 23 frame-0 machine. One state, one owner.
	UCharacterMovementComponent* Movement = GetCharacterMovement();
	Movement->MaxWalkSpeed = PatrolSpeed;

	// The rounds: walk the heading; a wall (or the clock) picks the next one.
	const FVector Dir = FRotator(0.f, HeadingYaw, 0.f).Vector();
	FHitResult Ahead;
	FCollisionQueryParams Params(FName(TEXT("ProwlerPath")), false, this);
	const FVector Eye = GetActorLocation() + FVector(0.f, 0.f, 80.f);
	const bool bBlocked = GetWorld()->LineTraceSingleByChannel(
		Ahead, Eye, Eye + Dir * 340.f, ECC_Visibility, Params);
	if (bBlocked || Now() >= NextHeadingAt)
	{
		PickNewHeading(bBlocked);
	}

	const FRotator Face(0.f, FMath::FixedTurn(GetActorRotation().Yaw, HeadingYaw, 140.f * DeltaTime), 0.f);
	SetActorRotation(Face);
	// CMC-honest drive (July 23 audit): AddMovementInput rides friction/braking
	// instead of fighting them with a raw velocity write every tick.
	AddMovementInput(Dir);
	PlayLoop(MoveAnim, PatrolAnimRate);   // feet rated to the ground, never skating

	// The eyes. A glimpse starts the startle clock; a held look starts the fight.
	if (CanSeeHero(Hero))
	{
		if (SpottedSince < 0.f)
		{
			SpottedSince = Now();
			if (TelegraphLight)
			{
				TelegraphLight->SetLightColor(ProwlerMoss);
				TelegraphLight->SetIntensity(TelegraphPulseIntensity);   // the glint of noticing
			}
		}
		else if (Now() - SpottedSince >= ReactionSeconds)
		{
			RoarAndEngage();
		}
	}
	else
	{
		SpottedSince = -1.f;
		if (TelegraphLight) { TelegraphLight->SetIntensity(0.f); }
	}
}

void AGladeProwler::RoarAndEngage()
{
	// The startle made honest (July 23 audit): the body STOPS, the roar clip
	// takes the skeleton for the whole Intro — no walk-cycle marching in place.
	UE_LOG(LogTemp, Display, TEXT("MOONWORKS_MARKER: the Glade Prowler spotted the hero"));
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 150.f),
	                         ProwlerMoss * 2.2f, 1.4f, 5200.f);
	UCharacterMovementComponent* Movement = GetCharacterMovement();
	Movement->StopMovementImmediately();
	Movement->MaxWalkSpeed = ApproachSpeed;
	SpottedSince = -1.f;
	PlayOneShot(TauntAnim ? TauntAnim : IdleAnim, IntroSeconds);
	EnterState(ERivalState::Intro, IntroSeconds);
}

bool AGladeProwler::OnStruck(int32 ComboBeat, bool bCharged)
{
	// Ambushed on his rounds: the sneak strike wakes him ROARING (the vision
	// contract's other half). Damage still lands through the normal path.
	if (State == ERivalState::Waiting)
	{
		RoarAndEngage();
	}
	return false;
}

void AGladeProwler::SelectMove(float DistToHero)
{
	TArray<EProwlerMove> Pool = { EProwlerMove::MossSwing, EProwlerMove::MossSwing, EProwlerMove::RootChop };
	if (Phase >= 2) { Pool.Add(EProwlerMove::BrambleSweep); }
	EProwlerMove Picked = Pool[FMath::RandRange(0, Pool.Num() - 1)];
	if (Picked == Move && Pool.Num() > 1)
	{
		Picked = Pool[(Pool.Find(Picked) + 1) % Pool.Num()];
	}
	Move = Picked;
}

void AGladeProwler::StartTelegraph()
{
	bHitThisAttack = false;
	GetCharacterMovement()->StopMovementImmediately();

	float Tell = SwingTell;
	switch (Move)
	{
	case EProwlerMove::RootChop:     Tell = ChopTell; break;
	case EProwlerMove::BrambleSweep: Tell = SweepTell; break;
	default: break;
	}
	Tell *= TellScale();

	if (TelegraphLight) { TelegraphLight->SetLightColor(ProwlerMoss); }

	switch (Move)
	{
	case EProwlerMove::MossSwing:
		PlayOneShot(SwingAnim, Tell + SwingActive + SwingRecover * 0.4f, SwingClipStart, SwingClipRate);
		break;
	case EProwlerMove::RootChop:
		PlayOneShot(ChopAnim, Tell + ChopActive + ChopRecover * 0.4f, ChopClipStart, ChopClipRate);
		break;
	case EProwlerMove::BrambleSweep:
		PlayOneShot(SweepAnim, Tell + SweepActive + SweepRecover * 0.4f, SweepClipStart, SweepClipRate);
		break;
	default: break;
	}
	EnterState(ERivalState::Telegraph, Tell);
}

void AGladeProwler::StartAttack()
{
	if (TelegraphLight) { TelegraphLight->SetIntensity(0.f); }
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 40.f),
	                         ProwlerMoss * 2.2f, 1.2f, 4200.f, 0.22f);
	switch (Move)
	{
	case EProwlerMove::MossSwing:    EnterState(ERivalState::Attack, SwingActive); break;
	case EProwlerMove::RootChop:     EnterState(ERivalState::Attack, ChopActive); break;
	case EProwlerMove::BrambleSweep: EnterState(ERivalState::Attack, SweepActive); break;
	default: FinishAttack(SwingRecover); break;
	}
}

void AGladeProwler::TickAttack(float DeltaTime, ASparkHeroCharacter* Hero)
{
	switch (Move)
	{
	case EProwlerMove::MossSwing:
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
	case EProwlerMove::RootChop:
		if (Hero && !bHitThisAttack)
		{
			const FVector To = Hero->GetActorLocation() - GetActorLocation();
			if (FVector::DotProduct(To.GetSafeNormal2D(), GetActorForwardVector()) > 0.25f
				&& To.Size() <= ChopReach)
			{
				bHitThisAttack = true;
				LandDuelHit(Hero, DuelHitEmbers * 1.3f);
			}
		}
		break;
	case EProwlerMove::BrambleSweep:
		if (Hero && !bHitThisAttack
			&& Hero->GetCharacterMovement()->IsMovingOnGround()
			&& FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= SweepRadius)
		{
			bHitThisAttack = true;
			LandDuelHit(Hero, DuelHitEmbers);
		}
		break;
	default: break;
	}
}

void AGladeProwler::HandleAttackExpired(ASparkHeroCharacter* Hero)
{
	switch (Move)
	{
	case EProwlerMove::RootChop:     FinishAttack(ChopRecover); break;
	case EProwlerMove::BrambleSweep: FinishAttack(SweepRecover); break;
	default:                         FinishAttack(SwingRecover); break;
	}
}

void AGladeProwler::NotifyRivalDefeated()
{
	// The first rung of the tier ladder: beating the Prowler wakes the powers.
	UE_LOG(LogTemp, Display, TEXT("MOONWORKS_MARKER: the Glade Prowler is beaten — power tiers rise"));
	if (ASparkHeroCharacter* Hero = ResolveHero())
	{
		Hero->RaiseAllPowerTiers(1);
	}
}
