// The Lantern — the smallest unit of the war between light and dark.

#include "Lantern.h"

#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "CheckpointSubsystem.h"
#include "GameFramework/Pawn.h"
#include "InteractionSubsystem.h"
#include "Kismet/GameplayStatics.h"
#include "LightStateComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "SparkHeroGameMode.h"
#include "UObject/ConstructorHelpers.h"

ALantern::ALantern()
{
	PrimaryActorTick.bCanEverTick = true;

	VisualRoot = CreateDefaultSubobject<USceneComponent>(TEXT("VisualRoot"));
	SetRootComponent(VisualRoot);

	PostMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PostMesh"));
	PostMesh->SetupAttachment(VisualRoot);
	PostMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	FlameMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("FlameMesh"));
	FlameMesh->SetupAttachment(VisualRoot);
	FlameMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	Light = CreateDefaultSubobject<UPointLightComponent>(TEXT("Light"));
	Light->SetupAttachment(VisualRoot);
	Light->SetCastShadows(false);

	LightState = CreateDefaultSubobject<ULightStateComponent>(TEXT("LightState"));

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cyl(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	if (Cyl.Succeeded()) { PostMesh->SetStaticMesh(Cyl.Object); }
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (Sphere.Succeeded()) { FlameMesh->SetStaticMesh(Sphere.Object); }
}

void ALantern::BeginPlay()
{
	Super::BeginPlay();

	const float TopZ = PostHeight * 100.f;   // engine cylinder is 100uu tall
	FlameTopZ = TopZ + 6.f;
	PostMesh->SetRelativeLocation(FVector(0.f, 0.f, TopZ * 0.5f));
	PostMesh->SetRelativeScale3D(FVector(0.12f, 0.12f, PostHeight));
	FlameMesh->SetRelativeLocation(FVector(0.f, 0.f, FlameTopZ));
	Light->SetRelativeLocation(FVector(0.f, 0.f, TopZ + 10.f));
	Light->SetAttenuationRadius(LitRadius);
	Light->SetLightColor(FlameColor);

	// The flame GLOWS via the plasma material (additive); MID at BeginPlay (CDO law).
	if (UMaterialInterface* Plasma = LoadObject<UMaterialInterface>(
			nullptr, TEXT("/Game/Art/FX/M_SparkPlasma.M_SparkPlasma")))
	{
		FlameMID = UMaterialInstanceDynamic::Create(Plasma, this);
		FlameMID->SetVectorParameterValue(TEXT("Tint"), FlameColor * 2.4f);
		FlameMesh->SetMaterial(0, FlameMID);
	}

	if (LightState)
	{
		LightState->LitRadius = LitRadius;
		LightState->OnStateChanged.AddDynamic(this, &ALantern::OnLightStateChanged);
	}

	// Register as an interactable so the hero's interaction component can find this lamp
	// (the lantern meshes have no collision, so the focus query uses the registry).
	if (UWorld* W = GetWorld())
	{
		if (UInteractionSubsystem* Sub = W->GetSubsystem<UInteractionSubsystem>())
		{
			Sub->Register(this);
		}
	}

	// A dead lamp waiting to be relit (checkpoint / goal / the Night's work).
	if (bStartDark && LightState)
	{
		LightState->SetState(ELightState::Dark);
		RelightAt = Now() + AutoRelightSeconds;
	}
	else if (bStartGuttering && LightState)
	{
		LightState->SetState(ELightState::Guttering);   // visible dim beckon, still relightable
	}

	PaintIdle();   // paint the current state now
}

float ALantern::Now() const
{
	return GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
}

bool ALantern::IsLit() const
{
	return LightState ? LightState->IsLit() : true;
}

void ALantern::Snuff()
{
	if (!IsLit()) { return; }
	bHolding = false;
	if (LightState) { LightState->SetState(ELightState::Dark); }   // -> OnLightStateChanged -> PaintIdle
	RelightAt = Now() + AutoRelightSeconds;
}

