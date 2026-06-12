#include "SparkImpactBurst.h"

#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

ASparkImpactBurst::ASparkImpactBurst()
{
	PrimaryActorTick.bCanEverTick = true;

	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	Core = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Core"));
	Core->SetupAttachment(Root);
	Core->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Core->SetCastShadow(false);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> Plasma(TEXT("/Game/Art/FX/M_SparkPlasma.M_SparkPlasma"));
	if (Sphere.Succeeded()) { Core->SetStaticMesh(Sphere.Object); }
	if (Plasma.Succeeded())
	{
		CoreMID = UMaterialInstanceDynamic::Create(Plasma.Object, this);
		Core->SetMaterial(0, CoreMID);
	}

	Flash = CreateDefaultSubobject<UPointLightComponent>(TEXT("Flash"));
	Flash->SetupAttachment(Root);
	Flash->SetAttenuationRadius(420.f);
	Flash->SetCastShadows(false);

	InitialLifeSpan = 1.f;   // belt and braces past LifeSeconds
}

namespace
{
	TArray<TWeakObjectPtr<ASparkImpactBurst>> GLiveBursts;   // LOAD LAW registry
}

void ASparkImpactBurst::Burst(UObject* WorldContext, const FVector& Location,
                              const FLinearColor& Tint, float Scale,
                              float LightIntensity, float Life)
{
	UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
	if (!World) { return; }

	// THE BURST CEILING: combat stays readable under any load — cosmetic
	// sparkle yields first, the oldest flash yields last, hits always show.
	GLiveBursts.RemoveAll([](const TWeakObjectPtr<ASparkImpactBurst>& B) { return !B.IsValid(); });
	const ASparkImpactBurst* CDO = GetDefault<ASparkImpactBurst>();
	if (GLiveBursts.Num() >= CDO->MaxLiveBurstsSoft && Scale < 0.8f) { return; }
	while (GLiveBursts.Num() >= CDO->MaxLiveBurstsHard && GLiveBursts.Num() > 0)
	{
		if (GLiveBursts[0].IsValid()) { GLiveBursts[0]->Destroy(); }
		GLiveBursts.RemoveAt(0);
	}

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ASparkImpactBurst* B = World->SpawnActor<ASparkImpactBurst>(Location, FRotator::ZeroRotator, Params);
	if (!B) { return; }
	B->BaseTint = Tint;
	B->BaseScale = Scale;
	B->BaseLight = LightIntensity;
	B->LifeSeconds = Life;
	B->Flash->SetLightColor(FLinearColor(Tint.R, Tint.G, Tint.B).GetClamped());
	B->Flash->SetIntensity(LightIntensity);
	GLiveBursts.Add(B);
}

void ASparkImpactBurst::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	Age += DeltaSeconds;
	const float T = FMath::Clamp(Age / FMath::Max(LifeSeconds, 0.05f), 0.f, 1.f);
	const float Ease = 1.f - FMath::Square(1.f - T);              // fast out
	const float Fade = FMath::Square(1.f - T);                    // additive: black = gone

	if (Core)
	{
		const float S = BaseScale * FMath::Lerp(0.25f, 1.5f, Ease);
		Core->SetRelativeScale3D(FVector(S));
	}
	if (CoreMID)
	{
		CoreMID->SetVectorParameterValue(TEXT("Tint"), BaseTint * Fade);
	}
	if (Flash)
	{
		Flash->SetIntensity(BaseLight * Fade);
	}
	if (T >= 1.f) { Destroy(); }
}
