// Super Claude Bros 2 — THE VOID STALKER, rival #3. Ink-black, bone mask, and
// the only rival who wears VILLAIN VIOLET honestly (design law: heroes glow
// amber, villains violet). His power is BLINK-FEINT (Powers Codex §3): he
// telegraphs, VANISHES, and the real strike arrives from a flank you weren't
// watching. His asymmetry is the INTERRUPT: strike him during the blink tell
// and the feint BREAKS — aggression beats him, turtling feeds him.
// Kraken punishes repetition · Reaver punishes face-tanking · Stalker punishes
// passivity. Three duels, three lessons.
//
// Concrete sibling #3 — the ASparkRivalBase extraction is now a dedicated
// refactor session (three proven voices to unify, none worth regressing live).

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "SparkContactTypes.h"
#include "VoidStalker.generated.h"

class ASparkHeroCharacter;
class UEmberMeterComponent;
class UPointLightComponent;
class UAnimSequence;

UENUM(BlueprintType)
enum class EStalkerState : uint8
{
	Waiting, Intro, Approach, Telegraph, Vanished, Attack, Recover, Staggered, Defeated
};

UENUM(BlueprintType)
enum class EStalkerMove : uint8
{
	None,
	ShadowStrike,   // a close blade-elbow — quick, honest
	DoubleCut,      // a two-mark string
	BlinkFeint      // the SIGNATURE: vanish, flank, strike
};

UCLASS()
class AVoidStalker : public ACharacter
{
	GENERATED_BODY()

public:
	AVoidStalker();

	/** CLASH row (8/8/15). Striking him during a BLINK TELL breaks the feint —
	    he staggers instead of vanishing (the duel's lesson: press in). */
	UFUNCTION(BlueprintCallable, Category = "Stalker")
	void TakeStrike(int32 ComboBeat, bool bCharged);

	UFUNCTION(BlueprintCallable, Category = "Stalker")
	void TakeStagger(float Seconds);

	UFUNCTION(BlueprintPure, Category = "Stalker")
	bool IsDefeated() const { return State == EStalkerState::Defeated; }

	bool IsDueling() const { return State != EStalkerState::Waiting && State != EStalkerState::Defeated; }
	float GetDuelFraction() const;

	UFUNCTION(BlueprintImplementableEvent, Category = "Stalker")
	void OnStalkerDefeated();

	UFUNCTION(BlueprintImplementableEvent, Category = "Stalker")
	void OnStalkerPhaseChanged(int32 NewPhase);

	// ---------------- Duel tuning ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Duel")
	float DuelStartRadius = 900.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Duel")
	float DisengageRadius = 1500.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Duel")
	float ApproachSpeed = 660.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Duel")
	float TurnRate = 9.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Duel")
	float DuelHitEmbers = 20.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Duel")
	float KnockbackForce = 780.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Duel")
	float KnockbackLift = 340.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Duel")
	float LightStrikeEmbers = 8.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Duel")
	float HeavyStrikeEmbers = 15.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Duel")
	float StaggerSeconds = 1.8f;

