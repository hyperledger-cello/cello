import { history } from 'umi';
import { stringify } from 'qs';
import { fakeAccountLogin, register } from '@/services/api';
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
      const response = yield call(fakeAccountLogin, payload);
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
      const response = yield call(register, payload);
      yield put({
        type: 'changeRegisterStatus',
        payload: {
          success: response.status === 'successful',
          msg: response.status === 'successful' ? 'Register successfully!' : response.msg,
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
