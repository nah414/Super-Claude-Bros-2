// Super Claude Bros 2 — shared skeletal-animation PERFORMANCE helper.
//
// The cull-freeze fix (every boss = AlwaysTickPoseAndRefreshBones) is correct but
// EXPENSIVE: every rival evaluates its full skeletal pose every frame, even far away
// and off-screen. A Hall (or a future world) full of rivals then pays for all of them
// at once — the lag Adam hit fighting several characters near a big boss.
//
// The fix is a distance pose-LOD: the boss you are NEAR keeps the full always-tick
// pose (so the body you're fighting can never stutter — the wide-pose cull-freeze is
// already prevented by the generous SetBoundsScale), but a boss FARTHER than
// NearRadius falls back to OnlyTickPoseWhenRendered — its pose stops evaluating when
// it is off-screen (the common case for the rest of a crowded arena). The threshold
// sits far outside the duel-start ring, so by the time you can fight a rival it has
// long since switched back to full quality.
//
// Header-only inline so the base AND the three legacy rivals AND the Bramblehulk
// (which each own their body component) share ONE implementation.

#pragma once

#include "CoreMinimal.h"
#include "Components/SkeletalMeshComponent.h"

/** Toggle a rival body between full always-tick (near) and render-culled (far) pose
    evaluation. STATELESS — reads the component's own current option, so no per-actor
    bookkeeping is needed; only writes on an actual change (cheap). */
inline void SCB2_TickPoseLOD(USkeletalMeshComponent* Body, float DistToHero, float NearRadius)
{
	if (!Body) { return; }
	const EVisibilityBasedAnimTickOption Want = (DistToHero < NearRadius)
		? EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones
		: EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
	if (Body->VisibilityBasedAnimTickOption != Want)
	{
		Body->VisibilityBasedAnimTickOption = Want;
	}
}
