// Super Claude Bros 2 — the Spark Hero.
// A 3D platformer character built for FEEL: momentum movement, variable-height jump,
// double-jump, coyote time, jump buffering, fast-fall, and a signature spark-dash.
// Every tunable is an EditAnywhere UPROPERTY so feel can be tuned live in-editor
// without recompiling. Input is built entirely in C++ at runtime (no .uasset deps).

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "InputActionValue.h"
#include "SparkHeroCharacter.generated.h"

class USpringArmComponent;
class UCameraComponent;
class UStaticMeshComponent;
class USkeletalMeshComponent;
class USceneComponent;
class UInputAction;
class UMaterialInterface;
class UInputMappingContext;
class UAnimSequence;
class UEmberMeterComponent;
class UPointLightComponent;
class AGrabbableProp;
class USparkInteractionComponent;

/** THE POWER WHEEL (Adam's RPG layout, June 12): the mouse wheel scrolls the
    selection, F fires it. Future powers (Keeper's Craft…) append here. */
UENUM(BlueprintType)
enum class ESparkPower : uint8
{
	Bolt      UMETA(DisplayName = "Spark Bolt"),
	Nova      UMETA(DisplayName = "Beacon Nova"),
	FireRing  UMETA(DisplayName = "Ember Ring"),
	COUNT     UMETA(Hidden)
};

/** Dual combat families: LMB chains punches, RMB chains kicks. */
UENUM(BlueprintType)
enum class EStrikeFamily : uint8 { Punch, Kick };

