#include "SparkHeroHUD.h"

#include "Bramblehulk.h"
#include "EmberMeterComponent.h"
#include "EmberReaver.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "Kismet/GameplayStatics.h"
#include "KrakenBoss.h"
#include "SparkHeroCharacter.h"
#include "SparkHeroineCharacter.h"
#include "SparkRivalBase.h"
#include "VoidStalker.h"

void ASparkHeroHUD::DrawBar(float X, float Y, float W, float H, float Fraction,
                            const FLinearColor& Fill, float S)
{
	DrawRect(FLinearColor(0.f, 0.f, 0.f, 0.6f), X, Y, W, H);
	DrawRect(Fill, X + 2.f * S, Y + 2.f * S,
	         FMath::Clamp(Fraction, 0.f, 1.f) * (W - 4.f * S), H - 4.f * S);
	DrawRect(BorderColor, X, Y, W, 1.5f * S);
	DrawRect(BorderColor, X, Y + H - 1.5f * S, W, 1.5f * S);
}

void ASparkHeroHUD::DrawHUD()
{
	Super::DrawHUD();
	if (!Canvas) { return; }
	ASparkHeroCharacter* Hero = Cast<ASparkHeroCharacter>(GetOwningPawn());
	if (!Hero) { return; }

	const float S = Canvas->SizeY / 1080.f;        // DPI scale
	const float W = Canvas->SizeX;
	const float H = Canvas->SizeY;
	UFont* Small = GEngine->GetSmallFont();
	UFont* Medium = GEngine->GetMediumFont();

	// ---- THE FRAME: top + bottom strips with amber edge lines ----
	const float TopH = 58.f * S, BotH = 104.f * S;
	DrawRect(FrameColor, 0, 0, W, TopH);
	DrawRect(FrameColor, 0, H - BotH, W, BotH);
	DrawRect(BorderColor, 0, TopH, W, 2.f * S);
	DrawRect(BorderColor, 0, H - BotH - 2.f * S, W, 2.f * S);

	// ---- Bottom-left: hero name + the EMBER BAR ----
	const bool bSonnet = Hero->IsA(ASparkHeroineCharacter::StaticClass());
	const float BX = 24.f * S, BY = H - BotH + 14.f * S;
	DrawText(bSonnet ? TEXT("SONNET — Keeper of the First Lantern")
	                 : TEXT("CLAUDE — the Spark of the Under-stacks"),
	         BorderColor, BX, BY, Small, S * 1.1f);
	if (UEmberMeterComponent* Meter = Hero->GetEmberMeter())
	{
		const float Frac = Meter->GetFraction();
		const bool bGutter = Frac < 0.25f;
		DrawBar(BX, BY + 22.f * S, 340.f * S, 20.f * S, Frac,
		        Meter->IsInGrace() ? FLinearColor::White : (bGutter ? GutterColor : EmberColor), S);
		DrawText(FString::Printf(TEXT("EMBERS %d"), FMath::RoundToInt(Frac * 100.f)),
		         FLinearColor::White, BX + 4.f * S, BY + 46.f * S, Small, S);
	}

	// ---- Bottom-center: THE POWER WHEEL with cooldown sweeps ----
	struct FSlot { ESparkPower P; const TCHAR* Name; float MaxCd; };
	static const FSlot Slots[3] = {
		{ ESparkPower::Bolt, TEXT("BOLT"), 0.25f },
		{ ESparkPower::Nova, TEXT("NOVA"), 3.0f },
		{ ESparkPower::FireRing, TEXT("RING"), 2.5f } };
	const float SlotW = 96.f * S, SlotH = 46.f * S, Gap = 10.f * S;
	float SX = W * 0.5f - (SlotW * 3.f + Gap * 2.f) * 0.5f;
	const float SY = H - BotH + 26.f * S;
	for (const FSlot& Slot : Slots)
	{
		const bool bSel = Hero->GetSelectedPower() == Slot.P;
		DrawRect(bSel ? BorderColor : FLinearColor(0.f, 0.f, 0.f, 0.7f), SX, SY, SlotW, SlotH);
		const float ReadyIn = Hero->GetPowerReadyIn(Slot.P);
		if (ReadyIn > 0.05f)
		{
			const float CdFrac = FMath::Clamp(ReadyIn / Slot.MaxCd, 0.f, 1.f);
			DrawRect(FLinearColor(0.f, 0.f, 0.f, 0.55f), SX, SY, SlotW, SlotH * CdFrac);
			DrawText(FString::Printf(TEXT("%.1f"), ReadyIn), FLinearColor::White,
			         SX + SlotW - 30.f * S, SY + 4.f * S, Small, S);
		}
		DrawText(Slot.Name, bSel ? FLinearColor::Black : BorderColor,
		         SX + 10.f * S, SY + SlotH * 0.5f - 7.f * S, Medium, S * 0.9f);
		SX += SlotW + Gap;
	}
	DrawText(TEXT("WHEEL select · F fire"), FLinearColor(1, 1, 1, 0.5f),
	         W * 0.5f - 70.f * S, SY + SlotH + 4.f * S, Small, S * 0.9f);

	// ---- Bottom-right: COMBO PIPS + family + carry state ----
	const float PX = W - 250.f * S, PY = H - BotH + 22.f * S;
	const bool bKick = Hero->GetStrikeFamily() == EStrikeFamily::Kick;
	DrawText(Hero->IsCarrying() ? TEXT("CARRYING — LMB throw / E drop")
	                            : (bKick ? TEXT("KICKS") : TEXT("PUNCHES")),
	         BorderColor, PX, PY, Small, S * 1.1f);
	for (int32 i = 0; i < 3; ++i)
	{
		const bool bLit = Hero->IsStriking() && Hero->GetComboBeat() >= i;
		DrawRect(bLit ? EmberColor : FLinearColor(0.f, 0.f, 0.f, 0.6f),
		         PX + i * 30.f * S, PY + 22.f * S, 22.f * S, 14.f * S);
	}
	if (Hero->IsChargingStrike())
	{
		DrawText(TEXT("CHARGING…"), FLinearColor::White, PX, PY + 42.f * S, Small, S);
	}

	// ---- Top-left: world name + power level ----
	const FString Map = GetWorld() ? GetWorld()->GetMapName() : TEXT("");
	const TCHAR* WorldName =
		Map.Contains(TEXT("NeonCity")) ? TEXT("ANTHROPICA — Festival District") :
		Map.Contains(TEXT("RosterHall")) ? TEXT("THE ROSTER HALL") :
		Map.Contains(TEXT("MoonlitGlade")) ? TEXT("THE MOONLIT GLADE") :
		Map.Contains(TEXT("FeelGym")) ? TEXT("THE FEEL GYM") : TEXT("THE LANTERN ROAD");
	DrawText(WorldName, BorderColor, 24.f * S, 12.f * S, Medium, S);
	DrawText(FString::Printf(TEXT("SPARK LEVEL %d"), Hero->PowerLevel),
	         FLinearColor::White, 24.f * S, 34.f * S, Small, S);

	// ---- Top-center: the contextual BOSS BAR (1s cached scan — load law) ----
	const double NowReal = FPlatformTime::Seconds();
	if (NowReal - LastScanRealTime > 1.0)
	{
		LastScanRealTime = NowReal;
		if (!Kraken.IsValid()) { Kraken = Cast<AKrakenBoss>(UGameplayStatics::GetActorOfClass(this, AKrakenBoss::StaticClass())); }
		if (!Reaver.IsValid()) { Reaver = Cast<AEmberReaver>(UGameplayStatics::GetActorOfClass(this, AEmberReaver::StaticClass())); }
		if (!Stalker.IsValid()) { Stalker = Cast<AVoidStalker>(UGameplayStatics::GetActorOfClass(this, AVoidStalker::StaticClass())); }
		if (!Hulk.IsValid()) { Hulk = Cast<ABramblehulk>(UGameplayStatics::GetActorOfClass(this, ABramblehulk::StaticClass())); }
		if (!AnyRival.IsValid()) { AnyRival = Cast<ASparkRivalBase>(UGameplayStatics::GetActorOfClass(this, ASparkRivalBase::StaticClass())); }
	}
	FString BossName;
	float BossFrac = 0.f;
	FLinearColor BossColor = GutterColor;
	if (Kraken.IsValid() && Kraken->IsDueling()) { BossName = TEXT("THE IRON KRAKEN"); BossFrac = Kraken->GetDuelFraction(); }
	else if (Reaver.IsValid() && Reaver->IsDueling()) { BossName = TEXT("THE EMBER REAVER"); BossFrac = Reaver->GetDuelFraction(); }
	else if (Stalker.IsValid() && Stalker->IsDueling()) { BossName = TEXT("THE VOID STALKER"); BossFrac = Stalker->GetDuelFraction(); }
	else if (Hulk.IsValid() && Hulk->IsAwake())
	{
		BossName = TEXT("THE BRAMBLEHULK — soothe him");
		BossFrac = Hulk->GetCalmFraction();
		BossColor = SootheColor;   // rising green = mercy winning
	}
	// Generic: ANY ASparkRivalBase (Warlord/Warden/Dragonlord/Unlight/FoundryKing +
	// the four guardians) — they read their own RivalDisplayName. Last so the legacy
	// hand-checked rivals above keep precedence.
	else if (AnyRival.IsValid() && AnyRival->IsDueling())
	{
		BossName = AnyRival->RivalDisplayName;
		BossFrac = AnyRival->GetDuelFraction();
	}
	if (!BossName.IsEmpty())
	{
		const float BW = 420.f * S;
		DrawText(BossName, FLinearColor::White, W * 0.5f - BW * 0.5f, 8.f * S, Medium, S);
		DrawBar(W * 0.5f - BW * 0.5f, 30.f * S, BW, 16.f * S, BossFrac, BossColor, S);
	}

	// ---- Top-right: the hints panel (the old debug card, framed) ----
	const TCHAR* Hints[] = {
		TEXT("LMB punch ×3   RMB kick ×3   hold = CHARGED"),
		TEXT("F fire power   WHEEL select   Q ring   E grab"),
		TEXT("SPACE jump ×2   SHIFT dash   C crouch   Z zoom   P hero") };
	for (int32 i = 0; i < 3; ++i)
	{
		DrawText(Hints[i], FLinearColor(1, 1, 1, 0.65f), W - 392.f * S, (8.f + i * 15.f) * S, Small, S * 0.92f);
	}
}
