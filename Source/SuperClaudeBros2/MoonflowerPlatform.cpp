#include "MoonflowerPlatform.h"

#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

AMoonflowerPlatform::AMoonflowerPlatform()
{
	PrimaryActorTick.bCanEverTick = true;

	VisualRoot = CreateDefaultSubobject<USceneComponent>(TEXT("VisualRoot"));
	SetRootComponent(VisualRoot);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cylinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> MeshyFlower(TEXT("/Game/Art/Moonworks/moonflower.moonflower"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> Plasma(TEXT("/Game/Art/FX/M_SparkPlasma.M_SparkPlasma"));

	PlatformDisc = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PlatformDisc"));
	PlatformDisc->SetupAttachment(VisualRoot);
	if (Cylinder.Succeeded()) { PlatformDisc->SetStaticMesh(Cylinder.Object.Get()); }
	if (Plasma.Succeeded()) { PlatformDisc->SetMaterial(0, Plasma.Object.Get()); }
	PlatformDisc->SetCollisionProfileName(TEXT("BlockAll"));
	PlatformDisc->SetRelativeLocation(FVector(0.f, 0.f, 12.f));
	PlatformDisc->SetRelativeScale3D(FVector(DiscClosedScale, DiscClosedScale, 0.24f));

	Pistil = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Pistil"));
	Pistil->SetupAttachment(VisualRoot);
	if (Sphere.Succeeded()) { Pistil->SetStaticMesh(Sphere.Object.Get()); }
	if (Plasma.Succeeded()) { Pistil->SetMaterial(0, Plasma.Object.Get()); }
	Pistil->SetCollisionProfileName(TEXT("BlockAll"));   // the beam must LAND here
	Pistil->SetRelativeLocation(FVector(0.f, 0.f, PistilHeight));
	Pistil->SetRelativeScale3D(FVector(0.55f, 0.55f, 0.55f));

	BloomMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BloomMesh"));
	BloomMesh->SetupAttachment(VisualRoot);
	BloomMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);   // the DISC is the floor
	BloomMesh->SetCastShadow(false);
	if (MeshyFlower.Succeeded())
	{
		BloomMesh->SetStaticMesh(MeshyFlower.Object.Get());
		bHasBloomMesh = true;
	}
	else
	{
		BloomMesh->SetVisibility(false);
	}

	BloomLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("BloomLight"));
	BloomLight->SetupAttachment(VisualRoot);
	BloomLight->SetRelativeLocation(FVector(0.f, 0.f, 90.f));
	BloomLight->SetLightColor(FLinearColor(0.75f, 1.35f, 1.5f));
	BloomLight->SetIntensity(0.f);
	BloomLight->SetAttenuationRadius(520.f);
	BloomLight->SetCastShadows(false);
}

void AMoonflowerPlatform::BeginPlay()
{
	Super::BeginPlay();

	// Placed actor: MIDs at BeginPlay, never the constructor (the unsavable-level law).
	if (UMaterialInterface* Base = Pistil ? Pistil->GetMaterial(0) : nullptr)
	{
		PistilMID = UMaterialInstanceDynamic::Create(Base, this);
		PistilMID->SetVectorParameterValue(TEXT("Tint"), BloomTint * 0.3f);
		Pistil->SetMaterial(0, PistilMID);
	}
	if (UMaterialInterface* Base = PlatformDisc ? PlatformDisc->GetMaterial(0) : nullptr)
	{
		DiscMID = UMaterialInstanceDynamic::Create(Base, this);
		DiscMID->SetVectorParameterValue(TEXT("Tint"), BloomTint * 0.4f);
		PlatformDisc->SetMaterial(0, DiscMID);
	}

	PulsePhase = GetActorLocation().Y * 0.011f;

	// Probe the real mesh, size the bloom to canon (bounds at import lied once already).
	if (bHasBloomMesh && BloomMesh && BloomMesh->GetStaticMesh())
	{
		const FBox B = BloomMesh->GetStaticMesh()->GetBoundingBox();
		const float Width = B.Max.X - B.Min.X;
		if (Width > 1.f) { BloomBaseScale = DesiredBloomWidth / Width; }
	}

	if (bStartBloomed)
	{
		Bloom = 1.f;
		LastFedTime = Now();
	}
}

float AMoonflowerPlatform::Now() const
{
	return GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
}

void AMoonflowerPlatform::FeedLight()
{
	LastFedTime = Now();
}

void AMoonflowerPlatform::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	const float SinceFed = Now() - LastFedTime;
	if (SinceFed < 0.15f)
	{
		Bloom = FMath::Min(1.f, Bloom + DeltaSeconds / FMath::Max(BloomSeconds, 0.05f));
	}
	else if (SinceFed > LingerSeconds)
	{
		// The linger already forgave the fumble; now the flower folds, gently.
		Bloom = FMath::Max(0.f, Bloom - DeltaSeconds / FMath::Max(CloseSeconds, 0.05f));
	}

	// The walkable payoff, per tick (movement must feel continuous underfoot).
	const float Eased = FMath::InterpEaseOut(0.f, 1.f, Bloom, 2.2f);
	const float DiscScale = FMath::Lerp(DiscClosedScale, DiscOpenScale, Eased);
	if (PlatformDisc) { PlatformDisc->SetRelativeScale3D(FVector(DiscScale, DiscScale, 0.24f)); }
	if (BloomMesh && bHasBloomMesh)
	{
		BloomMesh->SetRelativeScale3D(FVector(FMath::Lerp(0.12f, 1.f, Eased) * BloomBaseScale));
		BloomMesh->SetRelativeRotation(FRotator(0.f, Eased * 38.f, 0.f));   // she turns as she opens
	}

	// The truth channel for headless verify runs: one line, once, when she opens.
	if (!bLoggedOpen && Bloom > 0.9f)
	{
		bLoggedOpen = true;
		UE_LOG(LogTemp, Display, TEXT("MOONWORKS_MARKER: %s bloomed open"), *GetName());
	}

	// LOAD LAW: light + tint breathe at 10Hz.
	PulseClock += DeltaSeconds;
	if (PulseClock >= 0.1f)
	{
		PulseClock = 0.f;
		PulsePhase += 0.52f;
		const float Pulse = 0.9f + 0.2f * FMath::Sin(PulsePhase);
		if (BloomLight) { BloomLight->SetIntensity(2400.f * Eased * Pulse); }
		if (PistilMID)
		{
			const bool bDrinking = SinceFed < 0.15f;
			PistilMID->SetVectorParameterValue(TEXT("Tint"), BloomTint * (bDrinking ? 1.15f : 0.3f) * Pulse);
		}
		if (DiscMID) { DiscMID->SetVectorParameterValue(TEXT("Tint"), BloomTint * (0.25f + 0.55f * Eased) * Pulse); }
	}
}
