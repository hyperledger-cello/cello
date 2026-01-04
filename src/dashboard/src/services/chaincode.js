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

// Install chaincode (form data)
export const installChainCode = params => formDataRequest(`${BASE_URL}/install`, params);

// Approve chaincode for organization (JSON data)
export const approveChainCode = params =>
  customRequest(`${BASE_URL}/approve_for_my_org`, {
    method: 'POST',
    data: params,
  });

// Commit chaincode (JSON data)
export const commitChainCode = params =>
  customRequest(`${BASE_URL}/commit`, {
    method: 'POST',
    data: params,
  });
