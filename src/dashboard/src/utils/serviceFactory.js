/*
 SPDX-License-Identifier: Apache-2.0
*/
import { stringify } from 'qs';
import request from '@/utils/request';

/**
 * Creates a standard CRUD service for a given resource.
 *
 * @param {string} resourceName - The API resource name (e.g., 'agents', 'networks')
 * @param {Object} options - Optional configuration
 * @param {string} options.apiVersion - API version prefix (default: 'v1')
 * @returns {Object} An object containing CRUD methods
 *
 * @example
 * const agentService = createCrudService('agents');
 * agentService.list({ page: 1, per_page: 10 });
 * agentService.get('agent-id');
 * agentService.create({ name: 'new-agent' });
 * agentService.update('agent-id', { name: 'updated-agent' });
 * agentService.delete('agent-id');
 */
export function createCrudService(resourceName, options = {}) {
  const { apiVersion = 'v1' } = options;
  const baseUrl = `/api/${apiVersion}/${resourceName}`;

  return {
    /**
     * List resources with optional query parameters
     * @param {Object} params - Query parameters for filtering/pagination
     * @returns {Promise} API response
     */
    list: params => request(`${baseUrl}?${stringify(params)}`),

    /**
     * Get a single resource by ID
     * @param {string} id - Resource ID
     * @returns {Promise} API response
     */
    get: id => request(`${baseUrl}/${id}`),

    /**
     * Create a new resource
     * @param {Object} data - Resource data
     * @returns {Promise} API response
     */
    create: data =>
      request(baseUrl, {
        method: 'POST',
        data,
      }),

    /**
     * Update an existing resource
     * @param {string} id - Resource ID
     * @param {Object} data - Updated resource data
     * @returns {Promise} API response
     */
    update: (id, data) =>
      request(`${baseUrl}/${id}`, {
        method: 'PUT',
        data,
      }),

    /**
     * Delete a resource by ID
     * @param {string} id - Resource ID
     * @returns {Promise} API response
     */
    delete: id =>
      request(`${baseUrl}/${id}`, {
        method: 'DELETE',
      }),
  };
}

/**
 * Creates a custom API endpoint request
 *
 * @param {string} endpoint - The API endpoint path
 * @param {Object} options - Request options
 * @returns {Promise} API response
 *
 * @example
 * customRequest('/api/v1/agents/123/organization', { method: 'DELETE' });
 */
export function customRequest(endpoint, options = {}) {
  return request(endpoint, options);
}

/**
 * Creates a request with form data (for file uploads)
 *
 * @param {string} endpoint - The API endpoint path
 * @param {FormData} formData - Form data to send
 * @param {string} method - HTTP method (default: 'POST')
 * @returns {Promise} API response
 */
export function formDataRequest(endpoint, formData, method = 'POST') {
  return request(endpoint, {
    method,
    body: formData,
  });
}

/**
 * Creates a request that expects a blob response (for file downloads)
 *
 * @param {string} endpoint - The API endpoint path
 * @param {Object} options - Additional request options
 * @returns {Promise} API response with blob data
 */
export function blobRequest(endpoint, options = {}) {
  return request(endpoint, {
    method: 'GET',
    responseType: 'blob',
    getResponse: true,
    ...options,
  });
}

export default createCrudService;
