// The Void Stalker â€” the third voice of the duel framework. Where the others
// press you, he UNSEAMS SPACE: vanish-flank-strike. The counter is courage â€”
// hit him during the tell and the feint breaks in his hands.

#include "VoidStalker.h"

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
#include "UObject/ConstructorHelpers.h"

namespace
{
	const FLinearColor StalkerViolet(1.4f, 0.35f, 3.2f);   // the design law, worn honestly

	UAnimSequence* StalkerClip(const ConstructorHelpers::FObjectFinder<UAnimSequence>& Finder)
	{
		return Finder.Succeeded() ? Finder.Object.Get() : nullptr;
	}
}

AVoidStalker::AVoidStalker()
{
	PrimaryActorTick.bCanEverTick = true;

	GetCapsuleComponent()->SetCapsuleSize(40.f, 72.f);
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);

	GetCharacterMovement()->bOrientRotationToMovement = false;
	GetCharacterMovement()->MaxWalkSpeed = ApproachSpeed;
	GetCharacterMovement()->GravityScale = 1.9f;
	AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;

	VisualRoot = CreateDefaultSubobject<USceneComponent>(TEXT("VisualRoot"));
	VisualRoot->SetupAttachment(RootComponent);

	StalkerBody = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("StalkerBody"));
	StalkerBody->SetupAttachment(VisualRoot);
	StalkerBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	StalkerBody->SetAnimationMode(EAnimationMode::AnimationSingleNode);
	StalkerBody->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;   // LOAD LAW (distance pose-LOD throttles far)
	StalkerBody->bEnableUpdateRateOptimizations = true;   // PERF
	StalkerBody->SetBoundsScale(1.4f);   // cull-freeze insurance (the spiral/lunge spread)

	PlaceholderBody = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PlaceholderBody"));
	PlaceholderBody->SetupAttachment(VisualRoot);
	PlaceholderBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	DuelMeter = CreateDefaultSubobject<UEmberMeterComponent>(TEXT("DuelMeter"));
	DuelMeter->GraceDuration = 0.05f;

	TelegraphLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("TelegraphLight"));
	TelegraphLight->SetupAttachment(VisualRoot);
	TelegraphLight->SetRelativeLocation(FVector(0.f, 0.f, 45.f));
	TelegraphLight->SetAttenuationRadius(620.f);
	TelegraphLight->SetCastShadows(false);
	TelegraphLight->SetIntensity(0.f);
	TelegraphLight->SetLightColor(FLinearColor(0.5f, 0.15f, 1.f));

	ContactProfile.MassClass = EMassClass::Champion;
	ContactProfile.bStompImmune = true;
	ContactProfile.bDashImmune = true;
	ContactProfile.ContactDamageEmbers = 20.f;

	static ConstructorHelpers::FObjectFinder<USkeletalMesh> Model(TEXT("/Game/Art/StalkerSkelV1/SCB2Stalker.SCB2Stalker"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FIdle(TEXT("/Game/Art/StalkerSkelV1/A_Stalker_Idle_Anim.A_Stalker_Idle_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FRun(TEXT("/Game/Art/StalkerSkelV1/A_Stalker_Run_Anim.A_Stalker_Run_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FStrike(TEXT("/Game/Art/StalkerSkelV1/A_Stalker_Strike_Anim.A_Stalker_Strike_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FCut(TEXT("/Game/Art/StalkerSkelV1/A_Stalker_Combo_Anim.A_Stalker_Combo_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FLunge(TEXT("/Game/Art/StalkerSkelV1/A_Stalker_Lunge_Anim.A_Stalker_Lunge_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FSpiral(TEXT("/Game/Art/StalkerSkelV1/A_Stalker_Spiral_Anim.A_Stalker_Spiral_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FStagger(TEXT("/Game/Art/StalkerSkelV1/A_Stalker_Stagger_Anim.A_Stalker_Stagger_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FHit(TEXT("/Game/Art/StalkerSkelV1/A_Stalker_HitReact_Anim.A_Stalker_HitReact_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FDefeat(TEXT("/Game/Art/StalkerSkelV1/A_Stalker_Defeat_Anim.A_Stalker_Defeat_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FTaunt(TEXT("/Game/Art/StalkerSkelV1/A_Stalker_Taunt_Anim.A_Stalker_Taunt_Anim"));

	if (Model.Succeeded())
	{
		StalkerBody->SetSkeletalMesh(Model.Object);
		bHasSkeletalModel = true;
		PlaceholderBody->SetVisibility(false);
	}
	else
	{
		static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
		if (Sphere.Succeeded())
		{
			PlaceholderBody->SetStaticMesh(Sphere.Object);
			PlaceholderBody->SetRelativeScale3D(FVector(1.0f, 1.0f, 2.6f));
		}
	}
	IdleAnim = StalkerClip(FIdle);
	RunAnim = StalkerClip(FRun);
	StrikeAnim = StalkerClip(FStrike);
	CutAnim = StalkerClip(FCut);
	LungeAnim = StalkerClip(FLunge);
	SpiralAnim = StalkerClip(FSpiral);
	StaggerAnim = StalkerClip(FStagger);
	HitReactAnim = StalkerClip(FHit);
	DefeatAnim = StalkerClip(FDefeat);
	TauntAnim = StalkerClip(FTaunt);
}

void AVoidStalker::BeginPlay()
{
	Super::BeginPlay();
	if (bHasSkeletalModel)
	{
		StalkerBody->SetRelativeLocation(FVector(0.f, 0.f, -GetCapsuleComponent()->GetScaledCapsuleHalfHeight()));
		StalkerBody->SetRelativeRotation(FRotator(0.f, SkelMeshYaw, 0.f));
		StalkerBody->SetRelativeScale3D(FVector(SkelMeshScale));
	}
	if (DuelMeter)
	{
		DuelMeter->OnFlameOut.AddDynamic(this, &AVoidStalker::HandleDuelMeterEmpty);
	}
	PlayLoop(IdleAnim);
}

ASparkHeroCharacter* AVoidStalker::ResolveHero() const
{
	return Cast<ASparkHeroCharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
}

float AVoidStalker::Now() const
{
	return GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
}

void AVoidStalker::PlayLoop(UAnimSequence* Clip, float Rate)
{
	if (!bHasSkeletalModel || !Clip || !StalkerBody) { return; }
	if (CurrentLoop == Clip) { StalkerBody->SetPlayRate(Rate); return; }
	CurrentLoop = Clip;
	StalkerBody->PlayAnimation(Clip, true);
	StalkerBody->SetPlayRate(Rate);
}

void AVoidStalker::PlayOneShot(UAnimSequence* Clip, float FitSeconds, float StartFraction, float OverrideRate)
{
	if (!bHasSkeletalModel || !Clip || !StalkerBody) { return; }
	CurrentLoop = nullptr;
	StalkerBody->PlayAnimation(Clip, false);
	const float Rate = (OverrideRate > 0.f)
		? OverrideRate
		: Clip->GetPlayLength() * (1.f - StartFraction) / FMath::Max(FitSeconds, 0.05f);
	StalkerBody->SetPlayRate(FMath::Clamp(Rate, 0.3f, 5.f));
	if (StartFraction > 0.f)
	{
		StalkerBody->SetPosition(Clip->GetPlayLength() * StartFraction, false);
	}
}

void AVoidStalker::EnterState(EStalkerState NewState, float Duration)
{
	State = NewState;
	StateUntil = Now() + Duration;
}

void AVoidStalker::FaceHero(const ASparkHeroCharacter* Hero, float DeltaTime)
{
	if (!Hero) { return; }
	const FVector To = Hero->GetActorLocation() - GetActorLocation();
	const FRotator Want(0.f, To.Rotation().Yaw, 0.f);
	SetActorRotation(FMath::RInterpTo(GetActorRotation(), Want, DeltaTime, TurnRate));
}

void AVoidStalker::SelectMove(float DistToHero)
{
	// The blink IS the kit â€” it debuts immediately and grows bolder by phase.
	TArray<EStalkerMove> Pool = { EStalkerMove::ShadowStrike, EStalkerMove::BlinkFeint };
	if (Phase >= 2) { Pool.Add(EStalkerMove::DoubleCut); }
	if (Phase >= 3) { Pool.Add(EStalkerMove::BlinkFeint); }   // double weight: space frays
	EStalkerMove Picked = Pool[FMath::RandRange(0, Pool.Num() - 1)];
	if (Picked == Move && Pool.Num() > 1)
	{
		Picked = Pool[(Pool.Find(Picked) + 1) % Pool.Num()];
	}
	Move = Picked;
}

void AVoidStalker::StartTelegraph()
{
	bHitThisAttack = false;
	CutHitsDone = 0;
	BlinksThisAttack = 0;
	bLungeStarted = false;
	bSpiralArrival = false;
	GetCharacterMovement()->StopMovementImmediately();

	float Tell = StrikeTell;
	if (Move == EStalkerMove::DoubleCut) { Tell = CutTell; }
	else if (Move == EStalkerMove::BlinkFeint) { Tell = BlinkTell; }
	Tell *= TellScale();

	switch (Move)
	{
	case EStalkerMove::ShadowStrike:
		PlayOneShot(StrikeAnim, Tell + StrikeActive + StrikeRecover * 0.4f, StrikeClipStart, StrikeClipRate);
		break;
	case EStalkerMove::DoubleCut:
		PlayOneShot(CutAnim, Tell + CutActive + CutRecover * 0.4f, CutClipStart, CutClipRate);
		break;
	case EStalkerMove::BlinkFeint:
		PlayLoop(IdleAnim, 0.4f);   // he goes STILL â€” the stillness is the tell
		break;
	default: break;
	}
	EnterState(EStalkerState::Telegraph, Tell);
}

void AVoidStalker::DoVanish()
{
	// The seam opens: violet flash where he WAS, and he is gone.
	ASparkImpactBurst::Burst(this, GetActorLocation(), StalkerViolet * 2.4f, 1.3f, 6000.f, 0.3f);
	SetActorHiddenInGame(true);
	if (TelegraphLight) { TelegraphLight->SetIntensity(0.f); }
	++BlinksThisAttack;
	EnterState(EStalkerState::Vanished, BlinkGapSeconds);
}

void AVoidStalker::DoArrive()
{
	// Reappear on a flank the hero wasn't watching: Â±(110Â°-165Â°) around them.
	ASparkHeroCharacter* Hero = ResolveHero();
	FVector Spot = GetActorLocation();
	if (Hero)
	{
		const float Side = FMath::RandBool() ? 1.f : -1.f;
		const float AngleDeg = Side * FMath::FRandRange(110.f, 165.f);
		const FVector HeroFacing = Hero->GetActorForwardVector();
		const FVector Dir = HeroFacing.RotateAngleAxis(AngleDeg, FVector::UpVector).GetSafeNormal2D();
		Spot = Hero->GetActorLocation() + Dir * BlinkFlankDistance;
		Spot.Z = GetActorLocation().Z;
	}
	TeleportTo(Spot, GetActorRotation());   // engine handles walls/floors politely
	SetActorHiddenInGame(false);
	if (Hero)
	{
		const FVector To = (Hero->GetActorLocation() - GetActorLocation()).GetSafeNormal2D();
		SetActorRotation(FRotator(0.f, To.Rotation().Yaw, 0.f));
		LungeDirection = To;
	}
	// The arrival announces itself for one honest beat â€” vulnerable, violet.
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 30.f),
	                         StalkerViolet * 2.8f, 1.4f, 7000.f, 0.32f);
	// Phase 2+: sometimes the ARRIVAL is the weapon. He rematerializes already
	// winding the spin, and the whole ring around him becomes the strike zone.
	// The lunge teaches "watch your flank"; the spiral teaches "GET OFF the flank".
	bSpiralArrival = (Phase >= 2 && SpiralAnim && FMath::FRand() < SpiralChance);
	if (bSpiralArrival)
	{
		bLungeStarted = false;   // reused as the spiral's one-detonation latch
		PlayOneShot(SpiralAnim, RematerializeSeconds + SpiralActive + 0.3f, SpiralClipStart, SpiralClipRate);
		EnterState(EStalkerState::Attack, RematerializeSeconds + SpiralActive);
	}
	else
	{
		PlayOneShot(LungeAnim, RematerializeSeconds + BlinkLungeActive + 0.3f, LungeClipStart, LungeClipRate);
		EnterState(EStalkerState::Attack, RematerializeSeconds + BlinkLungeActive);
	}
}

void AVoidStalker::StartAttack()
{
	if (TelegraphLight) { TelegraphLight->SetIntensity(0.f); }
	switch (Move)
	{
	case EStalkerMove::ShadowStrike:
		ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 30.f),
		                         StalkerViolet * 2.f, 1.0f, 3800.f, 0.2f);
		EnterState(EStalkerState::Attack, StrikeActive);
		break;
	case EStalkerMove::DoubleCut:
		ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 30.f),
		                         StalkerViolet * 2.f, 1.0f, 3800.f, 0.2f);
		EnterState(EStalkerState::Attack, CutActive);
		break;
	case EStalkerMove::BlinkFeint:
		DoVanish();
		break;
	default:
		FinishAttack(StrikeRecover);
		break;
	}
}

void AVoidStalker::FinishAttack(float RecoverSeconds)
{
	GetCharacterMovement()->StopMovementImmediately();
	SetActorHiddenInGame(false);   // never recover invisible
	if (TelegraphLight) { TelegraphLight->SetIntensity(0.f); }
	EnterState(EStalkerState::Recover, RecoverSeconds);
}

void AVoidStalker::LandDuelHit(ASparkHeroCharacter* Hero, float Embers)
{
	if (!Hero) { return; }
	FVector Away = Hero->GetActorLocation() - GetActorLocation();
	Away.Z = 0.f;
	Away = Away.IsNearlyZero() ? GetActorForwardVector() : Away.GetSafeNormal();
	Hero->LaunchCharacter(Away * KnockbackForce + FVector(0.f, 0.f, KnockbackLift), true, true);
	Hero->TakeEmberHit(Embers);
	ASparkImpactBurst::Burst(this,
		(Hero->GetActorLocation() + GetActorLocation()) * 0.5f + FVector(0.f, 0.f, 40.f),
		StalkerViolet * 2.6f, 1.15f, 4800.f);
}

void AVoidStalker::TickAttack(float DeltaTime, ASparkHeroCharacter* Hero)
{
	switch (Move)
	{
	case EStalkerMove::ShadowStrike:
		if (Hero && !bHitThisAttack)
		{
			const FVector To = Hero->GetActorLocation() - GetActorLocation();
			if (FVector::DotProduct(To.GetSafeNormal2D(), GetActorForwardVector()) > 0.2f
				&& To.Size() <= StrikeReach)
			{
				bHitThisAttack = true;
				LandDuelHit(Hero, DuelHitEmbers);
			}
		}
		break;

	case EStalkerMove::DoubleCut:
		if (Hero)
		{
			FaceHero(Hero, DeltaTime * 0.6f);
			const float Elapsed = CutActive - (StateUntil - Now());
			const float Marks[2] = { CutActive * 0.3f, CutActive * 0.75f };
			if (CutHitsDone < 2 && Elapsed >= Marks[CutHitsDone])
			{
				++CutHitsDone;
				const FVector To = Hero->GetActorLocation() - GetActorLocation();
				if (FVector::DotProduct(To.GetSafeNormal2D(), GetActorForwardVector()) > 0.1f
					&& To.Size() <= StrikeReach + 20.f)
				{
					LandDuelHit(Hero, DuelHitEmbers * 0.6f);
				}
			}
		}
		break;

	case EStalkerMove::BlinkFeint:
	{
		if (bSpiralArrival)
		{
			// VOID SPIRAL: the honest beat still happens — then the spin
			// detonates a full circle. No safe angle; only distance answers.
			const float SpinElapsed = (RematerializeSeconds + SpiralActive) - (StateUntil - Now());
			if (SpinElapsed >= RematerializeSeconds + SpiralActive * 0.5f && !bLungeStarted)
			{
				bLungeStarted = true;   // detonate exactly once
				ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 40.f),
				                         StalkerViolet * 2.4f, 1.6f, 6200.f, 0.25f);
				if (Hero && !bHitThisAttack
					&& FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= SpiralRadius)
				{
					bHitThisAttack = true;
					LandDuelHit(Hero, DuelHitEmbers);
				}
			}
			break;
		}
		// Sub-phases: rematerialize beat (vulnerable, still) -> the lunge.
		const float Elapsed = (RematerializeSeconds + BlinkLungeActive) - (StateUntil - Now());
		if (Elapsed >= RematerializeSeconds)
		{
			if (!bLungeStarted) { bLungeStarted = true; }
			GetCharacterMovement()->Velocity =
				FVector(LungeDirection.X, LungeDirection.Y, 0.f) * BlinkLungeSpeed
				+ FVector(0.f, 0.f, GetCharacterMovement()->Velocity.Z);
			if (Hero && !bHitThisAttack
				&& FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= BlinkLungeReach)
			{
				bHitThisAttack = true;
				LandDuelHit(Hero, DuelHitEmbers);
			}
		}
		break;
	}
	default: break;
	}
}

void AVoidStalker::TakeStrike(int32 InComboBeat, bool bCharged)
{
	if (State == EStalkerState::Defeated || !DuelMeter) { return; }
	const float Embers = (bCharged || InComboBeat >= 2) ? HeavyStrikeEmbers : LightStrikeEmbers;
	DuelMeter->ApplyEmberDamage(Embers);

	// THE INTERRUPT REWARD: a strike during the blink tell BREAKS the feint.
	// Courage is the counter â€” he never gets to vanish.
	if (State == EStalkerState::Telegraph && Move == EStalkerMove::BlinkFeint)
	{
		ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 60.f),
		                         FLinearColor(4.f, 3.f, 5.f), 1.5f, 6500.f);   // the seam snaps shut
		TakeStagger(FeintBreakStagger);
		return;
	}

	const float Frac = DuelMeter->GetFraction();
	const int32 NewPhase = Frac <= Phase3Fraction ? 3 : (Frac <= Phase2Fraction ? 2 : 1);
	if (NewPhase > Phase)
	{
		Phase = NewPhase;
		OnStalkerPhaseChanged(Phase);
		if (State != EStalkerState::Staggered)
		{
			PlayOneShot(TauntAnim ? TauntAnim : HitReactAnim, 1.0f);
			EnterState(EStalkerState::Recover, 1.0f);
		}
	}
	else if (bCharged)
	{
		TakeStagger(StaggerSeconds);
	}
	else if (State == EStalkerState::Waiting || State == EStalkerState::Recover
	         || State == EStalkerState::Approach)
	{
		PlayOneShot(HitReactAnim, 0.45f);
		if (State != EStalkerState::Recover) { EnterState(EStalkerState::Recover, 0.45f); }
	}
}

void AVoidStalker::TakeStagger(float Seconds)
{
	if (State == EStalkerState::Defeated) { return; }
	SetActorHiddenInGame(false);
	if (TelegraphLight) { TelegraphLight->SetIntensity(0.f); }
	GetCharacterMovement()->StopMovementImmediately();
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 55.f),
	                         FLinearColor(5.f, 2.5f, 0.8f), 1.3f, 5200.f);
	PlayOneShot(StaggerAnim ? StaggerAnim : HitReactAnim, Seconds);
	EnterState(EStalkerState::Staggered, Seconds);
}

