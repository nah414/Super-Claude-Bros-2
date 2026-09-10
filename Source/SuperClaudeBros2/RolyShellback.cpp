// The Roly Shellback — he commits, and commitment is the whole design.

#include "RolyShellback.h"

#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "SparkHeroCharacter.h"
#include "SparkImpactBurst.h"
#include "UObject/ConstructorHelpers.h"

ARolyShellback::ARolyShellback()
{
	PrimaryActorTick.bCanEverTick = true;

	GetCapsuleComponent()->SetCapsuleSize(40.f, 36.f);   // a low ball
	GetCapsuleComponent()->OnComponentHit.AddDynamic(this, &ARolyShellback::OnCapsuleHit);
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);

	GetCharacterMovement()->bOrientRotationToMovement = false;
	GetCharacterMovement()->MaxWalkSpeed = RollSpeed;
	GetCharacterMovement()->GravityScale = 1.9f;
	AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;

	VisualRoot = CreateDefaultSubobject<USceneComponent>(TEXT("VisualRoot"));
	VisualRoot->SetupAttachment(RootComponent);

	ShellMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ShellMesh"));
	ShellMesh->SetupAttachment(VisualRoot);
	ShellMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	ContactProfile.MassClass = EMassClass::Mote;
	ContactProfile.bStompImmune = false;
	ContactProfile.bDashImmune = false;
	ContactProfile.ContactDamageEmbers = ContactChipEmbers;

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Model(TEXT("/Game/Art/Roster/roly_shellback/SM_roly_shellback.SM_roly_shellback"));
	if (Model.Succeeded())
	{
		ShellMesh->SetStaticMesh(Model.Object);
		bHasModel = true;
	}
	else
	{
		static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
		if (Sphere.Succeeded()) { ShellMesh->SetStaticMesh(Sphere.Object); }
	}
}

void ARolyShellback::BeginPlay()
{
	Super::BeginPlay();
	ShellMesh->SetRelativeLocation(FVector(0.f, 0.f, -GetCapsuleComponent()->GetScaledCapsuleHalfHeight()));
	ShellMesh->SetRelativeRotation(FRotator(0.f, MeshYaw, 0.f));
	ShellMesh->SetRelativeScale3D(FVector(BodyScale));
}

ASparkHeroCharacter* ARolyShellback::ResolveHero() const
{
	return Cast<ASparkHeroCharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
}

float ARolyShellback::Now() const
{
	return GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
}

void ARolyShellback::EnterState(EShellState NewState, float Duration)
{
	State = NewState;
	StateUntil = Now() + Duration;
}

void ARolyShellback::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (State == EShellState::Dead) { return; }

	ASparkHeroCharacter* Hero = ResolveHero();
	const float Dist = Hero ? FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) : 1e9f;

	switch (State)
	{
	case EShellState::Idle:
		GetCharacterMovement()->StopMovementImmediately();
		if (Hero && Dist <= AggroRadius && Now() >= NextRollTime)
		{
			EnterState(EShellState::Wind, WindSeconds);
		}
		break;

	case EShellState::Wind:
		// Lock onto the hero while winding — the LAST chance to aim is now.
		if (Hero)
		{
			const FVector To = (Hero->GetActorLocation() - GetActorLocation()).GetSafeNormal2D();
			SetActorRotation(FMath::RInterpTo(GetActorRotation(),
				FRotator(0.f, To.Rotation().Yaw, 0.f), DeltaSeconds, 8.f));
		}
		// a little curl-bounce tell
		ShellMesh->SetRelativeScale3D(FVector(BodyScale * (1.f + 0.12f * FMath::Sin(Now() * 26.f))));
		if (Now() >= StateUntil)
		{
			// COMMIT: the direction LOCKS here and never changes (the cannonball law).
			RollDir = Hero ? (Hero->GetActorLocation() - GetActorLocation()).GetSafeNormal2D()
			               : GetActorForwardVector();
			ShellMesh->SetRelativeScale3D(FVector(BodyScale));
			ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 20.f),
			                         FLinearColor(2.f, 1.4f, 0.7f), 0.7f, 1600.f, 0.2f);
			EnterState(EShellState::Roll, RollSeconds);
		}
		break;

	case EShellState::Roll:
		GetCharacterMovement()->MaxWalkSpeed = RollSpeed;
		AddMovementInput(RollDir);   // committed — RollDir is never recomputed
		ShellMesh->AddLocalRotation(FRotator(SpinRate * DeltaSeconds, 0.f, 0.f));   // visual roll
		if (Now() >= StateUntil)
		{
			EnterState(EShellState::Recover, RecoverSeconds);
		}
		break;

	case EShellState::Recover:
		GetCharacterMovement()->StopMovementImmediately();
		if (bFlipped)
		{
			// belly-up, legs waggling — the soft, open, vulnerable window
			ShellMesh->SetRelativeRotation(FRotator(180.f, MeshYaw, 12.f * FMath::Sin(Now() * 16.f)));
		}
		else
		{
			// a dizzy wobble
			ShellMesh->SetRelativeRotation(FRotator(0.f, MeshYaw + 8.f * FMath::Sin(Now() * 14.f), 0.f));
		}
		if (Now() >= StateUntil)
		{
			NextRollTime = Now() + RollCooldown;
			bFlipped = false;
			ShellMesh->SetRelativeRotation(FRotator(0.f, MeshYaw, 0.f));   // rights itself
			EnterState(EShellState::Idle, 0.f);
		}
		break;

	default: break;
	}
}

