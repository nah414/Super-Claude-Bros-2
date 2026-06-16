#include "EmberMeterComponent.h"

#include "CheckpointSubsystem.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"

UEmberMeterComponent::UEmberMeterComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UEmberMeterComponent::BeginPlay()
{
	Super::BeginPlay();
	CurrentEmbers = MaxEmbers;
	UpdateFlameVisuals(0.f);
}

float UEmberMeterComponent::Now() const
{
	return GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
}

bool UEmberMeterComponent::IsInGrace() const
{
	return Now() < GraceUntilTime;
}

bool UEmberMeterComponent::ApplyEmberDamage(float Embers)
{
	if (bFlameOut || Embers <= 0.f) { return false; }
	if (IsInGrace()) { return false; }    // the flare ate it — telegraphed safety

	CurrentEmbers = FMath::Max(0.f, CurrentEmbers - Embers);
	GraceUntilTime = Now() + GraceDuration;
	OnEmbersChanged.Broadcast(GetFraction());

	if (CurrentEmbers <= 0.f)
	{
		bFlameOut = true;
		OnFlameOut.Broadcast();          // the owner decides what death means
	}
	return true;
}

void UEmberMeterComponent::Refill(float Embers)
{
	if (Embers <= 0.f) { return; }
	CurrentEmbers = FMath::Min(MaxEmbers, CurrentEmbers + Embers);
	if (CurrentEmbers > 0.f) { bFlameOut = false; }
	OnEmbersChanged.Broadcast(GetFraction());
}

void UEmberMeterComponent::RefillFull()
{
	CurrentEmbers = MaxEmbers;
	bFlameOut = false;
	OnEmbersChanged.Broadcast(1.f);
}

void UEmberMeterComponent::ActivateGuard(float Seconds)
{
	if (bFlameOut) { return; }
	GraceUntilTime = FMath::Max(GraceUntilTime, Now() + Seconds);
}

void UEmberMeterComponent::FlashGlow(float Seconds, float IntensityBoost)
{
	GlowPulseUntil = Now() + Seconds;
	GlowPulseBoost = IntensityBoost;
}

void UEmberMeterComponent::RegisterFlameVisuals(UStaticMeshComponent* InFlame, UPointLightComponent* InGlow)
{
	Flame = InFlame;
	Glow = InGlow;
	UpdateFlameVisuals(0.f);
}

void UEmberMeterComponent::TickComponent(float DeltaTime, ELevelTick TickType,
                                         FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// Drink in lantern warmth: the heroes regain embers inside any lit lantern's radius
	// (canon "stay in the light" — a refuge heals). Gated so only the heroes refill.
	if (bRefillsInLanternLight && !bFlameOut && CurrentEmbers < MaxEmbers && LanternRefillRate > 0.f)
	{
		if (const AActor* OwnerActor = GetOwner())
		{
			if (UWorld* W = GetWorld())
			{
				if (UCheckpointSubsystem* CP = W->GetSubsystem<UCheckpointSubsystem>())
				{
					if (CP->IsInsideRefillZone(OwnerActor->GetActorLocation()))
					{
						Refill(LanternRefillRate * DeltaTime);
					}
				}
			}
		}
	}

	UpdateFlameVisuals(DeltaTime);
}

void UEmberMeterComponent::UpdateFlameVisuals(float DeltaTime)
{
	const float Fraction = GetFraction();

	// Guttering flame: below the gutter line it flickers — the warning IS diegetic
	// (no beeping UI; the world's light level is the player's information).
	float Flicker = 1.f;
	if (Fraction < GutterFraction && !bFlameOut)
	{
		Flicker = 0.65f + 0.35f * FMath::Sin(Now() * 22.f) * FMath::Sin(Now() * 7.3f);
	}
	// Grace flare: the brief post-hit safety reads as the flame burning WHITE-hot.
	const float GraceBoost = IsInGrace() ? 1.8f : 1.f;

	if (UStaticMeshComponent* F = Flame.Get())
	{
		const float Z = bFlameOut ? 0.01f
			: FMath::Lerp(FlameGutterScaleZ, FlameFullScaleZ, Fraction) * Flicker;
		const float XY = bFlameOut ? 0.01f : (0.08f + 0.06f * Fraction);
		F->SetRelativeScale3D(FVector(XY, XY, FMath::Max(Z, 0.01f)));
	}
	const float Pulse = (Now() < GlowPulseUntil) ? GlowPulseBoost : 1.f;
	if (UPointLightComponent* G = Glow.Get())
	{
		G->SetIntensity(bFlameOut ? 0.f : GlowFullIntensity * Fraction * Flicker * GraceBoost * Pulse);
	}
}
