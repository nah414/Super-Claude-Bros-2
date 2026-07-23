// Super Claude Bros 2 — THE MOONFLOWER PLATFORM. The Moonworks' payoff verb
// (Roadmap II): a flower that BLOOMS OPEN IN BEAMLIGHT, and its bloom is the
// platform — traversal granted by understanding, the Glade's whole thesis.
// A beam strikes the pistil (its light-drinking heart, held at beam height);
// while light feeds it the bloom opens and the landing disc grows walkable;
// starve it and it folds shut again — gently, after a Charter-kind linger.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MoonflowerPlatform.generated.h"

class UStaticMeshComponent;
class UPointLightComponent;
class UMaterialInstanceDynamic;

UCLASS()
class AMoonflowerPlatform : public AActor
{
	GENERATED_BODY()

public:
	AMoonflowerPlatform();

	/** A beam is on the pistil this frame — drink. */
	void FeedLight();

	UFUNCTION(BlueprintPure, Category = "Moonflower")
	float GetBloom() const { return Bloom; }

	/** Fully-open landing disc scale (engine cylinder is 100uu across). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Moonflower")
	float DiscOpenScale = 2.6f;

	/** Folded-shut stub scale — visible seed of the platform, never a trap. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Moonflower")
	float DiscClosedScale = 0.18f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Moonflower")
	float BloomSeconds = 1.1f;

	/** Kindness linger: light lost mid-jump still lands you (Charter rule 2 —
	    no cheap deaths from a beam nudged a half-second early). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Moonflower")
	float LingerSeconds = 2.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Moonflower")
	float CloseSeconds = 1.8f;

	/** Where the pistil holds its heart — must match the beam plane. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Moonflower")
	float PistilHeight = 150.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Moonflower")
	FLinearColor BloomTint = FLinearColor(0.8f, 1.7f, 1.9f);

	/** Blooms on BeginPlay (hub dressing / the screenshot state). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Moonflower")
	bool bStartBloomed = false;

	/** Open-bloom width in uu. The Meshy mesh is probed at BeginPlay and scaled to
	    hit this — import-time build scales have lied to us once already. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Moonflower")
	float DesiredBloomWidth = 420.f;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(VisibleAnywhere, Category = "Moonflower")
	USceneComponent* VisualRoot;

	/** The walkable payoff: grows from stub to landing pad with the bloom. */
	UPROPERTY(VisibleAnywhere, Category = "Moonflower")
	UStaticMeshComponent* PlatformDisc;

	/** The light-drinking heart the beam must strike (BlockAll so traces land). */
	UPROPERTY(VisibleAnywhere, Category = "Moonflower")
	UStaticMeshComponent* Pistil;

	/** The flower herself — the Meshy stage-29 moonflower when imported,
	    scaling open with the bloom; hidden when only primitives exist. */
	UPROPERTY(VisibleAnywhere, Category = "Moonflower")
	UStaticMeshComponent* BloomMesh;

	UPROPERTY(VisibleAnywhere, Category = "Moonflower")
	UPointLightComponent* BloomLight;

	UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> PistilMID;
	UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> DiscMID;

private:
	float Now() const;

	float Bloom = 0.f;          // 0 folded .. 1 open
	float LastFedTime = -1000.f;
	float PulseClock = 0.f;     // LOAD LAW: lights/tints at 10Hz
	float PulsePhase = 0.f;
	bool bHasBloomMesh = false;
	float BloomBaseScale = 1.f; // probed at BeginPlay: DesiredBloomWidth / mesh width
	bool bLoggedOpen = false;   // MOONWORKS_MARKER fires once per session
};
