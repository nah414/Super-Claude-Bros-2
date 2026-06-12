// Super Claude Bros 2 — THE BRAMBLEHULK, W2's storm of moss and granite.
// The roster's first SOOTHE boss (Interactivity Guide: mercy as a mechanic,
// boss-scale). He is a COLOSSUS: strikes CLANG off his hide and rebound the
// striker, bolts splash, stomps and dashes mean nothing. He cannot be beaten —
// only CALMED: stand inside the storm with the Spark Aura burning and his calm
// meter fills; his tantrum recovery windows are when the light reaches deepest.
// Violence undoes mercy: every clang costs calm. At full calm he sits down in
// the moss, soothed for good. Three duels teach fighting; he teaches stopping.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "SparkContactTypes.h"
#include "Bramblehulk.generated.h"

class ASparkHeroCharacter;
class UPointLightComponent;
class UAnimSequence;

UENUM(BlueprintType)
enum class EHulkState : uint8
{
	Dormant,     // asleep in the moss, breathing
	Waking,      // the roar — you woke the hill
	Approach,    // lumbering, slow, inevitable
	Telegraph,   // colossal tells (0.9-1.3s — mass is honest)
	Attack,
	Recover,     // THE soothing window (calm fills 1.5x here)
	Soothed      // the storm sits down; permanent, friendly
};

UENUM(BlueprintType)
enum class EHulkMove : uint8 { None, TantrumSlam, QuakeSlam };

UCLASS()
class ABramblehulk : public ACharacter
{
	GENERATED_BODY()

public:
	ABramblehulk();

	/** CLANG (the pre-W4 armor law, Colossus edition): zero damage, a spark,
	    and the STRIKER rebounds. Violence also wakes him and costs calm. */
	UFUNCTION(BlueprintCallable, Category = "Bramblehulk")
	void TakeStrikeClang(ASparkHeroCharacter* Striker, bool bCharged);

	/** Light reaches him: Beacon Wave grants a calm bonus. */
	UFUNCTION(BlueprintCallable, Category = "Bramblehulk")
	void AddCalm(float Amount);

	UFUNCTION(BlueprintPure, Category = "Bramblehulk")
	bool IsSoothed() const { return State == EHulkState::Soothed; }

	UFUNCTION(BlueprintPure, Category = "Bramblehulk")
	float GetCalmFraction() const { return CalmProgress / 100.f; }

	UFUNCTION(BlueprintImplementableEvent, Category = "Bramblehulk")
	void OnBramblehulkSoothed();

	// ---------------- The soothe ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Soothe")
	float CalmPerSecond = 12.f;

	/** During his Recover/Dormant the light reaches deepest. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Soothe")
	float CalmRecoverMultiplier = 1.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Soothe")
	float CalmDecayPerSecond = 4.f;

	/** Every clang of violence undoes this much mercy. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Soothe")
	float CalmLostPerClang = 8.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Soothe")
	float WaveCalmBonus = 12.f;

	// ---------------- The storm ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Storm")
	float WakeRadius = 480.f;

	/** Past this the rage fades and he settles back to sleep. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Storm")
	float ForgetRadius = 1800.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Storm")
	float ApproachSpeed = 380.f;   // slow, inevitable

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Storm")
	float TurnRate = 4.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Storm")
	float TantrumHitEmbers = 20.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Storm")
	float KnockbackForce = 1050.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Storm")
	float KnockbackLift = 460.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Storm")
	float SlamTell = 0.9f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Storm")
	float SlamRingRadius = 320.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Storm")
	float SlamRecover = 1.7f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Storm")
	float QuakeTell = 1.3f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Storm")
	float QuakeRingRadius = 500.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Storm")
	float QuakeRecover = 2.3f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Storm")
	float AttackTriggerRange = 360.f;

	// ---------------- Clip windows (scan-solved June 12; all live) ----------------
	/** Slam: window the loop's back half — warning stomp at 0.36s into the tell,
	    payoff stomp (beat frac 0.83) lands EXACTLY on the 0.9s ring. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float SlamClipStart = 0.45f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Anim")
	float SlamClipRate = 0.59f;

	/** Quake: open on the arms-high charge hold; the plunge impact (frac 0.57)
	    lands at 1.306s = the ring at tell end; crater hold + rise then SHOW
	    (the one-shot guard keeps the Recover loop from decapitating them). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float QuakeClipStart = 0.1f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Anim")
	float QuakeClipRate = 1.08f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Anim")
	float SkelMeshYaw = -90.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Anim")
	float SkelMeshScale = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Contact")
	FContactProfile ContactProfile;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bramblehulk|Contact")
	float SeparationPush = 2000.f;   // a hill shoulders harder

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaTime) override;

	UPROPERTY(VisibleAnywhere, Category = "Bramblehulk")
	USceneComponent* VisualRoot;

	UPROPERTY(VisibleAnywhere, Category = "Bramblehulk")
	USkeletalMeshComponent* HulkBody;

	UPROPERTY(VisibleAnywhere, Category = "Bramblehulk")
	UStaticMeshComponent* PlaceholderBody;

	/** Green when calm flows in, storm-amber when the tantrum builds. */
	UPROPERTY(VisibleAnywhere, Category = "Bramblehulk")
	UPointLightComponent* MoodLight;

private:
	EHulkState State = EHulkState::Dormant;
	EHulkMove Move = EHulkMove::None;
	float StateUntil = 0.f;
	float CalmProgress = 0.f;
	float WispClock = 0.f;
	bool bRangThisAttack = false;
	/** Calm filled mid-move: he finishes the swing FIRST, then sits (a soothe
	    that interrupts an attack freezes the pose — Adam's June 12 report). */
	bool bSoothePending = false;
	FTimerHandle SettleTimer;
	/** One-shot guard: loops may not replace a one-shot before its visible
	    window ends (a stomped follow-through never existed — the mush bug). */
	float OneShotHoldUntil = -1000.f;
	bool bEverWoken = false;   // once angry, he re-wakes at a wider radius
	float MoodClock = 0.f;     // LOAD LAW: mood light updates at 10Hz, not per-tick

	UPROPERTY() TObjectPtr<UAnimSequence> DormantAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> AlertAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> WalkAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> SlamAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> QuakeAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> RoarAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> HitReactAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> SoothedAnim;
	bool bHasSkeletalModel = false;
	TObjectPtr<UAnimSequence> CurrentLoop;

	ASparkHeroCharacter* ResolveHero() const;
	void EnterState(EHulkState NewState, float Duration);
	void Wake();
	void BecomeSoothed();
	void DeliverRing(ASparkHeroCharacter* Hero, float Radius);
	void TickSoothe(float DeltaTime, ASparkHeroCharacter* Hero);
	void FaceHero(const ASparkHeroCharacter* Hero, float DeltaTime);
	void PlayLoop(UAnimSequence* Clip, float Rate = 1.f);
	void PlayOneShot(UAnimSequence* Clip, float FitSeconds, float StartFraction = 0.f, float OverrideRate = 0.f);
	float Now() const;
};
