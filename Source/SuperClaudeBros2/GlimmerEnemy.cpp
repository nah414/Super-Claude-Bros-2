#include "GlimmerEnemy.h"

#include "CollisionQueryParams.h"
#include "Components/CapsuleComponent.h"
#include "DrawDebugHelpers.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/HitResult.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "SparkHeroCharacter.h"
#include "SparkImpactBurst.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h"

AGlimmerEnemy::AGlimmerEnemy()
{
	PrimaryActorTick.bCanEverTick = true;

	// --- Collision capsule: a squat little shadow ---
	// Radius grown 34 -> 44 (Adam's contact pass: the crystal body is wider than
	// the old capsule — heroes visually waded through it before physics noticed).
	GetCapsuleComponent()->InitCapsuleSize(44.f, 40.f);
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

	// The REAL Glimmer: the Roster's crystal sprite (Adam-reviewed in the Hall).
	// Fallback: the original ink sphere + cream eyes if the asset is missing.
	static ConstructorHelpers::FObjectFinder<UStaticMesh> SpriteMesh(TEXT("/Game/Art/Roster/glimmer_sprite/SM_glimmer_sprite.SM_glimmer_sprite"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	bHasRealModel = SpriteMesh.Succeeded();

	BodyMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BodyMesh"));
	BodyMesh->SetupAttachment(VisualRoot);
	BodyMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (bHasRealModel)
	{
		BodyMesh->SetStaticMesh(SpriteMesh.Object);
		// Mesh pivot at feet (Blender ground-drop); capsule half-height is 40.
		BodyMesh->SetRelativeLocation(FVector(0.f, 0.f, -40.f));
		BodyMesh->SetRelativeRotation(FRotator(0.f, 90.f, 0.f)); // face actor +X
		BodyMesh->SetRelativeScale3D(FVector(1.3f));             // 60uu sprite -> squat 78uu menace
	}
	else if (SphereMesh.Succeeded())
	{
		BodyMesh->SetStaticMesh(SphereMesh.Object);
		BodyMesh->SetRelativeScale3D(FVector(0.8f));
	}

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

	// The crystal sprite brings its own face — placeholder eyes and tint stay off.
	if (bHasRealModel)
	{
		if (LeftEye) { LeftEye->SetVisibility(false); }
		if (RightEye) { RightEye->SetVisibility(false); }
	}

	// Tint the placeholder in the night palette: ink body, cream eyes. The sphere
	// asset's default slot is the grid material (no Color param), so explicitly base
	// our dynamic materials on the engine's tintable BasicShapeMaterial.
	const FLinearColor Ink(0.078f, 0.078f, 0.075f);   // #141413
	const FLinearColor Cream(0.980f, 0.976f, 0.961f); // #faf9f5
	if (UMaterialInterface* BaseMat = LoadObject<UMaterialInterface>(
			nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
		BaseMat && !bHasRealModel)
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

	// Resolve the hero ROBUSTLY. A BeginPlay-cached pointer can come back EMPTY in packaged builds
	// (the Glimmer's BeginPlay can run before the player pawn is possessed), and P swaps the pawn at
	// runtime. Try cache -> player pawn -> world scan, refreshing the cache from whichever succeeds,
	// so the Glimmer ALWAYS finds the hero if one exists. (A null hero = no aggro AND no bonk = the
	// "does nothing / never attacks" symptom Adam saw.)
	ASparkHeroCharacter* Hero = CachedHero.Get();
	if (Hero == nullptr)
	{
		Hero = Cast<ASparkHeroCharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
		if (Hero == nullptr)
		{
			Hero = Cast<ASparkHeroCharacter>(
				UGameplayStatics::GetActorOfClass(GetWorld(), ASparkHeroCharacter::StaticClass()));
		}
		if (Hero) { CachedHero = Hero; }
	}
	if (!Hero) { CombatState = TEXT("NO-HERO"); }

	// TEMP debug label over the head (see header note) — drawn each frame so we can see the state.
	if (bShowCombatState)
	{
		DrawDebugString(GetWorld(), FVector(0.f, 0.f, 95.f), CombatState, this, FColor::Yellow, 0.f, true, 1.4f);
	}

	// Keep live-tuned values flowing into the movement component (editor tuning).
	GetCharacterMovement()->MaxWalkSpeed = PatrolSpeed;

	// Generous contact backstop: hit/overlap events do the heavy lifting, but a
	// plain radius check means a hero pressed flush against us never slips through.
	if (Hero)
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

	// The Spark Aura (hero power, L2+) CAN pacify wild things — but for Glimmers that "mercy" is OFF
	// by default (bCalmableByAura). The hero's always-on aura was calming EVERY Glimmer he walked up
	// to ("Calm" over their heads) instead of letting them fight — which is exactly why they "never
	// attacked". Gated off so Glimmers stay a combat threat.
	if (bCalmableByAura && Hero)
	{
		const bool bCalm = Hero->IsAuraActive()
			&& FVector::DistSquared(Hero->GetActorLocation(), GetActorLocation())
				<= FMath::Square(Hero->GetAuraRadius());
		if (bCalm != bCalmedByAura)
		{
			bCalmedByAura = bCalm;
			OnCalmChanged(bCalm);
			if (bCalm) { GetCharacterMovement()->StopMovementImmediately(); }
		}
	}
	if (bCalmedByAura) { CombatState = TEXT("CALM"); return; }   // settled in the warm light

	// Stunned (now only from a power-stagger — the contact bonk no longer self-stuns): hold a beat.
	if (Now() < StunnedUntilTime) { CombatState = TEXT("STUN"); return; }

	// AGGRO-ON-SIGHT: a hero inside AggroRadius is HUNTED. ChaseHero closes the gap and, once
	// inside StrikeRange, POUNCES (the active attack). The contact backstop above still owns the
	// bonk/stomp/dash outcome when the pounce lands.
	if (Hero && FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= AggroRadius)
	{
		ChaseHero(Hero);
		return;
	}

	// Patrol: walk the platform, turning back at walls and ledges.
	CombatState = TEXT("PATROL");
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
// Aggro: face the hero and walk straight at him — but never off a cliff.
// ---------------------------------------------------------------------------
void AGlimmerEnemy::ChaseHero(ASparkHeroCharacter* Hero)
{
	if (Hero == nullptr) { return; }

	// Commit to the hunt: a notch quicker than the patrol amble (reads as "coming for you").
	GetCharacterMovement()->MaxWalkSpeed = ChaseSpeed;

	// In strike range + off cooldown -> POUNCE, but ONLY if there's ground to land on. On a small
	// spiral landing the lunge would overshoot the edge and the Glimmer would fall + clip through the
	// floor below — there it just keeps hunting + bonking on contact instead of leaping.
	const FVector ToHeroFlat(Hero->GetActorLocation().X - GetActorLocation().X,
	                         Hero->GetActorLocation().Y - GetActorLocation().Y, 0.f);
	const FVector LungeDir = ToHeroFlat.IsNearlyZero() ? GetActorForwardVector() : ToHeroFlat.GetSafeNormal();
	if (FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= StrikeRange
		&& Now() >= NextStrikeTime
		&& GetCharacterMovement()->IsMovingOnGround()
		&& HasLungeRoom(LungeDir))
	{
		CombatState = TEXT("POUNCE");
		Lunge(Hero);
		return;
	}

	CombatState = TEXT("HUNT");
	// Otherwise close the gap on foot. Swing to face the hero (yaw only) — smooth, so the turn reads.
	const FVector ToHero = Hero->GetActorLocation() - GetActorLocation();
	if (!ToHero.IsNearlyZero())
	{
		const FRotator Want(0.f, ToHero.Rotation().Yaw, 0.f);
		SetActorRotation(FMath::RInterpTo(GetActorRotation(), Want,
			GetWorld()->GetDeltaSeconds(), 7.f));
	}

	// Ledge-safety stays ON: SenseAndTurn still about-faces us at a real cliff/wall.
	// (The hero is ignored by that trace, so he reads as open path, not a wall — the
	// Glimmer walks INTO him and the contact backstop handles the bonk.) A Glimmer will
	// dance at a gap edge rather than dive after a hero across it.
	if (GetCharacterMovement()->IsMovingOnGround())
	{
		SenseAndTurn();
	}
	AddMovementInput(GetActorForwardVector());
}

// ---------------------------------------------------------------------------
// The active attack: a telegraphed POUNCE at the hero. Ledge-guarded so the
// Glimmer never dives into a pit. The pounce carries it into the hero, where
// the contact backstop / HandleHeroContact lands the bonk (ember drain + shove).
// ---------------------------------------------------------------------------
void AGlimmerEnemy::Lunge(ASparkHeroCharacter* Hero)
{
	if (Hero == nullptr) { return; }
	NextStrikeTime = Now() + StrikeCooldown;

	FVector ToHero = Hero->GetActorLocation() - GetActorLocation();
	ToHero.Z = 0.f;
	const FVector Dir = ToHero.IsNearlyZero() ? GetActorForwardVector() : ToHero.GetSafeNormal();

	// Ledge guard: confirm ground partway along the pounce, or skip it (keep walking + bonking).
	if (UWorld* World = GetWorld())
	{
		const float HalfHeight = GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
		const FVector Probe = GetActorLocation() + Dir * 160.f;
		FHitResult Ground;
		FCollisionQueryParams P(TEXT("GlimmerLunge"), false, this);
		P.AddIgnoredActor(Hero);
		const bool bGround = World->LineTraceSingleByChannel(
			Ground, Probe, Probe - FVector(0.f, 0.f, HalfHeight + 120.f), ECC_Visibility, P);
		if (!bGround) { return; }
	}

	// Snap to face the hero, flash a cold spark telegraph, then leap.
	SetActorRotation(FRotator(0.f, Dir.Rotation().Yaw, 0.f));
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 20.f),
	                         FLinearColor(0.45f, 1.6f, 2.3f), 0.55f, 1500.f);   // a cold pounce flash
	LaunchCharacter(Dir * LungeSpeed + FVector(0.f, 0.f, LungeLift), true, true);
}

// ---------------------------------------------------------------------------
// Pounce-room check: ground must exist all along the lunge reach, or the Glimmer
// would leap off a small landing (the spiral) into a gap and sink through the floor.
// ---------------------------------------------------------------------------
bool AGlimmerEnemy::HasLungeRoom(const FVector& Dir) const
{
	const UWorld* World = GetWorld();
	if (World == nullptr) { return false; }
	const float HalfHeight = GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	FCollisionQueryParams P(TEXT("GlimmerLungeRoom"), false, this);
	if (const ASparkHeroCharacter* Hero = CachedHero.Get()) { P.AddIgnoredActor(Hero); }
	// Every point along the lunge reach must have ground within a comfortable step-down.
	for (const float D : { 160.f, 280.f, 400.f })
	{
		const FVector Probe = GetActorLocation() + Dir * D;
		FHitResult Ground;
		const bool bHit = World->LineTraceSingleByChannel(
			Ground, Probe, Probe - FVector(0.f, 0.f, HalfHeight + 130.f), ECC_Visibility, P);
		if (!bHit) { return false; }
	}
	return true;
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

	// A calmed Glimmer never bonks — docile contact is harmless both ways.
	// (Stomp and dash above still work: the mercy stays the player's choice.)
	if (bCalmedByAura) { return; }

	// Side bonk: shove the hero away. Cooldown so contact can't re-trigger every frame.
	if ((Now() - LastHitTime) < HitCooldown) { return; }
	LastHitTime = Now();

	FVector Away = Hero->GetActorLocation() - GetActorLocation();
	Away.Z = 0.f;
	Away = Away.IsNearlyZero() ? -GetActorForwardVector() : Away.GetSafeNormal();
	Hero->LaunchCharacter(Away * KnockbackForce + FVector(0.f, 0.f, KnockbackLift), true, true);

	// Contact costs momentum AND fire: the bonk drains embers (10, per the spec §2
	// damage table) unless the hero's grace flare eats it. Knockback applies either
	// way — the flame and the shove are separate ledgers.
	Hero->TakeEmberHit(ContactProfile.ContactDamageEmbers);

	// NO self-stun here. The old "stand still after a bonk" was THE freeze: a hero held close
	// re-triggered the bonk every HitCooldown, and each bonk StopMovement+stunned the Glimmer for
	// StunDuration -> it froze in place and never got to hunt/pounce ("freezes when you get close,
	// doesn't attack"). HitCooldown alone now paces the contact hit; the Glimmer keeps attacking.
}

void AGlimmerEnemy::TakeStrike()
{
	if (!bDead)
	{
		Die(false);   // squashed sideways — same exit as a dash kill
	}
}

void AGlimmerEnemy::TakeStagger(float Seconds)
{
	if (bDead) { return; }
	StunnedUntilTime = FMath::Max(StunnedUntilTime, Now() + Seconds);
	GetCharacterMovement()->StopMovementImmediately();
}

// ---------------------------------------------------------------------------
// Death: squash flat, switch the body off, linger a beat, clean up
// ---------------------------------------------------------------------------
void AGlimmerEnemy::Die(bool bByStomp)
{
	if (bDead) { return; }
	bDead = true;

	// Every contact SHOWS (Adam's universal-impact law): a spark pop at the kill.
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 10.f),
	                         FLinearColor(3.2f, 1.5f, 0.45f), 0.85f, 2600.f);

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