UCLASS()
class ASparkHeroCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	ASparkHeroCharacter();

	// ---------------- Components ----------------
	/** Scales for squash & stretch without touching the collision capsule. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<USceneComponent> VisualRoot;

	/** Placeholder body (engine capsule mesh) until the real Spark Hero model lands. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<UStaticMeshComponent> BodyMesh;

	/** Placeholder spark head (engine sphere mesh). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<UStaticMeshComponent> SparkHead;

	/** The rigged hero (Meshy pipeline). When it loads, the static placeholders hide. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<USkeletalMeshComponent> SkelBody;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<USpringArmComponent> SpringArm;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<UCameraComponent> FollowCamera;

	/** The Ember Meter — the hero's health IS this flame (SCB2_INTERACTION_SPEC.md §2). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<UEmberMeterComponent> EmberMeter;

	/** The visible Spark-flame above the dome; the meter drives its height.
	    Rides the HEAD BONE (found at BeginPlay) so it follows animated poses. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<UStaticMeshComponent> EmberFlame;

	/** The flame MESH is hidden (Adam's call, round 2: "hide the light egg") —
	    the glow light still rides the head and carries the health telegraph
	    (dim with damage, flicker when guttering, flare during grace). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Ember")
	bool bShowEmberFlame = false;

	/** The flame's warm light — the world dims with the hero's health, no HUD. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<UPointLightComponent> EmberGlow;

	/** Power VFX, asset-free: an expanding ground shockwave disc + a light flash.
	    (The powers worked but were invisible — Adam's round-5 rendering call.) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<UStaticMeshComponent> PulseDisc;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<UPointLightComponent> PulseLight;

	/** Ember Guard's RING OF FIRE: orbs that orbit and flicker while the guard
	    burns (Adam's round-6 look). Hidden outside the guard window. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TArray<TObjectPtr<UStaticMeshComponent>> GuardFlames;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SparkHero|Components")
	TObjectPtr<UPointLightComponent> GuardLight;

	/** The forged additive plasma material (built by build_power_materials.py). */
	UPROPERTY(Transient)
	TObjectPtr<UMaterialInterface> PlasmaMaterial;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UMaterialInstanceDynamic>> GuardFlameMIDs;

	// ---------------- Movement feel ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Movement")
	float MaxRunSpeed = 650.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Movement")
	float GroundAcceleration = 2600.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Movement")
	float BrakingDeceleration = 2200.f;

	/** 0..1 — how much steering you keep while airborne. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Movement", meta = (ClampMin = "0", ClampMax = "1"))
	float AirControlAmount = 0.85f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Movement")
	float BaseGravityScale = 1.9f;

	/** Falling below this world Z teleports the hero back to the start — no endless void falls. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|World")
	float RespawnBelowZ = -2000.f;

	// ---------------- Jump feel ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Jump")
	float JumpVelocity = 950.f;

	/** Releasing jump while rising clamps upward speed to this — variable jump height. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Jump")
	float JumpCutoffVelocity = 320.f;

	/** Grace window after walking off a ledge in which a jump still counts (seconds). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Jump")
	float CoyoteTime = 0.12f;

	/** Pressing jump slightly before landing still fires the jump (seconds). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Jump")
	float JumpBufferTime = 0.10f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Jump")
	int32 MaxAirJumps = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Jump")
	float AirJumpVelocity = 850.f;

	/** Holding fast-fall in the air multiplies gravity by this. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Jump")
	float FastFallGravityScale = 3.4f;

	// ---------------- Spark dash ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Dash")
	float DashSpeed = 1900.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Dash")
	float DashDuration = 0.18f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Dash")
	float DashCooldown = 0.7f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Dash")
	int32 MaxAirDashes = 1;

	// ---------------- The Spark Combo (hand-to-hand — Adam's June 11 lock) ----------------
	// Three beats: tentacle lash, tentacle lash, fist HAYMAKER. No block button —
	// the dash is the dodge. Full design: SCB2_POWERS_CODEX.md §1.
	/** How far ahead of the hero the strike sphere lands. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Strike")
	float StrikeRange = 85.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Strike")
	float StrikeRadius = 55.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Strike")
	float StrikeLightDuration = 0.22f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Strike")
	float StrikeHeavyDuration = 0.38f;

	/** Forward step the lash carries (the strike IS movement — squid boxing). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Strike")
	float StrikeLightLunge = 420.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Strike")
	float StrikeHeavyLunge = 550.f;

	/** Next beat must be pressed within this window after a beat ends, or the combo resets. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Strike")
	float StrikeComboWindow = 0.45f;

	/** Breather after the haymaker before the string can start again. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Strike")
	float StrikeComboCooldown = 0.35f;

	// ---------------- Crouch (Adam's round-3 verb) ----------------
	/** Capsule half-height while crouched (standing: 72). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Crouch")
	float CrouchHalfHeight = 44.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Crouch")
	float CrouchSpeed = 260.f;

	// ---------------- Climb (Adam's round-4 verb: "our Hero's need to climb") ----------------
	/** Vertical/lateral speed while clinging to a wall. (M6: 220->400 for parity with run.) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Climb")
	float ClimbSpeed = 400.f;

	/** How far past the capsule we probe for a climbable wall. (M6: 24->56, reach ~90u.) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Climb")
	float ClimbCheckDistance = 56.f;

	/** M6: fraction of along-wall momentum kept on grab (0=dead-stop, 1=full) so a jump-into-
	    wall flows instead of snapping. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Climb")
	float ClimbGrabMomentumRetain = 0.35f;

	/** Wall-leap: jump while climbing kicks away from the wall and up. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Climb")
	float WallLeapAway = 500.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Climb")
	float WallLeapUp = 700.f;

	/** Dev default: any wall climbs. Flip false for shipping -> only actors tagged ClimbableTag
	    (the M5 cliff climb-architecture) can be gripped. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Climb")
	bool bClimbAnywhere = true;

	/** M7: when bClimbAnywhere is false, only actors carrying this tag are climbable. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Climb")
	FName ClimbableTag = FName("Climbable");

	// ---------------- THE SPARK SURGE KIT (Powers Codex §2 — Adam: build the FULL
	// hero now, stage per-world later) ----------------
	/** The 1–10 staging gate. L1 verbs+combo · L2 Spark Aura · L3 Charged Haymaker ·
	    L4 Prism Burst · L5 Ember Guard · L6 Beacon Wave · L7 Aura+combo amplified ·
	    L8 Burst amplified · L9 Guard amplified + 2nd air dash · L10 Full Spark.
	    Default 10 for Adam's playtests; world deployment stages this per relight. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Power", meta = (ClampMin = "1", ClampMax = "10"))
	int32 PowerLevel = 10;

	/** L2 — Spark Aura: kept-fire radius that calms Mote-class wildlife. L7: ×1.5. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Power")
	float AuraRadius = 400.f;

	/** L3 — Charged Haymaker: hold strike this long and it AUTO-FIRES (the
	    responsiveness law, June 12 — nothing in the kit waits for a release). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Power")
	float StrikeChargeTime = 0.45f;

	/** Rapid-fire governor for the hand blast: taps this far apart all fire.
	    The bolt leaves on PRESS; this is the only thing limiting the cadence. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Power")
	float BlastCooldown = 0.18f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Power")
	float ChargedLunge = 700.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Power")
	float ChargedRadiusBonus = 45.f;

	/** L4 — Prism Burst (tap power): a light pulse that staggers Motes in a ring. L8: ×1.3 radius. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Power")
	float BurstRadius = 450.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Power")
	float BurstStagger = 1.5f;

	/** Was 4s in the rare-ultimate era — duels demand bread-and-butter bolts
	    (Adam's frequency verdict, June 12). The press governor sets the cadence. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Power")
	float BurstCooldown = 0.25f;

	/** L5 — Ember Guard (tap Q): the flame armors itself — grace extends. L9: 3 s. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Power")
	float GuardDuration = 2.f;

	/** Was 8s — now the ring is back almost as soon as it gutters out. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Power")
	float GuardCooldown = 2.5f;

	/** L6 — Beacon Wave (hold power, release): the big pulse — staggers wide, and
	    relights every lantern in radius once the light-state system lands (M0.2). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Power")
	float WaveRadius = 900.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Power")
	float WaveChargeTime = 0.6f;

	/** Was 12s — the nova is now a once-per-exchange weapon, not a once-per-fight one. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Power")
	float WaveCooldown = 3.f;

	/** Capture-harness hook: throw a combo beat on command (the GameMode's
	    -SCB2ShotStrike flag uses this to photograph strikes headlessly). */
	void CaptureStrike();

	// ---------------- Camera feel ----------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Camera")
	float BaseArmLength = 460.f;

	/** Arm length when looking steeply DOWN (tighter, tactical). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Camera")
	float ArmLengthLookingDown = 330.f;

	/** Arm length when looking UP (wider, scenic). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Camera")
	float ArmLengthLookingUp = 580.f;

	// Mouse-wheel zoom (Adam's call: ~5x visual control either way).
	/** Each wheel notch multiplies/divides the camera distance by this. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Camera")
	float ZoomStepPerNotch = 1.18f;

	/** Closest zoom: 0.2 = five times closer than the context camera's choice. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Camera")
	float ZoomMinMultiplier = 0.2f;

	/** Farthest zoom: 5 = five times farther. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Camera")
	float ZoomMaxMultiplier = 5.f;

	// Camera look/pan speed. 0.85 = 15% slower than the old 1.0 (Adam, June 19) — calmer aiming;
	// scales BOTH yaw + pitch (HandleLook multiplies both axes by this).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Camera")
	float LookSensitivity = 0.85f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Camera")
	bool bInvertLookY = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Camera")
	float CameraPitchMin = -70.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Camera")
	float CameraPitchMax = 45.f;

	// ---------------- Squash & stretch ----------------
	/** Z scale on landing (XY bulges to conserve volume). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Juice")
	float LandSquash = 0.80f;

	/** Z scale on jump takeoff. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Juice")
	float JumpStretch = 1.14f;

	/** How fast the visual scale springs back to 1. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Juice")
	float SquashRecoverySpeed = 11.f;

	// ---------------- Event hooks (Niagara/SFX wire in later, in Blueprint) ----------------
	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnHeroJumped(bool bWasAirJump);

	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnHeroLanded(float ImpactSpeed);

	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnDashStarted(FVector DashDirection);

	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnDashEnded();

	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnHeroRespawned();

	/** A hit got through (grace didn't eat it). NewFraction is the flame's new 0..1. */
	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnHeroEmberHit(float NewFraction);

	/** The flame went out. Fires just before the lantern relights the hero. */
	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnHeroFlameOut();

	/** Enemies route ember damage through here (Contact Matrix, spec §5). Knockback
	    is the caller's job and always applies; fire only drains outside grace. */
	UFUNCTION(BlueprintCallable, Category = "SparkHero")
	void TakeEmberHit(float Embers);

	/** True while the spark-dash owns the hero's velocity (read by enemies for dash-kills). */
	UFUNCTION(BlueprintPure, Category = "SparkHero")
	bool IsDashing() const { return bIsDashing; }

	/** True mid-strike (read by duelists for CLASH resolution, later). */
	UFUNCTION(BlueprintPure, Category = "SparkHero")
	bool IsStriking() const { return bStriking; }

	// ---- Dashboard getters (the HUD reads, never writes) ----
	ESparkPower GetSelectedPower() const { return SelectedPower; }
	EStrikeFamily GetStrikeFamily() const { return CurrentFamily; }
	int32 GetComboBeat() const { return ComboBeat; }
	bool IsChargingStrike() const { return bChargingStrike; }
	/** Seconds until the given power is ready (0 = ready now). */
	float GetPowerReadyIn(ESparkPower Power) const;
	UEmberMeterComponent* GetEmberMeter() const { return EmberMeter; }
	bool IsCarrying() const { return CarriedProp.IsValid(); }

	/** E reaches this far for a prop; LMB hurls it this fast. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Interact")
	float GrabRange = 240.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Interact")
	float ThrowSpeed = 1400.f;

	/** Staging gate check — the whole kit reads through this. */
	UFUNCTION(BlueprintPure, Category = "SparkHero|Power")
	bool HasPowerLevel(int32 Level) const { return PowerLevel >= Level; }

	UFUNCTION(BlueprintPure, Category = "SparkHero")
	bool IsClimbing() const { return bClimbing; }

	/** L2+ and the flame is lit: the Spark Aura calms wild things (read by fauna). */
	UFUNCTION(BlueprintPure, Category = "SparkHero|Power")
	bool IsAuraActive() const;

	UFUNCTION(BlueprintPure, Category = "SparkHero|Power")
	float GetAuraRadius() const { return AuraRadius * (HasPowerLevel(7) ? 1.5f : 1.f); }

	// Power-cast VFX/SFX seams.
	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnHeroChargedStrike();

	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnHeroPrismBurst(float Radius);

	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnHeroEmberGuard();

	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnHeroBeaconWave(float Radius);

	/** A combo beat fired (0/1 = lash, 2 = haymaker) — VFX/SFX seam. */
	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnHeroStrike(int32 Beat);

	/** A strike connected with something. */
	UFUNCTION(BlueprintImplementableEvent, Category = "SparkHero|Events")
	void OnHeroStrikeHit(AActor* Victim, int32 Beat);

	/** Most negative recent vertical velocity — landing zeroes velocity BEFORE contact
	    events fire, so stomp checks must read the fall as it was a tick ago. */
	UFUNCTION(BlueprintPure, Category = "SparkHero")
	float GetRecentFallSpeed() const
	{
		return FMath::Min(GetVelocity().Z, PrevTickVelZ);
	}

	// ---------------- Hero model (imported glb; falls back to placeholder shapes) ----------------
	/** Yaw correction for the imported hero mesh (axis conventions differ between tools). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Model")
	float HeroMeshYaw = -90.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Model")
	float HeroMeshScale = 1.05f;   // mesh is 132uu tall (scale baked); capsule is 144

	/** Yaw correction for the skeletal hero. Meshy-NATIVE FBX (HeroSkelV4) faces the
	    opposite way from the old Blender-baked rigs — Adam's playtest: "walking in
	    rewind." -90 turns the native model to the actor's +X forward. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Model")
	float SkelMeshYaw = -90.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Model")
	float SkelMeshScale = 1.0f;

	// ---------------- Animation (single-node playback; no AnimBP assets) ----------------
	/** Clip playback gate (June 11): V3 assets carry the anim-scale fix — clips
	    convert at factor 1.0 (no Blender scale bake) and UE applies the 0.8 at
	    import, scaling rig and curves together. ON by default; flip OFF live if
	    a future import regresses (the hero falls back to his handsome ref-pose). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Anim")
	bool bEnableClipPlayback = true;

	/** Meshy jump presets are ~10 s ROUTINES (idle, crouch, leap, land, idle) —
	    a 1 s hop only ever showed the rigid lead-in (Adam: "knees should bend").
	    Start the clip where the leap lives and play it fitted. Both EditAnywhere:
	    tune by feel — earlier/later = fraction, snappier/slower = rate. */
	/** Data-scanned values (hips-Z over the clip): the crouch dip sits at frac
	    0.076, leap peak at 0.127, landed by ~0.18 — start at 0.06, rate 1.2 fits
	    that window to a ~1 s hop. Knees bend at takeoff, tuck at apex. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float JumpClipStartFraction = 0.06f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Anim")
	float JumpClipRate = 1.2f;

	/** Per-strike clip windows (the jump-fix pattern, combat edition): library
	    punch clips are routines with wind-up and recovery — start mid-clip at
	    the swing and play at a chosen rate so the IMPACT lands inside the beat.
	    StartFraction 0 + Rate 0 = legacy auto-fit (the hero's default). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float Strike1ClipStartFraction = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Anim")
	float Strike1ClipRate = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float Strike2ClipStartFraction = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Anim")
	float Strike2ClipRate = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float HaymakerClipStartFraction = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Anim")
	float HaymakerClipRate = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float ChargedClipStartFraction = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Anim")
	float ChargedClipRate = 0.f;

	// Kick-family windows (scan-set per hero; 0/0 = auto-fit fallback).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float Kick1ClipStartFraction = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Anim")
	float Kick1ClipRate = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float Kick2ClipStartFraction = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Anim")
	float Kick2ClipRate = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Anim", meta = (ClampMin = "0", ClampMax = "0.9"))
	float KickHeavyClipStartFraction = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Anim")
	float KickHeavyClipRate = 0.f;

	/** Ground speed above which the run cycle replaces the walk cycle. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Anim")
	float RunAnimSpeedThreshold = 420.f;

	/** Ground speed below which the hero counts as standing still. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SparkHero|Anim")
	float WalkAnimMinSpeed = 60.f;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
	virtual void NotifyControllerChanged() override;
	virtual void Landed(const FHitResult& Hit) override;
	virtual void FellOutOfWorld(const UDamageType& DmgType) override;

	// Input handlers
	void HandleMove(const FInputActionValue& Value);
	void HandleLook(const FInputActionValue& Value);
	void HandleZoom(const FInputActionValue& Value);
	void HandleJumpPressed();
	void HandleJumpReleased();
	void HandleDashPressed();
	void HandleStrikePressed();
	void HandleStrikeReleased();
	void BeginStrikeFamily(EStrikeFamily Family);
	void HandleKickPressed();
	void HandleKickReleased();
	void HandleFirePressed();                          // F: fire the selected power
	void HandlePowerScroll(const FInputActionValue& Value);   // wheel: scroll the wheel
	void HandleZoomPreset();                           // Z: near / default / far
	void HandleInteractPressed();                      // E: interact (relight) else grab / drop
	void HandleInteractReleased();                     // E release: finish/interrupt a hold
	void HandleGuardPressed();
	void HandleSwitchHero();
	void HandleFastFallPressed();
	void HandleFastFallReleased();
	void HandleQuit();

	virtual void OnStartCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust) override;
	virtual void OnEndCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust) override;

private:
	// Runtime-built Enhanced Input (no content assets needed).
	void BuildInputObjects();

	UPROPERTY(Transient) TObjectPtr<UInputMappingContext> MappingContext;
	UPROPERTY(Transient) TObjectPtr<UInputAction> MoveAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> KickAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> PowerScrollAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> ZoomPresetAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> InteractAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> LookAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> ZoomAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> JumpAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> DashAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> StrikeAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> PowerAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> GuardAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> SwitchHeroAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> FastFallAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> QuitAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> SkinAction;

	// ---- Hero SKINS (the guardians' aspects, granted to the Spark; cycle with B) ----
	UPROPERTY(EditAnywhere, Category = "Hero|Skins")
	TArray<TObjectPtr<UMaterialInterface>> HeroSkins;
	int32 CurrentSkin = 0;
	void HandleCycleSkin();
	void ApplySkin(int32 Index);
	/** Sonnet returns false — the hero skins recolor HIS base texture, not hers. */
	virtual bool AllowSkins() const { return true; }

	// Jump state
	void TryJump();
	void DoJump(bool bAirJump);
	float LastGroundedTime = -1000.f;
	float LastJumpPressedTime = -1000.f;
	int32 AirJumpsRemaining = 0;
	bool bCoyoteConsumed = false;

	// Dash state
	void EndDash();
	bool bIsDashing = false;
	int32 AirDashesRemaining = 0;
	float LastDashEndTime = -1000.f;
	FTimerHandle DashTimerHandle;

	// Strike state (the Spark Combo + the L3 charge)
	void DoStrike();
	void DoChargedStrike();
	void StrikeHitCheck();
	void EndStrike();
	bool bStriking = false;
	bool bStrikeQueued = false;
	bool bChargingStrike = false;
	bool bChargedStrike = false;         // current swing is the charged variant
	float StrikeChargeStart = -1000.f;
	int32 ComboBeat = 0;                 // 0/1 = lash, 2 = haymaker
	// Dual families: which chain is live, which is held charging, which queued.
	EStrikeFamily CurrentFamily = EStrikeFamily::Punch;
	EStrikeFamily ChargingFamily = EStrikeFamily::Punch;
	EStrikeFamily QueuedFamily = EStrikeFamily::Punch;
	// The power wheel.
	ESparkPower SelectedPower = ESparkPower::Bolt;
	float PowerScrollAccum = 0.f;
	int32 ZoomPresetIndex = 1;           // {near, default, far}
	// The carried prop (E grabs, E drops, LMB throws).
	TWeakObjectPtr<AGrabbableProp> CarriedProp;

	/** The hero's one interaction brain (focus + tap/hold relight; reused world-wide). */
	UPROPERTY(VisibleAnywhere, Category = "SparkHero|Components")
	TObjectPtr<USparkInteractionComponent> InteractionComp;
	void ThrowCarried();
	float LastStrikeEndTime = -1000.f;
	float ComboCooldownUntil = -1000.f;
	FTimerHandle StrikeTimerHandle;
	FTimerHandle StrikeHitTimerHandle;

	// Power state (the Spark Surge kit)
	void DoPrismBurst();
	void DoBeaconWave();
	void FireBlast(const FVector& Direction);
	void FirePulse(float Radius, float Duration, float LightIntensity);
	FName HandBoneName = NAME_None;      // found at BeginPlay — blasts spawn here
	float GuardVisualUntil = -1000.f;    // the fire ring burns until this moment
	float PulseStartTime = -1000.f;
	float PulseDuration = 0.45f;
	float PulseTargetRadius = 450.f;
	bool bChargingPower = false;
	float PowerChargeStart = -1000.f;
	float NextBlastTime = -1000.f;    // the rapid-fire governor's clock
	float BurstReadyTime = -1000.f;
	float WaveReadyTime = -1000.f;
	float GuardReadyTime = -1000.f;

	// True when the imported SparkHero model loaded in the constructor.
	bool bHasRealModel = false;

