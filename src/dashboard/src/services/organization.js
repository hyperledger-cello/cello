/*
 SPDX-License-Identifier: Apache-2.0
*/
import { createCrudService } from '@/utils/serviceFactory';

// Create standard CRUD service for organizations
const organizationService = createCrudService('organizations');

// Export standard CRUD operations
export const listOrganization = organizationService.list;
export const createOrganization = organizationService.create;
export const updateOrganization = params => organizationService.update(params.id, params);
export const deleteOrganization = organizationService.delete;

// Get a single organization by ID
export const getOrganization = params => organizationService.get(params.id);
