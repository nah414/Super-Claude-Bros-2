// The Bramblehulk — the boss you cannot punch. The fourth voice of the roster
// answers the other three: Kraken tests reading, Reaver tests geometry,
// Stalker tests courage — the Hulk tests RESTRAINT. The proven skeleton
// (states, tells, rings, solid bodies) carries a brand-new win condition.

#include "Bramblehulk.h"

#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "SparkCameraShakes.h"
#include "SparkHeroCharacter.h"
#include "SparkImpactBurst.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	const FLinearColor MossGreen(0.45f, 2.6f, 0.55f);     // mercy made visible
	const FLinearColor StormAmber(2.6f, 1.1f, 0.25f);     // the tantrum building
	const FLinearColor ClangWhite(4.5f, 4.5f, 3.6f);      // stone refusing the fist

	UAnimSequence* HulkClip(const ConstructorHelpers::FObjectFinder<UAnimSequence>& Finder)
	{
		return Finder.Succeeded() ? Finder.Object.Get() : nullptr;
	}
}

ABramblehulk::ABramblehulk()
{
	PrimaryActorTick.bCanEverTick = true;

	GetCapsuleComponent()->SetCapsuleSize(70.f, 110.f);   // a walking hill
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);

	GetCharacterMovement()->bOrientRotationToMovement = false;
	GetCharacterMovement()->MaxWalkSpeed = ApproachSpeed;
	GetCharacterMovement()->GravityScale = 1.9f;
	AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;

	VisualRoot = CreateDefaultSubobject<USceneComponent>(TEXT("VisualRoot"));
	VisualRoot->SetupAttachment(RootComponent);

	HulkBody = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("HulkBody"));
	HulkBody->SetupAttachment(VisualRoot);
	HulkBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	HulkBody->SetAnimationMode(EAnimationMode::AnimationSingleNode);

	PlaceholderBody = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PlaceholderBody"));
	PlaceholderBody->SetupAttachment(VisualRoot);
	PlaceholderBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	MoodLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("MoodLight"));
	MoodLight->SetupAttachment(VisualRoot);
	MoodLight->SetRelativeLocation(FVector(0.f, 0.f, 80.f));
	MoodLight->SetAttenuationRadius(700.f);
	MoodLight->SetCastShadows(false);
	MoodLight->SetIntensity(0.f);

	ContactProfile.MassClass = EMassClass::Colossus;
	ContactProfile.bStompImmune = true;
	ContactProfile.bDashImmune = true;
	ContactProfile.ContactDamageEmbers = 20.f;
	ContactProfile.bHasHP = false;   // there is no HP — only weather

	static ConstructorHelpers::FObjectFinder<USkeletalMesh> Model(TEXT("/Game/Art/BrambleSkelV1/SCB2Bramble.SCB2Bramble"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FDormant(TEXT("/Game/Art/BrambleSkelV1/A_Bramble_Dormant_Anim.A_Bramble_Dormant_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FAlert(TEXT("/Game/Art/BrambleSkelV1/A_Bramble_Alert_Anim.A_Bramble_Alert_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FWalk(TEXT("/Game/Art/BrambleSkelV1/A_Bramble_Walk_Anim.A_Bramble_Walk_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FSlam(TEXT("/Game/Art/BrambleSkelV1/A_Bramble_Slam_Anim.A_Bramble_Slam_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FQuake(TEXT("/Game/Art/BrambleSkelV1/A_Bramble_Quake_Anim.A_Bramble_Quake_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FRoar(TEXT("/Game/Art/BrambleSkelV1/A_Bramble_Roar_Anim.A_Bramble_Roar_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FHit(TEXT("/Game/Art/BrambleSkelV1/A_Bramble_HitReact_Anim.A_Bramble_HitReact_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FSoothed(TEXT("/Game/Art/BrambleSkelV1/A_Bramble_Soothed_Anim.A_Bramble_Soothed_Anim"));

	if (Model.Succeeded())
	{
		HulkBody->SetSkeletalMesh(Model.Object);
		bHasSkeletalModel = true;
		PlaceholderBody->SetVisibility(false);
	}
	else
	{
		static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
		if (Sphere.Succeeded())
		{
			PlaceholderBody->SetStaticMesh(Sphere.Object);
			PlaceholderBody->SetRelativeScale3D(FVector(2.0f, 2.0f, 4.0f));
		}
	}
	DormantAnim = HulkClip(FDormant);
	AlertAnim = HulkClip(FAlert);
	WalkAnim = HulkClip(FWalk);
	SlamAnim = HulkClip(FSlam);
	QuakeAnim = HulkClip(FQuake);
	RoarAnim = HulkClip(FRoar);
	HitReactAnim = HulkClip(FHit);
	SoothedAnim = HulkClip(FSoothed);
}

void ABramblehulk::BeginPlay()
{
	Super::BeginPlay();
	if (bHasSkeletalModel)
	{
		HulkBody->SetRelativeLocation(FVector(0.f, 0.f, -GetCapsuleComponent()->GetScaledCapsuleHalfHeight()));
		HulkBody->SetRelativeRotation(FRotator(0.f, SkelMeshYaw, 0.f));
		HulkBody->SetRelativeScale3D(FVector(SkelMeshScale));
	}
	PlayLoop(DormantAnim, 0.6f);
}

ASparkHeroCharacter* ABramblehulk::ResolveHero() const
{
	return Cast<ASparkHeroCharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
}

float ABramblehulk::Now() const
{
	return GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
}

void ABramblehulk::PlayLoop(UAnimSequence* Clip, float Rate)
{
	if (!bHasSkeletalModel || !Clip || !HulkBody) { return; }
	if (CurrentLoop == Clip) { HulkBody->SetPlayRate(Rate); return; }
	CurrentLoop = Clip;
	HulkBody->PlayAnimation(Clip, true);
	HulkBody->SetPlayRate(Rate);
}

void ABramblehulk::PlayOneShot(UAnimSequence* Clip, float FitSeconds, float StartFraction, float OverrideRate)
{
	if (!bHasSkeletalModel || !Clip || !HulkBody) { return; }
	CurrentLoop = nullptr;
	HulkBody->PlayAnimation(Clip, false);
	const float Rate = (OverrideRate > 0.f)
		? OverrideRate
		: Clip->GetPlayLength() * (1.f - StartFraction) / FMath::Max(FitSeconds, 0.05f);
	HulkBody->SetPlayRate(FMath::Clamp(Rate, 0.25f, 5.f));
	if (StartFraction > 0.f)
	{
		HulkBody->SetPosition(Clip->GetPlayLength() * StartFraction, false);
	}
}

void ABramblehulk::EnterState(EHulkState NewState, float Duration)
{
	State = NewState;
	StateUntil = Now() + Duration;
}

void ABramblehulk::FaceHero(const ASparkHeroCharacter* Hero, float DeltaTime)
{
	if (!Hero) { return; }
	const FVector To = Hero->GetActorLocation() - GetActorLocation();
	const FRotator Want(0.f, To.Rotation().Yaw, 0.f);
	SetActorRotation(FMath::RInterpTo(GetActorRotation(), Want, DeltaTime, TurnRate));
}

void ABramblehulk::Wake()
{
	if (State != EHulkState::Dormant) { return; }
	PlayOneShot(RoarAnim ? RoarAnim : AlertAnim, 1.6f);
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 90.f),
	                         StormAmber * 2.2f, 1.8f, 6000.f, 0.4f);
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
	{
		PC->ClientStartCameraShake(USparkBigLandShake::StaticClass());
	}
	EnterState(EHulkState::Waking, 1.6f);
}

void ABramblehulk::TakeStrikeClang(ASparkHeroCharacter* Striker, bool bCharged)
{
	if (State == EHulkState::Soothed) { return; }

	// CLANG: stone refuses the fist. Zero damage; the STRIKER rebounds
	// (the pre-W4 armor law, 400 uu/s self-rebound) — and mercy is undone.
	if (Striker)
	{
		FVector Away = Striker->GetActorLocation() - GetActorLocation();
		Away.Z = 0.f;
		Away = Away.IsNearlyZero() ? -GetActorForwardVector() : Away.GetSafeNormal();
		Striker->LaunchCharacter(Away * 400.f + FVector(0.f, 0.f, 160.f), true, false);
		ASparkImpactBurst::Burst(this,
			(Striker->GetActorLocation() + GetActorLocation()) * 0.5f + FVector(0.f, 0.f, 50.f),
			ClangWhite, bCharged ? 1.2f : 0.85f, 3600.f, 0.2f);
	}
	CalmProgress = FMath::Max(0.f, CalmProgress - CalmLostPerClang);

	if (State == EHulkState::Dormant)
	{
		Wake();   // you punched a sleeping hill
	}
	else if ((State == EHulkState::Approach || State == EHulkState::Recover) && HitReactAnim)
	{
		PlayOneShot(HitReactAnim, 0.6f);
		if (State == EHulkState::Approach) { EnterState(EHulkState::Recover, 0.6f); }
	}
}

void ABramblehulk::AddCalm(float Amount)
{
	if (State == EHulkState::Soothed) { return; }
	CalmProgress = FMath::Clamp(CalmProgress + Amount, 0.f, 100.f);
	if (CalmProgress >= 100.f)
	{
		// Mid-move calm DEFERS: a storm finishes its last thunder, then sits.
		// (Soothing mid-swing froze his pose — Adam's first soothe, June 12.)
		if (State == EHulkState::Telegraph || State == EHulkState::Attack
			|| State == EHulkState::Waking)
		{
			bSoothePending = true;
		}
		else
		{
			BecomeSoothed();
		}
	}
}

void ABramblehulk::BecomeSoothed()
{
	if (State == EHulkState::Soothed) { return; }
	bSoothePending = false;
	GetCharacterMovement()->StopMovementImmediately();
	GetCharacterMovement()->DisableMovement();
	if (SoothedAnim)
	{
		// The settle... and then he BREATHES. A soothed hill is alive — the
		// dormant sleep-cycle loops forever after the settle lands (a held
		// final frame reads as a freeze, never as peace).
		const float SettleSeconds = 1.4f;
		PlayOneShot(SoothedAnim, SettleSeconds);
		GetWorldTimerManager().SetTimer(SettleTimer, [this]()
		{
			PlayLoop(DormantAnim, 0.45f);
		}, SettleSeconds, false);
	}
	else
	{
		PlayLoop(DormantAnim, 0.45f);
	}
	// The bloom: the storm exhales, green.
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 100.f),
	                         MossGreen * 2.4f, 2.6f, 9000.f, 0.7f);
	ASparkImpactBurst::Burst(this, GetActorLocation() - FVector(0.f, 0.f, GetCapsuleComponent()->GetScaledCapsuleHalfHeight() - 16.f),
	                         MossGreen * 1.6f, 3.4f, 5000.f, 0.6f);
	if (MoodLight)
	{
		MoodLight->SetLightColor(FLinearColor(0.35f, 1.f, 0.4f));
		MoodLight->SetIntensity(2400.f);   // a soft green hearth, kept
	}
	EnterState(EHulkState::Soothed, 0.f);
	OnBramblehulkSoothed();
}

void ABramblehulk::DeliverRing(ASparkHeroCharacter* Hero, float Radius)
{
	const FVector Feet = GetActorLocation()
		- FVector(0.f, 0.f, GetCapsuleComponent()->GetScaledCapsuleHalfHeight() - 14.f);
	ASparkImpactBurst::Burst(this, Feet, StormAmber, Radius / 65.f, 8500.f, 0.45f);
	ASparkImpactBurst::Burst(this, Feet, FLinearColor(5.f, 3.f, 1.2f), 1.2f, 4200.f, 0.25f);
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
	{
		PC->ClientStartCameraShake(USparkBigLandShake::StaticClass());
	}
	if (Hero && Hero->GetCharacterMovement()->IsMovingOnGround()
		&& FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= Radius)
	{
		FVector Away = Hero->GetActorLocation() - GetActorLocation();
		Away.Z = 0.f;
		Away = Away.IsNearlyZero() ? GetActorForwardVector() : Away.GetSafeNormal();
		Hero->LaunchCharacter(Away * KnockbackForce + FVector(0.f, 0.f, KnockbackLift), true, true);
		Hero->TakeEmberHit(TantrumHitEmbers);
	}
}

void ABramblehulk::TickSoothe(float DeltaTime, ASparkHeroCharacter* Hero)
{
	// THE HEART OF HIM: the Spark Aura, held close, fills the calm meter.
	bool bBeingSoothed = false;
	if (Hero && Hero->IsAuraActive())
	{
		const float Reach = Hero->GetAuraRadius() + GetCapsuleComponent()->GetScaledCapsuleRadius();
		if (FVector::DistSquared(Hero->GetActorLocation(), GetActorLocation()) <= FMath::Square(Reach))
		{
			bBeingSoothed = true;
			const bool bDeepWindow = (State == EHulkState::Recover || State == EHulkState::Dormant);
			AddCalm(CalmPerSecond * (bDeepWindow ? CalmRecoverMultiplier : 1.f) * DeltaTime);
		}
	}
	if (!bBeingSoothed && State != EHulkState::Soothed)
	{
		CalmProgress = FMath::Max(0.f, CalmProgress - CalmDecayPerSecond * DeltaTime);
	}

	// Mercy made visible: green wisps drift off him while the light works,
	// and the mood lamp blends storm-amber toward moss-green with his calm.
	if (bBeingSoothed)
	{
		WispClock += DeltaTime;
		if (WispClock >= 0.4f)
		{
			WispClock = 0.f;
			const FVector Drift(FMath::FRandRange(-60.f, 60.f), FMath::FRandRange(-60.f, 60.f),
			                    FMath::FRandRange(30.f, 150.f));
			ASparkImpactBurst::Burst(this, GetActorLocation() + Drift, MossGreen, 0.5f, 1200.f, 0.45f);
		}
	}
	if (MoodLight && State != EHulkState::Soothed)
	{
		const float T = GetCalmFraction();
		MoodLight->SetLightColor(FMath::Lerp(FLinearColor(1.f, 0.45f, 0.1f), FLinearColor(0.35f, 1.f, 0.4f), T));
		MoodLight->SetIntensity(State == EHulkState::Dormant && T <= 0.f ? 0.f : 900.f + 1500.f * T);
	}
}

void ABramblehulk::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	ASparkHeroCharacter* Hero = ResolveHero();
	const float Dist = Hero ? FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) : 1e9f;

	TickSoothe(DeltaTime, Hero);
	if (State == EHulkState::Soothed) { return; }

	// A deferred soothe lands the moment the current move is spent.
	if (bSoothePending && State != EHulkState::Telegraph
		&& State != EHulkState::Attack && State != EHulkState::Waking)
	{
		BecomeSoothed();
		return;
	}

	// Solid-body law — a hill does not share its footprint.
	if (Hero)
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

	switch (State)
	{
	case EHulkState::Dormant:
		PlayLoop(DormantAnim, 0.6f);
		if (Dist <= WakeRadius) { Wake(); }
		break;

	case EHulkState::Waking:
		if (Hero) { FaceHero(Hero, DeltaTime); }
		if (Now() >= StateUntil) { EnterState(EHulkState::Approach, 0.f); }
		break;

	case EHulkState::Approach:
	{
		if (!Hero) { break; }
		if (Dist > ForgetRadius)
		{
			// The storm forgets: back to the moss, the rage fades.
			GetCharacterMovement()->StopMovementImmediately();
			EnterState(EHulkState::Dormant, 0.f);
			break;
		}
		FaceHero(Hero, DeltaTime);
		PlayLoop(WalkAnim, 0.9f);
		GetCharacterMovement()->MaxWalkSpeed = ApproachSpeed;
		AddMovementInput((Hero->GetActorLocation() - GetActorLocation()).GetSafeNormal2D());
		if (Dist <= AttackTriggerRange)
		{
			Move = (FMath::RandRange(0, 2) == 0) ? EHulkMove::QuakeSlam : EHulkMove::TantrumSlam;
			bRangThisAttack = false;
			GetCharacterMovement()->StopMovementImmediately();
			const float Tell = (Move == EHulkMove::QuakeSlam ? QuakeTell : SlamTell);
			if (Move == EHulkMove::QuakeSlam)
			{
				PlayOneShot(QuakeAnim ? QuakeAnim : SlamAnim, Tell + 0.5f + QuakeRecover * 0.4f, QuakeClipStart, QuakeClipRate);
			}
			else
			{
				PlayOneShot(SlamAnim, Tell + 0.4f + SlamRecover * 0.4f, SlamClipStart, SlamClipRate);
			}
			EnterState(EHulkState::Telegraph, Tell);
		}
		break;
	}

	case EHulkState::Telegraph:
		if (Hero) { FaceHero(Hero, DeltaTime * 0.5f); }   // slow tracking — mass is honest
		if (Now() >= StateUntil)
		{
			EnterState(EHulkState::Attack, 0.35f);
		}
		break;

	case EHulkState::Attack:
		if (!bRangThisAttack)
		{
			bRangThisAttack = true;
			DeliverRing(Hero, Move == EHulkMove::QuakeSlam ? QuakeRingRadius : SlamRingRadius);
		}
		if (Now() >= StateUntil)
		{
			EnterState(EHulkState::Recover,
			           Move == EHulkMove::QuakeSlam ? QuakeRecover : SlamRecover);
		}
		break;

	case EHulkState::Recover:
		PlayLoop(AlertAnim ? AlertAnim : DormantAnim, 0.9f);   // heaving, spent — soothe NOW
		if (Now() >= StateUntil)
		{
			Move = EHulkMove::None;
			EnterState(EHulkState::Approach, 0.f);
		}
		break;

	default:
		break;
	}
}
