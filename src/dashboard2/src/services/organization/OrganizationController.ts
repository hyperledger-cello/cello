import { request } from "@umijs/max";
import type { API } from "../typings";

export async function queryOrganizationList(
    params: {
        page?: number;
        per_page?: number;
    },
    options?: { [key: string]: any },
) {
    return request<API.Result<OrganizationAPI.Info[]>>(
        '/api/v1/organizations',
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
