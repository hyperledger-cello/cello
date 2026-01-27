import { stringify } from 'qs';
import request from '@/utils/request';

export async function getOrganization(params) {
  return request(`/api/v1/organizations?${params.id}`);
}

export async function listOrganization(params) {
  return request(`/api/v1/organizations?${stringify(params)}`);
}

export async function createOrganization(params) {
  return request('/api/v1/organizations', {
    method: 'POST',
    data: params,
  });
}

export async function updateOrganization(params) {
  return request(`/api/v1/organizations/${params.id}`, {
    method: 'PUT',
    data: params,
  });
}

export async function deleteOrganization(id) {
  return request(`/api/v1/organizations/${id}`, {
    method: 'DELETE',
  });
}