protected:
	// Skeletal hero + clips (constructor-loaded; all optional). PROTECTED so the
	// heroine subclass can swap in her own body and clips (full parity by code).
	UPROPERTY() TObjectPtr<UAnimSequence> IdleAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> WalkAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> RunAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> JumpAnim;
	// M0.6 Hero Ascension II — the combo made flesh (+ the relight kneel, wired at M0.2).
	UPROPERTY() TObjectPtr<UAnimSequence> Strike1Anim;
	UPROPERTY() TObjectPtr<UAnimSequence> Strike2Anim;
	UPROPERTY() TObjectPtr<UAnimSequence> HaymakerAnim;
	/** Optional split: the CHARGED strike's own clip (falls back to HaymakerAnim).
	    Lets a character kick the combo finisher but still punch the charged one. */
	UPROPERTY() TObjectPtr<UAnimSequence> ChargedStrikeAnim;
	// The KICK family (RMB chains; per-hero signature sets — custom-moves law).
	UPROPERTY() TObjectPtr<UAnimSequence> Kick1Anim;
	UPROPERTY() TObjectPtr<UAnimSequence> Kick2Anim;
	UPROPERTY() TObjectPtr<UAnimSequence> KickHeavyAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> HitReactAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> RelightAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> CrouchAnim;
	bool bHasSkeletalModel = false;

