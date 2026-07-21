import { extend } from 'umi-request';
import { notification } from 'antd';
import { history, formatMessage } from 'umi';
import { stringify } from 'qs';

/**
 * Build an error result that callers (dva effects) can inspect.
 * Every path through errorHandler returns this shape so that
 * `response` in saga effects is never undefined.
 */
const makeErrorResult = (data, msg) => ({
  _error: true,
  ...(data || {}),
  _errorMsg: msg || '',
});

/**
 * Extract a human-readable description from Django error response data.
 * For 400 validation errors Django sends: { "field_name": ["Error msg"], "code": 20001, "detail": "..." }
 * We surface the field-level messages rather than the generic "detail".
 */
const extractErrorDescription = (data, status) => {
  if (!data) return '';

  if (status === 400) {
    const fieldErrors = Object.entries(data)
      .filter(([key]) => !['code', 'detail', 'msg', '_error', '_errorMsg'].includes(key))
      .map(([key, val]) => `${key}: ${Array.isArray(val) ? val.join(', ') : val}`)
      .join('\n');
    if (fieldErrors) return fieldErrors;
  }

  const raw = data.detail || data.msg || '';
  if (typeof raw === 'string') return raw;
  if (typeof raw === 'object') return JSON.stringify(raw);
  return String(raw);
};

/**
 * Error handler
 */
const errorHandler = error => {
  const { response, data } = error;

  if (!response) {
    const msg = formatMessage({
      id: 'error.network',
      defaultMessage: 'Network Error',
    });
    notification.error({ message: msg });
    return makeErrorResult(data, msg);
  }

  const { status, url } = response;

  // Handle specific error cases
  if (status === 401) {
    const api = url.split('/').pop();

    if (api === 'login') {
      const msg = formatMessage({
        id: 'error.login.invalidCredentials',
        defaultMessage: 'Invalid username or password.',
      });
      notification.error({ message: msg });
      return makeErrorResult(data, msg);
    }

    const msg = formatMessage({
      id: 'error.login.expired',
      defaultMessage: 'Not logged in or session expired. Please log in again.',
    });
    notification.error({ message: msg });
    history.replace({
      pathname: '/user/login',
      search: stringify({
        redirect: window.location.href,
      }),
    });
    return makeErrorResult(data, msg);
  }

  if (status === 409) {
    const api = url.split('/').pop();
    if (api === 'register') {
      const msg = formatMessage({
        id: 'error.register.duplicate',
        defaultMessage: 'Email address or organization name already exists.',
      });
      notification.error({ message: msg });
      return makeErrorResult(data, msg);
    }
  }

  // Generic error handling
  const errorMessage = formatMessage({
    id: `error.request.${status}`,
    defaultMessage: `Request error (${status})`,
  });

  const description =
    extractErrorDescription(data, status) ||
    formatMessage({
      id: 'error.request.generic',
      defaultMessage: 'An error occurred while processing your request.',
    });

  notification.error({
    message: errorMessage,
    description,
  });

  // Handle navigation for specific error codes,
  // but NOT for auth endpoints — keep the user on the login/register page.
  const isAuthEndpoint = url.includes('/register') || url.includes('/login');
  if (!isAuthEndpoint) {
    if (status === 403) {
      history.push('/exception/403');
    } else if (status >= 500 && status <= 504) {
      history.push('/exception/500');
    } else if (status >= 404 && status < 422) {
      history.push('/exception/404');
    }
  }

  return makeErrorResult(data, description);
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

export default request;
