/*
 SPDX-License-Identifier: Apache-2.0
 */
import { stringify } from 'qs';
import { customRequest } from '@/utils/serviceFactory';

/**
 * Build the base path for channel invitation endpoints.
 * @param {string} channelId - Channel UUID
 * @returns {string} Base path `/api/v1/channels/{channelId}/invitations`
 */
const basePath = channelId => `/api/v1/channels/${channelId}/invitations`;

/**
 * List invitations for a channel (paginated).
 * @param {Object} params
 * @param {string} params.channelId - Channel UUID
 * @param {Object} [payload] - Pagination params (page, per_page)
 * @returns {Promise} API response
 */
export const listInvitation = ({ channelId, ...payload }) =>
  customRequest(`${basePath(channelId)}?${stringify(payload)}`);

/**
 * Retrieve a single invitation.
 * @param {Object} params
 * @param {string} params.channelId - Channel UUID
 * @param {string} params.invitationId - Invitation UUID
 * @returns {Promise} API response
 */
export const getInvitation = ({ channelId, invitationId }) =>
  customRequest(`${basePath(channelId)}/${invitationId}`);

/**
 * Create a channel invitation.
 * @param {Object} params
 * @param {string} params.channelId - Channel UUID
 * @param {string[]} [params.organization_names] - Invited organization names
 * @param {string[]} [params.organization_ids] - Invited organization UUIDs (compat)
 * @param {number} [params.required_signatures] - Required signature count
 * @returns {Promise} API response
 */
export const createInvitation = ({ channelId, ...payload }) =>
  customRequest(basePath(channelId), {
    method: 'POST',
    data: payload,
  });

/**
 * Sign an invitation artifact as the current member organization.
 * @param {Object} params
 * @param {string} params.channelId - Channel UUID
 * @param {string} params.invitationId - Invitation UUID
 * @returns {Promise} API response
 */
export const signInvitation = ({ channelId, invitationId }) =>
  customRequest(`${basePath(channelId)}/${invitationId}/sign`, {
    method: 'POST',
  });

/**
 * Accept an invitation as an invited organization.
 * @param {Object} params
 * @param {string} params.channelId - Channel UUID
 * @param {string} params.invitationId - Invitation UUID
 * @returns {Promise} API response
 */
export const acceptInvitation = ({ channelId, invitationId }) =>
  customRequest(`${basePath(channelId)}/${invitationId}/accept`, {
    method: 'POST',
  });

/**
 * Reject an invitation as an invited organization.
 * @param {Object} params
 * @param {string} params.channelId - Channel UUID
 * @param {string} params.invitationId - Invitation UUID
 * @returns {Promise} API response
 */
export const rejectInvitation = ({ channelId, invitationId }) =>
  customRequest(`${basePath(channelId)}/${invitationId}/reject`, {
    method: 'POST',
  });

/**
 * Cancel a pending invitation as a member organization.
 * @param {Object} params
 * @param {string} params.channelId - Channel UUID
 * @param {string} params.invitationId - Invitation UUID
 * @returns {Promise} API response
 */
export const cancelInvitation = ({ channelId, invitationId }) =>
  customRequest(`${basePath(channelId)}/${invitationId}/cancel`, {
    method: 'POST',
  });
