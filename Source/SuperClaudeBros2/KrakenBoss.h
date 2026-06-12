// Super Claude Bros 2 — THE IRON KRAKEN, rival #1 (spec §4 "the Champion in
// borrowed colors"). The first duelist: player-initiated, telegraph-heavy,
// prideful — every heavy is followed by an opening (Kraken recovery 1.4s, the
// canon number). His unique power is IRON GRIP: he punishes the third identical
// approach by seizing the hero — the grapple legally ignores knockback rules
// for its 1s hold (Powers Codex §3). He NEVER stomps (kit omission, spec §8).
// Duel meter = a reused EmberMeterComponent (its header promised this day).
// Defeat is a state, never Destroy() — this boss has an epilogue to attend.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "SparkContactTypes.h"
#include "KrakenBoss.generated.h"

class ASparkHeroCharacter;
class UEmberMeterComponent;
class USkeletalMeshComponent;
class UStaticMeshComponent;
class UAnimSequence;

UENUM(BlueprintType)
enum class EKrakenState : uint8
{
	Waiting,      // visibly ready; duels are player-initiated (spec §6.1)
	Intro,        // the chest-pound flourish when the hero commits
	Approach,     // slow heavy menace at ~0.9x hero tunings
	Telegraph,    // the theatrical tell — pride is a mechanic
	Attack,       // the active window
	Recover,      // THE OPENING (1.4s after heavies — canon)
	Staggered,    // charged-haymaker reward: the punish window
	Defeated      // kneels in the moss; tears the orange strip (story beat)
};

UENUM(BlueprintType)
enum class EKrakenMove : uint8
{
	None,
	ShowSwing,     // wide haymaker, 0.6s wind-up, big whiff window
	PauldronRush,  // 0.8s crouch-tell -> 1100 uu/s line -> 1.4s recovery
	ChampionsSlam, // leaping ground-pound; ring-shock answer = JUMP
	IronGrip       // the signature: seize, hold 1s, slam
};

UCLASS()
class AKrakenBoss : public ACharacter
{
	GENERATED_BODY()

public:
	AKrakenBoss();

	/** Hero strikes route here (CLASH row: duel meters take 8/8/15 embers). */
	UFUNCTION(BlueprintCallable, Category = "Kraken")
	void TakeStrike(int32 ComboBeat, bool bCharged);

	/** Charged haymaker / future stagger sources: opens the punish window. */
	UFUNCTION(BlueprintCallable, Category = "Kraken")
	void TakeStagger(float Seconds);

	UFUNCTION(BlueprintPure, Category = "Kraken")
	bool IsDefeated() const { return State == EKrakenState::Defeated; }

	/** Story seam: he tears the orange strip from his pauldron (W2 C3). */
	UFUNCTION(BlueprintImplementableEvent, Category = "Kraken")
	void OnKrakenDefeated();

	UFUNCTION(BlueprintImplementableEvent, Category = "Kraken")
	void OnKrakenPhaseChanged(int32 NewPhase);

	// ---------------- Duel tuning (every number spec-cited, all live) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Duel")
	float DuelStartRadius = 900.f;