private:
	enum class EHeroAnimState : uint8 { None, Idle, Walk, Run, Jump, Crouch, Climb };
	EHeroAnimState AnimState = EHeroAnimState::None;
	void UpdateHeroAnimation();

	// Action-override layer: one-shot clips (strikes, hit-react) take the body;
	// the locomotion state machine waits, then resumes via the None sentinel.
	void PlayActionClip(UAnimSequence* Clip, float FitDuration, float StartFraction = 0.f, float OverrideRate = 0.f);
	void EndActionClip();
	bool bActionAnimActive = false;
	FTimerHandle HitReactTimerHandle;

	// Respawn (solid-ground guarantee)
	void RespawnAtStart();
	void RespawnAtTransform(const FVector& Loc, const FRotator& Rot);   // checkpoint respawn
	UFUNCTION() void HandleFlameOut();   // bound to the meter's OnFlameOut
	FVector SpawnLocation = FVector::ZeroVector;     // the level's PlayerStart
	FRotator SpawnRotation = FRotator::ZeroRotator;
	FVector SafeGroundLocation = FVector::ZeroVector; // last spot we truly stood on

	// Climb state
	void TryStartClimb();
	void StopClimb();
	bool bClimbing = false;
	FVector ClimbWallNormal = FVector::ForwardVector;

	// Misc state
	float ZoomMultiplier = 1.f;                          // mouse-wheel camera zoom
	FVector LastWorldMoveInput = FVector::ForwardVector; // dash direction fallback
	float PrevTickVelZ = 0.f;                            // landing impact speed
	bool bFastFalling = false;
	FVector VisualScaleTarget = FVector::OneVector;
	FVector VisualScaleCurrent = FVector::OneVector;

	void ApplySquash(float ZScale);
	float Now() const;

	// Juice helpers — every asset is optional (nullptr-safe) so the game runs
	// before/without the audio pack and shake classes.
	void PlaySfx(const TCHAR* AssetPath) const;
	void PlayShake(TSubclassOf<class UCameraShakeBase> ShakeClass) const;
};
