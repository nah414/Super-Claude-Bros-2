// Super Claude Bros 2 — THE FLAGPOLE GOAL. The Mario-style victory pole that crowns the
// spiral staircase. Reach it (walk into it, or press E) and a BANNER RAISES up the mast
// while the city kindles back to amber and the world is won.
//
// Built ASSET-FREE from /Engine/BasicShapes/* (the no-.uasset doctrine, see ALantern), it
// stands beside the guttering First-Lantern beacon at the crown and routes into the SAME
// idempotent win hook — ASparkHeroGameMode::OnWorldGoalLit(). So the hold-E relight rite
// (the lantern) and this touch-the-pole capture coexist: whichever the hero triggers first
// wins, the other becomes a no-op. This actor adds the capture; it never touches the lantern.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Interactable.h"
#include "FlagpoleGoal.generated.h"

class USceneComponent;
class UStaticMeshComponent;
class USphereComponent;
class USoundBase;

UCLASS()
class AFlagpoleGoal : public AActor, public IInteractable
{
	GENERATED_BODY()

public:
	AFlagpoleGoal();

	/** Claim the flag: raise the banner, sound the fanfare, win the world. Idempotent
	    (the bCaptured guard means re-touch / Tap+touch double-fire does nothing). */
	UFUNCTION(BlueprintCallable, Category = "Flagpole")
	void CaptureFlag();

	/** Mast height in engine-cylinder units (the cylinder is 100uu tall); ~14 = a 1400uu pole. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flagpole")
	float PoleHeight = 14.f;

	/** How long the banner takes to climb the mast on capture. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flagpole")
	float RaiseSeconds = 1.5f;

	/** Banner cloth color — warm amber by default, to echo the lantern light law. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flagpole")
	FLinearColor BannerColor = FLinearColor(1.5f, 0.95f, 0.4f);

	/** The claim hit, played the instant the flag is captured. Null = silent (asset-free safe).
	    Autoloaded from /Game/Art/Audio/sfx_capture if left unset and the asset exists. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flagpole|Audio")
	TObjectPtr<USoundBase> CaptureSound;

	/** The rising flourish, played as the banner climbs. Null = silent.
	    Autoloaded from /Game/Art/Audio/sfx_flag_raise if left unset and the asset exists. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flagpole|Audio")
	TObjectPtr<USoundBase> RaiseSound;

	// ---------------- Drama (Adam 2026-07-21: "make the flag light interaction more dramatic") ----------------
	/** Time-dilation rate for the capture slow-mo beat (1 = off). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flagpole|Drama")
	float CaptureSlowMoRate = 0.35f;

	/** Real-time seconds the capture slow-mo holds before snapping back. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flagpole|Drama")
	float CaptureSlowMoSeconds = 0.45f;

	/** Seconds between spark bursts chasing the banner up the mast (0 = off). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flagpole|Drama")
	float RaiseBurstInterval = 0.18f;

	// ---------------- IInteractable (a TAP of E also claims the flag) ----------------
	virtual EInteractKind GetInteractKind() const override { return EInteractKind::Tap; }
	virtual bool CanInteract(const ASparkHeroCharacter* Hero) const override { return !bCaptured; }
	virtual float GetFocusRadius() const override { return 240.f; }
	virtual bool OnInteractTap(ASparkHeroCharacter* Hero) override;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	/** The hero walks into the capture sphere — the Mario "touch the pole" finish. */
	UFUNCTION()
	void OnPoleOverlap(UPrimitiveComponent* OverlappedComp, AActor* OtherActor,
	                   UPrimitiveComponent* OtherComp, int32 OtherBodyIndex,
	                   bool bFromSweep, const FHitResult& SweepResult);

	UPROPERTY(VisibleAnywhere, Category = "Flagpole")
	USceneComponent* VisualRoot;

	UPROPERTY(VisibleAnywhere, Category = "Flagpole")
	UStaticMeshComponent* PoleMesh;

	UPROPERTY(VisibleAnywhere, Category = "Flagpole")
	UStaticMeshComponent* BallMesh;

	UPROPERTY(VisibleAnywhere, Category = "Flagpole")
	UStaticMeshComponent* CrossbarMesh;

	UPROPERTY(VisibleAnywhere, Category = "Flagpole")
	UStaticMeshComponent* BannerMesh;

	UPROPERTY(VisibleAnywhere, Category = "Flagpole")
	USphereComponent* Trigger;

private:
	/** Skip-if-missing autoload of the audio-pack sounds (so the actor needs no Blueprint). */
	void LoadDefaultSounds();

	bool  bCaptured = false;
	bool  bRaising  = false;
	float RaiseElapsed = 0.f;
	float NextRaiseBurstTime = 0.f;    // drama: next spark-burst beat while raising
	FTimerHandle SlowMoTimerHandle;    // drama: restores normal time after the capture beat
	float BannerBottomZ = 0.f;   // banner start height (just above the trigger)
	float BannerTopZ    = 0.f;   // banner finish height (just under the ball topper)

	UPROPERTY() TObjectPtr<class UMaterialInstanceDynamic> BannerMID;
};
