// Super Claude Bros 2 — THE DASHBOARD (Adam's RPG round, June 12).
// A framed, code-only Canvas HUD in the Chrome & Ember palette: ember bar,
// power wheel with cooldown sweeps, combo pips, world name, a contextual
// boss/soothe meter, and the controls hints. No assets, every color a knob.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "SparkHeroHUD.generated.h"

UCLASS()
class ASparkHeroHUD : public AHUD
{
	GENERATED_BODY()

public:
	virtual void DrawHUD() override;

	UPROPERTY(EditAnywhere, Category = "Dashboard")
	FLinearColor FrameColor = FLinearColor(0.02f, 0.015f, 0.01f, 0.62f);

	UPROPERTY(EditAnywhere, Category = "Dashboard")
	FLinearColor BorderColor = FLinearColor(1.0f, 0.62f, 0.2f, 0.9f);

	UPROPERTY(EditAnywhere, Category = "Dashboard")
	FLinearColor EmberColor = FLinearColor(1.0f, 0.55f, 0.12f, 1.f);

	UPROPERTY(EditAnywhere, Category = "Dashboard")
	FLinearColor GutterColor = FLinearColor(0.9f, 0.15f, 0.05f, 1.f);

	UPROPERTY(EditAnywhere, Category = "Dashboard")
	FLinearColor SootheColor = FLinearColor(0.35f, 0.95f, 0.4f, 1.f);

private:
	void DrawBar(float X, float Y, float W, float H, float Fraction,
	             const FLinearColor& Fill, float S);
	// LOAD LAW: boss refs re-resolve on a 1s clock, never per frame.
	TWeakObjectPtr<class AKrakenBoss> Kraken;
	TWeakObjectPtr<class AEmberReaver> Reaver;
	TWeakObjectPtr<class AVoidStalker> Stalker;
	TWeakObjectPtr<class ABramblehulk> Hulk;
	float BossScanClock = 0.f;
	double LastScanRealTime = 0.0;
};
