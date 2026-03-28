/*
 SPDX-License-Identifier: Apache-2.0
*/
import { customRequest, formDataRequest } from '@/utils/serviceFactory';

const BASE_URL = '/api/v1/chaincodes';

// List all chaincodes (no params needed for this endpoint)
export const listChainCode = () => customRequest(BASE_URL);

// Create/upload chaincode package (form data)
export const createChainCode = params => formDataRequest(BASE_URL, params);

// Upload chaincode to repository (form data)
export const uploadChainCode = params => formDataRequest(`${BASE_URL}/chaincodeRepo`, params);

// Install chaincode (PUT request with id)
export const installChainCode = params =>
  customRequest(`${BASE_URL}/${params.id}/install`, {
    method: 'PUT',
  });

// Approve chaincode (PUT request with id)
export const approveChainCode = params =>
  customRequest(`${BASE_URL}/${params.id}/approve`, {
    method: 'PUT',
  });

// Commit chaincode (PUT request with id)
export const commitChainCode = params =>
  customRequest(`${BASE_URL}/${params.id}/commit`, {
    method: 'PUT',
  });
