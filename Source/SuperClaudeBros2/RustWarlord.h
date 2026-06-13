// Super Claude Bros 2 — THE RUST WARLORD, rival #4 (Powers Codex). The FIRST
// thin ASparkRivalBase subclass: the base owns the whole duel framework, so the
// Warlord is just his four moves and his power. He is the SLOW heavy — big tells,
// big openings; he punishes greed where the Stalker punished patience.
//
// His unique power is FURNACE VENT: when you break his armor (a phase threshold)
// he does not merely reel — he ROOTS and the furnace in his chest roars a violet
// heat-cone (area denial, ~3s). The wound becomes a weapon; you wait it out, or
// you DASH THROUGH it (the codex's "before the furnace can be dashed").

#pragma once

#include "CoreMinimal.h"
#include "SparkRivalBase.h"
#include "RustWarlord.generated.h"

class UAnimSequence;

UENUM(BlueprintType)
enum class EWarlordMove : uint8
{
	None,
	HeavySwing,   // the bread-and-butter hammer arc
	AxeChop,      // a long-telegraphed overhead — the biggest punish opening
	SpinSweep,    // a wide spinning sweep (phase 2+): give him room or JUMP
	FurnaceVent   // the signature: armor-break -> rooted violet heat-cone
};

UCLASS()
class ARustWarlord : public ASparkRivalBase
{
	GENERATED_BODY()

public:
	ARustWarlord();

	/** Story seam: the foundry-king kneels, his furnace banked (W4 setup). */
	UFUNCTION(BlueprintImplementableEvent, Category = "Warlord")
	void OnWarlordDefeated();

	UFUNCTION(BlueprintImplementableEvent, Category = "Warlord")
	void OnWarlordPhaseChanged(int32 NewPhase);

	// ---------------- Heavy Swing ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Moves")
	float SwingTell = 0.7f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Moves")
	float SwingActive = 0.4f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Moves")
	float SwingRecover = 1.1f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Moves")
	float SwingReach = 280.f;

	// ---------------- Axe Chop (the telegraphed overhead) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Moves")
	float ChopTell = 1.0f;     // the longest tell — the biggest opening
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Moves")
	float ChopActive = 0.35f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Moves")
	float ChopRecover = 1.5f;  // whiff it and he is wide open
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Moves")
	float ChopReach = 250.f;

	// ---------------- Spin Sweep (wide — phase 2+) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Moves")
	float SweepTell = 0.65f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Moves")
	float SweepActive = 0.45f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Moves")
	float SweepRecover = 1.2f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Moves")
	float SweepRadius = 320.f;   // a wide ring — back off or jump it

	// ---------------- FURNACE VENT (the unique power) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Furnace")
	float VentTell = 0.55f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Furnace")
	float VentActive = 3.0f;     // the area-denial window (codex)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Furnace")
	float VentRecover = 1.3f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Furnace")
	float VentConeHalfAngleDeg = 45.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Furnace")
	float VentConeReach = 420.f;
	/** Chip damage per tick to a hero standing in the cone — dash through to escape. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Furnace")
	float VentTickEmbers = 5.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Furnace")
	float VentTickInterval = 0.35f;

	// ---------------- Clip windows (scan after import; placeholder auto-fit) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float SwingClipStart = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Anim")
	float SwingClipRate = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float ChopClipStart = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Anim")
	float ChopClipRate = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float SweepClipStart = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Anim")
	float SweepClipRate = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float VentClipStart = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warlord|Anim")
	float VentClipRate = 0.f;

protected:
	// ---- pure-virtual seams ----
	virtual void SelectMove(float DistToHero) override;
	virtual void StartTelegraph() override;
	virtual void StartAttack() override;
	virtual void TickAttack(float DeltaTime, ASparkHeroCharacter* Hero) override;
	virtual void HandleAttackExpired(ASparkHeroCharacter* Hero) override;
	virtual float GetTriggerRange() const override;
	virtual bool HasMoveSelected() const override { return Move != EWarlordMove::None; }
	virtual void ClearMove() override { Move = EWarlordMove::None; }

	// ---- hooks ----
	virtual void NotifyRivalDefeated() override { OnWarlordDefeated(); }
	virtual void NotifyRivalPhaseChanged(int32 NewPhase) override;

private:
	EWarlordMove Move = EWarlordMove::None;
	bool bVentPending = false;   // set on armor-break; the next move is the vent
	float NextVentTick = 0.f;

	UPROPERTY() TObjectPtr<UAnimSequence> SwingAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> ChopAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> SweepAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> VentAnim;
};
