#include "VerdantBreath.h"

#include "Components/AudioComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"
#include "Sound/SoundBase.h"

AVerdantBreath::AVerdantBreath()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.1f;   // Load Law: ambience at 10Hz, never per frame.

	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	WindBed = CreateDefaultSubobject<UAudioComponent>(TEXT("WindBed"));
	WindBed->SetupAttachment(Root);
	WindBed->bAutoActivate = false;
	WindBed->bAllowSpatialization = false;

	GustLayer = CreateDefaultSubobject<UAudioComponent>(TEXT("GustLayer"));
	GustLayer->SetupAttachment(Root);
	GustLayer->bAutoActivate = false;
	GustLayer->bAllowSpatialization = false;
}

void AVerdantBreath::BeginPlay()
{
	Super::BeginPlay();

	// Assets load at BeginPlay, nullptr-safe (CDO law) — the actor works muted/still
	// until the Verdant kit exists, and wakes fully once it does.
	BreathMPC = LoadObject<UMaterialParameterCollection>(
		nullptr, TEXT("/Game/Art/Verdant/MPC_VerdantBreath.MPC_VerdantBreath"));

	if (USoundBase* Bed = LoadObject<USoundBase>(
			nullptr, TEXT("/Game/Audio/Verdant/amb_wind_loop.amb_wind_loop")))
	{
		WindBed->SetSound(Bed);
		WindBed->SetVolumeMultiplier(WindBedVolume * 0.55f);
		WindBed->Play();
	}
	static const TCHAR* SwellPaths[3] = {
		TEXT("/Game/Audio/Verdant/amb_gust_a.amb_gust_a"),
		TEXT("/Game/Audio/Verdant/amb_gust_b.amb_gust_b"),
		TEXT("/Game/Audio/Verdant/amb_gust_c.amb_gust_c") };
	for (const TCHAR* Path : SwellPaths)
	{
		if (USoundBase* Swell = LoadObject<USoundBase>(nullptr, Path))
		{
			GustSwells.Add(Swell);
		}
	}

	NextGustTime = GetWorld()->GetTimeSeconds() + FMath::FRandRange(4.f, GustMinInterval);
	UE_LOG(LogTemp, Display, TEXT("REACH_MARKER: VR_BREATH driver up (10Hz, mpc=%d, bed=%d, swells=%d)"),
	       BreathMPC ? 1 : 0, WindBed->GetSound() ? 1 : 0, GustSwells.Num());
}

void AVerdantBreath::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const float T = GetWorld()->GetTimeSeconds();

	const float TwoPi = 6.28318f;
	const float Base = 0.5f
		+ 0.25f * FMath::Sin(TwoPi * T / FMath::Max(1.f, BreathPeriodA))
		+ 0.25f * FMath::Sin(TwoPi * T / FMath::Max(1.f, BreathPeriodB) + 1.3f);

	if (T >= NextGustTime)
	{
		GustT0 = T;
		NextGustTime = T + FMath::FRandRange(GustMinInterval, GustMaxInterval);
		if (GustSwells.Num() > 0)
		{
			GustLayer->SetSound(GustSwells[FMath::RandRange(0, GustSwells.Num() - 1)]);
			GustLayer->Play();
		}
	}
	const float GustX = (T - GustT0) / FMath::Max(0.5f, GustDuration);
	const float GustEnv = (GustX >= 0.f && GustX <= 1.f)
		? FMath::Sin(3.14159f * GustX) * GustStrength : 0.f;

	const float Breath = FMath::Clamp(Base + GustEnv * 0.6f, 0.f, 1.5f);
	if (BreathMPC)
	{
		UKismetMaterialLibrary::SetScalarParameterValue(this, BreathMPC, TEXT("Breath"), Breath);
		UKismetMaterialLibrary::SetScalarParameterValue(this, BreathMPC, TEXT("Gust"), GustEnv);
	}
	WindBed->SetVolumeMultiplier(WindBedVolume * (0.55f + 0.45f * FMath::Clamp(Base, 0.f, 1.f)));
	GustLayer->SetVolumeMultiplier(FMath::Clamp(GustEnv, 0.f, 1.f));

	// One heartbeat line every ~10s — proof of life without log spam.
	if ((TickCount++ % 100) == 0)
	{
		UE_LOG(LogTemp, Display, TEXT("REACH_MARKER: VR_BREATH t=%.1f breath=%.2f gust=%.2f"),
		       T, Breath, GustEnv);
	}
}
