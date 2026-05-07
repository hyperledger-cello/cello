import { request } from "@umijs/max";
import type { API } from "../typings";

export async function login(
  body: {
    email: string;
    password: string;  
  }
) {
  return request<API.Result<AuthAPI.Token>>(
    'api/v1/login',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      data: body,
    }
  );
}

export async function register(
  body: {
    org_name: string;
    email: string;
    password: string;
    agent_url: string
  }
) {
  return request<API.Result<AuthAPI.Token>>(
    'api/v1/register',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      data: body,
    }
  );
}
