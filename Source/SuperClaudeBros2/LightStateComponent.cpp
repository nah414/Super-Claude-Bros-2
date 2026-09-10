// ULightStateComponent — owns the lamp's Lit/Guttering/Dark state, broadcasts changes.

#include "LightStateComponent.h"

#include "CheckpointSubsystem.h"

ULightStateComponent::ULightStateComponent()
{
	PrimaryComponentTick.bCanEverTick = false;   // pure state; the owner ticks visuals
}

void ULightStateComponent::BeginPlay()
{
	Super::BeginPlay();
	// Register with the world's light services so the ember-refill query stays cheap.
	if (UWorld* W = GetWorld())
	{
		if (UCheckpointSubsystem* CP = W->GetSubsystem<UCheckpointSubsystem>())
		{
			CP->RegisterLight(this);
		}
	}
	// Broadcast the initial state so the owner paints itself correctly on spawn.
	OnStateChanged.Broadcast(State);
}

void ULightStateComponent::SetState(ELightState NewState)
{
	if (State == NewState) { return; }
	State = NewState;
	OnStateChanged.Broadcast(State);
}
