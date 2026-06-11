// Super Claude Bros 2 — the rain.
// Three concentric cylinder shells that follow the player's camera, each skinned
// with the panning M_RainStreak material at a different tilt and drift so the
// layers parallax like real rainfall. Light rain by design — it should read as
// atmosphere backlit by neon, never as noise. All tunables EditAnywhere.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RainCurtain.generated.h"

class UStaticMeshComponent;

UCLASS()
class ARainCurtain : public AActor
{
	GENERATED_BODY()

public:
	ARainCurtain();

	/** Shell radii in uu — inner sells the streaks, outer sells the depth. */
	UPROPERTY(EditAnywhere, Category = "Rain")
	TArray<float> ShellRadii = {500.f, 1100.f, 2000.f};

	/** Vertical span of each shell (uu). */
	UPROPERTY(EditAnywhere, Category = "Rain")
	float ShellHeight = 3200.f;

	/** Slow yaw drift per shell (deg/s) so layers never look static. */
	UPROPERTY(EditAnywhere, Category = "Rain")
	float DriftDegPerSec = 4.f;

	/** How far above the camera the shells are centered. */
	UPROPERTY(EditAnywhere, Category = "Rain")
	float HeightOffset = 600.f;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	UPROPERTY()
	TArray<TObjectPtr<UStaticMeshComponent>> Shells;
};
