// Super Claude Bros 2 — THE HOLLOW WARDEN, a major boss (Powers Codex). A
// corrupted knight in black-and-gold plate. Another thin ASparkRivalBase
// subclass — his soul is a sword kit and the dark.
//
// His unique power is LAMP-EATER: his sword arcs SNUFF the lights along their
// path, and the darkness EMPOWERS him (each light eaten shortens his tells — he
// gets faster the darker it gets). In phase 3 he unleashes VOID SPILL: he fights
// with the absence itself, a dark pulse that floods the ground around him.

#pragma once

#include "CoreMinimal.h"
#include "SparkRivalBase.h"
#include "HollowWarden.generated.h"

class UAnimSequence;
class UPointLightComponent;

UENUM(BlueprintType)
enum class EWardenMove : uint8
{
	None,
	Slash,      // a quick horizontal arc
	Judgment,   // a heavy overhead — the biggest punish
	LampArc,    // the SIGNATURE wide arc: it snuffs nearby lights
	VoidSpill   // phase 3: a dark pulse floods the ground
};

UCLASS()
class AHollowWarden : public ASparkRivalBase
{
	GENERATED_BODY()

public:
	AHollowWarden();

	UFUNCTION(BlueprintImplementableEvent, Category = "Warden")
	void OnWardenDefeated();

	UFUNCTION(BlueprintImplementableEvent, Category = "Warden")
	void OnWardenPhaseChanged(int32 NewPhase);

	// ---------------- Slash ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|Moves")
	float SlashTell = 0.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|Moves")
	float SlashActive = 0.3f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|Moves")
	float SlashRecover = 0.8f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|Moves")
	float SlashReach = 250.f;

	// ---------------- Judgment (heavy overhead) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|Moves")
	float JudgTell = 0.85f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|Moves")
	float JudgActive = 0.35f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|Moves")
	float JudgRecover = 1.2f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|Moves")
	float JudgReach = 260.f;

	// ---------------- LAMP-EATER (the signature wide arc) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|LampEater")
	float LampTell = 0.7f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|LampEater")
	float LampActive = 0.45f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|LampEater")
	float LampRecover = 1.0f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|LampEater")
	float LampArcReach = 320.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|LampEater")
	float LampArcHalfAngleDeg = 70.f;   // a WIDE arc
	/** Point lights within this radius are eaten (dimmed) when the arc lands. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|LampEater")
	float LampSnuffRadius = 800.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|LampEater")
	float LampDimFactor = 0.22f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|LampEater")
	float LampDarkSeconds = 4.0f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|LampEater")
	int32 MaxLightsEaten = 24;          // Load Law cap

	// --- the darkness empowers him: each eaten light shortens his next tells ---
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|LampEater")
	int32 MaxDarkStacks = 5;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|LampEater")
	float DarkTellPerStack = 0.06f;     // up to -30% tell at 5 stacks
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|LampEater")
	float DarkStackSeconds = 6.0f;      // a stack fades after this long

	// ---------------- VOID SPILL (phase 3) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|VoidSpill")
	float VoidTell = 0.9f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|VoidSpill")
	float VoidActive = 0.6f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|VoidSpill")
	float VoidRecover = 1.4f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|VoidSpill")
	float VoidRadius = 380.f;

	// ---------------- Clip windows (scan after import) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float SlashClipStart = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|Anim")
	float SlashClipRate = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float JudgClipStart = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|Anim")
	float JudgClipRate = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float LampClipStart = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|Anim")
	float LampClipRate = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float VoidClipStart = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warden|Anim")
	float VoidClipRate = 0.f;

protected:
	virtual void Tick(float DeltaTime) override;   // restores eaten lights + decays stacks

	// ---- seams ----
	virtual void SelectMove(float DistToHero) override;
	virtual void StartTelegraph() override;
	virtual void StartAttack() override;
	virtual void TickAttack(float DeltaTime, ASparkHeroCharacter* Hero) override;
	virtual void HandleAttackExpired(ASparkHeroCharacter* Hero) override;
	virtual float GetTriggerRange() const override;
	virtual bool HasMoveSelected() const override { return Move != EWardenMove::None; }
	virtual void ClearMove() override { Move = EWardenMove::None; }

	// ---- hooks ----
	virtual void ClearActiveMoveState() override;   // releases eaten light early
	virtual void NotifyRivalDefeated() override;
	virtual void NotifyRivalPhaseChanged(int32 NewPhase) override;

private:
	void EatNearbyLights();
	void RestoreEatenLights();
	float DarknessTellMult() const;

	EWardenMove Move = EWardenMove::None;
	bool bVoidPending = false;
	bool bVoidStruck = false;
	int32 DarkStacks = 0;
	float DarkStackFadeTime = 0.f;
	float RestoreLightsTime = 0.f;

	UPROPERTY() TArray<TWeakObjectPtr<UPointLightComponent>> EatenLights;
	TArray<float> EatenOrig;

	UPROPERTY() TObjectPtr<UAnimSequence> SlashAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> JudgmentAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> ChargedAnim;   // the LampArc
	UPROPERTY() TObjectPtr<UAnimSequence> VoidAnim;
};
