// Super Claude Bros 2 — THE UNLIGHT, the TRUE final boss (Story Bible / Powers
// Codex §3). The Dragonlord undone: it wears his very shape (BORROWED SHAPE — it
// can only wear what others made) in ink-black and violet, and turns his kindness
// inside out. Its power is EXTINGUISH: it snuffs the lanterns and the killing dark
// SPREADS from where each one dies. A thin ASparkRivalBase subclass that reuses
// the entire Dragonlord rig + clips, with a violet material and a hostile soul.

#pragma once

#include "CoreMinimal.h"
#include "SparkRivalBase.h"
#include "Unlight.generated.h"

class UAnimSequence;

UENUM(BlueprintType)
enum class EUnlightMove : uint8
{
	None,
	VoidSweep,    // a wide dark arc — the Wing Sweep, turned to harm
	Extinguish,   // SIGNATURE: snuff nearby lanterns, spread killing void where they die
	VoidLunge     // a dark rush — the Shepherd's shove, made a strike
};

UCLASS()
class AUnlight : public ASparkRivalBase
{
	GENERATED_BODY()

public:
	AUnlight();

	UFUNCTION(BlueprintImplementableEvent, Category = "Unlight")
	void OnUnlightDefeated();

	UFUNCTION(BlueprintImplementableEvent, Category = "Unlight")
	void OnUnlightPhaseChanged(int32 NewPhase);

	// ---------------- Void Sweep ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Moves")
	float SweepTell = 0.7f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Moves")
	float SweepActive = 0.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Moves")
	float SweepRecover = 1.1f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Moves")
	float SweepRadius = 440.f;

	// ---------------- Void Lunge ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Moves")
	float LungeTell = 0.55f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Moves")
	float LungeActive = 0.45f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Moves")
	float LungeRecover = 1.0f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Moves")
	float LungeSpeed = 1500.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Moves")
	float LungeReach = 320.f;

	// ---------------- EXTINGUISH (the unique power) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Extinguish")
	float ExtinguishTell = 0.85f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Extinguish")
	float ExtinguishActive = 0.6f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Extinguish")
	float ExtinguishRecover = 1.3f;
	/** Lanterns within this die when it casts; the void grows from each one. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Extinguish")
	float SnuffRadius = 1100.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Extinguish")
	float VoidSpotRadius = 320.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Extinguish")
	float VoidSpotSeconds = 7.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Extinguish")
	float VoidChipEmbers = 7.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Extinguish")
	float VoidChipInterval = 0.4f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Extinguish")
	int32 MaxVoidSpots = 12;

	// ---------------- Clip windows (BORROWED from the Dragon's scans) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float SweepClipStart = 0.45f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Anim")
	float SweepClipRate = 2.90f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float ExtinguishClipStart = 0.10f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Anim")
	float ExtinguishClipRate = 0.76f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float LungeClipStart = 0.30f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Unlight|Anim")
	float LungeClipRate = 1.41f;

protected:
	virtual void Tick(float DeltaTime) override;   // the void floor chips + spreads

	virtual void SelectMove(float DistToHero) override;
	virtual void StartTelegraph() override;
	virtual void StartAttack() override;
	virtual void TickAttack(float DeltaTime, ASparkHeroCharacter* Hero) override;
	virtual void HandleAttackExpired(ASparkHeroCharacter* Hero) override;
	virtual float GetTriggerRange() const override;
	virtual bool HasMoveSelected() const override { return Move != EUnlightMove::None; }
	virtual void ClearMove() override { Move = EUnlightMove::None; }

	virtual void NotifyRivalDefeated() override { OnUnlightDefeated(); }
	virtual void NotifyRivalPhaseChanged(int32 NewPhase) override { OnUnlightPhaseChanged(NewPhase); }

private:
	void Extinguish();   // snuff lanterns in range, sow void where they die

	EUnlightMove Move = EUnlightMove::None;
	bool bHitThisLunge = false;
	FVector LungeDir = FVector::ForwardVector;

	TArray<FVector> VoidSpots;
	TArray<float> VoidSpotUntil;
	float NextVoidChip = 0.f;
	float NextVoidFx = 0.f;

	UPROPERTY() TObjectPtr<UAnimSequence> SweepAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> ExtinguishAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> LungeAnim;
};
