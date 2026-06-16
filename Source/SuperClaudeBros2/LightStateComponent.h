// Super Claude Bros 2 — ULightStateComponent: the single Lit / Guttering / Dark source
// of truth on every lamp. It drives nothing on its own — it just OWNS the state and
// broadcasts changes, so the lamp's visuals, the ember-refill system, and the
// LightNetworkManager (which sequences whole groups for "The Night" and every relight
// finale) all talk to one uniform handle. Nullptr-safe; a lamp with no manager present
// still works (the component just never gets sequenced).

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "LightStateComponent.generated.h"

UENUM(BlueprintType)
enum class ELightState : uint8
{
	Lit         UMETA(DisplayName = "Lit"),         // warm, safe, refills embers
	Guttering   UMETA(DisplayName = "Guttering"),   // dying — the moment before dark
	Dark        UMETA(DisplayName = "Dark")         // out; the Hollow's foothold
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnLightStateChanged, ELightState, NewState);

UCLASS(ClassGroup = (SCB2), meta = (BlueprintSpawnableComponent))
class ULightStateComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	ULightStateComponent();

	/** Which named group this lamp belongs to — the LightNetworkManager sequences by group
	    (e.g. "Streets", "FirstLantern") so the Night cascades and the finale kindles. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Light")
	FName GroupName = NAME_None;

	/** A LIT lamp with this set is a warm refuge: it refills the hero's embers in range. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Light")
	bool bRefillsEmbers = true;

	/** The reach of this lamp's warmth (mirrors the owner's lit radius; the refill range). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Light")
	float LitRadius = 520.f;

	/** Fired whenever the state changes — the owner repaints its flame/light here. */
	UPROPERTY(BlueprintAssignable, Category = "Light")
	FOnLightStateChanged OnStateChanged;

	UFUNCTION(BlueprintCallable, Category = "Light")
	void SetState(ELightState NewState);

	UFUNCTION(BlueprintPure, Category = "Light")
	ELightState GetState() const { return State; }

	UFUNCTION(BlueprintPure, Category = "Light")
	bool IsLit() const { return State == ELightState::Lit; }

	/** A warm refuge the ember meter can pull refill from: lit AND flagged to refill. */
	UFUNCTION(BlueprintPure, Category = "Light")
	bool IsRefillZone() const { return State == ELightState::Lit && bRefillsEmbers; }

protected:
	virtual void BeginPlay() override;

private:
	ELightState State = ELightState::Lit;
};
