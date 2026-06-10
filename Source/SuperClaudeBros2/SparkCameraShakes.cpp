// Super Claude Bros 2 — subtle camera shakes (see header for API/module notes).
//
// Each constructor builds a UPerlinNoiseCameraShakePattern default subobject,
// dials in tiny amplitudes, and installs it with SetRootShakePattern().
//
// UPerlinNoiseCameraShakePattern cheat-sheet (UE 5.x, Engine module):
//   - Inherits USimpleCameraShakePattern: Duration / BlendInTime / BlendOutTime.
//   - FPerlinNoiseShaker members X, Y, Z (location, in cm), Pitch, Yaw, Roll
//     (rotation, in degrees) and FOV (degrees); each shaker has .Amplitude and
//     .Frequency (Hz-ish — higher = busier noise).
//   - If 5.7 renamed these fields, open the pattern header and match — the values
//     below are the design intent and transfer 1:1 to any oscillator-style API.

#include "SparkCameraShakes.h"

// Engine-module header; if this path fails in 5.7 see the fallback notes in
// SparkCameraShakes.h (UDefaultCameraShakeBase via "Shakes/DefaultCameraShakeBase.h").
#include "Shakes/PerlinNoiseCameraShakePattern.h"

namespace SparkShakePrivate
{
	/** Shared boilerplate: make a Perlin pattern subobject on `Outer` with timing set. */
	static UPerlinNoiseCameraShakePattern* MakePattern(
		UCameraShakeBase* Outer, float Duration, float BlendIn, float BlendOut)
	{
		UPerlinNoiseCameraShakePattern* Pattern =
			Outer->CreateDefaultSubobject<UPerlinNoiseCameraShakePattern>(TEXT("ShakePattern"));
		Pattern->Duration = Duration;
		Pattern->BlendInTime = BlendIn;
		Pattern->BlendOutTime = BlendOut;
		return Pattern;
	}
}

// ---------------------------------------------------------------------------
// USparkLandShake — every-landing tap. Near-subliminal vertical bob.
// ---------------------------------------------------------------------------
USparkLandShake::USparkLandShake(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	// Landings can repeat quickly (bunny-hopping) — restart the one instance
	// instead of stacking several shakes on top of each other.
	bSingleInstance = true;

	UPerlinNoiseCameraShakePattern* Pattern =
		SparkShakePrivate::MakePattern(this, /*Duration*/ 0.18f, /*BlendIn*/ 0.02f, /*BlendOut*/ 0.10f);

	// Small, fast vertical bob: ~6 cm at a fast frequency reads as a crisp "tap".
	Pattern->Z.Amplitude = 6.f;
	Pattern->Z.Frequency = 22.f;

	// A whisper of pitch so the bob does not feel purely translational.
	Pattern->Pitch.Amplitude = 0.4f;
	Pattern->Pitch.Frequency = 18.f;

	SetRootShakePattern(Pattern);
}

// ---------------------------------------------------------------------------
// USparkBigLandShake — heavy landing. ~2x the soft land, a touch longer,
// slightly slower noise so it reads as WEIGHT rather than buzz.
// ---------------------------------------------------------------------------
USparkBigLandShake::USparkBigLandShake(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	bSingleInstance = true;

	UPerlinNoiseCameraShakePattern* Pattern =
		SparkShakePrivate::MakePattern(this, /*Duration*/ 0.30f, /*BlendIn*/ 0.02f, /*BlendOut*/ 0.16f);

	// ~2x the soft land on the vertical axis.
	Pattern->Z.Amplitude = 12.f;
	Pattern->Z.Frequency = 16.f;

	// A hint of lateral shove + roll sells the impact without disorienting.
	Pattern->X.Amplitude = 2.f;
	Pattern->X.Frequency = 14.f;

	Pattern->Pitch.Amplitude = 0.8f;
	Pattern->Pitch.Frequency = 15.f;

	Pattern->Roll.Amplitude = 0.3f;
	Pattern->Roll.Frequency = 12.f;

	SetRootShakePattern(Pattern);
}

// ---------------------------------------------------------------------------
// USparkDashShake — spark-dash jolt. Mostly rotational/FOV so the world
// "vibrates with speed" instead of physically displacing the camera.
// ---------------------------------------------------------------------------
USparkDashShake::USparkDashShake(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	bSingleInstance = true;

	UPerlinNoiseCameraShakePattern* Pattern =
		SparkShakePrivate::MakePattern(this, /*Duration*/ 0.20f, /*BlendIn*/ 0.02f, /*BlendOut*/ 0.10f);

	// Energetic = high frequency, small amplitude. Yaw wobble is the star…
	Pattern->Yaw.Amplitude = 0.6f;
	Pattern->Yaw.Frequency = 26.f;

	// …with a dash (sorry) of roll for energy…
	Pattern->Roll.Amplitude = 0.25f;
	Pattern->Roll.Frequency = 24.f;

	// …and a quick FOV pulse (~1 degree) for the speed-surge feeling.
	Pattern->FOV.Amplitude = 1.0f;
	Pattern->FOV.Frequency = 20.f;

	SetRootShakePattern(Pattern);
}