	/** Walk-away allowed: past this, he stands down and the meter refills. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Duel")
	float DisengageRadius = 1500.f;

	/** ~0.9x the hero's 650 — worse footwork, better reach (spec §4). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Duel")
	float ApproachSpeed = 585.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Duel")
	float TurnRate = 6.f;

	/** CLASH: a landed Kraken hit costs 20 embers (spec §2 damage table). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Duel")
	float DuelHitEmbers = 20.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Duel")
	float KnockbackForce = 950.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Duel")
	float KnockbackLift = 420.f;

	/** Strike embers per beat: lash / lash / haymaker (spec strike row 8/8/15). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Duel")
	float LightStrikeEmbers = 8.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Duel")
	float HeavyStrikeEmbers = 15.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Duel")
	float StaggerSeconds = 2.2f;

	/** Phase thresholds (spec §6.3): new move enters the rotation at each. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Duel")
	float Phase2Fraction = 0.66f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Duel")
	float Phase3Fraction = 0.33f;

	/** Charter rule 7: two hero flame-outs soften the tells by +20%, invisibly. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Duel")
	float TellSoftenScale = 1.2f;

	// ---------------- Show-Swing ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Moves")
	float SwingTell = 0.6f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Moves")
	float SwingActive = 0.35f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Moves")
	float SwingRecover = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Moves")
	float SwingReach = 270.f;

	// ---------------- Pauldron Rush ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Moves")
	float RushTell = 0.8f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Moves")
	float RushSpeed = 1100.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Moves")
	float RushActive = 0.85f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Moves")
	float RushRecover = 1.4f;   // THE opening — canon

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Moves")
	float RushHitRange = 160.f;

	// ---------------- Champion's Slam ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Moves")
	float SlamTell = 0.7f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Moves")
	float SlamRecover = 1.2f;

	/** Ring shock on landing — grounded heroes inside it are hit; JUMP dodges. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Moves")
	float SlamRingRadius = 320.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Moves")
	float SlamLeapSpeed = 620.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Moves")
	float SlamLeapLift = 680.f;

	// ---------------- IRON GRIP (the unique power) ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|IronGrip")
	float GripTell = 0.8f;      // tentacles coil + rear back (codex)

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|IronGrip")
	float GripRange = 350.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|IronGrip")
	float GripPullSpeed = 1400.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|IronGrip")
	float GripHoldSeconds = 1.0f;  // the licensed rule-bend (codex §3)

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|IronGrip")
	float GripSlamForce = 1100.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|IronGrip")
	float GripRecover = 1.6f;   // whiffed grips are the biggest opening of all

	// ---------------- Clip windows (data-scanned June 12; all live) ----------------
	/** Swing scan: wind-up rise peaks frac 0.39 (hips z136, hands z213), the
	    double-hand ground strike lands 0.50-0.53 — start at the rise. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float SwingClipStart = 0.36f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Anim")
	float SwingClipRate = 1.55f;

	/** Slam scan: leap 0.17-0.28, crash-down 0.33-0.44 — the natural clip arc
	    matches the tell+leap+landing mechanic, so auto-fit carries it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float SlamClipStart = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Anim")
	float SlamClipRate = 0.f;

	/** Grip scan: seize-reach 0.19-0.25 (hand z164), hold aloft to 0.7 (z190),
	    throw-down 0.72-0.75 — rate 1.7 syncs the throw to the mechanic's slam. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float GripClipStart = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Anim")
	float GripClipRate = 1.7f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Anim")
	float SkelMeshYaw = -90.f;  // native FBX law

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Anim")
	float SkelMeshScale = 1.f;

	/** Contact Matrix row: Champion 90kg, stomp/dash immune, contact 20. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Kraken|Contact")
	FContactProfile ContactProfile;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaTime) override;
	virtual void Landed(const FHitResult& Hit) override;

	UPROPERTY(VisibleAnywhere, Category = "Kraken")
	USceneComponent* VisualRoot;

	UPROPERTY(VisibleAnywhere, Category = "Kraken")
	USkeletalMeshComponent* KrakenBody;

	UPROPERTY(VisibleAnywhere, Category = "Kraken")
	UStaticMeshComponent* PlaceholderBody;

	UPROPERTY(VisibleAnywhere, Category = "Kraken")
	UEmberMeterComponent* DuelMeter;

	UFUNCTION()
	void HandleCapsuleHit(UPrimitiveComponent* HitComp, AActor* OtherActor,
	                      UPrimitiveComponent* OtherComp, FVector NormalImpulse,
	                      const FHitResult& Hit);

	UFUNCTION()
	void HandleDuelMeterEmpty();

private:
	// ---- state machine ----
	EKrakenState State = EKrakenState::Waiting;
	EKrakenMove Move = EKrakenMove::None;
	float StateUntil = 0.f;
	int32 Phase = 1;
	int32 HeroLossCount = 0;     // Charter 7: softening lives on the boss
	bool bHitThisAttack = false;
	bool bGripHolding = false;
	FVector RushDirection = FVector::ForwardVector;
	bool bSlamAirborne = false;

	// ---- pattern-punish ring buffer (the third identical approach is SEIZED) ----
	uint8 ApproachHistory[3] = {0, 0, 0};
	int32 ApproachWrites = 0;

	// ---- clips (FObjectFinder, nullptr-safe; the boss runs clipless if needed) ----
	UPROPERTY() TObjectPtr<UAnimSequence> IdleAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> WalkAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> ChargeAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> SwingAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> SlamAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> GripAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> StaggerAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> HitReactAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> DefeatAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> TauntAnim;
	bool bHasSkeletalModel = false;
	TObjectPtr<UAnimSequence> CurrentLoop;

	ASparkHeroCharacter* ResolveHero() const;   // P-switch-proof: never cache
	void EnterState(EKrakenState NewState, float Duration);
	void SelectMove(float DistToHero);
	void StartTelegraph();
	void StartAttack();
	void FinishAttack(float RecoverSeconds);
	void TickAttack(float DeltaTime, ASparkHeroCharacter* Hero);
	void LandDuelHit(ASparkHeroCharacter* Hero, float Embers);
	void FaceHero(const ASparkHeroCharacter* Hero, float DeltaTime);
	void PlayLoop(UAnimSequence* Clip, float Rate = 1.f);
	void PlayOneShot(UAnimSequence* Clip, float FitSeconds, float StartFraction = 0.f, float OverrideRate = 0.f);
	void RecordApproach(const ASparkHeroCharacter* Hero);
	bool PatternDemandsGrip() const;
	float TellScale() const { return HeroLossCount >= 2 ? TellSoftenScale : 1.f; }
	float Now() const;
};
