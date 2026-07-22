import { history } from 'umi';
import { stringify } from 'qs';
import { login, register } from '@/services/api';
import { setAuthority } from '@/utils/authority';
import { getPageQuery } from '@/utils/utils';
import { reloadAuthorized } from '@/utils/Authorized';

export default {
  namespace: 'login',

  state: {
    status: undefined,
    register: {
      success: true,
      registerMsg: '',
    },
  },

  effects: {
    *login({ payload }, { call, put }) {
      const response = yield call(login, payload);
      // Login successfully
      if (response.data.token) {
        const { user, token } = response.data;
        localStorage.setItem('cello-token', token);
        yield put({
          type: 'changeLoginStatus',
          payload: {
            status: 'ok',
            currentAuthority: user.role.toLowerCase() || 'member',
            type: 'account',
          },
        });
        reloadAuthorized();
        const urlParams = new URL(window.location.href);
        const params = getPageQuery();
        let { redirect } = params;
        if (redirect) {
          const redirectUrlParams = new URL(redirect);
          if (redirectUrlParams.origin === urlParams.origin) {
            redirect = redirect.substr(urlParams.origin.length);
            if (redirect.match(/^\/.*#/)) {
              redirect = redirect.substr(redirect.indexOf('#') + 1);
            }
          } else {
            redirect = null;
          }
        }
        yield put(history.replace(redirect || '/'));
      }
    },

    *register({ payload }, { call, put }) {
      let response;
      try {
        response = yield call(register, payload);
      } catch (error) {
        response = error.data || error;
      }

      const isSuccessful =
        response && response.status && response.status.toLowerCase() === 'successful';

      if (!isSuccessful) {
        const responseErrorMsg = response && response._errorMsg; // eslint-disable-line no-underscore-dangle
        let errorMsg =
          response && (responseErrorMsg || response.msg || response.detail || response.message);

        if (response && typeof response === 'object' && !responseErrorMsg && !response.msg) {
          const fieldErrors = Object.entries(response)
            .filter(([key]) => !['code', 'detail', 'msg', 'status'].includes(key))
            .map(([key, val]) => `${key}: ${Array.isArray(val) ? val.join(', ') : val}`)
            .join(' | ');
          if (fieldErrors) {
            errorMsg = fieldErrors;
          }
        }

        yield put({
          type: 'changeRegisterStatus',
          payload: {
            success: false,
            msg: errorMsg || 'Registration failed. Please check the form and try again.',
          },
        });
        return;
      }

      yield put({
        type: 'changeRegisterStatus',
        payload: {
          success: true,
          msg: 'Register successfully!',
        },
      });
      yield put({
        type: 'login',
        payload: {
          email: payload.email,
          password: payload.password,
          type: 'account',
        },
      });
    },

    *logout(_, { put }) {
      localStorage.removeItem('cello-token');

      yield put({
        type: 'changeLoginStatus',
        payload: {
          status: false,
          currentAuthority: 'guest',
        },
      });
      reloadAuthorized();
      const { redirect } = getPageQuery();
      // redirect
      if (window.location.hash.indexOf('/user/login') === -1 && !redirect) {
        yield put(
          history.replace({
            pathname: '/user/login',
            search: stringify({
              redirect: window.location.href,
            }),
          })
        );
      }
    },
  },

  reducers: {
    changeLoginStatus(state, { payload }) {
      setAuthority(payload.currentAuthority);
      return {
        ...state,
        status: payload.status,
        type: payload.type,
      };
    },
    changeRegisterStatus(state, { payload }) {
      return {
        ...state,
        register: {
          success: payload.success,
          registerMsg: payload.msg,
        },
      };
    },
  },
};
