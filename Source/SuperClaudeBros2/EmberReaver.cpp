// The Ember Reaver â€” duel framework, second voice. Same proven skeleton as the
// Kraken (concrete on purpose; base extraction at rival #3), different soul:
// speed instead of mass, fire instead of grip, geometry instead of patterns.

#include "EmberReaver.h"

#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "EmberMeterComponent.h"
#include "EmberTrailPatch.h"
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
	const FLinearColor ReaverEmber(3.0f, 0.42f, 0.1f);   // crimson fire, his own voice

	UAnimSequence* ReaverClip(const ConstructorHelpers::FObjectFinder<UAnimSequence>& Finder)
	{
		return Finder.Succeeded() ? Finder.Object.Get() : nullptr;
	}
}

AEmberReaver::AEmberReaver()
{
	PrimaryActorTick.bCanEverTick = true;

	GetCapsuleComponent()->SetCapsuleSize(42.f, 72.f);   // slender duelist, visual-true
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);

	GetCharacterMovement()->bOrientRotationToMovement = false;
	GetCharacterMovement()->MaxWalkSpeed = ApproachSpeed;
	GetCharacterMovement()->GravityScale = 1.9f;
	AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;

	VisualRoot = CreateDefaultSubobject<USceneComponent>(TEXT("VisualRoot"));
	VisualRoot->SetupAttachment(RootComponent);

	ReaverBody = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("ReaverBody"));
	ReaverBody->SetupAttachment(VisualRoot);
	ReaverBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	ReaverBody->SetAnimationMode(EAnimationMode::AnimationSingleNode);
	ReaverBody->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;   // LOAD LAW

	PlaceholderBody = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PlaceholderBody"));
	PlaceholderBody->SetupAttachment(VisualRoot);
	PlaceholderBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	DuelMeter = CreateDefaultSubobject<UEmberMeterComponent>(TEXT("DuelMeter"));
	DuelMeter->GraceDuration = 0.05f;   // every combo beat counts in a duel

	TelegraphLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("TelegraphLight"));
	TelegraphLight->SetupAttachment(VisualRoot);
	TelegraphLight->SetRelativeLocation(FVector(0.f, 0.f, 45.f));
	TelegraphLight->SetAttenuationRadius(620.f);
	TelegraphLight->SetCastShadows(false);
	TelegraphLight->SetIntensity(0.f);
	TelegraphLight->SetLightColor(FLinearColor(1.f, 0.3f, 0.08f));

	ContactProfile.MassClass = EMassClass::Champion;
	ContactProfile.bStompImmune = true;
	ContactProfile.bDashImmune = true;
	ContactProfile.ContactDamageEmbers = 20.f;
	ContactProfile.BlindSideConeHalfAngle = 55.f;

	static ConstructorHelpers::FObjectFinder<USkeletalMesh> Model(TEXT("/Game/Art/ReaverSkelV1/SCB2Reaver.SCB2Reaver"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FIdle(TEXT("/Game/Art/ReaverSkelV1/A_Reaver_Idle_Anim.A_Reaver_Idle_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FRun(TEXT("/Game/Art/ReaverSkelV1/A_Reaver_Run_Anim.A_Reaver_Run_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FSlash(TEXT("/Game/Art/ReaverSkelV1/A_Reaver_Slash_Anim.A_Reaver_Slash_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FDash(TEXT("/Game/Art/ReaverSkelV1/A_Reaver_Dash_Anim.A_Reaver_Dash_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FFlurry(TEXT("/Game/Art/ReaverSkelV1/A_Reaver_Flurry_Anim.A_Reaver_Flurry_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FStagger(TEXT("/Game/Art/ReaverSkelV1/A_Reaver_Stagger_Anim.A_Reaver_Stagger_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FHit(TEXT("/Game/Art/ReaverSkelV1/A_Reaver_HitReact_Anim.A_Reaver_HitReact_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FDefeat(TEXT("/Game/Art/ReaverSkelV1/A_Reaver_Defeat_Anim.A_Reaver_Defeat_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FTaunt(TEXT("/Game/Art/ReaverSkelV1/A_Reaver_Taunt_Anim.A_Reaver_Taunt_Anim"));
	static ConstructorHelpers::FObjectFinder<UAnimSequence> FCrescent(TEXT("/Game/Art/ReaverSkelV1/A_Reaver_Crescent_Anim.A_Reaver_Crescent_Anim"));

	if (Model.Succeeded())
	{
		ReaverBody->SetSkeletalMesh(Model.Object);
		bHasSkeletalModel = true;
		PlaceholderBody->SetVisibility(false);
	}
	else
	{
		static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
		if (Sphere.Succeeded())
		{
			PlaceholderBody->SetStaticMesh(Sphere.Object);
			PlaceholderBody->SetRelativeScale3D(FVector(1.1f, 1.1f, 2.6f));
		}
	}
	IdleAnim = ReaverClip(FIdle);
	RunAnim = ReaverClip(FRun);
	SlashAnim = ReaverClip(FSlash);
	DashAnim = ReaverClip(FDash);
	FlurryAnim = ReaverClip(FFlurry);
	StaggerAnim = ReaverClip(FStagger);
	HitReactAnim = ReaverClip(FHit);
	DefeatAnim = ReaverClip(FDefeat);
	TauntAnim = ReaverClip(FTaunt);
	CrescentAnim = ReaverClip(FCrescent);
}

void AEmberReaver::BeginPlay()
{
	Super::BeginPlay();
	if (bHasSkeletalModel)
	{
		ReaverBody->SetRelativeLocation(FVector(0.f, 0.f, -GetCapsuleComponent()->GetScaledCapsuleHalfHeight()));
		ReaverBody->SetRelativeRotation(FRotator(0.f, SkelMeshYaw, 0.f));
		ReaverBody->SetRelativeScale3D(FVector(SkelMeshScale));
	}
	if (DuelMeter)
	{
		DuelMeter->OnFlameOut.AddDynamic(this, &AEmberReaver::HandleDuelMeterEmpty);
	}
	PlayLoop(IdleAnim);
}

ASparkHeroCharacter* AEmberReaver::ResolveHero() const
{
	return Cast<ASparkHeroCharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
}

float AEmberReaver::Now() const
{
	return GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
}

void AEmberReaver::PlayLoop(UAnimSequence* Clip, float Rate)
{
	if (!bHasSkeletalModel || !Clip || !ReaverBody) { return; }
	if (CurrentLoop == Clip) { ReaverBody->SetPlayRate(Rate); return; }
	CurrentLoop = Clip;
	ReaverBody->PlayAnimation(Clip, true);
	ReaverBody->SetPlayRate(Rate);
}

void AEmberReaver::PlayOneShot(UAnimSequence* Clip, float FitSeconds, float StartFraction, float OverrideRate)
{
	if (!bHasSkeletalModel || !Clip || !ReaverBody) { return; }
	CurrentLoop = nullptr;
	ReaverBody->PlayAnimation(Clip, false);
	const float Rate = (OverrideRate > 0.f)
		? OverrideRate
		: Clip->GetPlayLength() * (1.f - StartFraction) / FMath::Max(FitSeconds, 0.05f);
	ReaverBody->SetPlayRate(FMath::Clamp(Rate, 0.3f, 5.f));
	if (StartFraction > 0.f)
	{
		ReaverBody->SetPosition(Clip->GetPlayLength() * StartFraction, false);
	}
}

void AEmberReaver::EnterState(EReaverState NewState, float Duration)
{
	State = NewState;
	StateUntil = Now() + Duration;
}

void AEmberReaver::FaceHero(const ASparkHeroCharacter* Hero, float DeltaTime)
{
	if (!Hero) { return; }
	const FVector To = Hero->GetActorLocation() - GetActorLocation();
	const FRotator Want(0.f, To.Rotation().Yaw, 0.f);
	SetActorRotation(FMath::RInterpTo(GetActorRotation(), Want, DeltaTime, TurnRate));
}

void AEmberReaver::SelectMove(float DistToHero)
{
	// Phase rotation: the dash is his SIGNATURE â€” it debuts in phase 1 (villains
	// own their full kit from the first bell; phases change pressure, not kit).
	TArray<EReaverMove> Pool = { EReaverMove::FeintSlash, EReaverMove::EmberDash };
	if (Phase >= 2) { Pool.Add(EReaverMove::CrossingFlurry); }
	if (Phase >= 2 && CrescentAnim) { Pool.Add(EReaverMove::CinderCrescent); }
	if (Phase >= 3) { Pool.Add(EReaverMove::EmberDash); }   // double weight: fire everywhere
	EReaverMove Picked = Pool[FMath::RandRange(0, Pool.Num() - 1)];
	if (Picked == Move && Pool.Num() > 1)
	{
		Picked = Pool[(Pool.Find(Picked) + 1) % Pool.Num()];
	}
	Move = Picked;
}

void AEmberReaver::StartTelegraph()
{
	bHitThisAttack = false;
	FlurryHitsDone = 0;
	DashesThisAttack = 0;
	GetCharacterMovement()->StopMovementImmediately();

	float Tell = SlashTell;
	if (Move == EReaverMove::CrossingFlurry) { Tell = FlurryTell; }
	else if (Move == EReaverMove::EmberDash) { Tell = DashTell; }
	else if (Move == EReaverMove::CinderCrescent) { Tell = CrescentTell; }
	Tell *= TellScale();

	switch (Move)
	{
	case EReaverMove::FeintSlash:
		PlayOneShot(SlashAnim, Tell + SlashActive + SlashRecover * 0.4f, SlashClipStart, SlashClipRate);
		break;
	case EReaverMove::CinderCrescent:
		PlayOneShot(CrescentAnim, Tell + CrescentActive + 0.3f, 0.f, CrescentClipRate);
		break;
	case EReaverMove::CrossingFlurry:
		PlayOneShot(FlurryAnim, Tell + FlurryActive + FlurryRecover * 0.4f, FlurryClipStart, FlurryClipRate);
		break;
	case EReaverMove::EmberDash:
		PlayOneShot(DashAnim, Tell + DashMaxSeconds + 0.3f, DashClipStart, DashClipRate);
		break;
	default: break;
	}
	EnterState(EReaverState::Telegraph, Tell);
}

void AEmberReaver::StartDashLeg(const ASparkHeroCharacter* Hero)
{
	// He crosses THROUGH where you stand â€” the dodge is to move, the lesson is
	// that where he ran is now on fire.
	FVector Target = Hero
		? Hero->GetActorLocation() + (Hero->GetActorLocation() - GetActorLocation()).GetSafeNormal2D() * 260.f
		: GetActorLocation() + GetActorForwardVector() * 600.f;
	FVector Dir = Target - GetActorLocation();
	Dir.Z = 0.f;
	const float Dist = FMath::Max(Dir.Size(), 50.f);
	DashDirection = Dir / Dist;
	DashUntil = Now() + FMath::Min(Dist / DashSpeed, DashMaxSeconds);
	LastTrailPos = GetActorLocation();
	++DashesThisAttack;
}

void AEmberReaver::StartAttack()
{
	ASparkHeroCharacter* Hero = ResolveHero();
	if (TelegraphLight) { TelegraphLight->SetIntensity(0.f); }
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 30.f),
	                         ReaverEmber * 2.4f, 1.1f, 4000.f, 0.2f);

	switch (Move)
	{
	case EReaverMove::FeintSlash:
		EnterState(EReaverState::Attack, SlashActive);
		break;
	case EReaverMove::CrossingFlurry:
		EnterState(EReaverState::Attack, FlurryActive);
		break;
	case EReaverMove::CinderCrescent:
	{
		// The rising arc: he leaps INTO you — the apex kick hits airborne
		// heroes too, and his landing line catches fire.
		FVector Fwd = Hero ? (Hero->GetActorLocation() - GetActorLocation()).GetSafeNormal2D()
		                   : GetActorForwardVector();
		LaunchCharacter(Fwd * 320.f + FVector(0.f, 0.f, 520.f), true, true);
		EnterState(EReaverState::Attack, CrescentActive);
		break;
	}
	case EReaverMove::EmberDash:
		StartDashLeg(Hero);
		EnterState(EReaverState::Attack, DashMaxSeconds * (Phase >= 2 ? 2.3f : 1.1f));
		break;
	default:
		FinishAttack(SlashRecover);
		break;
	}
}

void AEmberReaver::FinishAttack(float RecoverSeconds)
{
	GetCharacterMovement()->StopMovementImmediately();
	if (TelegraphLight) { TelegraphLight->SetIntensity(0.f); }
	EnterState(EReaverState::Recover, RecoverSeconds);
}

void AEmberReaver::LandDuelHit(ASparkHeroCharacter* Hero, float Embers)
{
	if (!Hero) { return; }
	FVector Away = Hero->GetActorLocation() - GetActorLocation();
	Away.Z = 0.f;
	Away = Away.IsNearlyZero() ? GetActorForwardVector() : Away.GetSafeNormal();
	Hero->LaunchCharacter(Away * KnockbackForce + FVector(0.f, 0.f, KnockbackLift), true, true);
	Hero->TakeEmberHit(Embers);
	ASparkImpactBurst::Burst(this,
		(Hero->GetActorLocation() + GetActorLocation()) * 0.5f + FVector(0.f, 0.f, 40.f),
		ReaverEmber * 3.f, 1.15f, 4800.f);
}

void AEmberReaver::TickAttack(float DeltaTime, ASparkHeroCharacter* Hero)
{
	switch (Move)
	{
	case EReaverMove::FeintSlash:
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

	case EReaverMove::CrossingFlurry:
	{
		// A pressure string: he steps INTO you, two bites across the window.
		if (Hero)
		{
			FaceHero(Hero, DeltaTime * 0.6f);
			AddMovementInput((Hero->GetActorLocation() - GetActorLocation()).GetSafeNormal2D(),
			                 FlurryStepSpeed / FMath::Max(ApproachSpeed, 1.f));
			const float Elapsed = FlurryActive - (StateUntil - Now());
			const float Marks[2] = { FlurryActive * 0.3f, FlurryActive * 0.75f };
			if (FlurryHitsDone < 2 && Elapsed >= Marks[FlurryHitsDone])
			{
				++FlurryHitsDone;
				const FVector To = Hero->GetActorLocation() - GetActorLocation();
				if (FVector::DotProduct(To.GetSafeNormal2D(), GetActorForwardVector()) > 0.1f
					&& To.Size() <= FlurryReach)
				{
					LandDuelHit(Hero, DuelHitEmbers * 0.6f);
				}
			}
		}
		break;
	}

	case EReaverMove::CinderCrescent:
		if (Hero && !bHitThisAttack
			&& FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= CrescentReach)
		{
			bHitThisAttack = true;
			LandDuelHit(Hero, DuelHitEmbers);
		}
		// The apex line ignites beneath him as he comes down.
		if (GetCharacterMovement()->IsMovingOnGround() && DashesThisAttack == 0)
		{
			++DashesThisAttack;   // reuse as a one-shot latch for the landing fire
			const FVector Feet = GetActorLocation()
				- FVector(0.f, 0.f, GetCapsuleComponent()->GetScaledCapsuleHalfHeight() - 6.f);
			AEmberTrailPatch::Plant(this, Feet);
			AEmberTrailPatch::Plant(this, Feet + GetActorForwardVector() * 110.f);
		}
		break;

	case EReaverMove::EmberDash:
	{
		if (Now() < DashUntil)
		{
			GetCharacterMovement()->Velocity =
				FVector(DashDirection.X, DashDirection.Y, 0.f) * DashSpeed
				+ FVector(0.f, 0.f, GetCharacterMovement()->Velocity.Z);
			SetActorRotation(FRotator(0.f, DashDirection.Rotation().Yaw, 0.f));

			// THE SIGNATURE SHOWS: the floor ignites behind him.
			if (FVector::DistSquared2D(GetActorLocation(), LastTrailPos) >= FMath::Square(TrailSpacing))
			{
				LastTrailPos = GetActorLocation();
				AEmberTrailPatch::Plant(this, GetActorLocation()
					- FVector(0.f, 0.f, GetCapsuleComponent()->GetScaledCapsuleHalfHeight() - 6.f));
			}
			if (Hero && !bHitThisAttack
				&& FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= DashHitRange)
			{
				bHitThisAttack = true;
				LandDuelHit(Hero, DuelHitEmbers * 0.5f);   // the dash grazes; the FIRE is the threat
			}
		}
		else if (Phase >= 2 && DashesThisAttack < 2 && Now() < StateUntil - DashMaxSeconds * 0.4f)
		{
			bHitThisAttack = false;
			StartDashLeg(Hero);   // phase 2+: the second leg crosses the first â€” an L of fire
		}
		else
		{
			FinishAttack(DashRecover);
		}
		break;
	}
	default: break;
	}
}

void AEmberReaver::TakeStrike(int32 InComboBeat, bool bCharged)
{
	if (State == EReaverState::Defeated || !DuelMeter) { return; }
	float Embers = (bCharged || InComboBeat >= 2) ? HeavyStrikeEmbers : LightStrikeEmbers;

	// THE ONE-EYE RULE: strikes from inside the blind cone bite 1.5x. Geometry,
	// not stats â€” the duel rewards the player who learns to circle.
	if (ASparkHeroCharacter* Hero = ResolveHero())
	{
		const FVector ToHero = (Hero->GetActorLocation() - GetActorLocation()).GetSafeNormal2D();
		const float CosAngle = FVector::DotProduct(-GetActorForwardVector(), ToHero);
		if (CosAngle > FMath::Cos(FMath::DegreesToRadians(BlindConeHalfAngleDeg)))
		{
			Embers *= BlindSideMultiplier;
			ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 70.f),
			                         FLinearColor(5.f, 2.2f, 0.6f), 1.0f, 3600.f);   // the deep-cut flash
		}
	}
	DuelMeter->ApplyEmberDamage(Embers);

	const float Frac = DuelMeter->GetFraction();
	const int32 NewPhase = Frac <= Phase3Fraction ? 3 : (Frac <= Phase2Fraction ? 2 : 1);
	if (NewPhase > Phase)
	{
		Phase = NewPhase;
		OnReaverPhaseChanged(Phase);
		if (State != EReaverState::Staggered)
		{
			PlayOneShot(TauntAnim ? TauntAnim : HitReactAnim, 1.0f);
			EnterState(EReaverState::Recover, 1.0f);
		}
	}
	else if (bCharged)
	{
		TakeStagger(StaggerSeconds);
	}
	else if (State == EReaverState::Waiting || State == EReaverState::Recover
	         || State == EReaverState::Approach)
	{
		PlayOneShot(HitReactAnim, 0.45f);
		if (State != EReaverState::Recover) { EnterState(EReaverState::Recover, 0.45f); }
	}
}

void AEmberReaver::TakeStagger(float Seconds)
{
	if (State == EReaverState::Defeated) { return; }
	if (TelegraphLight) { TelegraphLight->SetIntensity(0.f); }
	GetCharacterMovement()->StopMovementImmediately();
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 55.f),
	                         FLinearColor(5.f, 2.5f, 0.8f), 1.3f, 5200.f);
	PlayOneShot(StaggerAnim ? StaggerAnim : HitReactAnim, Seconds);
	EnterState(EReaverState::Staggered, Seconds);
}

void AEmberReaver::HandleDuelMeterEmpty()
{
	if (State == EReaverState::Defeated) { return; }
	if (TelegraphLight) { TelegraphLight->SetIntensity(0.f); }
	GetCharacterMovement()->StopMovementImmediately();
	GetCharacterMovement()->DisableMovement();
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
	if (DefeatAnim) { PlayOneShot(DefeatAnim, DefeatAnim->GetPlayLength()); }
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 50.f),
	                         ReaverEmber * 3.2f, 1.9f, 7000.f, 0.55f);
	EnterState(EReaverState::Defeated, 0.f);
	OnReaverDefeated();
}

void AEmberReaver::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
	if (State == EReaverState::Defeated) { return; }

	ASparkHeroCharacter* Hero = ResolveHero();
	const float Dist = Hero ? FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) : 1e9f;

	// Solid-body law: nobody stands inside the duelist.
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

	if (State != EReaverState::Waiting && Dist > DisengageRadius)
	{
		DuelMeter->RefillFull();
		Phase = 1;
		GetCharacterMovement()->StopMovementImmediately();
		PlayLoop(IdleAnim);
		State = EReaverState::Waiting;
		return;
	}

	switch (State)
	{
	case EReaverState::Waiting:
		PlayLoop(IdleAnim);
		if (Hero) { FaceHero(Hero, DeltaTime * 0.5f); }
		if (Dist <= DuelStartRadius)
		{
			PlayOneShot(TauntAnim ? TauntAnim : IdleAnim, 1.6f);
			EnterState(EReaverState::Intro, 1.6f);
		}
		break;

	case EReaverState::Intro:
		if (Hero) { FaceHero(Hero, DeltaTime); }
		if (Now() >= StateUntil) { EnterState(EReaverState::Approach, 0.f); }
		break;

	case EReaverState::Approach:
	{
		if (!Hero) { break; }
		FaceHero(Hero, DeltaTime);
		PlayLoop(RunAnim ? RunAnim : IdleAnim, 1.1f);
		GetCharacterMovement()->MaxWalkSpeed = ApproachSpeed;
		AddMovementInput((Hero->GetActorLocation() - GetActorLocation()).GetSafeNormal2D());

		if (Move == EReaverMove::None) { SelectMove(Dist); }
		const float TriggerRange =
			Move == EReaverMove::EmberDash ? 620.f :
			Move == EReaverMove::CrossingFlurry ? FlurryReach * 0.9f : SlashReach * 0.85f;
		if (Dist <= TriggerRange) { StartTelegraph(); }
		break;
	}

	case EReaverState::Telegraph:
		if (Hero) { FaceHero(Hero, DeltaTime); }
		if (TelegraphLight)
		{
			const float Pulse = 0.55f + 0.45f * FMath::Sin(Now() * 22.f);   // faster pulse â€” faster danger
			TelegraphLight->SetIntensity(5800.f * Pulse);
		}
		if (Now() >= StateUntil) { StartAttack(); }
		break;

	case EReaverState::Attack:
		TickAttack(DeltaTime, Hero);
		if (State == EReaverState::Attack && Now() >= StateUntil)
		{
			float Recover = SlashRecover;
			if (Move == EReaverMove::CrossingFlurry) { Recover = FlurryRecover; }
			else if (Move == EReaverMove::EmberDash) { Recover = DashRecover; }
			else if (Move == EReaverMove::CinderCrescent) { Recover = CrescentRecover; }
			FinishAttack(Recover);
		}
		break;

	case EReaverState::Recover:
		if (Now() >= StateUntil)
		{
			Move = EReaverMove::None;
			EnterState(EReaverState::Approach, 0.f);
		}
		break;

	case EReaverState::Staggered:
		if (Now() >= StateUntil)
		{
			Move = EReaverMove::None;
			EnterState(EReaverState::Approach, 0.f);
		}
		break;

	default:
		break;
	}
}


float AEmberReaver::GetDuelFraction() const
{
	return DuelMeter ? DuelMeter->GetFraction() : 1.f;
}
