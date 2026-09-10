#include "SparkBlastProjectile.h"

#include "Components/PointLightComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "Bramblehulk.h"
#include "EmberReaver.h"
#include "GlimmerEnemy.h"
#include "KrakenBoss.h"
#include "RolyShellback.h"
#include "SparkHeroCharacter.h"
#include "SparkRivalBase.h"
#include "VoidStalker.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "SparkImpactBurst.h"
#include "UObject/ConstructorHelpers.h"

ASparkBlastProjectile::ASparkBlastProjectile()
{
	PrimaryActorTick.bCanEverTick = true;   // the lance spins, crackles, and sheds light
	InitialLifeSpan = 1.4f;   // flies ~21 m, then fades — no stray lances forever

	Collision = CreateDefaultSubobject<USphereComponent>(TEXT("Collision"));
	Collision->InitSphereRadius(16.f);
	Collision->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Collision->SetCollisionObjectType(ECC_WorldDynamic);
	Collision->SetCollisionResponseToAllChannels(ECR_Ignore);
	Collision->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	Collision->SetGenerateOverlapEvents(true);   // guarantee the boss-capsule overlap fires
	SetRootComponent(Collision);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> ConeMesh(TEXT("/Engine/BasicShapes/Cone.Cone"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylMesh(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> Plasma(TEXT("/Game/Art/FX/M_SparkPlasma.M_SparkPlasma"));
	PlasmaMaterial = Plasma.Succeeded() ? Plasma.Object : nullptr;

	// The dart spins as ONE assembly around the flight axis.
	ShardRoot = CreateDefaultSubobject<USceneComponent>(TEXT("ShardRoot"));
	ShardRoot->SetupAttachment(Collision);

	auto MakePiece = [&](const TCHAR* Name, UStaticMesh* Mesh) -> UStaticMeshComponent*
	{
		UStaticMeshComponent* C = CreateDefaultSubobject<UStaticMeshComponent>(Name);
		C->SetupAttachment(ShardRoot);
		if (Mesh) { C->SetStaticMesh(Mesh); }
		if (PlasmaMaterial) { C->SetMaterial(0, PlasmaMaterial); }
		C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		C->SetCastShadow(false);
		return C;
	};
	UStaticMesh* SphereM = SphereMesh.Succeeded() ? SphereMesh.Object.Get() : nullptr;
	UStaticMesh* ConeM = ConeMesh.Succeeded() ? ConeMesh.Object.Get() : nullptr;

	// The needle core: a white-hot lozenge stretched along flight.
	Ball = MakePiece(TEXT("Ball"), SphereM);
	Ball->SetRelativeScale3D(FVector(0.52f, 0.13f, 0.13f));

	// The crystalline point (cone +Z pitched onto +X) and the long shard tail.
	TipShard = MakePiece(TEXT("TipShard"), ConeM);
	TipShard->SetRelativeLocation(FVector(30.f, 0.f, 0.f));
	TipShard->SetRelativeRotation(FRotator(90.f, 0.f, 0.f));
	TipShard->SetRelativeScale3D(FVector(0.15f, 0.15f, 0.32f));

	TailShard = MakePiece(TEXT("TailShard"), ConeM);
	TailShard->SetRelativeLocation(FVector(-14.f, 0.f, 0.f));
	TailShard->SetRelativeRotation(FRotator(-90.f, 0.f, 0.f));
	TailShard->SetRelativeScale3D(FVector(0.12f, 0.12f, 0.58f));

	Halo = MakePiece(TEXT("Halo"), SphereM);
	Halo->SetRelativeScale3D(FVector(0.66f, 0.34f, 0.34f));

	// The crackle: two sparks orbiting the dart in opposite senses.
	OrbiterA = MakePiece(TEXT("OrbiterA"), SphereM);
	OrbiterA->SetRelativeScale3D(FVector(0.07f));
	OrbiterB = MakePiece(TEXT("OrbiterB"), SphereM);
	OrbiterB->SetRelativeScale3D(FVector(0.055f));

	// The ribbon: pooled streaks parked in WORLD space along the wake.
	UStaticMesh* CylM = CylMesh.Succeeded() ? CylMesh.Object.Get() : nullptr;
	TrailStreaks.Reserve(NumStreaks);
	for (int32 i = 0; i < NumStreaks; ++i)
	{
		UStaticMeshComponent* S = CreateDefaultSubobject<UStaticMeshComponent>(
			*FString::Printf(TEXT("Streak%d"), i));
		S->SetupAttachment(Collision);
		S->SetAbsolute(true, true, true);
		if (CylM) { S->SetStaticMesh(CylM); }
		if (PlasmaMaterial) { S->SetMaterial(0, PlasmaMaterial); }
		S->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		S->SetCastShadow(false);
		S->SetVisibility(false);
		TrailStreaks.Add(S);
	}

	Light = CreateDefaultSubobject<UPointLightComponent>(TEXT("Light"));
	Light->SetupAttachment(Collision);
	Light->SetIntensity(1600.f);
	Light->SetAttenuationRadius(320.f);
	Light->SetLightColor(FColor(255, 170, 70));   // kept-fire amber (Color Law)
	Light->SetCastShadows(false);

	Movement = CreateDefaultSubobject<UProjectileMovementComponent>(TEXT("Movement"));
	Movement->InitialSpeed = BlastSpeed;
	Movement->MaxSpeed = BlastSpeed;
	Movement->ProjectileGravityScale = 0.f;   // spark-fire flies true (a bent law, priced by lifespan)
	Movement->bRotationFollowsVelocity = true;
}

void ASparkBlastProjectile::BeginPlay()
{
	Super::BeginPlay();

	Collision->OnComponentBeginOverlap.AddDynamic(this, &ASparkBlastProjectile::OnBlastOverlap);
	LastStreakPos = GetActorLocation();

	// PLASMA tints: white-hot needle, crystalline shards, faint corona, hot sparks.
	auto Tint = [&](UStaticMeshComponent* C, const FLinearColor& Color) -> UMaterialInstanceDynamic*
	{
		if (!C || !PlasmaMaterial) { return nullptr; }
		UMaterialInstanceDynamic* MID = C->CreateDynamicMaterialInstance(0, PlasmaMaterial);
		if (MID) { MID->SetVectorParameterValue(TEXT("Tint"), Color); }
		return MID;
	};
	Tint(Ball, FLinearColor(3.6f, 2.6f, 1.6f));
	Tint(TipShard, FLinearColor(4.2f, 3.f, 1.8f));
	Tint(TailShard, FLinearColor(2.6f, 1.2f, 0.35f));
	Tint(Halo, FLinearColor(0.45f, 0.2f, 0.06f));
	Tint(OrbiterA, FLinearColor(4.5f, 3.2f, 1.6f));
	Tint(OrbiterB, FLinearColor(4.5f, 2.4f, 0.9f));
	StreakMIDs.Reset(NumStreaks);
	for (UStaticMeshComponent* S : TrailStreaks)
	{
		StreakMIDs.Add(Tint(S, FLinearColor(2.8f, 1.6f, 0.55f)));
	}
}

void ASparkBlastProjectile::ApplyTier(int32 InTier)
{
	Tier = FMath::Clamp(InTier, 1, 3);
	static const float Sizes[3] = { 1.f, 1.4f, 1.85f };
	static const float Lights[3] = { 1.f, 1.9f, 3.f };
	static const float Speeds[3] = { 1.f, 1.12f, 1.25f };
	SizeScale = Sizes[Tier - 1];

	if (Collision) { Collision->SetSphereRadius(16.f * SizeScale); }
	if (ShardRoot) { ShardRoot->SetRelativeScale3D(FVector(SizeScale)); }
	if (Light)
	{
		Light->SetIntensity(1600.f * Lights[Tier - 1]);
		Light->SetAttenuationRadius(320.f * SizeScale);
		if (Tier == 3) { Light->SetLightColor(FColor(255, 214, 150)); }   // hotter core, amber family
	}
	if (Movement)
	{
		Movement->MaxSpeed = BlastSpeed * Speeds[Tier - 1];
		Movement->Velocity *= Speeds[Tier - 1];
	}
}

void ASparkBlastProjectile::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const float T = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;

	// The lance ROLLS around its flight axis; the crackle-sparks orbit against it.
	if (ShardRoot) { ShardRoot->AddLocalRotation(FRotator(0.f, 0.f, 640.f * DeltaSeconds)); }
	const float OrbitA = T * 15.f;
	if (OrbiterA) { OrbiterA->SetRelativeLocation(FVector(4.f, FMath::Cos(OrbitA) * 26.f, FMath::Sin(OrbitA) * 26.f)); }
	if (OrbiterB) { OrbiterB->SetRelativeLocation(FVector(-6.f, FMath::Cos(-OrbitA * 1.3f) * 33.f, FMath::Sin(-OrbitA * 1.3f) * 33.f)); }

	// The core breathes; the corona rolls against the spin.
	const float Breathe = 1.f + 0.12f * FMath::Sin(T * 21.f);
	if (Ball) { Ball->SetRelativeScale3D(FVector(0.52f, 0.13f, 0.13f) * Breathe); }
	if (Halo) { Halo->SetRelativeScale3D(FVector(0.66f, 0.34f, 0.34f) * (2.f - Breathe)); }

	// The ribbon: drop a world-parked streak every few centiseconds; each fades
	// over 0.4s and gets recycled (ring buffer — the trail can never outgrow it).
	if (T >= NextStreakAt && TrailStreaks.Num() == NumStreaks)
	{
		NextStreakAt = T + 0.045f;
		const FVector Here = GetActorLocation();
		const FVector Span = Here - LastStreakPos;
		const float Len = Span.Size();
		if (Len > 8.f)
		{
			UStaticMeshComponent* S = TrailStreaks[StreakIdx];
			if (S)
			{
				S->SetWorldLocation(LastStreakPos + Span * 0.5f);
				S->SetWorldRotation(FRotationMatrix::MakeFromZ(Span / Len).Rotator());
				S->SetWorldScale3D(FVector(0.05f * SizeScale, 0.05f * SizeScale, Len / 100.f));
				S->SetVisibility(true);
				StreakBorn[StreakIdx] = T;
			}
			StreakIdx = (StreakIdx + 1) % NumStreaks;
			LastStreakPos = Here;
		}
	}
	for (int32 i = 0; i < NumStreaks; ++i)
	{
		if (!TrailStreaks[i] || !TrailStreaks[i]->IsVisible()) { continue; }
		const float Age = T - StreakBorn[i];
		if (Age > 0.4f)
		{
			TrailStreaks[i]->SetVisibility(false);
		}
		else if (StreakMIDs.IsValidIndex(i) && StreakMIDs[i])
		{
			const float Fade = FMath::Square(1.f - Age / 0.4f);   // additive: black = gone
			StreakMIDs[i]->SetVectorParameterValue(TEXT("Tint"),
				FLinearColor(2.8f, 1.6f, 0.55f) * Fade);
		}
	}
}

void ASparkBlastProjectile::OnBlastOverlap(UPrimitiveComponent*, AActor* OtherActor,
                                           UPrimitiveComponent*, int32, bool, const FHitResult&)
{
	if (!OtherActor || OtherActor == GetOwner() || OtherActor == GetInstigator()) { return; }

	// Spark-fire is a real ranged hit: a LIGHT duel-meter strike on any damageable
	// boss, mirroring the hero's own StrikeHitCheck branch-for-branch. Tier is the
	// bolt's combo weight; a T3 lance lands as a CHARGED hit.
	bool bHandled = false;

	if (AGlimmerEnemy* Glimmer = Cast<AGlimmerEnemy>(OtherActor))
	{
		Glimmer->TakeStrike();          // Motes die to spark-fire (mass-class ladder)
		bHandled = true;
	}
	else if (ARolyShellback* Shell = Cast<ARolyShellback>(OtherActor))
	{
		Shell->TakeStrike();            // the Cannonball pops (covers Shellback Alpha)
		bHandled = true;
	}
	else if (AKrakenBoss* Kraken = Cast<AKrakenBoss>(OtherActor))
	{
		Kraken->TakeStrike(Tier, Tier >= 3);
		bHandled = true;
	}
	else if (AEmberReaver* Reaver = Cast<AEmberReaver>(OtherActor))
	{
		Reaver->TakeStrike(Tier, Tier >= 3);
		bHandled = true;
	}
	else if (AVoidStalker* Stalker = Cast<AVoidStalker>(OtherActor))
	{
		Stalker->TakeStrike(Tier, Tier >= 3);
		bHandled = true;
	}
	// Every ASparkRivalBase subclass — the Warlord, the Glade Prowler, the
	// guardians, and every boss after them.
	else if (ASparkRivalBase* AnyRival = Cast<ASparkRivalBase>(OtherActor))
	{
		AnyRival->TakeStrike(Tier, Tier >= 3);
		bHandled = true;
	}
	else if (ABramblehulk* Hulk = Cast<ABramblehulk>(OtherActor))
	{
		// The gentle giant has no health to drain — aggression COSTS calm (a clang),
		// exactly as a melee hit does. You soothe him with light, not the lance.
		Hulk->TakeStrikeClang(Cast<ASparkHeroCharacter>(GetInstigator()), false);
		bHandled = true;
	}

	if (bHandled)
	{
		ASparkImpactBurst::Burst(this, GetActorLocation(),
		                         FLinearColor(4.f, 1.6f, 0.45f), 1.1f * SizeScale, 3200.f * SizeScale);
		Destroy();
	}
}
