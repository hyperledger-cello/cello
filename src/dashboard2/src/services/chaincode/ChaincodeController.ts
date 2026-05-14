import { request } from "@umijs/max";
import type { API } from "../typings";

export async function queryChaincodeList(
  params: {
    page?: number;
    per_page?: number;
  },
  options?: { [key: string]: any },
) {
  return request<API.Result<ChaincodeAPI.Info[]>>(
    '/api/v1/chaincodes',
    {
      method: 'GET',
      params: {
          ...params,
      },
      headers: {
          Authorization: 'JWT ' + localStorage.getItem('token'),
      },
      ...(options || {}),
    }
  );
}

export async function createChaincode(
  body: ChaincodeAPI.CreationPayload,
  options?: { [key: string]: any },
) {
  const formData = new FormData();
  formData.append('package', body.package[0].originFileObj);
  formData.append('name', body.name);
  formData.append('version', body.version);
  formData.append('sequence', String(body.sequence));
  formData.append('channel', body.channel);
  return request<API.Result<void>>('/api/v1/chaincodes', {
    method: 'POST',
    headers: {
      Authorization: 'JWT ' + localStorage.getItem('token'),
    },
    data: formData,
    ...(options || {}),
  });
}

export async function installChaincode(
  id: string,
) {
  return request<API.Result<void>>(`/api/v1/chaincodes/${id}/install`, {
    method: 'PUT',
    headers: {
      Authorization: 'JWT ' + localStorage.getItem('token'),
    },

  });
}

export async function approveChaincode(
  id: string,
) {
  return request<API.Result<void>>(`/api/v1/chaincodes/${id}/approve`, {
    method: 'PUT',
    headers: {
      Authorization: 'JWT ' + localStorage.getItem('token'),
    },

  });
}

export async function commitChaincode(
  id: string,
) {
  return request<API.Result<void>>(`/api/v1/chaincodes/${id}/commit`, {
    method: 'PUT',
    headers: {
      Authorization: 'JWT ' + localStorage.getItem('token'),
    },

  });
}
