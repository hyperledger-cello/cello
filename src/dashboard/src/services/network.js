/*
 SPDX-License-Identifier: Apache-2.0
*/
import { createCrudService } from '@/utils/serviceFactory';

// Create standard CRUD service for networks
const networkService = createCrudService('networks');

// Export standard CRUD operations
export const listNetwork = networkService.list;
export const createNetwork = networkService.create;
export const deleteNetwork = networkService.delete;
