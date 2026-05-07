import { request } from "@umijs/max";
import type { API } from "../typings";

export async function queryNodeList(
    params: {
        page?: number;
        per_page?: number;
    },
    options?: { [key: string]: any },
) {
    return request<API.Result<NodeAPI.Info[]>>(
        '/api/v1/nodes',
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
