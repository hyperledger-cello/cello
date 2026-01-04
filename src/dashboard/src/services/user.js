/*
 SPDX-License-Identifier: Apache-2.0
*/
import { createCrudService, customRequest } from '@/utils/serviceFactory';

// Create standard CRUD service for users
const userService = createCrudService('users');

// Export standard CRUD operations
export const query = () => customRequest('/api/v1/users');
export const createUser = userService.create;
export const deleteUser = userService.delete;

// Verify current user token
// eslint-disable-next-line consistent-return
export const queryCurrent = () => {
  const token = localStorage.getItem('cello-token');
  if (token && token !== '') {
    return customRequest('/api/v1/token-verify', {
      method: 'POST',
      data: { token },
    });
  }
};
