import { extend } from 'umi-request';
import { notification } from 'antd';
import { history, formatMessage } from 'umi';
import { stringify } from 'qs';

/**
 * Error handler
 */
const errorHandler = error => {
  const { response, data } = error;

  if (!response) {
    notification.error({
      message: formatMessage({
        id: 'error.network',
        defaultMessage: 'Network Error',
      }),
    });
    return;
  }

  const { status, url } = response;

  // Handle specific error cases
  if (status === 401) {
    const api = url.split('/').pop();

    if (api === 'login') {
      notification.error({
        message: formatMessage({
          id: 'error.login.invalidCredentials',
          defaultMessage: 'Invalid username or password.',
        }),
        description: url,
      });
      return;
    }

    notification.error({
      message: formatMessage({
        id: 'error.login.expired',
        defaultMessage: 'Not logged in or session expired. Please log in again.',
      }),
      description: url,
    });
    history.replace({
      pathname: '/user/login',
      search: stringify({
        redirect: window.location.href,
      }),
    });
    return;
  }

  if (status === 409) {
    const api = url.split('/').pop();
    if (api === 'register') {
      notification.error({
        message: formatMessage({
          id: 'error.register.duplicate',
          defaultMessage: 'Email address or organization name already exists.',
        }),
        description: url,
      });
      return;
    }
  }

  // Generic error handling
  const errorMessage = formatMessage({
    id: `error.request.${status}`,
    defaultMessage: `Request error (${status})`,
  });

  const detailMessage =
    data?.detail ||
    data?.msg ||
    formatMessage({
      id: 'error.request.generic',
      defaultMessage: 'An error occurred while processing your request.',
    });

  notification.error({
    message: errorMessage,
    description: `${url}\n${detailMessage}`,
  });

  // Handle navigation for specific error codes
  if (status === 403) {
    history.push('/exception/403');
  } else if (status >= 500 && status <= 504) {
    history.push('/exception/500');
  } else if (status >= 404 && status < 422) {
    history.push('/exception/404');
  }
};

const request = extend({
  errorHandler,
  credentials: 'include',
});

request.interceptors.request.use(async (url, options) => {
  const token = window.localStorage.getItem('cello-token');
  if (url.indexOf('api/v1/login') < 0 && url.indexOf('api/v1/register') < 0 && token) {
    const headers = {
      Authorization: `JWT ${token}`,
    };
    return {
      url,
      options: { ...options, headers },
    };
  }
  return {
    url,
    options,
  };
});

// 第一个拦截器有可能返回Promise,那么Promise由第二个拦截器处理
request.interceptors.request.use(async (url, options) => {
  const token = localStorage.getItem('cello-token');
  if (url.indexOf('api/v1/login') < 0 && url.indexOf('api/v1/register') < 0 && token) {
    // 如果有token 就走token逻辑
    const headers = {
      Authorization: `JWT ${token}`,
    };
    return {
      url,
      options: { ...options, headers },
    };
  }
  return {
    url,
    options,
  };
});

export default request;
