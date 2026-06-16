#include "SparkHeroGameMode.h"
#include "SparkHeroHUD.h"
#include "Bramblehulk.h"
#include "EmberReaver.h"
#include "KrakenBoss.h"
#include "RustWarlord.h"
#include "HollowWarden.h"
#include "LumenDragonlord.h"
#include "Unlight.h"
#include "VoidStalker.h"
#include "GuardianFighter.h"
#include "LightNetworkManager.h"
#include "SparkHeroCharacter.h"
#include "SparkHeroineCharacter.h"

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Engine/GameViewportClient.h"
#include "Framework/Application/SlateApplication.h"
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
	HUDClass = ASparkHeroHUD::StaticClass();   // THE DASHBOARD (June 12)
}

UClass* ASparkHeroGameMode::GetDefaultPawnClassForController_Implementation(AController* InController)
{
	// -SCB2Sonnet starts the run as the heroine (capture harness + player choice
	// from a shortcut); in-game P still swaps freely either way.
	if (FParse::Param(FCommandLine::Get(), TEXT("SCB2Sonnet")))
	{
		return ASparkHeroineCharacter::StaticClass();
	}
	return Super::GetDefaultPawnClassForController_Implementation(InController);
}

void ASparkHeroGameMode::OnWorldGoalLit()
{
	if (bWorldWon) { return; }
	bWorldWon = true;

	// The First Lantern roars: kindle the whole city back to amber — the celebration.
	if (AActor* Found = UGameplayStatics::GetActorOfClass(this, ALightNetworkManager::StaticClass()))
	{
		Cast<ALightNetworkManager>(Found)->KindleGroup(NAME_None, 4.f);
	}
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(-1, 9.f, FColor::Orange,
			TEXT("THE FIRST LANTERN ROARS  —  ANTHROPICA is lit.  THE ROAD OPENS."));
	}
	// Travel to the next world after the celebration, if one is wired (else W1 stands alone).
	if (!NextWorldMap.IsNone())
	{
		const FName Map = NextWorldMap;
		GetWorldTimerManager().SetTimer(WinTravelTimer, [this, Map]()
		{
			UGameplayStatics::OpenLevel(this, Map);
		}, 6.f, false);
	}
}

