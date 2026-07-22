/*
 SPDX-License-Identifier: Apache-2.0
 */
import { stringify } from 'qs';
import { customRequest } from '@/utils/serviceFactory';

const basePath = channelId => `/api/v1/channels/${channelId}/invitations`;

export const listInvitation = ({ channelId, ...payload }) =>
  customRequest(`${basePath(channelId)}?${stringify(payload)}`);

export const createInvitation = ({ channelId, ...payload }) =>
  customRequest(basePath(channelId), {
    method: 'POST',
    data: payload,
  });

export const signInvitation = ({ channelId, invitationId }) =>
  customRequest(`${basePath(channelId)}/${invitationId}/sign`, {
    method: 'POST',
  });

export const acceptInvitation = ({ channelId, invitationId }) =>
  customRequest(`${basePath(channelId)}/${invitationId}/accept`, {
    method: 'POST',
  });

export const rejectInvitation = ({ channelId, invitationId }) =>
  customRequest(`${basePath(channelId)}/${invitationId}/reject`, {
    method: 'POST',
  });

export const cancelInvitation = ({ channelId, invitationId }) =>
  customRequest(`${basePath(channelId)}/${invitationId}/cancel`, {
    method: 'POST',
  });
