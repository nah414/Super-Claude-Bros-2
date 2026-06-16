// ULightStateComponent — owns the lamp's Lit/Guttering/Dark state, broadcasts changes.

#include "LightStateComponent.h"

ULightStateComponent::ULightStateComponent()
{
	PrimaryComponentTick.bCanEverTick = false;   // pure state; the owner ticks visuals
}

void ULightStateComponent::BeginPlay()
{
	Super::BeginPlay();
	// Broadcast the initial state so the owner paints itself correctly on spawn, and so
	// the LightNetworkManager (which discovers components on its own BeginPlay) sees a
	// settled state. Self-registration into the manager is wired when that system lands.
	OnStateChanged.Broadcast(State);
}

void ULightStateComponent::SetState(ELightState NewState)
{
	if (State == NewState) { return; }
	State = NewState;
	OnStateChanged.Broadcast(State);
}
