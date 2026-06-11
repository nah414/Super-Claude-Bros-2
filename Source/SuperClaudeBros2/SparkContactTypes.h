// Super Claude Bros 2 — shared contact-law types.
// The mass-class ladder and per-character contact profile from the design canon
// (SCB2_PHYSICS_RULEBOOK.md §5, SCB2_INTERACTION_SPEC.md §5/§8). Limitations are
// DATA, not prose: every "cannot" a character has lives in its FContactProfile,
// readable in the editor. The Contact Matrix in the spec is the master record —
// per-character values here may not silently diverge from it.

#pragma once

#include "CoreMinimal.h"
#include "SparkContactTypes.generated.h"

/** The knockback ladder. You can stagger your own class and below; one class up
    trades at a discount; two classes up, the contact reverses onto YOU.
    (Δv = J/m — the Warlord ignoring a dash is division, not a special case.) */
UENUM(BlueprintType)
enum class EMassClass : uint8
{
	Mote      UMETA(DisplayName = "Mote (~8 kg: Sprite, Moth, Roly)"),
	Spark     UMETA(DisplayName = "Spark (~60 kg: the heroes)"),
	Champion  UMETA(DisplayName = "Champion (~90 kg: Kraken, Reaver, Stalker)"),
	Colossus  UMETA(DisplayName = "Colossus (~400 kg: Warlord, Bramblehulk, Warden)"),
	Mythic    UMETA(DisplayName = "Mythic (immovable: Dragonlord, Unlight)")
};

/** One row of the Limitations Ledger, attached to a character. Defaults describe
    the friendliest possible body (a Mote you can stomp); heavier and stranger
    characters override per the spec's stat blocks. */
USTRUCT(BlueprintType)
struct FContactProfile
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Contact")
	EMassClass MassClass = EMassClass::Mote;

	/** Colossus armor and stranger things shrug the boot off (stomp reverses to a bonk). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Contact")
	bool bStompImmune = false;

	/** Dash clangs off instead of killing (the W4 armor lesson). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Contact")
	bool bDashImmune = false;

	/** Flit Moths are the canonical false: no HP value EVER — herded, never hurt. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Contact")
	bool bHasHP = true;

	/** Embers a side-contact costs the hero (the spec §2 damage table). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Contact")
	float ContactDamageEmbers = 10.f;

	/** Half-angle (degrees) of a geometric blind side, 0 = none.
	    (The Ember Reaver's dark socket: ~110. The wound is the weakness.) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Contact")
	float BlindSideConeHalfAngle = 0.f;
};
