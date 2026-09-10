// The Flagpole Goal — the crown's Mario-style victory pole. Touch it (or press E) and the
// banner climbs the mast; the world is won via the lantern's own idempotent win hook.

#include "FlagpoleGoal.h"

#include "Components/SceneComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "InteractionSubsystem.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "SparkCameraShakes.h"
#include "SparkHeroCharacter.h"
#include "SparkHeroGameMode.h"
#include "SparkImpactBurst.h"
#include "GameFramework/PlayerController.h"
#include "Sound/SoundBase.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h"

AFlagpoleGoal::AFlagpoleGoal()
{
	PrimaryActorTick.bCanEverTick = true;   // ticks, but early-outs unless a raise is running

	VisualRoot = CreateDefaultSubobject<USceneComponent>(TEXT("VisualRoot"));
	SetRootComponent(VisualRoot);

	// The capture volume: a generous sphere the hero overlaps on reaching the crown. Query
	// only, ignore everything but pawns (overlap, never block) — the SparkBlast idiom, so the
	// hero is caught without ever being wedged against the thin pole.
	Trigger = CreateDefaultSubobject<USphereComponent>(TEXT("Trigger"));
	Trigger->SetupAttachment(VisualRoot);
	Trigger->InitSphereRadius(250.f);
	Trigger->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Trigger->SetCollisionObjectType(ECC_WorldDynamic);
	Trigger->SetCollisionResponseToAllChannels(ECR_Ignore);
	Trigger->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	Trigger->SetGenerateOverlapEvents(true);

	// All four flag meshes are decorative — NO collision, so only the Trigger participates and
	// the hero never snags on the mast.
	PoleMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PoleMesh"));
	PoleMesh->SetupAttachment(VisualRoot);
	PoleMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	BallMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BallMesh"));
	BallMesh->SetupAttachment(VisualRoot);
	BallMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	CrossbarMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CrossbarMesh"));
	CrossbarMesh->SetupAttachment(VisualRoot);
	CrossbarMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	BannerMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BannerMesh"));
	BannerMesh->SetupAttachment(VisualRoot);
	BannerMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cyl(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	if (Cyl.Succeeded()) { PoleMesh->SetStaticMesh(Cyl.Object); CrossbarMesh->SetStaticMesh(Cyl.Object); }
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (Sphere.Succeeded()) { BallMesh->SetStaticMesh(Sphere.Object); }
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (Cube.Succeeded()) { BannerMesh->SetStaticMesh(Cube.Object); }
}

void AFlagpoleGoal::BeginPlay()
{
	Super::BeginPlay();

	const float TopZ = PoleHeight * 100.f;   // engine cylinder is 100uu tall

	// The mast: a tall thin cylinder, centered, scaled to TopZ.
	PoleMesh->SetRelativeLocation(FVector(0.f, 0.f, TopZ * 0.5f));
	PoleMesh->SetRelativeScale3D(FVector(0.16f, 0.16f, PoleHeight));

	// The ball topper, capping the mast (Mario flagpole signature).
	BallMesh->SetRelativeLocation(FVector(0.f, 0.f, TopZ + 16.f));
	BallMesh->SetRelativeScale3D(FVector(0.5f));

	// A short yardarm near the top, the banner's finish marker, reaching out in +Y.
	CrossbarMesh->SetRelativeLocation(FVector(0.f, 60.f, TopZ - 30.f));
	CrossbarMesh->SetRelativeRotation(FRotator(90.f, 0.f, 0.f));   // lay the cylinder horizontal along +Y
	CrossbarMesh->SetRelativeScale3D(FVector(0.05f, 0.05f, 1.2f));

	// The banner: a flat panel beside the mast that climbs from bottom to top on capture.
	BannerBottomZ = TopZ * 0.12f;
	BannerTopZ    = TopZ - 80.f;
	BannerMesh->SetRelativeLocation(FVector(0.f, 55.f, BannerBottomZ));
	BannerMesh->SetRelativeScale3D(FVector(0.04f, 1.0f, 0.66f));

	// The trigger rides at standing height so the hero overlaps it on arriving at the crown.
	Trigger->SetRelativeLocation(FVector(0.f, 0.f, 150.f));

	// Tint the banner + ball warm amber via the plasma material (the lantern color law). MID at
	// BeginPlay, never the constructor (CDO law). If the FX material is missing, leave default.
	if (UMaterialInterface* Plasma = LoadObject<UMaterialInterface>(
			nullptr, TEXT("/Game/Art/FX/M_SparkPlasma.M_SparkPlasma")))
	{
		BannerMID = UMaterialInstanceDynamic::Create(Plasma, this);
		BannerMID->SetVectorParameterValue(TEXT("Tint"), BannerColor * 2.4f);
		BannerMesh->SetMaterial(0, BannerMID);
		BallMesh->SetMaterial(0, BannerMID);
	}

	LoadDefaultSounds();

	// Register so the hero's E-interaction can focus the pole (a Tap also captures). The flag
	// meshes are NoCollision, so the focus query uses this registry — same as the lantern.
	if (UWorld* W = GetWorld())
	{
		if (UInteractionSubsystem* Sub = W->GetSubsystem<UInteractionSubsystem>())
		{
			Sub->Register(this);
		}
	}

	if (Trigger)
	{
		Trigger->OnComponentBeginOverlap.AddDynamic(this, &AFlagpoleGoal::OnPoleOverlap);
	}
}

void AFlagpoleGoal::LoadDefaultSounds()
{
	// Skip-if-missing autoload (the game runs before the audio pack is imported).
	if (!CaptureSound)
	{
		CaptureSound = LoadObject<USoundBase>(nullptr, TEXT("/Game/Art/Audio/sfx_capture.sfx_capture"));
	}
	if (!RaiseSound)
	{
		RaiseSound = LoadObject<USoundBase>(nullptr, TEXT("/Game/Art/Audio/sfx_flag_raise.sfx_flag_raise"));
	}
}

void AFlagpoleGoal::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!bRaising) { return; }   // idle flagpole = near-zero cost

	RaiseElapsed += DeltaSeconds;
	const float P = FMath::Clamp(RaiseElapsed / FMath::Max(RaiseSeconds, 0.01f), 0.f, 1.f);
	const float Eased = FMath::InterpEaseOut(0.f, 1.f, P, 2.0f);   // snappy pop, decelerating
	const float BannerZ = FMath::Lerp(BannerBottomZ, BannerTopZ, Eased);
	BannerMesh->SetRelativeLocation(FVector(0.f, 55.f, BannerZ));

	// Drama: sparks chase the banner up the mast — the light climbs WITH the flag.
	if (RaiseBurstInterval > 0.f && RaiseElapsed >= NextRaiseBurstTime)
	{
		NextRaiseBurstTime = RaiseElapsed + RaiseBurstInterval;
		const FVector BurstPos = GetActorLocation()
			+ GetActorRotation().RotateVector(FVector(0.f, 55.f, BannerZ));
		ASparkImpactBurst::Burst(this, BurstPos, BannerColor * 1.8f, 0.45f, 1200.f);
	}

	if (P >= 1.f)
	{
		bRaising = false;

		// The summit finale: a crown of light erupts at the ball topper + a camera thump —
		// the banner ARRIVING is its own event, not just the end of a lerp.
		const FVector TopPos = GetActorLocation() + FVector(0.f, 0.f, PoleHeight * 100.f + 16.f);
		ASparkImpactBurst::Burst(this, TopPos, BannerColor * 2.6f, 1.5f, 3800.f);
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
		{
			PC->ClientStartCameraShake(USparkBigLandShake::StaticClass(), 1.2f);
		}
		if (CaptureSound) { UGameplayStatics::PlaySoundAtLocation(this, CaptureSound, TopPos); }
	}
}

