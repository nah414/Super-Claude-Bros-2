#include "SparkHeroGameMode.h"
#include "SparkHeroHUD.h"
#include "Bramblehulk.h"
#include "EmberReaver.h"
#include "KrakenBoss.h"
#include "GladeProwler.h"
#include "RustWarlord.h"
#include "HollowWarden.h"
#include "LumenDragonlord.h"
#include "Unlight.h"
#include "VoidStalker.h"
#include "GuardianFighter.h"
#include "LightNetworkManager.h"
#include "SparkHeroCharacter.h"
#include "SparkHeroineCharacter.h"

#include "Camera/CameraActor.h"
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
#include "Components/AudioComponent.h"
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

	// Duck the world music under the fanfare, then sound the victory sting — the audio half of
	// the celebration (both guarded, so a missing audio pack just stays silent).
	if (MusicComp)
	{
		MusicComp->AdjustVolume(0.6f, 0.12f);   // (fade seconds, target volume multiplier)
	}
	if (USoundBase* Sting = LoadObject<USoundBase>(nullptr,
			TEXT("/Game/Art/Audio/music_victory_sting.music_victory_sting")))
	{
		UGameplayStatics::PlaySound2D(this, Sting, 1.0f);
	}

	// The First Lantern roars: kindle the whole city back to amber — the celebration.
	if (AActor* Found = UGameplayStatics::GetActorOfClass(this, ALightNetworkManager::StaticClass()))
	{
		Cast<ALightNetworkManager>(Found)->KindleGroup(NAME_None, 4.f);
	}
	if (GEngine)
	{
		const FString WonMap = GetWorld() ? GetWorld()->GetMapName() : TEXT("");
		const TCHAR* WinLine = (WonMap.Contains(TEXT("MoonlitGlade")) || WonMap.Contains(TEXT("WorldStageTesting")))
			? TEXT("THE MOONWELL SHINES  —  THE GLADE IS BRIGHT.  THE ROAD GOES ON.")
			: TEXT("THE FIRST LANTERN ROARS  —  ANTHROPICA is lit.  THE ROAD OPENS.");
		GEngine->AddOnScreenDebugMessage(-1, 9.f, FColor::Orange, WinLine);
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

	// THE WORLD ROAD (Adam, July 23: "just like any game — the worlds run in
	// succession"): per-map defaults for the win-travel chain. An explicit
	// EditAnywhere NextWorldMap still wins over the road.
	//   World 1 (the Lantern Climb) -> World 2 (the Moonlit Glade, promoted
	//   off the stage 2026-07-23) -> the Roster Hall curtain call. The stage
	//   (WorldStageTesting) keeps a road to the Hall so win-travel stays
	//   testable while World 3 rises there.
	if (NextWorldMap.IsNone() && GetWorld())
	{
		const FString ThisMap = GetWorld()->GetMapName();
		if (ThisMap.Contains(TEXT("LanternClimb")))
		{
			NextWorldMap = TEXT("MoonlitGlade");
		}
		else if (ThisMap.Contains(TEXT("MoonlitGlade")))
		{
			NextWorldMap = TEXT("RosterHall");
		}
		else if (ThisMap.Contains(TEXT("WorldStageTesting")))
		{
			NextWorldMap = TEXT("RosterHall");
		}
	}

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
	// The Verdant Reach (W3, on the World Stage): NO night crickets, NO glade music —
	// AVerdantBreath owns this world's air (wind bed + gust swells). A future
	// music_reach_loop slots into this same branch.
	const bool bVerdant = GetWorld() && GetWorld()->GetMapName().Contains(TEXT("WorldStageTesting"));
	// NeonCity ambience swapped from amb_rain_loop -> amb_night_loop: the rain was eliminated
	// (Adam, June 19), so World 1 plays a dry night ambience, no rain patter.
	const TCHAR* AmbPath = bNeonCity
		? TEXT("/Game/Art/Audio/amb_night_loop.amb_night_loop")
		: TEXT("/Game/Art/Audio/amb_night_loop.amb_night_loop");
	if (USoundBase* Amb = bVerdant ? nullptr : LoadObject<USoundBase>(nullptr, AmbPath))
	{
		UGameplayStatics::PlaySound2D(this, Amb, 0.7f);
	}

	// NeonCity now plays the UPGRADED v2 track; fall back to the original (or none) if the v2
	// asset isn't imported yet. Retain the component (SpawnSound2D returns it) so the win can
	// DUCK the music under the victory fanfare.
	USoundBase* Music = nullptr;
	if (bNeonCity)
	{
		Music = LoadObject<USoundBase>(nullptr, TEXT("/Game/Art/Audio/music_city_loop_v2.music_city_loop_v2"));
		if (!Music) { Music = LoadObject<USoundBase>(nullptr, TEXT("/Game/Art/Audio/music_city_loop.music_city_loop")); }
	}
	else if (!bVerdant)
	{
		Music = LoadObject<USoundBase>(nullptr, TEXT("/Game/Art/Audio/music_glade_loop.music_glade_loop"));
	}
	if (Music)
	{
		MusicComp = UGameplayStatics::SpawnSound2D(this, Music, 0.5f);
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

		// A parsed delay of <= 0 (e.g. -SCB2ShotDelay=0, or a malformed value that
		// resolves non-positive) fires the capture timer before the offscreen render
		// thread has produced a frame, so FScreenshotRequest never resolves and the
		// process hangs indefinitely. Clamp back to the 3.0s default to stay safe.
		if (Delay <= 0.f)
		{
			UE_LOG(LogTemp, Warning,
				TEXT("SCB2: SCB2ShotDelay resolved to %.3f (<= 0); clamping to 3.0s default."), Delay);
			Delay = 3.f;
		}

		// Optional framing: -SCB2ShotArm=160 pulls the camera in for hero close-ups,
		// -SCB2ShotYaw=180 orbits it (180 = face-on portrait), -SCB2ShotPitch=55
		// tilts it (+ = look up — the Reach's roots_up vantage), and
		// -SCB2ShotAt=x,y,z teleports the hero first (W3 vertical vantages).
		float ShotArm = 0.f, ShotYaw = 0.f, ShotPitch = 0.f;
		FString ShotAt;
		const bool bHasArm = FParse::Value(FCommandLine::Get(), TEXT("SCB2ShotArm="), ShotArm);
		const bool bHasYaw = FParse::Value(FCommandLine::Get(), TEXT("SCB2ShotYaw="), ShotYaw);
		const bool bHasPitch = FParse::Value(FCommandLine::Get(), TEXT("SCB2ShotPitch="), ShotPitch);
		// bShouldStopOnSeparator=false: the value is a comma list; default parsing
		// stops at the first comma and hands back a lone "0".
		const bool bHasAt = FParse::Value(FCommandLine::Get(), TEXT("SCB2ShotAt="), ShotAt,
		                                  /*bShouldStopOnSeparator*/ false);
		if (bHasArm || bHasYaw || bHasPitch || bHasAt)
		{
			if (ASparkHeroCharacter* Hero = Cast<ASparkHeroCharacter>(
					UGameplayStatics::GetPlayerPawn(this, 0)))
			{
				if (bHasAt)
				{
					TArray<FString> Parts;
					ShotAt.ParseIntoArray(Parts, TEXT(","));
					if (Parts.Num() == 3)
					{
						const FVector Dest(FCString::Atof(*Parts[0]),
						                   FCString::Atof(*Parts[1]),
						                   FCString::Atof(*Parts[2]));
						const bool bMoved = Hero->TeleportTo(Dest, Hero->GetActorRotation());
						UE_LOG(LogTemp, Display, TEXT("SCB2: ShotAt teleport to %s -> %s"),
							*Dest.ToCompactString(), bMoved ? TEXT("OK") : TEXT("BLOCKED"));
					}
					else
					{
						UE_LOG(LogTemp, Warning,
							TEXT("SCB2: -SCB2ShotAt wants x,y,z — got '%s'; ignoring."), *ShotAt);
					}
				}
				if (bHasArm)
				{
					Hero->BaseArmLength = ShotArm;
					Hero->ArmLengthLookingDown = ShotArm;
					Hero->ArmLengthLookingUp = ShotArm;
					Hero->SpringArm->TargetArmLength = ShotArm;
					Hero->SpringArm->bEnableCameraLag = false;
					Hero->SpringArm->bEnableCameraRotationLag = false;
				}
				if (bHasYaw || bHasPitch)
				{
					if (AController* C = Hero->GetController())
					{
						C->SetControlRotation(FRotator(ShotPitch, ShotYaw, 0.f));
					}
				}
			}
		}

		// -SCB2ShotCam=x,y,z,pitch,yaw — a FREE camera, detached from the hero.
		// The spring arm's collision probe pins look-up framings at the hero's
		// feet (it cannot descend through the floor), so world-scale vantages
		// (a 400m tree from its roots, the crown looking down) view through a
		// spawned CameraActor instead.
		FString ShotCam;
		if (FParse::Value(FCommandLine::Get(), TEXT("SCB2ShotCam="), ShotCam,
		                  /*bShouldStopOnSeparator*/ false))
		{
			TArray<FString> CamParts;
			ShotCam.ParseIntoArray(CamParts, TEXT(","));
			if (CamParts.Num() == 5)
			{
				const FVector CamLoc(FCString::Atof(*CamParts[0]),
				                     FCString::Atof(*CamParts[1]),
				                     FCString::Atof(*CamParts[2]));
				const FRotator CamRot(FCString::Atof(*CamParts[3]),
				                      FCString::Atof(*CamParts[4]), 0.f);
				if (ACameraActor* Cam = GetWorld()->SpawnActor<ACameraActor>(CamLoc, CamRot))
				{
					// Possession lands AFTER BeginPlay in standalone -game, and the
					// controller's bAutoManageActiveCameraTarget re-targets the pawn a
					// frame later — so the free cam takes the view on a short timer,
					// after possession settles (the KrakenNear pattern).
					FTimerHandle CamTimer;
					GetWorldTimerManager().SetTimer(CamTimer, [this, Cam]()
					{
						if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
						{
							PC->bAutoManageActiveCameraTarget = false;
							PC->SetViewTargetWithBlend(Cam, 0.f);
							UE_LOG(LogTemp, Display,
								TEXT("SCB2: free shot cam took the view at %s"),
								*Cam->GetActorLocation().ToCompactString());
						}
					}, 0.6f, false);
				}
			}
			else
			{
				UE_LOG(LogTemp, Warning,
					TEXT("SCB2: -SCB2ShotCam wants x,y,z,pitch,yaw — got '%s'; ignoring."), *ShotCam);
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

		// -SCB2ProwlerNear: teleport the Glade Prowler to dueling distance (he will
		// SPOT the hero and engage on camera) + log his live animation vitals twice,
		// one second apart — position delta proves whether the pose evaluates.
		if (FParse::Param(FCommandLine::Get(), TEXT("SCB2ProwlerNear")))
		{
			FTimerHandle NearTimer;
			GetWorldTimerManager().SetTimer(NearTimer, [this]()
			{
				AGladeProwler* Prowler = Cast<AGladeProwler>(
					UGameplayStatics::GetActorOfClass(this, AGladeProwler::StaticClass()));
				APawn* Pawn = UGameplayStatics::GetPlayerPawn(this, 0);
				if (Prowler && Pawn)
				{
					Prowler->SetActorLocation(Pawn->GetActorLocation()
						+ Pawn->GetActorForwardVector() * 560.f + FVector(0.f, 0.f, 30.f));
				}
			}, 1.0f, false);

			auto LogVitals = [this](const TCHAR* Tag)
			{
				AGladeProwler* Prowler = Cast<AGladeProwler>(
					UGameplayStatics::GetActorOfClass(this, AGladeProwler::StaticClass()));
				if (!Prowler) { return; }
				// ACharacter's built-in (empty) Mesh comes first — probe the component
				// that actually WEARS the model.
				USkeletalMeshComponent* Body = nullptr;
				TArray<USkeletalMeshComponent*> Bodies;
				Prowler->GetComponents<USkeletalMeshComponent>(Bodies);
				for (USkeletalMeshComponent* B : Bodies)
				{
					if (B && B->GetSkeletalMeshAsset()) { Body = B; break; }
				}
				UE_LOG(LogTemp, Display, TEXT("MOONWORKS_MARKER: prowler skel comps=%d modeled=%d"),
				       Bodies.Num(), Body ? 1 : 0);
				if (!Body) { return; }
				UE_LOG(LogTemp, Display,
					TEXT("MOONWORKS_MARKER: prowler vitals %s: playing=%d pos=%.3f rate=%.2f dilation=%.2f uro=%d tickopt=%d rendered=%d"),
					Tag, Body->IsPlaying() ? 1 : 0, Body->GetPosition(), Body->GetPlayRate(),
					Prowler->CustomTimeDilation, Body->bEnableUpdateRateOptimizations ? 1 : 0,
					static_cast<int32>(Body->VisibilityBasedAnimTickOption),
					Body->bRecentlyRendered ? 1 : 0);
			};
			FTimerHandle ProbeA, ProbeB;
			GetWorldTimerManager().SetTimer(ProbeA, [LogVitals]() { LogVitals(TEXT("t4")); }, 4.0f, false);
			GetWorldTimerManager().SetTimer(ProbeB, [LogVitals]() { LogVitals(TEXT("t5")); }, 5.0f, false);
		}

		// -SCB2ShotPower=bolt|nova|ring [-SCB2ShotTier=3]: cast the power just
		// before the shutter so captures photograph the spectacle (recipe §6:
		// extend the harness per new verb).
		FString ShotPower;
		if (FParse::Value(FCommandLine::Get(), TEXT("SCB2ShotPower="), ShotPower))
		{
			int32 ShotTier = 3;
			FParse::Value(FCommandLine::Get(), TEXT("SCB2ShotTier="), ShotTier);
			FTimerHandle PowerTimer;
			GetWorldTimerManager().SetTimer(PowerTimer, [this, ShotPower, ShotTier]()
			{
				if (ASparkHeroCharacter* PowerHero = Cast<ASparkHeroCharacter>(
						UGameplayStatics::GetPlayerPawn(this, 0)))
				{
					const ESparkPower P =
						ShotPower.Equals(TEXT("nova"), ESearchCase::IgnoreCase) ? ESparkPower::Nova :
						ShotPower.Equals(TEXT("ring"), ESearchCase::IgnoreCase) ? ESparkPower::FireRing :
						ESparkPower::Bolt;
					PowerHero->Debug_CastPower(P, ShotTier);
				}
			}, FMath::Max(Delay - 0.35f, 0.5f), false);
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

		// -SCB2ShotClimb=up|down|hang: nudge the hero into the REAL grab laws just
		// before the shutter (recipe §6: extend the harness per new verb). Spawn
		// beside any wall via -SCB2ShotAt; bClimbAnywhere makes every wall legal.
		FString ShotClimb;
		if (FParse::Value(FCommandLine::Get(), TEXT("SCB2ShotClimb="), ShotClimb))
		{
			const float UpSign = ShotClimb.Equals(TEXT("down"), ESearchCase::IgnoreCase) ? -1.f
			                   : ShotClimb.Equals(TEXT("hang"), ESearchCase::IgnoreCase) ? 0.f : 1.f;
			FTimerHandle ClimbTimer;
			GetWorldTimerManager().SetTimer(ClimbTimer, [this, UpSign]()
			{
				if (ASparkHeroCharacter* Hero = Cast<ASparkHeroCharacter>(
						UGameplayStatics::GetPlayerPawn(this, 0)))
				{
					Hero->Debug_ForceClimb(UpSign);
				}
			}, FMath::Max(Delay - 1.4f, 0.05f), false);
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
