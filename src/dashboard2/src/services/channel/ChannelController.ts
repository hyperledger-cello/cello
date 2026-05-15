import { request } from "@umijs/max";
import type { API } from "../typings";

export async function queryChannelList(
    params: {
        page?: number;
        per_page?: number;
    },
    options?: { [key: string]: any },
) {
    return request<API.Result<ChannelAPI.Info[]>>(
        '/api/v1/channels',
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

export async function createChannel(
  body?: ChannelAPI.CreationPayload,
  options?: { [key: string]: any },
) {
  return request<API.Result<void>>('/api/v1/channels', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: 'JWT ' + localStorage.getItem('token'),
    },
    data: body,
    ...(options || {}),
  });
}
