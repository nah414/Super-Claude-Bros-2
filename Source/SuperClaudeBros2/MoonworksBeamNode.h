// Super Claude Bros 2 — THE MOONWORKS. W2's world system: moonbeam optics. A beam
// node emits light, and the world answers — crystals redirect it, prisms split it,
// moonflowers bloom in it, and a certain hill of moss and granite is CALMED by it
// (the soothe channel: the beam kit pointed at a big friend, per Roadmap II).
// This file: the shared node (trace + render + feed + the rotate interaction) and
// the beam SOURCE. Crystals/prisms live in MoonCrystal.h; flowers in
// MoonflowerPlatform.h.
//
// Design laws honored here:
//  - Beams are authored optics, not physics (Roadmap II build note: it needs to
//    FEEL like optics, not be optics) — straight traces, snap-step rotation.
//  - ONE interact verb: a crystal is a Tap — each E press commits one snap step
//    ON THE PRESS (Responsiveness Law); the visual swing is cosmetic interp.
//  - The hero's body blocks a beam (readable, Charter-fair: you can stand in
//    the light, so the light can be stood in).
//  - LOAD LAW: fixed two-beam pool per node, no shadow-casting beam lights,
//    material/light params on the 10Hz ambience clock; transforms per tick.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Interactable.h"
#include "MoonworksBeamNode.generated.h"

class UStaticMeshComponent;
class UPointLightComponent;
class UMaterialInstanceDynamic;

UCLASS()
class AMoonworksBeamNode : public AActor, public IInteractable
{
	GENERATED_BODY()

public:
	AMoonworksBeamNode();

	/** An upstream node's light arrived this frame: drink it and pass it on. */
	void OnBeamFed(float DeltaTime, int32 Depth);

	UFUNCTION(BlueprintPure, Category = "Moonworks")
	bool IsFed() const;

	// ---------------- The optics ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Moonworks|Beam")
	float MaxBeamRange = 6000.f;

	/** Visual half-thickness of the shaft (engine cylinder is 50uu radius). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Moonworks|Beam")
	float BeamRadius = 14.f;

	/** Beams live on one authored plane: emitted this high off the node's base. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Moonworks|Beam")
	float EmitHeight = 150.f;

	/** Moonlight, silver-teal. Brightness War: damped base, shimmer stays small. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Moonworks|Beam")
	FLinearColor BeamTint = FLinearColor(0.55f, 1.6f, 2.0f);

	/** The soothe channel: calm per second a beam feeds the Bramblehulk. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Moonworks|Beam")
	float BeamCalmPerSecond = 10.f;

	/** A node still counts as lit this long after the last photon (hides the
	    one-frame ripple while a chain re-routes). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Moonworks|Beam")
	float FedGraceSeconds = 0.12f;

	/** Chain depth cap — the loop/prism-tree guard (a mirror maze never hangs a frame). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Moonworks|Beam")
	int32 MaxDepth = 8;

	// ---------------- The rotate (the player's verb on the optics) ----------------
	/** Crystals/prisms say true; sources stay world-authored. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Moonworks|Rotate")
	bool bPlayerRotatable = false;

	/** One E-tap = one snap step. 22.5 = 16 stops; authored angles, never free-spin. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Moonworks|Rotate")
	float RotateStepDeg = 22.5f;

	/** Cosmetic swing speed toward the committed stop (the press already counted). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Moonworks|Rotate")
	float RotateInterpSpeed = 9.f;

	// ---------------- IInteractable (Tap = nudge one stop) ----------------
	virtual EInteractKind GetInteractKind() const override { return EInteractKind::Tap; }
	virtual bool CanInteract(const ASparkHeroCharacter* Hero) const override { return bPlayerRotatable; }
	virtual float GetFocusRadius() const override { return 240.f; }
	virtual bool OnInteractTap(ASparkHeroCharacter* Hero) override;
	virtual void SetFocusHighlight(bool bNewFocused) override;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	/** Sources emit with nobody feeding them (the Mirror never sets). */
	virtual bool EmitsUnfed() const { return false; }

	/** Outgoing shafts in WORLD space (after the node's own rotation). */
	virtual void GetOutDirections(TArray<FVector>& Out) const;

	/** Trace + lay the shafts + resolve what the light touched. */
	void Propagate(float DeltaTime, int32 Depth);

	FVector EmitPoint() const;
	float Now() const;

	UPROPERTY(VisibleAnywhere, Category = "Moonworks")
	USceneComponent* VisualRoot;

	/** The node's physical body — blocks beams and feet alike. Prefers the Meshy
	    Moonworks prop when imported; engine primitive until then (Pick chain). */
	UPROPERTY(VisibleAnywhere, Category = "Moonworks")
	UStaticMeshComponent* BodyMesh;

	/** The node's own presence-glow; brightens as the diegetic focus prompt. */
	UPROPERTY(VisibleAnywhere, Category = "Moonworks")
	UPointLightComponent* CrownGlow;

	/** Fixed pool: at most two outgoing shafts (a prism's split). LOAD LAW. */
	UPROPERTY(VisibleAnywhere, Category = "Moonworks")
	UStaticMeshComponent* BeamMesh[2];

	/** Where each shaft lands: a small pooled splash of moonlight. */
	UPROPERTY(VisibleAnywhere, Category = "Moonworks")
	UPointLightComponent* ImpactGlow[2];

	UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> BodyMID;
	UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> BeamMID[2];

	/** The committed stop (press already counted); the mesh swings after it. */
	float TargetYaw = 0.f;

private:
	void LayBeam(int32 Index, const FVector& From, const FVector& To, bool bHitSomething);
	void HideBeams();

	float LastFedTime = -1000.f;
	uint64 PropagatedFrame = 0;   // one propagation per node per frame — the mirror-loop guard
	bool bLoggedFed = false;      // MOONWORKS_MARKER truth channel: once per session
	bool bLoggedSoothe = false;
	bool bFocused = false;
	float ShimmerClock = 0.f;     // LOAD LAW: 10Hz for tints/intensities
	float ShimmerPhase = 0.f;
	bool bBeamVisible[2] = { false, false };
	FVector BeamEnd[2];
};

/** The Mirror's gift made local: a pylon that pours one permanent moonbeam along
    its facing. Where the light goes from there is the player's puzzle. */
UCLASS()
class AMoonBeamSource : public AMoonworksBeamNode
{
	GENERATED_BODY()

public:
	AMoonBeamSource();

protected:
	virtual bool EmitsUnfed() const override { return true; }
};
