// The Flit Moth — it loves the light, and that love is the whole design.

#include "FlitMoth.h"

#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Kismet/GameplayStatics.h"
#include "SparkHeroCharacter.h"
#include "UObject/ConstructorHelpers.h"

AFlitMoth::AFlitMoth()
{
	PrimaryActorTick.bCanEverTick = true;

	VisualRoot = CreateDefaultSubobject<USceneComponent>(TEXT("VisualRoot"));
	SetRootComponent(VisualRoot);

	MothMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MothMesh"));
	MothMesh->SetupAttachment(VisualRoot);
	MothMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);   // fists puff through

	Glow = CreateDefaultSubobject<UPointLightComponent>(TEXT("Glow"));
	Glow->SetupAttachment(VisualRoot);
	Glow->SetRelativeLocation(FVector(0.f, 0.f, 10.f));
	Glow->SetIntensity(220.f);
	Glow->SetAttenuationRadius(180.f);
	Glow->SetLightColor(FLinearColor(1.6f, 1.1f, 0.5f));   // a soft mothlight amber
	Glow->SetCastShadows(false);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Model(TEXT("/Game/Art/Roster/flit_moth/SM_flit_moth.SM_flit_moth"));
	if (Model.Succeeded())
	{
		MothMesh->SetStaticMesh(Model.Object);
		bHasModel = true;
	}
	else
	{
		static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
		if (Sphere.Succeeded()) { MothMesh->SetStaticMesh(Sphere.Object); }
	}
}

void AFlitMoth::BeginPlay()
{
	Super::BeginPlay();
	HomeLoc = GetActorLocation();
	MothMesh->SetRelativeScale3D(FVector(BodyScale));
	MothMesh->SetRelativeRotation(FRotator(0.f, MeshYaw, 0.f));
	// Per-instance desync from the spawn position — no RNG needed.
	Phase = FMath::Frac(HomeLoc.X * 0.013f + HomeLoc.Y * 0.017f) * 6.2832f;
	OrbitAngle = Phase;
}

ASparkHeroCharacter* AFlitMoth::ResolveHero() const
{
	return Cast<ASparkHeroCharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
}

float AFlitMoth::Now() const
{
	return GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
}

void AFlitMoth::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const float T = Now() + Phase;

	// LIGHTLOVE: drift toward the hero and circle them; otherwise ease home.
	FVector Target = HomeLoc;
	ASparkHeroCharacter* Hero = ResolveHero();
	if (Hero && FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= LoveRadius)
	{
		OrbitAngle += FMath::DegreesToRadians(OrbitSpeed) * DeltaSeconds;
		const FVector Light = Hero->GetActorLocation() + FVector(0.f, 0.f, 90.f);
		Target = Light + FVector(FMath::Cos(OrbitAngle), FMath::Sin(OrbitAngle), 0.f) * OrbitRadius;
	}

	FVector Pos = FMath::VInterpConstantTo(GetActorLocation(), Target, DeltaSeconds, DriftSpeed);
	Pos.Z += HoverAmplitude * FMath::Sin(T * HoverHz);   // the hover bob
	SetActorLocation(Pos);

	// Face the way it drifts, with a fluttering wing-beat scale pulse.
	const FVector Vel = (Target - GetActorLocation());
	if (!Vel.IsNearlyZero())
	{
		const FRotator Want(0.f, Vel.Rotation().Yaw + MeshYaw, 0.f);
		MothMesh->SetWorldRotation(FMath::RInterpTo(MothMesh->GetComponentRotation(), Want, DeltaSeconds, 6.f));
	}
	const float Beat = 1.f + 0.12f * FMath::Sin(T * FlutterHz);
	MothMesh->SetRelativeScale3D(FVector(BodyScale * Beat, BodyScale, BodyScale * Beat));
}
