#include "SparkHeroGameMode.h"
#include "SparkHeroCharacter.h"

#include "Engine/World.h"
#include "GameFramework/SpringArmComponent.h"
#include "HAL/PlatformMisc.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Sound/SoundBase.h"
#include "TimerManager.h"
#include "UnrealClient.h"

ASparkHeroGameMode::ASparkHeroGameMode()
{
	DefaultPawnClass = ASparkHeroCharacter::StaticClass();
}

void ASparkHeroGameMode::BeginPlay()
{
	Super::BeginPlay();

	// Night ambience + music (loop flags are set on the SoundWave assets at import;
	// both are optional — the game runs silently before the audio pack is imported).
	if (USoundBase* Amb = LoadObject<USoundBase>(nullptr, TEXT("/Game/Art/Audio/amb_night_loop.amb_night_loop")))
	{
		UGameplayStatics::PlaySound2D(this, Amb, 0.7f);
	}
	if (USoundBase* Music = LoadObject<USoundBase>(nullptr, TEXT("/Game/Art/Audio/music_glade_loop.music_glade_loop")))
	{
		UGameplayStatics::PlaySound2D(this, Music, 0.5f);
	}

	// ----- Claude's eyes: automated capture mode -----
	// Launch with:  -SCB2Shot="C:\path\out.png" [-SCB2ShotDelay=3]
	// The game waits for the world to settle/render, saves a screenshot, then quits.
	// This powers the edit -> build -> screenshot -> Claude-reads-the-PNG loop.
	FString ShotPath;
	if (FParse::Value(FCommandLine::Get(), TEXT("SCB2Shot="), ShotPath))
	{
		float Delay = 3.f;
		FParse::Value(FCommandLine::Get(), TEXT("SCB2ShotDelay="), Delay);

		// Optional framing: -SCB2ShotArm=160 pulls the camera in for hero close-ups,
		// -SCB2ShotYaw=180 orbits it (180 = face-on portrait).
		float ShotArm = 0.f, ShotYaw = 0.f;
		const bool bHasArm = FParse::Value(FCommandLine::Get(), TEXT("SCB2ShotArm="), ShotArm);
		const bool bHasYaw = FParse::Value(FCommandLine::Get(), TEXT("SCB2ShotYaw="), ShotYaw);
		if (bHasArm || bHasYaw)
		{
			if (ASparkHeroCharacter* Hero = Cast<ASparkHeroCharacter>(
					UGameplayStatics::GetPlayerPawn(this, 0)))
			{
				if (bHasArm)
				{
					Hero->BaseArmLength = ShotArm;
					Hero->ArmLengthLookingDown = ShotArm;
					Hero->ArmLengthLookingUp = ShotArm;
					Hero->SpringArm->TargetArmLength = ShotArm;
					Hero->SpringArm->bEnableCameraLag = false;
					Hero->SpringArm->bEnableCameraRotationLag = false;
				}
				if (bHasYaw)
				{
					if (AController* C = Hero->GetController())
					{
						C->SetControlRotation(FRotator(0.f, ShotYaw, 0.f));
					}
				}
			}
		}

		FTimerHandle ShotTimer;
		GetWorldTimerManager().SetTimer(ShotTimer, [this, ShotPath]()
		{
			FScreenshotRequest::RequestScreenshot(ShotPath, /*bShowUI*/ false, /*bAddSuffix*/ false);
			UE_LOG(LogTemp, Display, TEXT("SCB2: screenshot requested -> %s"), *ShotPath);

			// Give the renderer a beat to flush the file, then exit cleanly.
			FTimerHandle QuitTimer;
			GetWorldTimerManager().SetTimer(QuitTimer, []()
			{
				UE_LOG(LogTemp, Display, TEXT("SCB2: screenshot capture complete, exiting."));
				FPlatformMisc::RequestExit(false);
			}, 2.f, false);
		}, Delay, false);
	}
}
