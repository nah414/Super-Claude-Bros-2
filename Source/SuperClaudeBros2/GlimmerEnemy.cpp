#include "GlimmerEnemy.h"

#include "CollisionQueryParams.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/HitResult.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "SparkHeroCharacter.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h"

AGlimmerEnemy::AGlimmerEnemy()
{
	PrimaryActorTick.bCanEverTick = true;

	// --- Collision capsule: a squat little shadow ---
	GetCapsuleComponent()->InitCapsuleSize(34.f, 40.f);
	GetCapsuleComponent()->OnComponentHit.AddDynamic(this, &AGlimmerEnemy::OnCapsuleHit);
	GetCapsuleComponent()->OnComponentBeginOverlap.AddDynamic(this, &AGlimmerEnemy::OnCapsuleOverlap);

	// --- Patrol rotation is flipped directly in SenseAndTurn(), never controller-steered ---
	bUseControllerRotationYaw = false;
	bUseControllerRotationPitch = false;
	bUseControllerRotationRoll = false;

	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->bOrientRotationToMovement = false; // SenseAndTurn() owns the yaw
	Move->bUseControllerDesiredRotation = false;
	Move->MaxWalkSpeed = PatrolSpeed;
	Move->MaxAcceleration = 1400.f;
	Move->BrakingDecelerationWalking = 1600.f;
	Move->GroundFriction = 8.f;
	Move->GravityScale = 1.9f; // match the hero's world feel

	// AI possession so AddMovementInput actually moves an enemy placed in a level.
	AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;

	// --- Visual root so the death-squash never touches collision ---
	VisualRoot = CreateDefaultSubobject<USceneComponent>(TEXT("VisualRoot"));
	VisualRoot->SetupAttachment(RootComponent);

	// Placeholder Glimmer from engine primitives: one ink sphere + two cream eyes.
	// (UE 5.7 ships no Capsule in /Engine/BasicShapes — only Cone/Cube/Cylinder/Plane/Sphere.)
	// The real procedural-modeled Glimmer (glTF) replaces these meshes later.
	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));

	BodyMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BodyMesh"));
	BodyMesh->SetupAttachment(VisualRoot);
	BodyMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (SphereMesh.Succeeded())
	{
		BodyMesh->SetStaticMesh(SphereMesh.Object);
	}
	BodyMesh->SetRelativeScale3D(FVector(0.8f));

	LeftEye = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("LeftEye"));
	LeftEye->SetupAttachment(VisualRoot);
	LeftEye->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (SphereMesh.Succeeded())
	{
		LeftEye->SetStaticMesh(SphereMesh.Object);
	}
	LeftEye->SetRelativeScale3D(FVector(0.14f));
	LeftEye->SetRelativeLocation(FVector(36.f, -14.f, 10.f));

	RightEye = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("RightEye"));
	RightEye->SetupAttachment(VisualRoot);
	RightEye->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (SphereMesh.Succeeded())
	{
		RightEye->SetStaticMesh(SphereMesh.Object);
	}
	RightEye->SetRelativeScale3D(FVector(0.14f));
	RightEye->SetRelativeLocation(FVector(36.f, 14.f, 10.f));
}

float AGlimmerEnemy::Now() const
{
	return GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
}