void ARolyShellback::OnCapsuleHit(UPrimitiveComponent*, AActor* OtherActor,
                                  UPrimitiveComponent*, FVector, const FHitResult&)
{
	if (State == EShellState::Dead) { return; }
	ASparkHeroCharacter* Hero = Cast<ASparkHeroCharacter>(OtherActor);
	if (!Hero) { return; }

	// Stomp: a falling hero from above pops the shell (Mote ladder).
	const bool bAbove = Hero->GetActorLocation().Z
		> GetActorLocation().Z + GetCapsuleComponent()->GetScaledCapsuleHalfHeight() * 0.4f;
	if (bAbove && Hero->GetRecentFallSpeed() < StompVelocityThreshold)
	{
		Hero->LaunchCharacter(FVector(0.f, 0.f, StompBounce), false, true);
		ReceiveDefeatHit(true);   // a boss-shell flips instead of popping
		return;
	}

	// Rolling into the hero is the cannonball's bite; otherwise just a nudge.
	FVector Away = Hero->GetActorLocation() - GetActorLocation();
	Away.Z = 0.f;
	Away = Away.IsNearlyZero() ? GetActorForwardVector() : Away.GetSafeNormal();
	if (State == EShellState::Roll)
	{
		Hero->LaunchCharacter(Away * KnockbackForce + FVector(0.f, 0.f, KnockbackLift), true, true);
		Hero->TakeEmberHit(ContactChipEmbers);
		ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 25.f),
		                         FLinearColor(2.4f, 1.2f, 0.4f), 0.9f, 2400.f);
	}
	else
	{
		Hero->LaunchCharacter(Away * 260.f + FVector(0.f, 0.f, 160.f), true, true);
	}
}

void ARolyShellback::TakeStrike()
{
	if (State != EShellState::Dead) { ReceiveDefeatHit(false); }
}

void ARolyShellback::ReceiveDefeatHit(bool bByStomp)
{
	if (State == EShellState::Dead) { return; }
	if (--HitsToDefeat <= 0)
	{
		Die(bByStomp);
		return;
	}
	// A boss-shell SURVIVES — it flips belly-up, soft and open: stomp it again.
	GetCharacterMovement()->StopMovementImmediately();
	bFlipped = true;
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 30.f),
	                         FLinearColor(2.4f, 1.6f, 0.6f), 1.2f, 3200.f, 0.22f);
	EnterState(EShellState::Recover, FlipRecoverSeconds);
}

void ARolyShellback::TakeStagger(float Seconds)
{
	if (State == EShellState::Dead) { return; }
	// A power pulse dazzles him into an early dizzy recovery.
	GetCharacterMovement()->StopMovementImmediately();
	EnterState(EShellState::Recover, FMath::Max(Seconds, RecoverSeconds));
}

void ARolyShellback::Die(bool bByStomp)
{
	State = EShellState::Dead;
	GetCharacterMovement()->StopMovementImmediately();
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 20.f),
	                         FLinearColor(2.6f, 1.5f, 0.6f), 1.1f, 3000.f, 0.25f);
	OnShellbackPopped(bByStomp);
	SetLifeSpan(0.35f);
}
