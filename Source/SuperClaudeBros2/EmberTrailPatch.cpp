#include "EmberTrailPatch.h"

#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "SparkHeroCharacter.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	const FLinearColor EmberRed(3.0f, 0.45f, 0.1f);
}

AEmberTrailPatch::AEmberTrailPatch()
{
	PrimaryActorTick.bCanEverTick = true;

	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	Flame = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Flame"));
	Flame->SetupAttachment(Root);
	Flame->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Flame->SetCastShadow(false);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cone(TEXT("/Engine/BasicShapes/Cone.Cone"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> Plasma(TEXT("/Game/Art/FX/M_SparkPlasma.M_SparkPlasma"));
	if (Cone.Succeeded()) { Flame->SetStaticMesh(Cone.Object); }
	if (Plasma.Succeeded())
	{
		FlameMID = UMaterialInstanceDynamic::Create(Plasma.Object, this);
		FlameMID->SetVectorParameterValue(TEXT("Tint"), EmberRed);
		Flame->SetMaterial(0, FlameMID);
	}
	Flame->SetRelativeScale3D(FVector(0.55f, 0.55f, 0.9f));

	Glow = CreateDefaultSubobject<UPointLightComponent>(TEXT("Glow"));
	Glow->SetupAttachment(Root);
	Glow->SetRelativeLocation(FVector(0.f, 0.f, 35.f));
	Glow->SetLightColor(FLinearColor(1.f, 0.32f, 0.08f));
	Glow->SetIntensity(1400.f);
	Glow->SetAttenuationRadius(300.f);
	Glow->SetCastShadows(false);

	InitialLifeSpan = 3.f;
}

namespace
{
	// LOAD LAW registry: weak ptrs self-invalidate on Destroy — no bookkeeping.
	TArray<TWeakObjectPtr<AEmberTrailPatch>> GLivePatches;
}

void AEmberTrailPatch::Plant(UObject* WorldContext, const FVector& GroundLocation)
{
	UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
	if (!World) { return; }

	// THE PATCH CEILING: oldest flame gutters out first.
	GLivePatches.RemoveAll([](const TWeakObjectPtr<AEmberTrailPatch>& P) { return !P.IsValid(); });
	const int32 Cap = GetDefault<AEmberTrailPatch>()->MaxLivePatches;
	while (GLivePatches.Num() >= Cap && GLivePatches.Num() > 0)
	{
		if (GLivePatches[0].IsValid()) { GLivePatches[0]->Destroy(); }
		GLivePatches.RemoveAt(0);
	}

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	if (AEmberTrailPatch* P = World->SpawnActor<AEmberTrailPatch>(GroundLocation, FRotator::ZeroRotator, Params))
	{
		GLivePatches.Add(P);
	}
}

void AEmberTrailPatch::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	Age += DeltaSeconds;
	FlickerPhase += DeltaSeconds * 21.f;
	const float T = FMath::Clamp(Age / FMath::Max(LifeSeconds, 0.1f), 0.f, 1.f);
	const float Fade = FMath::Square(1.f - T);          // additive: black = out

	// A flame is never still: the cone licks and gutters as it dies.
	const float Lick = 0.9f + 0.35f * FMath::Sin(FlickerPhase) * FMath::Sin(FlickerPhase * 0.37f + 1.7f);
	if (Flame)
	{
		Flame->SetRelativeScale3D(FVector(0.55f * (0.7f + 0.3f * Fade),
		                                  0.55f * (0.7f + 0.3f * Fade),
		                                  0.9f * Lick * (0.35f + 0.65f * Fade)));
	}
	if (FlameMID) { FlameMID->SetVectorParameterValue(TEXT("Tint"), EmberRed * (0.4f + 0.9f * Fade) * Lick); }
	if (Glow) { Glow->SetIntensity(1400.f * Fade * Lick); }

	// The bite: standing in his fire costs embers (the hero's grace window
	// rate-limits the burn — the lesson is taught, not griefed).
	// LOAD LAW: cached weak-ptr hero (30 patches were calling GetPlayerPawn
	// EVERY frame); re-resolve only when invalid — P-switch-safe by design.
	if (!CachedHero.IsValid())
	{
		CachedHero = Cast<ASparkHeroCharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
	}
	if (ASparkHeroCharacter* Hero = CachedHero.Get())
	{
		FVector To = Hero->GetActorLocation() - GetActorLocation();
		const float Dz = FMath::Abs(To.Z);
		To.Z = 0.f;
		if (To.SizeSquared() < FMath::Square(BurnRadius) && Dz < 110.f)
		{
			Hero->LaunchCharacter(FVector(0.f, 0.f, 200.f), false, true);
			Hero->TakeEmberHit(BurnEmbers);
		}
	}

	if (T >= 1.f) { Destroy(); }
}
