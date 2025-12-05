/*
 SPDX-License-Identifier: Apache-2.0
*/
import { createCrudService, customRequest } from '@/utils/serviceFactory';

// Create standard CRUD service for agents
const agentService = createCrudService('agents');

// Export standard CRUD operations
export const listAgent = agentService.list;
export const getAgent = params => agentService.get(params.id);
export const createAgent = agentService.create;
export const updateAgent = params => agentService.update(params.id, params);
export const deleteAgent = agentService.delete;

// applyAgent is identical to createAgent, keep as alias for backward compatibility
export const applyAgent = agentService.create;

// Custom endpoint for releasing agent from organization
export const releaseAgent = id =>
  customRequest(`/api/v1/agents/${id}/organization`, {
    method: 'DELETE',
  });
