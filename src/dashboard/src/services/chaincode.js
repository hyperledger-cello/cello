// import { stringify } from 'qs';
import request from '@/utils/request';

// eslint-disable-next-line no-unused-vars
export async function listChainCode(params) {
  return request('/api/v1/chaincodes');
}

export async function uploadChainCode(params) {
  return request('/api/v1/chaincodes/chaincodeRepo', {
    method: 'POST',
    body: params,
  });
}

export async function installChainCode(params) {
  return request('/api/v1/chaincodes/install', {
    method: 'POST',
    body: params,
  });
}

export async function approveChainCode(params) {
  return request('/api/v1/chaincodes/approve_for_my_org', {
    method: 'POST',
    data: params,
  });
}