void ASparkHeroGameMode::BeginPlay()
{
	Super::BeginPlay();

	// -game windowed launches can come up WITHOUT keyboard focus (the Live
	// Coding console spawns right after the game window and steals it) — the
	// game then looks completely frozen: every key dead, mouse ignored (Adam's
	// June 12 report). Claim focus OURSELVES, twice: now, and again after the
	// late-arriving thief has come and gone. Clicking must never be required.
	auto ClaimFocus = [this]()
	{
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
		{
			FInputModeGameOnly Mode;
			Mode.SetConsumeCaptureMouseDown(false);
			PC->SetInputMode(Mode);
			PC->bShowMouseCursor = false;
			PC->FlushPressedKeys();
		}
		if (GEngine && GEngine->GameViewport && FSlateApplication::IsInitialized())
		{
			GEngine->GameViewport->GetWindow()->BringToFront(true);
			FSlateApplication::Get().SetAllUserFocusToGameViewport();
		}
	};
	ClaimFocus();
	FTimerHandle FocusTimer;
	GetWorldTimerManager().SetTimer(FocusTimer, ClaimFocus, 1.0f, false);

	// Per-map ambience + music (loop flags set on the SoundWave assets at import;
	// all optional — the game runs silently before the audio pack is imported).
	const bool bNeonCity = GetWorld() && GetWorld()->GetMapName().Contains(TEXT("NeonCity"));
	const TCHAR* AmbPath = bNeonCity
		? TEXT("/Game/Art/Audio/amb_rain_loop.amb_rain_loop")
		: TEXT("/Game/Art/Audio/amb_night_loop.amb_night_loop");
	const TCHAR* MusicPath = bNeonCity
		? TEXT("/Game/Art/Audio/music_city_loop.music_city_loop")
		: TEXT("/Game/Art/Audio/music_glade_loop.music_glade_loop");
	if (USoundBase* Amb = LoadObject<USoundBase>(nullptr, AmbPath))
	{
		UGameplayStatics::PlaySound2D(this, Amb, 0.7f);
	}
	if (USoundBase* Music = LoadObject<USoundBase>(nullptr, MusicPath))
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

		// -SCB2KrakenNear teleports the level's Kraken to dueling distance so
		// captures can photograph telegraphs, slams, and the grip tether.
		if (FParse::Param(FCommandLine::Get(), TEXT("SCB2KrakenNear")))
		{
			FTimerHandle KrakenTimer;
			GetWorldTimerManager().SetTimer(KrakenTimer, [this]()
			{
				AKrakenBoss* Kraken = Cast<AKrakenBoss>(
					UGameplayStatics::GetActorOfClass(this, AKrakenBoss::StaticClass()));
				APawn* Pawn = UGameplayStatics::GetPlayerPawn(this, 0);
				if (Kraken && Pawn)
				{
					Kraken->SetActorLocation(Pawn->GetActorLocation()
						+ Pawn->GetActorForwardVector() * 520.f + FVector(0.f, 0.f, 20.f));
				}
			}, 1.0f, false);
		}

		// -SCB2ReaverNear: same trick for rival #2 (dash trails want a camera).
		if (FParse::Param(FCommandLine::Get(), TEXT("SCB2ReaverNear")))
		{
			FTimerHandle ReaverTimer;
			GetWorldTimerManager().SetTimer(ReaverTimer, [this]()
			{
				AEmberReaver* Reaver = Cast<AEmberReaver>(
					UGameplayStatics::GetActorOfClass(this, AEmberReaver::StaticClass()));
				APawn* Pawn = UGameplayStatics::GetPlayerPawn(this, 0);
				if (Reaver && Pawn)
				{
					Reaver->SetActorLocation(Pawn->GetActorLocation()
						+ Pawn->GetActorForwardVector() * 520.f + FVector(0.f, 0.f, 20.f));
				}
			}, 1.0f, false);
		}

		// -SCB2StalkerNear: rival #3's blink wants a camera too.
		if (FParse::Param(FCommandLine::Get(), TEXT("SCB2StalkerNear")))
		{
			FTimerHandle StalkerTimer;
			GetWorldTimerManager().SetTimer(StalkerTimer, [this]()
			{
				AVoidStalker* Stalker = Cast<AVoidStalker>(
					UGameplayStatics::GetActorOfClass(this, AVoidStalker::StaticClass()));
				APawn* Pawn = UGameplayStatics::GetPlayerPawn(this, 0);
				if (Stalker && Pawn)
				{
					Stalker->SetActorLocation(Pawn->GetActorLocation()
						+ Pawn->GetActorForwardVector() * 520.f + FVector(0.f, 0.f, 20.f));
				}
			}, 1.0f, false);
		}

		// -SCB2BrambleNear: the sleeping hill wakes on camera.
		if (FParse::Param(FCommandLine::Get(), TEXT("SCB2BrambleNear")))
		{
			FTimerHandle BrambleTimer;
			GetWorldTimerManager().SetTimer(BrambleTimer, [this]()
			{
				ABramblehulk* Hulk = Cast<ABramblehulk>(
					UGameplayStatics::GetActorOfClass(this, ABramblehulk::StaticClass()));
				APawn* Pawn = UGameplayStatics::GetPlayerPawn(this, 0);
				if (Hulk && Pawn)
				{
					Hulk->SetActorLocation(Pawn->GetActorLocation()
						+ Pawn->GetActorForwardVector() * 430.f + FVector(0.f, 0.f, 50.f));
				}
			}, 1.0f, false);
		}

		// -SCB2WarlordNear: rival #4's furnace wants a camera too.
		if (FParse::Param(FCommandLine::Get(), TEXT("SCB2WarlordNear")))
		{
			FTimerHandle WarlordTimer;
			GetWorldTimerManager().SetTimer(WarlordTimer, [this]()
			{
				ARustWarlord* Warlord = Cast<ARustWarlord>(
					UGameplayStatics::GetActorOfClass(this, ARustWarlord::StaticClass()));
				APawn* Pawn = UGameplayStatics::GetPlayerPawn(this, 0);
				if (Warlord && Pawn)
				{
					Warlord->SetActorLocation(Pawn->GetActorLocation()
						+ Pawn->GetActorForwardVector() * 540.f + FVector(0.f, 0.f, 20.f));
				}
			}, 1.0f, false);
		}

		// -SCB2WardenNear: the Lamp-Eater wants a camera (watch the lights die).
		if (FParse::Param(FCommandLine::Get(), TEXT("SCB2WardenNear")))
		{
			FTimerHandle WardenTimer;
			GetWorldTimerManager().SetTimer(WardenTimer, [this]()
			{
				AHollowWarden* Warden = Cast<AHollowWarden>(
					UGameplayStatics::GetActorOfClass(this, AHollowWarden::StaticClass()));
				APawn* Pawn = UGameplayStatics::GetPlayerPawn(this, 0);
				if (Warden && Pawn)
				{
					Warden->SetActorLocation(Pawn->GetActorLocation()
						+ Pawn->GetActorForwardVector() * 520.f + FVector(0.f, 0.f, 20.f));
				}
			}, 1.0f, false);
		}

		// -SCB2DragonNear: the final boss wants a camera (the lantern, the sanctuary).
		if (FParse::Param(FCommandLine::Get(), TEXT("SCB2DragonNear")))
		{
			FTimerHandle DragonTimer;
			GetWorldTimerManager().SetTimer(DragonTimer, [this]()
			{
				ALumenDragonlord* Dragon = Cast<ALumenDragonlord>(
					UGameplayStatics::GetActorOfClass(this, ALumenDragonlord::StaticClass()));
				APawn* Pawn = UGameplayStatics::GetPlayerPawn(this, 0);
				if (Dragon && Pawn)
				{
					Dragon->SetActorLocation(Pawn->GetActorLocation()
						+ Pawn->GetActorForwardVector() * 600.f + FVector(0.f, 0.f, 20.f));
				}
			}, 1.0f, false);
		}

		// -SCB2UnlightNear: the true final boss wants a camera (the violet void).
		if (FParse::Param(FCommandLine::Get(), TEXT("SCB2UnlightNear")))
		{
			FTimerHandle UnlightTimer;
			GetWorldTimerManager().SetTimer(UnlightTimer, [this]()
			{
				AUnlight* Unlight = Cast<AUnlight>(
					UGameplayStatics::GetActorOfClass(this, AUnlight::StaticClass()));
				APawn* Pawn = UGameplayStatics::GetPlayerPawn(this, 0);
				if (Unlight && Pawn)
				{
					Unlight->SetActorLocation(Pawn->GetActorLocation()
						+ Pawn->GetActorForwardVector() * 600.f + FVector(0.f, 0.f, 20.f));
				}
			}, 1.0f, false);
		}

		// -SCB2GuardianNear=<ClassName> teleports the named guardian (SleekKnight /
		// HeroicTank / Powerhouse / ClassicSpark) to dueling distance — one flag for
		// all four, matched by class name on the live AGuardianFighter actors.
		FString GuardianName;
		if (FParse::Value(FCommandLine::Get(), TEXT("SCB2GuardianNear="), GuardianName))
		{
			FTimerHandle GuardianTimer;
			GetWorldTimerManager().SetTimer(GuardianTimer, [this, GuardianName]()
			{
				TArray<AActor*> Guardians;
				UGameplayStatics::GetAllActorsOfClass(this, AGuardianFighter::StaticClass(), Guardians);
				APawn* Pawn = UGameplayStatics::GetPlayerPawn(this, 0);
				if (!Pawn) { return; }
				for (AActor* G : Guardians)
				{
					if (G && G->GetClass()->GetName() == GuardianName)
					{
						G->SetActorLocation(Pawn->GetActorLocation()
							+ Pawn->GetActorForwardVector() * 520.f + FVector(0.f, 0.f, 20.f));
						break;
					}
				}
			}, 1.0f, false);
		}

		// -SCB2ShotStrike throws a combo beat just before the shutter so the
		// capture catches the punch at its data-scanned impact frame.
		if (FParse::Param(FCommandLine::Get(), TEXT("SCB2ShotStrike")))
		{
			FTimerHandle StrikeTimer;
			GetWorldTimerManager().SetTimer(StrikeTimer, [this]()
			{
				if (ASparkHeroCharacter* Hero = Cast<ASparkHeroCharacter>(
						UGameplayStatics::GetPlayerPawn(this, 0)))
				{
					Hero->CaptureStrike();
				}
			}, FMath::Max(Delay - 0.15f, 0.05f), false);
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
