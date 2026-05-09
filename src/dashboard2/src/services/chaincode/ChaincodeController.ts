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
