#include "EmberDrift.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

AEmberDrift::AEmberDrift()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.033f;   // 30 Hz is plenty for drifting sparks

	Motes = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Motes"));
	SetRootComponent(Motes);
	Motes->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Motes->SetCastShadow(false);
	Motes->SetCanEverAffectNavigation(false);
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (Sphere.Succeeded()) { Motes->SetStaticMesh(Sphere.Object); }
}

float AEmberDrift::Now() const
{
	return GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
}

void AEmberDrift::BeginPlay()
{
	Super::BeginPlay();

	// Glow material: the plasma FX material if present (Tint param), else the
	// engine tintable fallback (Color param). MID at BeginPlay — the CDO law.
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
		MID->SetVectorParameterValue(TEXT("Tint"), Tint);
		MID->SetVectorParameterValue(TEXT("Color"), Tint);
		Motes->SetMaterial(0, MID);
	}

	const int32 N = FMath::Max(1, NumMotes);
	Anchors.Reserve(N);
	Phases.Reserve(N);
	RiseMul.Reserve(N);
	for (int32 i = 0; i < N; ++i)
	{
		Anchors.Add(FVector(FMath::FRandRange(-Extent.X, Extent.X),
		                    FMath::FRandRange(-Extent.Y, Extent.Y),
		                    FMath::FRandRange(-Extent.Z, Extent.Z)));
		Phases.Add(FMath::FRandRange(0.f, 6.28318f));
		RiseMul.Add(FMath::FRandRange(0.7f, 1.4f));
		Motes->AddInstance(FTransform(FQuat::Identity, Anchors[i], FVector(MoteScale)));
	}
}

void AEmberDrift::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const float T = Now();
	const int32 N = Anchors.Num();
	const float Span = 2.f * Extent.Z;
	for (int32 i = 0; i < N; ++i)
	{
		// Rise forever, wrapping bottom-to-top through the volume.
		const float Rise = FMath::Fmod(Anchors[i].Z + Extent.Z + T * RiseSpeed * RiseMul[i], Span);
		const FVector P(
			Anchors[i].X + FMath::Sin(T * 0.6f + Phases[i]) * WanderAmp,
			Anchors[i].Y + FMath::Cos(T * 0.5f + Phases[i] * 1.3f) * WanderAmp,
			-Extent.Z + Rise);
		// A living flicker: each spark breathes at its own tempo.
		const float S = MoteScale * (0.75f + 0.35f * FMath::Sin(T * 7.f + Phases[i] * 5.f));
		Motes->UpdateInstanceTransform(i, FTransform(FQuat::Identity, P, FVector(S)),
		                               /*bWorldSpace*/ false,
		                               /*bMarkRenderStateDirty*/ i == N - 1,
		                               /*bTeleport*/ true);
	}
}
