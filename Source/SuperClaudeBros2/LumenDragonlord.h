// Super Claude Bros 2 — THE LUMEN DRAGONLORD, the final boss (Story Bible). The
// checkpoint-keeper, Lumen, in his true form: an emerald biomech dragon-man with
// a lantern burning in his chest. The twist the whole game builds to — his power
// SHEPHERDS you. He does not hurt; he pushes you to SAFETY (Shepherd's Wing) and
// floods the ground with a healing SANCTUARY that refills your embers. "Amber,
// always amber — it was always amber." A thin ASparkRivalBase subclass whose
// moves bend physics toward kindness.
//
// NOTE (for Adam): this is the Hall presence + the kindness-bending move set. The
// EMOTIONAL FINALE (the jump-from-above last blow, his dialogue, whether he is
// "fought" at all) is the game's climax and waits for your design blessing.

#pragma once

#include "CoreMinimal.h"
#include "SparkRivalBase.h"
#include "LumenDragonlord.generated.h"

class UAnimSequence;
class UPointLightComponent;

UENUM(BlueprintType)
enum class EDragonMove : uint8
{
	None,
	WingShove,    // SHEPHERD'S WING — pushes you to safety, never harms
	WingSweep,    // a grand wide arc (a gentle nudge)
	Sanctuary,    // WING-GLOW SANCTUARY — healing ground that refills embers
	FirstFlame    // THE FIRST FLAME — a pillar of amber light (spectacle, phase 2+)
};

UCLASS()
class ALumenDragonlord : public ASparkRivalBase
{
	GENERATED_BODY()

public:
	ALumenDragonlord();

	UFUNCTION(BlueprintImplementableEvent, Category = "Dragonlord")
	void OnDragonlordDefeated();   // the lantern gutters low (it is never truly out)

	UFUNCTION(BlueprintImplementableEvent, Category = "Dragonlord")
	void OnDragonlordPhaseChanged(int32 NewPhase);

	// ---------------- Shepherd's Wing (the protective shove) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Moves")
	float ShoveTell = 0.6f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Moves")
	float ShoveActive = 0.4f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Moves")
	float ShoveRecover = 1.0f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Moves")
	float ShoveReach = 360.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Moves")
	float ShoveForce = 1150.f;     // launches you AWAY (to safety), no damage
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Moves")
	float ShoveLift = 420.f;

	// ---------------- Wing Sweep (a grand, gentle arc) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Moves")
	float SweepTell = 0.7f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Moves")
	float SweepActive = 0.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Moves")
	float SweepRecover = 1.2f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Moves")
	float SweepRadius = 430.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Moves")
	float SweepEmbers = 6.f;       // the lightest brush — he barely touches you

	// ---------------- WING-GLOW SANCTUARY (the healing ground) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Sanctuary")
	float SanctTell = 0.8f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Sanctuary")
	float SanctActive = 0.6f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Sanctuary")
	float SanctRecover = 1.2f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Sanctuary")
	float SanctRadius = 320.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Sanctuary")
	float SanctHealPerSec = 32.f;  // refills the hero's embers — the gift
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Sanctuary")
	float SanctSeconds = 6.0f;     // the ground glows this long after the cast

	// ---------------- The First Flame (spectacle, phase 2+) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Moves")
	float FlameTell = 0.9f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Moves")
	float FlameActive = 0.6f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Moves")
	float FlameRecover = 1.4f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Moves")
	float FlameRadius = 360.f;

	// ---------------- Clip windows (scanned) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float ShoveClipStart = 0.30f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Anim")
	float ShoveClipRate = 1.41f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float SweepClipStart = 0.45f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Anim")
	float SweepClipRate = 2.90f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float SanctClipStart = 0.10f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Anim")
	float SanctClipRate = 0.76f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float FlameClipStart = 0.05f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dragonlord|Anim")
	float FlameClipRate = 0.82f;

protected:
	virtual void Tick(float DeltaTime) override;   // the sanctuary heals + the lantern breathes

	virtual void SelectMove(float DistToHero) override;
	virtual void StartTelegraph() override;
	virtual void StartAttack() override;
	virtual void TickAttack(float DeltaTime, ASparkHeroCharacter* Hero) override;
	virtual void HandleAttackExpired(ASparkHeroCharacter* Hero) override;
	virtual float GetTriggerRange() const override;
	virtual bool HasMoveSelected() const override { return Move != EDragonMove::None; }
	virtual void ClearMove() override { Move = EDragonMove::None; }

	virtual void PostRivalBeginPlay() override;
	virtual void NotifyRivalDefeated() override { OnDragonlordDefeated(); }
	virtual void NotifyRivalPhaseChanged(int32 NewPhase) override { OnDragonlordPhaseChanged(NewPhase); }

	UPROPERTY(VisibleAnywhere, Category = "Dragonlord")
	UPointLightComponent* LanternLight;   // the heart of the game, burning amber

private:
	EDragonMove Move = EDragonMove::None;
	FVector SanctuaryLoc = FVector::ZeroVector;
	float SanctuaryUntil = 0.f;
	bool bSanctuaryActive = false;
	float NextSanctFx = 0.f;

	UPROPERTY() TObjectPtr<UAnimSequence> ShoveAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> SweepAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> SanctuaryAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> FlameAnim;
};
