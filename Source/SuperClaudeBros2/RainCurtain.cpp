#include "RainCurtain.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

ARainCurtain::ARainCurtain()
{
	PrimaryActorTick.bCanEverTick = true;

	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cylinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> RainMat(TEXT("/Game/Art/CityMat/M_RainStreak.M_RainStreak"));

	for (int32 i = 0; i < 3; ++i)
	{
		UStaticMeshComponent* Shell = CreateDefaultSubobject<UStaticMeshComponent>(
			*FString::Printf(TEXT("Shell%d"), i));
		Shell->SetupAttachment(Root);
		Shell->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Shell->SetCastShadow(false);
		if (Cylinder.Succeeded())
		{
			Shell->SetStaticMesh(Cylinder.Object);
		}
		if (RainMat.Succeeded())
		{
			Shell->SetMaterial(0, RainMat.Object);
		}
		// A whisper of tilt so the three layers never align.
		Shell->SetRelativeRotation(FRotator(i == 1 ? 2.5f : 0.f, i * 60.f, i == 2 ? -2.f : 0.f));
		Shells.Add(Shell);
	}
}

void ARainCurtain::BeginPlay()
{
	Super::BeginPlay();

	// Engine cylinder is 100uu across, 100uu tall at scale 1.
	for (int32 i = 0; i < Shells.Num(); ++i)
	{
		const float R = Shells.IsValidIndex(i) && ShellRadii.IsValidIndex(i) ? ShellRadii[i] : 800.f;
		Shells[i]->SetRelativeScale3D(FVector(R / 50.f, R / 50.f, ShellHeight / 100.f));
	}
}

void ARainCurtain::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// Follow the live camera — rain reads around the LENS, not the character.
	if (const APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
	{
		if (PC->PlayerCameraManager)
		{
			FVector Target = PC->PlayerCameraManager->GetCameraLocation();
			Target.Z += HeightOffset;
			SetActorLocation(Target);
		}
	}
	for (int32 i = 0; i < Shells.Num(); ++i)
	{
		const float Dir = (i % 2 == 0) ? 1.f : -1.f;
		Shells[i]->AddRelativeRotation(FRotator(0.f, Dir * DriftDegPerSec * DeltaSeconds, 0.f));
	}
}
