[//]: # (SPDX-License-Identifier: CC-BY-4.0)

# Channel Invitation Workflow Plan

## Context

The first AI agent plan was too broad for the maintainer feedback. It proposed a
standalone chat-style agent service, but the requested feature is a specific
Fabric channel membership workflow:

* Existing channel members create an invitation for new organizations.
* The API engine stores the generated channel definition/update artifact.
* Current member organizations sign the same artifact one by one.
* After enough signatures are collected, invited organizations can accept.
* The invited organization's Fabric agent joins the channel.

Cello already has the right architectural layers for this:

* `src/api-engine`: Django REST orchestration layer and database state.
* `src/agents/hyperledger-fabric`: Django Fabric worker that runs Fabric tools.
* `src/dashboard`: React/Umi dashboard where channel management lives.

The revised plan should extend those layers instead of adding a new
`src/ai-agent` FastAPI service.

## Existing Codebase Fit

Relevant current code:

* `src/api-engine/channel/models.py`
  stores `Channel` records and channel-to-organization membership.
* `src/api-engine/channel/views.py`
  exposes `list`, `create`, `retrieve`, and `add_organization`.
* `src/api-engine/channel/service.py`
  creates channels and directly asks the new organization agent to join.
* `src/agents/hyperledger-fabric/channel/service.py`
  creates channels using Fabric tools and stores channel files under
  `CELLO_HOME/<channel_name>`.
* `src/dashboard/src/pages/Channel/Channel.js`
  has the existing Channel Management UI and direct Add Organization modal.

The current `add_organization` path is too simple for real Fabric channel
updates. It should become an invitation workflow rather than immediately adding
the organization to the database.

## Proposed State Machine

Add a channel invitation entity in the API engine:

* `DRAFT`: invitation created, unsigned channel update artifact stored.
* `SIGNING`: current member signatures are being collected.
* `READY`: enough current member signatures have been collected.
* `ACCEPTED`: invited organization accepted and its agent joined the channel.
* `REJECTED`: invited organization declined.
* `FAILED`: agent/Fabric operation failed and requires retry or cancellation.
* `CANCELED`: creator or authorized channel member canceled the invitation.

The API engine should be the source of truth for invitation status, signer
records, invited organizations, artifact location, and audit metadata.

## Data Model

Add models in `src/api-engine/channel/models.py`:

* `ChannelInvitation`
  * `id`
  * `channel`
  * `creator_organization`
  * `status`
  * `artifact`
  * `artifact_hash`
  * `required_signatures`
  * `created_at`
  * `updated_at`
  * `error_message`
* `ChannelInvitationInvitee`
  * `invitation`
  * `organization`
  * `status`
  * `responded_at`
* `ChannelInvitationSignature`
  * `invitation`
  * `organization`
  * `signed_at`
  * `artifact_hash`

Recommended constraints:

* One signer row per invitation and organization.
* One invitee row per invitation and organization.
* Invitees cannot already be channel members.
* Signers must already be channel members.
* Stored artifact hash must match the latest uploaded/signed artifact.

Use Django `FileField` stored under `MEDIA_ROOT/channel_invitations/` or a
dedicated setting such as `CHANNEL_INVITATION_ROOT`. The maintainer explicitly
said the API engine should store the file inside its volume, so the file should
not live only inside an agent container.

## API Engine Endpoints

Add actions to `ChannelViewSet` or a nested invitation viewset:

* `GET /api/v1/channels/{channel_id}/invitations`
  lists invitations visible to the current user's organization.
* `POST /api/v1/channels/{channel_id}/invitations`
  creates an invitation for one or more organization IDs/names.
* `GET /api/v1/channels/{channel_id}/invitations/{invitation_id}`
  returns invitation status, invitees, signatures, and current user's available
  action.
* `POST /api/v1/channels/{channel_id}/invitations/{invitation_id}/sign`
  asks the current member organization's agent to sign the stored artifact.
* `POST /api/v1/channels/{channel_id}/invitations/{invitation_id}/accept`
  lets an invited organization accept and join the channel.
* `POST /api/v1/channels/{channel_id}/invitations/{invitation_id}/reject`
  lets an invited organization reject.
* `POST /api/v1/channels/{channel_id}/invitations/{invitation_id}/cancel`
  cancels a pending invitation.

Visibility rules:

* Current channel members can see `DRAFT`, `SIGNING`, `READY`, `FAILED`, and
  `CANCELED` invitations for that channel.
* Invited organizations should only see the invitation after it reaches
  `READY`.
* Organizations outside both groups must not see the invitation.

Authorization rules:

* Only authenticated users can access these endpoints.
* Only channel member organizations can create and sign invitations.
* Only invited organizations can accept or reject.
* Prefer admin-only mutations if the project wants stricter governance, because
  `UserProfile` already has `role` and `is_admin`.

## Fabric Agent Endpoints

Extend `src/agents/hyperledger-fabric/channel/views.py` and
`channel/service.py` with file-oriented endpoints:

* `POST /api/v1/channels/{channel_name}/invitations/definition`
  creates the unsigned channel update artifact that includes the invited
  organizations.
* `POST /api/v1/channels/{channel_name}/invitations/sign`
  receives the current artifact, appends this organization's signature, and
  returns the updated artifact.
* `POST /api/v1/channels/{channel_name}/invitations/join`
  receives the fully signed artifact and joins the channel for the invited
  organization.

These endpoints should operate on bytes/files, not implicit shared local paths,
because each organization agent has its own volume.

Fabric implementation should be split into small service functions:

* Fetch/decode current channel config.
* Add invited organization's MSP definition and anchor peer data.
* Compute config update.
* Wrap update in an envelope.
* Sign envelope using the current organization's admin identity.
* Submit/join once signatures satisfy policy.

The current `create_channel` function is long and command-heavy. New code should
avoid expanding that function further; instead add small helpers that can be
unit-tested by mocking `subprocess.run` and filesystem operations.

## Dashboard Plan

Replace the direct Add Organization user flow in
`src/dashboard/src/pages/Channel/Channel.js` with an invitation workflow.

Recommended UI:

* Add a route under channel management:
  `src/dashboard/src/pages/Channel/Invitation.js`.
* Add a menu or action link labeled `Invitations`.
* Add an `Invite Organization` action from the channel table.
* Show invitation rows with channel, invitees, status, current signatures, and
  the current user's available action.
* Show action buttons only when valid:
  * member organization: `Sign`, `Cancel`
  * invited organization after `READY`: `Accept`, `Reject`
  * failed invitation: `Retry` if backend supports retry

Dashboard files likely involved:

* `src/dashboard/config/router.config.js`
* `src/dashboard/src/services/channel.js`
* `src/dashboard/src/models/channel.js`
* `src/dashboard/src/pages/Channel/Channel.js`
* `src/dashboard/src/pages/Channel/Invitation.js`
* `src/dashboard/src/locales/en-US/Channel.js`
* `src/dashboard/src/locales/zh-CN/Channel.js`

## PR Breakdown

### PR 1: Design Document

Add this design plan and API proposal only. Ask maintainers to confirm:

* Whether direct `add_organization` should be removed, hidden, or preserved as
  an internal compatibility endpoint.
* What signature threshold counts as "enough signatures".
* Whether invitation mutations should be admin-only or all organization users.

### PR 2: API Engine Invitation Models

Add models, migrations, serializers, and visibility query helpers.

Tests:

* Model constraint tests.
* Invitation visibility tests for member, invitee, and unrelated organization.
* Serializer validation for duplicate invitees and existing channel members.

### PR 3: API Engine Invitation Endpoints

Add list/create/retrieve/cancel endpoints. Creation should call the current
member organization's agent to create the unsigned artifact, then store it in
the API engine volume.

Tests:

* Auth required.
* Channel member can create.
* Non-member cannot create.
* Artifact is stored and hashed.
* Agent failure returns a controlled error and does not create partial state.

### PR 4: Fabric Agent Artifact Generation

Add agent service functions and endpoint to create a channel update artifact for
invited organizations.

Tests:

* Serializer accepts required channel/invitee data.
* Service constructs expected Fabric commands.
* `subprocess.run` failures are surfaced predictably.
* Temporary files are cleaned up.

### PR 5: Signing Workflow

Add API engine sign endpoint and agent sign endpoint. Signing should pass the
stored artifact to the signer agent and replace the stored file with the
returned signed artifact without losing previous signatures.

Tests:

* Existing channel member can sign once.
* Duplicate signature is rejected.
* Non-member cannot sign.
* Artifact hash changes after successful signing.
* Previous signatures are not discarded.
* Status moves to `READY` when threshold is met.

### PR 6: Accept/Reject and Join Workflow

Add accept/reject endpoints. Accept should call the invited organization's agent
to join the channel, then add the organization to `Channel.organizations`.

Tests:

* Invitee cannot accept before `READY`.
* Unrelated organization cannot accept.
* Agent join failure leaves membership unchanged and status `FAILED`.
* Successful accept adds channel membership and marks invitee accepted.
* Reject does not add membership.

### PR 7: Dashboard Invitation Page

Add invitation list, create modal, sign/accept/reject/cancel actions, and locale
strings.

Tests:

* Service functions hit the intended URLs.
* Model effects call callbacks with API responses.
* UI renders status and valid action buttons.

### PR 8: Documentation and Operational Notes

Document the workflow for operators and developers.

Include:

* What each status means.
* Where artifacts are stored.
* How to retry failed invitations.
* How to test locally with multiple organizations.

## Testing Strategy

Run checks at the smallest useful scope before each PR:

* API engine lint: `cd src/api-engine && tox -e flake8`
* API engine tests: `cd src/api-engine && python manage.py test channel`
* Fabric agent tests: `cd src/agents/hyperledger-fabric && python manage.py test channel`
* Dashboard lint/tests: `cd src/dashboard && yarn lint` and targeted `yarn test`

Where real Fabric tools are required, keep unit tests mocked and add a manual
or integration checklist that maintainers can run in the Docker compose
environment.

## Maintainer Questions

Ask these before implementation:

1. Should the existing `add_organization` endpoint be removed, hidden from the
   UI, or converted into invitation creation?
2. What policy should define "enough signatures": majority of current channel
   members, all current members, or Fabric policy evaluation?
3. Should only organization admins be allowed to create/sign/accept invitations?
4. Should invitations support one invited organization at a time, or multiple
   invitees in one channel update?
5. Should failed invitations be retryable from the same record, or should users
   create a new invitation?

## Suggested Review Message

Hi maintainers, I revised the implementation plan around the channel invitation
workflow rather than a generic chat agent service. The plan now follows Cello's
existing API engine, Fabric agent, and dashboard layers, and treats the channel
update artifact like a contract file that each member organization signs in
sequence. Could you confirm the signature threshold and whether the current
direct Add Organization endpoint should become invitation creation?