void ALantern::Relight()
{
	if (IsLit()) { return; }
	bHolding = false;
	if (LightState) { LightState->SetState(ELightState::Lit); }

	// A deliberately-relit CHECKPOINT lamp becomes the hero's respawn anchor.
	if (bIsCheckpoint)
	{
		if (UWorld* W = GetWorld())
		{
			if (UCheckpointSubsystem* CP = W->GetSubsystem<UCheckpointSubsystem>())
			{
				CP->SetActiveCheckpoint(this);
			}
		}
	}

	// The First Lantern: relighting it WINS the world.
	if (bIsWorldGoal)
	{
		if (ASparkHeroGameMode* GM = Cast<ASparkHeroGameMode>(UGameplayStatics::GetGameMode(this)))
		{
			GM->OnWorldGoalLit();
		}
	}
}

void ALantern::OnLightStateChanged(ELightState /*NewState*/)
{
	PaintIdle();
}

void ALantern::PaintIdle()
{
	if (bHolding) { return; }   // the flame-climb owns the visuals mid-hold
	const ELightState S = LightState ? LightState->GetState() : ELightState::Lit;
	switch (S)
	{
	case ELightState::Lit:
		Light->SetIntensity(LitIntensity);
		FlameMesh->SetVisibility(true);
		FlameMesh->SetRelativeScale3D(FVector(0.22f));
		break;
	case ELightState::Guttering:
		Light->SetIntensity(LitIntensity * 0.32f);
		FlameMesh->SetVisibility(true);
		FlameMesh->SetRelativeScale3D(FVector(0.13f));
		break;
	case ELightState::Dark:
		// dark — but a faint amber hint when the hero is focused on it (the relight prompt)
		Light->SetIntensity(bFocused ? LitIntensity * 0.08f : 0.f);
		FlameMesh->SetVisibility(false);
		break;
	}
}

void ALantern::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (bHolding) { return; }   // the relight climb drives the visuals

	if (LightState && LightState->IsLit())
	{
		// A small living flicker — desynced per lantern by its position.
		const float Phase = GetActorLocation().X * 0.01f + GetActorLocation().Y * 0.013f;
		Light->SetIntensity(LitIntensity * (0.9f + 0.1f * FMath::Sin(Now() * 6.f + Phase)));
		return;
	}

	// Snuffed. The hero's own light rekindles AMBIENT lamps he passes (checkpoint/goal
	// lamps set RelightByHeroRadius=0, so those require the deliberate HOLD). Only
	// snuffed lanterns ever run this proximity check, so it stays cheap.
	if (RelightByHeroRadius > 0.f)
	{
		if (APawn* Hero = UGameplayStatics::GetPlayerPawn(this, 0))
		{
			if (FVector::Dist(Hero->GetActorLocation(), GetActorLocation()) <= RelightByHeroRadius)
			{
				Relight();
				return;
			}
		}
	}
	if (AutoRelightSeconds > 0.f && Now() >= RelightAt)
	{
		Relight();   // otherwise the world slowly re-warms on its own
	}
}

// ---------------- IInteractable: the relight rite (a flame climbs the wick) ----------------

void ALantern::OnHoldBegin(ASparkHeroCharacter* /*Hero*/)
{
	bHolding = true;
	FlameMesh->SetVisibility(true);
	FlameMesh->SetRelativeScale3D(FVector(0.03f));
	Light->SetIntensity(LitIntensity * 0.10f);
}

void ALantern::OnHoldTick(ASparkHeroCharacter* /*Hero*/, float Progress01)
{
	if (!bHolding) { return; }
	const float P = FMath::Clamp(Progress01, 0.f, 1.f);
	FlameMesh->SetRelativeScale3D(FVector(FMath::Lerp(0.03f, 0.22f, P)));
	Light->SetIntensity(FMath::Lerp(LitIntensity * 0.10f, LitIntensity, P));
}

void ALantern::OnHoldComplete(ASparkHeroCharacter* /*Hero*/)
{
	bHolding = false;
	Relight();   // the rite is done — the lamp is Lit (checkpoint/goal handling layers on top)
}

void ALantern::OnHoldInterrupted(ASparkHeroCharacter* /*Hero*/)
{
	bHolding = false;
	PaintIdle();   // fall back to dark (with the focus hint if still focused)
}

void ALantern::SetFocusHighlight(bool bNewFocused)
{
	bFocused = bNewFocused;
	if (!bHolding) { PaintIdle(); }
}
