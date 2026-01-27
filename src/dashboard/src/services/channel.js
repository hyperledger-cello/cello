/*
 SPDX-License-Identifier: Apache-2.0
*/
import { createCrudService, customRequest } from '@/utils/serviceFactory';

// Create standard CRUD service for channels
const channelService = createCrudService('channels');

// Export standard CRUD operations
export const listChannel = channelService.list;
export const createChannel = channelService.create;
export const getChannel = channelService.get;

// Update channel config with form data
export const updateChannelConfig = (id, params) =>
  customRequest(`/api/v1/channels/${id}`, {
    method: 'PUT',
    data: params,
  });

// Get node configuration for a channel (returns JSON)
export const getNodeConfig = params =>
  customRequest(`/api/v1/channels/${params.id}/configs`, {
    method: 'GET',
    responseType: 'json',
    getResponse: true,
  });
