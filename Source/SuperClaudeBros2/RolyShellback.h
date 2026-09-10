// Super Claude Bros 2 — THE ROLY SHELLBACK (Powers Codex critters). An armored
// roly-poly. Its power is CANNONBALL: the committed roll — once it commits a
// direction it CANNOT steer (a = g·sinθ; the limitation IS the power). Telegraph,
// dodge the line, then punish the recovery — or stomp it like any Mote.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "SparkContactTypes.h"
#include "RolyShellback.generated.h"

class USceneComponent;
class UStaticMeshComponent;
class ASparkHeroCharacter;

UENUM(BlueprintType)
enum class EShellState : uint8 { Idle, Wind, Roll, Recover, Dead };

UCLASS()
class ARolyShellback : public ACharacter
{
	GENERATED_BODY()

public:
	ARolyShellback();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shellback")
	float BodyScale = 0.45f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shellback")
	float AggroRadius = 750.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shellback")
	float WindSeconds = 0.6f;     // the curl-up tell — your window to read the line

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shellback")
	float RollSpeed = 1150.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shellback")
	float RollSeconds = 1.1f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shellback")
	float RecoverSeconds = 1.3f;   // dizzy and open after the charge

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shellback")
	float RollCooldown = 0.4f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shellback")
	float SpinRate = 720.f;        // degrees/sec visual roll

	/** Mote class: stompable, dashable; rolling into the hero chips embers. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shellback")
	FContactProfile ContactProfile;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shellback")
	float ContactChipEmbers = 8.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shellback")
	float KnockbackForce = 760.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shellback")
	float KnockbackLift = 320.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shellback")
	float StompBounce = 620.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shellback")
	float StompVelocityThreshold = -300.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shellback")
	float MeshYaw = -90.f;

	/** A boss-shell survives this many defeat-hits, flipping BELLY-UP (the soft
	    vulnerable window) between each. Roly = 1: one stomp pops it, never flips.
	    Shellback Alpha sets this to 3 — flip it, stomp it, drive it off. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shellback")
	int32 HitsToDefeat = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shellback")
	float FlipRecoverSeconds = 2.4f;

	/** W3 Alpha law (locked canon): "bait the charge into the bowl's hard knots ->
	    the crash flips him." A committed roll slamming head-on into STATIC
	    architecture flips the shell belly-up (the punish window) — no defeat-hit,
	    just the opening. The Alpha ships with this true; base Rolys keep false. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shellback")
	bool bWallCrashFlips = false;

	/** Seconds between defeat-hits — one punch-combo string can no longer shred the whole
	    health bar in a second (the "boss died in one blow" bug, Adam 2026-07-21). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shellback")
	float DamageCooldown = 0.8f;

	/** Motes die to any beat (mass-class ladder), applied by fist. */
	UFUNCTION(BlueprintCallable, Category = "Shellback")
	void TakeStrike();

	UFUNCTION(BlueprintCallable, Category = "Shellback")
	void TakeStagger(float Seconds);

	UFUNCTION(BlueprintImplementableEvent, Category = "Shellback")
	void OnShellbackPopped(bool bByStomp);

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UFUNCTION()
	void OnCapsuleHit(UPrimitiveComponent* HitComp, AActor* OtherActor, UPrimitiveComponent* OtherComp,
	                  FVector NormalImpulse, const FHitResult& Hit);

	UPROPERTY(VisibleAnywhere, Category = "Shellback")
	USceneComponent* VisualRoot;

	UPROPERTY(VisibleAnywhere, Category = "Shellback")
	UStaticMeshComponent* ShellMesh;

private:
	ASparkHeroCharacter* ResolveHero() const;
	void EnterState(EShellState NewState, float Duration);
	void ReceiveDefeatHit(bool bByStomp);   // boss armor + flip cycle, else Die
	void Die(bool bByStomp);
	float Now() const;
	bool bFlipped = false;
	bool bBossShell = false;        // true when HitsToDefeat > 1 at BeginPlay (the Alpha)
	float LastDefeatHitTime = -1000.f;
	float RollStartTime = -1000.f;  // crash-flip grace: no self-flip in the first instants

	EShellState State = EShellState::Idle;
	float StateUntil = 0.f;
	float NextRollTime = 0.f;
	FVector RollDir = FVector::ForwardVector;   // LOCKED at commit — never re-steered
	bool bHasModel = false;
};