void AGlimmerEnemy::BeginPlay()
{
	Super::BeginPlay();

	GetCharacterMovement()->MaxWalkSpeed = PatrolSpeed;

	// Tint the placeholder in the night palette: ink body, cream eyes. The sphere
	// asset's default slot is the grid material (no Color param), so explicitly base
	// our dynamic materials on the engine's tintable BasicShapeMaterial.
	const FLinearColor Ink(0.078f, 0.078f, 0.075f);   // #141413
	const FLinearColor Cream(0.980f, 0.976f, 0.961f); // #faf9f5
	if (UMaterialInterface* BaseMat = LoadObject<UMaterialInterface>(
			nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")))
	{
		if (BodyMesh)
		{
			UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(BaseMat, this);
			MID->SetVectorParameterValue(TEXT("Color"), Ink);
			BodyMesh->SetMaterial(0, MID);
		}
		if (LeftEye)
		{
			UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(BaseMat, this);
			MID->SetVectorParameterValue(TEXT("Color"), Cream);
			LeftEye->SetMaterial(0, MID);
		}
		if (RightEye)
		{
			UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(BaseMat, this);
			MID->SetVectorParameterValue(TEXT("Color"), Cream);
			RightEye->SetMaterial(0, MID);
		}
	}

	// Cache the hero once for the per-frame proximity backstop (capsule hit/overlap
	// events are the primary contact path; the radius check is the safety net).
	CachedHero = Cast<ASparkHeroCharacter>(
		UGameplayStatics::GetActorOfClass(GetWorld(), ASparkHeroCharacter::StaticClass()));
}

// ---------------------------------------------------------------------------
// Per-frame: contact backstop, stun wait, patrol
// ---------------------------------------------------------------------------
void AGlimmerEnemy::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (bDead) { return; }

	// Keep live-tuned values flowing into the movement component (editor tuning).
	GetCharacterMovement()->MaxWalkSpeed = PatrolSpeed;

	// Generous contact backstop: hit/overlap events do the heavy lifting, but a
	// plain radius check means a hero pressed flush against us never slips through.
	if (ASparkHeroCharacter* Hero = CachedHero.Get())
	{
		const float RadiusSum = GetCapsuleComponent()->GetScaledCapsuleRadius()
			+ Hero->GetCapsuleComponent()->GetScaledCapsuleRadius() + 20.f;
		const float HeightSum = GetCapsuleComponent()->GetScaledCapsuleHalfHeight()
			+ Hero->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 25.f;
		const FVector ToHero = Hero->GetActorLocation() - GetActorLocation();
		if (FMath::Abs(ToHero.Z) <= HeightSum && ToHero.Size2D() <= RadiusSum)
		{
			HandleHeroContact(Hero);
		}
	}
	if (bDead) { return; } // contact may have squashed us this frame

	// Stunned after a bonk: stand still and let the hero get clear.
	if (Now() < StunnedUntilTime) { return; }

	// Patrol: walk the platform, turning back at walls and ledges.
	if (GetCharacterMovement()->IsMovingOnGround())
	{
		SenseAndTurn();
	}
	AddMovementInput(GetActorForwardVector());
}

// ---------------------------------------------------------------------------
// Patrol senses: a wall poke ahead + a ledge probe down past the leading edge
// ---------------------------------------------------------------------------
void AGlimmerEnemy::SenseAndTurn()
{
	// A short cooldown so one turn can't re-trigger while we're still settling.
	if ((Now() - LastTurnTime) < 0.25f) { return; }

	UWorld* World = GetWorld();
	if (World == nullptr) { return; }

	const float Radius = GetCapsuleComponent()->GetScaledCapsuleRadius();
	const float HalfHeight = GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	const FVector Forward = GetActorForwardVector();
	const FVector LeadingEdge = GetActorLocation() + Forward * (Radius + TurnCheckDistance);

	FCollisionQueryParams TraceParams(TEXT("GlimmerSense"), false, this);
	if (const ASparkHeroCharacter* Hero = CachedHero.Get())
	{
		TraceParams.AddIgnoredActor(Hero); // the hero is contact, not a wall
	}

	// Wall check: a straight poke ahead at body height.
	FHitResult WallHit;
	const bool bWallAhead = World->LineTraceSingleByChannel(
		WallHit, GetActorLocation(), LeadingEdge, ECC_Visibility, TraceParams);

	// Ledge check: from past the leading edge, straight down past our feet. No floor
	// within a comfortable step-down means a cliff — and Glimmers do not do cliffs.
	FHitResult GroundHit;
	const FVector DropEnd = LeadingEdge - FVector(0.f, 0.f, HalfHeight + 100.f);
	const bool bGroundAhead = World->LineTraceSingleByChannel(
		GroundHit, LeadingEdge, DropEnd, ECC_Visibility, TraceParams);

	if (bWallAhead || !bGroundAhead)
	{
		LastTurnTime = Now();
		AddActorWorldRotation(FRotator(0.f, 180.f, 0.f)); // about-face, keep walking
	}
}

// ---------------------------------------------------------------------------
// Hero contact: stomp/dash squashes the Glimmer, anything else bonks the hero
// ---------------------------------------------------------------------------
void AGlimmerEnemy::OnCapsuleHit(UPrimitiveComponent* HitComp, AActor* OtherActor,
                                 UPrimitiveComponent* OtherComp, FVector NormalImpulse, const FHitResult& Hit)
{
	HandleHeroContact(Cast<ASparkHeroCharacter>(OtherActor));
}

void AGlimmerEnemy::OnCapsuleOverlap(UPrimitiveComponent* OverlappedComp, AActor* OtherActor,
                                     UPrimitiveComponent* OtherComp, int32 OtherBodyIndex,
                                     bool bFromSweep, const FHitResult& SweepResult)
{
	HandleHeroContact(Cast<ASparkHeroCharacter>(OtherActor));
}

void AGlimmerEnemy::HandleHeroContact(ASparkHeroCharacter* Hero)
{
	if (bDead || Hero == nullptr) { return; }

	// Stomp: the hero is above us and was falling hard a moment ago. (Landing on our
	// capsule zeroes his velocity BEFORE this event fires — read the RECENT fall, or
	// every clean head-jump degrades into a mutual bonk.)
	const float HalfHeight = GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	const bool bHeroAbove = Hero->GetActorLocation().Z > GetActorLocation().Z + HalfHeight * 0.25f;
	const bool bStomp = bHeroAbove && Hero->GetRecentFallSpeed() < StompVelocityThreshold;

	if (bStomp || Hero->IsDashing())
	{
		if (bStomp)
		{
			// Bounce the hero off our flattened remains (Z only — keep his run speed).
			Hero->LaunchCharacter(FVector(0.f, 0.f, StompBounce), false, true);
		}
		Die(bStomp);
		return;
	}

	// Side bonk: shove the hero away. Cooldown so contact can't re-trigger every frame.
	if ((Now() - LastHitTime) < HitCooldown) { return; }
	LastHitTime = Now();

	FVector Away = Hero->GetActorLocation() - GetActorLocation();
	Away.Z = 0.f;
	Away = Away.IsNearlyZero() ? -GetActorForwardVector() : Away.GetSafeNormal();
	Hero->LaunchCharacter(Away * KnockbackForce + FVector(0.f, 0.f, KnockbackLift), true, true);

	// No damage system yet — the Glimmer just pauses, smug, before walking on.
	StunnedUntilTime = Now() + StunDuration;
	GetCharacterMovement()->StopMovementImmediately();
}

// ---------------------------------------------------------------------------
// Death: squash flat, switch the body off, linger a beat, clean up
// ---------------------------------------------------------------------------
void AGlimmerEnemy::Die(bool bByStomp)
{
	if (bDead) { return; }
	bDead = true;

	// Squash flat and drop the pancake to the capsule's feet (visual only).
	if (VisualRoot)
	{
		const float HalfHeight = GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
		VisualRoot->SetRelativeScale3D(FVector(1.4f, 1.4f, 0.15f));
		VisualRoot->SetRelativeLocation(FVector(0.f, 0.f, -HalfHeight + 8.f));
	}

	// Switch the body off: no more collision, no more walking.
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	GetCharacterMovement()->StopMovementImmediately();
	GetCharacterMovement()->DisableMovement();
	SetActorEnableCollision(false);

	OnGlimmerSquashed(bByStomp);

	// Let the flattened body linger a beat, then clean up.
	GetWorldTimerManager().SetTimer(DestroyTimerHandle, this, &AGlimmerEnemy::FinishDeath,
	                                SquashLingerTime, false);
}

void AGlimmerEnemy::FinishDeath()
{
	Destroy();
}
