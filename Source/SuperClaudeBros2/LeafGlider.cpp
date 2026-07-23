#include "LeafGlider.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

ALeafGlider::ALeafGlider()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.034f;   // 30 Hz — ambience, not gameplay

	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Plane(TEXT("/Engine/BasicShapes/Plane.Plane"));

	auto MakeWing = [&](const TCHAR* Name, float YawOff) -> UStaticMeshComponent*
	{
		UStaticMeshComponent* W = CreateDefaultSubobject<UStaticMeshComponent>(Name);
		W->SetupAttachment(Root);
		W->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		W->SetCastShadow(false);
		W->SetCanEverAffectNavigation(false);
		if (Plane.Succeeded()) { W->SetStaticMesh(Plane.Object); }
		W->SetRelativeRotation(FRotator(0.f, YawOff, 0.f));
		W->SetRelativeScale3D(FVector(1.6f, 0.5f, 1.f));
		return W;
	};
	WingA = MakeWing(TEXT("WingA"), 0.f);
	WingB = MakeWing(TEXT("WingB"), 90.f);
}

void ALeafGlider::BeginPlay()
{
	Super::BeginPlay();
	Home = GetActorLocation();
	Phase = FMath::FRandRange(0.f, 6.28318f);

	// MID at BeginPlay — the CDO law (GlassWing's pattern).
	UMaterialInterface* BaseMat = LoadObject<UMaterialInterface>(
		nullptr, TEXT("/Game/Art/FX/M_SparkPlasma.M_SparkPlasma"));
	if (!BaseMat)
	{
		BaseMat = LoadObject<UMaterialInterface>(
			nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	}
	if (BaseMat)
	{
		UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(BaseMat, this);
		MID->SetVectorParameterValue(TEXT("Tint"), GlowTint);
		MID->SetVectorParameterValue(TEXT("Color"), GlowTint);
		WingA->SetMaterial(0, MID);
		WingB->SetMaterial(0, MID);
	}
}

void ALeafGlider::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const float T = GetWorld() ? static_cast<float>(GetWorld()->GetTimeSeconds()) : 0.f;
	const float A = Phase + FMath::DegreesToRadians(OrbitSpeed) * T / 10.f;
	// The spiral breath: slow sink, brisker relift (the wind-breath's cousin).
	const float CycleT = FMath::Fmod(T + Phase * 3.f, FMath::Max(CyclePeriod, 1.f))
	                     / FMath::Max(CyclePeriod, 1.f);
	const float Sink = DropDepth * 0.5f * (1.f - FMath::Cos(6.28318f * CycleT));
	SetActorLocation(FVector(Home.X + FMath::Cos(A) * OrbitRadius,
	                         Home.Y + FMath::Sin(A) * OrbitRadius,
	                         Home.Z - Sink));
	// Face the direction of travel, banked into the turn.
	SetActorRotation(FRotator(-8.f + 10.f * FMath::Sin(T * 0.7f + Phase),
	                          FMath::RadiansToDegrees(A) + 90.f,
	                          25.f * FMath::Sin(T * 0.9f + Phase)));
}