	/** The interrupt reward: a broken feint staggers him this long. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Duel")
	float FeintBreakStagger = 1.4f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Duel")
	float Phase2Fraction = 0.66f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Duel")
	float Phase3Fraction = 0.33f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Duel")
	float TellSoftenScale = 1.2f;

	// ---------------- Shadow Strike / Double Cut ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Moves")
	float StrikeTell = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Moves")
	float StrikeActive = 0.3f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Moves")
	float StrikeRecover = 0.9f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Moves")
	float StrikeReach = 230.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Moves")
	float CutTell = 0.55f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Moves")
	float CutActive = 0.7f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Moves")
	float CutRecover = 1.0f;

	// ---------------- BLINK-FEINT (the unique power) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Blink")
	float BlinkTell = 0.55f;

	/** How long he is GONE between vanish and arrival. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Blink")
	float BlinkGapSeconds = 0.14f;

	/** The rematerialize beat — visible, vulnerable, before the lunge. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Blink")
	float RematerializeSeconds = 0.22f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Blink")
	float BlinkFlankDistance = 240.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Blink")
	float BlinkLungeActive = 0.32f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Blink")
	float BlinkLungeSpeed = 900.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Blink")
	float BlinkLungeReach = 230.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Blink")
	float BlinkRecover = 1.0f;

	// ---------------- VOID SPIRAL (phase 2+: sometimes the ARRIVAL is the weapon) ----------------
	/** Chance a blink arrival detonates as the spinning ring instead of the lunge. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Blink")
	float SpiralChance = 0.3f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Blink")
	float SpiralActive = 0.5f;

	/** Full-circle strike zone — no safe angle; distance is the answer. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Blink")
	float SpiralRadius = 270.f;

	// ---------------- Clip windows (scan after import; all live) ----------------
	// Phase-1 articulation pass: scanned windows (were auto-fit-from-0 = floaty).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float StrikeClipStart = 0.34f;   // scan: thrust reach peak @0.52 of 2.47s

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Anim")
	float StrikeClipRate = 0.89f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float CutClipStart = 0.12f;      // Cut uses the Combo clip: first cut @~0.27 of 2.83s

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Anim")
	float CutClipRate = 0.78f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float LungeClipStart = 0.10f;    // movement-driven: just trim the dead lead-in, auto-fit the rest

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Anim")
	float LungeClipRate = 0.f;

	/** Scan (360 power spin): explosive rotation peaks 0.50-0.52 — start 0.30, rate 1.5. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float SpiralClipStart = 0.30f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Anim")
	float SpiralClipRate = 1.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Anim")
	float SkelMeshYaw = -90.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Anim")
	float SkelMeshScale = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Contact")
	FContactProfile ContactProfile;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stalker|Contact")
	float SeparationPush = 1600.f;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaTime) override;

	UPROPERTY(VisibleAnywhere, Category = "Stalker")
	USceneComponent* VisualRoot;

	UPROPERTY(VisibleAnywhere, Category = "Stalker")
	USkeletalMeshComponent* StalkerBody;

	UPROPERTY(VisibleAnywhere, Category = "Stalker")
	UStaticMeshComponent* PlaceholderBody;

	UPROPERTY(VisibleAnywhere, Category = "Stalker")
	UEmberMeterComponent* DuelMeter;

	/** Violet, honestly worn — the only rival whose tell is his true color. */
	UPROPERTY(VisibleAnywhere, Category = "Stalker")
	UPointLightComponent* TelegraphLight;

	UFUNCTION()
	void HandleDuelMeterEmpty();

private:
	EStalkerState State = EStalkerState::Waiting;
	EStalkerMove Move = EStalkerMove::None;
	float StateUntil = 0.f;
	int32 Phase = 1;
	int32 HeroLossCount = 0;
	bool bHitThisAttack = false;
	int32 CutHitsDone = 0;
	int32 BlinksThisAttack = 0;
	bool bLungeStarted = false;
	bool bSpiralArrival = false;
	FVector LungeDirection = FVector::ForwardVector;

	UPROPERTY() TObjectPtr<UAnimSequence> IdleAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> RunAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> StrikeAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> CutAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> LungeAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> SpiralAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> StaggerAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> HitReactAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> DefeatAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> TauntAnim;
	bool bHasSkeletalModel = false;
	TObjectPtr<UAnimSequence> CurrentLoop;

	ASparkHeroCharacter* ResolveHero() const;
	void EnterState(EStalkerState NewState, float Duration);
	void SelectMove(float DistToHero);
	void StartTelegraph();
	void StartAttack();
	void DoVanish();
	void DoArrive();
	void FinishAttack(float RecoverSeconds);
	void TickAttack(float DeltaTime, ASparkHeroCharacter* Hero);
	void LandDuelHit(ASparkHeroCharacter* Hero, float Embers);
	void FaceHero(const ASparkHeroCharacter* Hero, float DeltaTime);
	void PlayLoop(UAnimSequence* Clip, float Rate = 1.f);
	void PlayOneShot(UAnimSequence* Clip, float FitSeconds, float StartFraction = 0.f, float OverrideRate = 0.f);
	float TellScale() const { return HeroLossCount >= 2 ? TellSoftenScale : 1.f; }
	float Now() const;
};