void AVoidStalker::HandleDuelMeterEmpty()
{
	if (State == EStalkerState::Defeated) { return; }
	SetActorHiddenInGame(false);
	if (TelegraphLight) { TelegraphLight->SetIntensity(0.f); }
	GetCharacterMovement()->StopMovementImmediately();
	GetCharacterMovement()->DisableMovement();
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
	if (DefeatAnim) { PlayOneShot(DefeatAnim, DefeatAnim->GetPlayLength()); }
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 50.f),
	                         StalkerViolet * 3.f, 2.0f, 7500.f, 0.6f);
	EnterState(EStalkerState::Defeated, 0.f);
	OnStalkerDefeated();
}

void AVoidStalker::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
	if (State == EStalkerState::Defeated) { return; }

	ASparkHeroCharacter* Hero = ResolveHero();
	const float Dist = Hero ? FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) : 1e9f;
	SCB2_TickPoseLOD(StalkerBody, Dist, 3500.f);   // PERF: far rivals cull off-screen

	// Solid-body law.
	if (Hero && State != EStalkerState::Vanished)
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

	if (State != EStalkerState::Waiting && Dist > DisengageRadius)
	{
		DuelMeter->RefillFull();
		Phase = 1;
		SetActorHiddenInGame(false);
		GetCharacterMovement()->StopMovementImmediately();
		PlayLoop(IdleAnim);
		State = EStalkerState::Waiting;
		return;
	}

	switch (State)
	{
	case EStalkerState::Waiting:
		PlayLoop(IdleAnim);
		if (Hero) { FaceHero(Hero, DeltaTime * 0.5f); }
		if (Dist <= DuelStartRadius)
		{
			PlayOneShot(TauntAnim ? TauntAnim : IdleAnim, 1.5f);
			EnterState(EStalkerState::Intro, 1.5f);
		}
		break;

	case EStalkerState::Intro:
		if (Hero) { FaceHero(Hero, DeltaTime); }
		if (Now() >= StateUntil) { EnterState(EStalkerState::Approach, 0.f); }
		break;

	case EStalkerState::Approach:
	{
		if (!Hero) { break; }
		FaceHero(Hero, DeltaTime);
		PlayLoop(RunAnim ? RunAnim : IdleAnim, 1.f);
		GetCharacterMovement()->MaxWalkSpeed = ApproachSpeed;
		AddMovementInput((Hero->GetActorLocation() - GetActorLocation()).GetSafeNormal2D());

		if (Move == EStalkerMove::None) { SelectMove(Dist); }
		const float TriggerRange =
			Move == EStalkerMove::BlinkFeint ? 700.f : StrikeReach * 0.85f;
		if (Dist <= TriggerRange) { StartTelegraph(); }
		break;
	}

	case EStalkerState::Telegraph:
		if (Hero) { FaceHero(Hero, DeltaTime); }
		if (TelegraphLight)
		{
			const float Pulse = 0.55f + 0.45f * FMath::Sin(Now() * 20.f);
			TelegraphLight->SetIntensity(6000.f * Pulse);
		}
		if (Now() >= StateUntil) { StartAttack(); }
		break;

	case EStalkerState::Vanished:
		if (Now() >= StateUntil) { DoArrive(); }
		break;

	case EStalkerState::Attack:
		TickAttack(DeltaTime, Hero);
		if (State == EStalkerState::Attack && Now() >= StateUntil)
		{
			// Phase 3: space frays â€” a missed blink-strike chains a second blink.
			if (Move == EStalkerMove::BlinkFeint && Phase >= 3
				&& !bHitThisAttack && BlinksThisAttack < 2)
			{
				DoVanish();
			}
			else
			{
				float Recover = StrikeRecover;
				if (Move == EStalkerMove::DoubleCut) { Recover = CutRecover; }
				else if (Move == EStalkerMove::BlinkFeint) { Recover = BlinkRecover; }
				FinishAttack(Recover);
			}
		}
		break;

	case EStalkerState::Recover:
		if (Now() >= StateUntil)
		{
			Move = EStalkerMove::None;
			EnterState(EStalkerState::Approach, 0.f);
		}
		break;

	case EStalkerState::Staggered:
		if (Now() >= StateUntil)
		{
			Move = EStalkerMove::None;
			EnterState(EStalkerState::Approach, 0.f);
		}
		break;

	default:
		break;
	}
}


float AVoidStalker::GetDuelFraction() const
{
	return DuelMeter ? DuelMeter->GetFraction() : 1.f;
}