void AFlagpoleGoal::CaptureFlag()
{
	if (bCaptured) { return; }   // once only — covers re-overlap, Tap+touch, hero+heroine
	bCaptured = true;
	bRaising = true;
	RaiseElapsed = 0.f;
	NextRaiseBurstTime = 0.f;

	// --- DRAMA (Adam 2026-07-21): the claim is a MOMENT — flash, slow-mo beat, camera thump. ---
	ASparkImpactBurst::Burst(this, GetActorLocation() + FVector(0.f, 0.f, 130.f),
	                         BannerColor * 2.2f, 1.1f, 3200.f);
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
	{
		PC->ClientStartCameraShake(USparkBigLandShake::StaticClass(), 1.6f);
	}
	if (CaptureSlowMoRate > 0.f && CaptureSlowMoRate < 1.f)
	{
		UGameplayStatics::SetGlobalTimeDilation(this, CaptureSlowMoRate);
		if (UWorld* W = GetWorld())
		{
			// Timer runs on DILATED time: duration = real-seconds x rate, so the hold
			// lasts CaptureSlowMoSeconds of wall-clock before snapping back to 1.0.
			W->GetTimerManager().SetTimer(SlowMoTimerHandle,
				FTimerDelegate::CreateWeakLambda(this, [this]()
				{
					UGameplayStatics::SetGlobalTimeDilation(this, 1.f);
				}),
				CaptureSlowMoSeconds * CaptureSlowMoRate, false);
		}
	}

	// The capturing hero performs the flagpole finish — grip the pole, then a fist-pump
	// victory (Meshy stage 36). Null-safe inside the hero if the clips aren't present.
	if (ASparkHeroCharacter* Hero = Cast<ASparkHeroCharacter>(UGameplayStatics::GetPlayerPawn(this, 0)))
	{
		Hero->PlayFlagCapture();
	}

	if (CaptureSound) { UGameplayStatics::PlaySoundAtLocation(this, CaptureSound, GetActorLocation()); }
	if (RaiseSound)   { UGameplayStatics::PlaySoundAtLocation(this, RaiseSound,   GetActorLocation()); }

	// The win: kindle the whole city + (if wired) open the road. Idempotent, so the lantern's
	// own relight route and this capture can both exist — first to fire wins.
	if (ASparkHeroGameMode* GM = Cast<ASparkHeroGameMode>(UGameplayStatics::GetGameMode(this)))
	{
		GM->OnWorldGoalLit();
	}
}

void AFlagpoleGoal::OnPoleOverlap(UPrimitiveComponent* /*OverlappedComp*/, AActor* OtherActor,
	UPrimitiveComponent* /*OtherComp*/, int32 /*OtherBodyIndex*/, bool /*bFromSweep*/,
	const FHitResult& /*SweepResult*/)
{
	if (Cast<ASparkHeroCharacter>(OtherActor))   // catches Sonnet too (she derives from the hero)
	{
		CaptureFlag();
	}
}

bool AFlagpoleGoal::OnInteractTap(ASparkHeroCharacter* /*Hero*/)
{
	CaptureFlag();
	return true;
}
