/*
 SPDX-License-Identifier: Apache-2.0
*/
import { stringify } from 'qs';
import {
  createCrudService,
  customRequest,
  formDataRequest,
  blobRequest,
} from '@/utils/serviceFactory';

// Create standard CRUD service for nodes
const nodeService = createCrudService('nodes');

// Export standard CRUD operations
export const listNode = nodeService.list;
export const createNode = nodeService.create;
export const deleteNode = nodeService.delete;

// Note: Original implementation used stringify for get, keeping same behavior
export const getNode = params => customRequest(`/api/v1/nodes/${stringify(params)}`);

// Custom endpoint for listing users of a node
export const listUserForNode = params => customRequest(`/api/v1/nodes/${stringify(params)}/users`);

// Register a user to a node
export const registerUserToNode = params =>
  customRequest(`/api/v1/nodes/${params.id}/users`, {
    method: 'POST',
    data: params.message,
  });

// Operate on a node (start, stop, etc.)
export const operateNode = params =>
  customRequest(`/api/v1/nodes/${params.id}/operations`, {
    method: 'POST',
    data: { action: params.message },
  });

// Download node configuration (returns blob)
export const downloadNodeConfig = params => blobRequest(`/api/v1/nodes/${params.id}/config`);

// Upload node configuration
export const uploadNodeConfig = params =>
  formDataRequest(`/api/v1/nodes/${params.id}/config`, params.form);

// Node join channel
export const nodeJoinChannel = params =>
  formDataRequest(`/api/v1/nodes/${params.id}/block`, params.form);
