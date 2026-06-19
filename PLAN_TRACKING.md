# Channel Invitation Workflow — Plan Modifications & Implementation Status

**DO NOT COMMIT OR PUSH.** Local tracking only.

---

## Deviations from Original Plan (`docs/design/channel_invitation_workflow_plan.md`)

| Original Plan | Current Decision | Reason |
|---------------|-----------------|--------|
| "Prefer admin-only" | **Enforced**: create/sign/cancel require `request.user.is_admin` | Real Fabric requires admin credentials to sign config updates |
| DRAFT/SIGNING/FAILED only for cancel | **Also READY** — DRAFT, SIGNING, FAILED, READY | Invited org may want to cancel before accepting |
| Only member orgs can cancel | **Member admin OR invited org** (only their own) | Invitee should have agency to withdraw |
| Cancel = single action | **Cancel** hard-stops entire invitation. **Reject** (PR 6) = per-invitee decline | Two different semantics needed |
| add_organization to be removed? | **Left untouched** | Maintainer decision pending; no breaking change |
| Signature threshold (TBD) | **All current members** by default, creator overrides with `required_signatures` | Simple default, flexible |
| Retry support | **Re-create** only — no retry endpoint | Cancel and start fresh |

## Implementation Status

| PR | Branch | Status | PR Opened? | Tests | Notes |
|----|--------|--------|:----------:|-------|-------|
| 1 — Design Doc | `docs/channel-invitation-workflow` | ✅ Done | ❌ | — | Just the proposal |
| 2 — API Models | `feat/channel-invitation-workflow-part-2` | ✅ Done | ✅ Awaiting merge | 13 model/serializer tests | Models, migration, serializers, visibility |
| 3 — API Endpoints | `feat/channel-invitation-workflow-part-3` | ✅ Done | ✅ | 14 endpoint tests | List/create/retrieve/cancel. 34/34 total with PR2. Stacked on part-2 |
| 4 — Agent Artifact Gen | `feat/channel-invitation-workflow-part-4` | ✅ Done | ❌ | 7 tests | `POST /channels/{name}/invitations/definition` |
| 5 — Signing Workflow | — | ⬜ Pending | — | — | API engine sign + agent sign |
| 6 — Accept/Reject & Join | — | ⬜ Pending | — | — | Accept/reject/join endpoints |
| 7 — Dashboard UI | — | ⬜ Pending | — | — | New Invitation.js page |
| 8 — Operations Docs | — | ⬜ Pending | — | — | Workflow docs for operators |

## Decisions Made (to confirm with Maintainers)

Questions from the original plan — we made a call but should raise in PR review.

| Original Question | Our Decision | Notes |
|-------------------|-------------|-------|
| Should `add_organization` be removed, hidden, or converted? | **Leave untouched** for now | Avoids breaking existing deployments. Can revisit later. |
| What counts as "enough signatures"? | **All current members** by default. Creator overrides with `required_signatures`. | Matches Fabric's common policy. Flexible per-invitation. |
| Should failed invitations be retryable? | **No retry.** Cancel and re-create. | Simpler state machine. Failed invitation stays FAILED for audit trail. |

## All Decisions — Quick Reference

| Area | Decision |
|------|----------|
| Admin-only? | ✅ Yes — create/sign/cancel require `is_admin` |
| Cancelable states | ✅ DRAFT, SIGNING, FAILED, READY |
| Who can cancel | ✅ Member admin (any org) OR invited org (their own only) |
| Cancel vs Reject | ✅ Cancel = whole invitation dies. Reject = per-invitee (PR 6) |
| add_organization | ✅ Left untouched |
| Signature threshold | ✅ All members by default, creator overrides |
| Retry | ✅ No — re-create |
| One or multiple invitees | ✅ Multiple |
| Visibility: members see | ✅ DRAFT, SIGNING, READY, FAILED, CANCELED |
| Visibility: invitees see | ✅ Only READY+ (READY, ACCEPTED, REJECTED, FAILED) |
| Visibility: unrelated | ✅ Nothing
