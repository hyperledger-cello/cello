import { request } from "@umijs/max";
import type { API } from "../typings";

export async function quereyUserProfile() {
  return request<API.Result<UserAPI.Info>>(
    '/api/v1/users/profile',
    {
      method: 'GET',
      headers: {
          Authorization: 'JWT ' + localStorage.getItem('token'),
      },
    }
  );
}
