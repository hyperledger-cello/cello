import {
  getOrganization,
  listOrganization,
  createOrganization,
  updateOrganization,
  deleteOrganization,
} from '@/services/organization';

export default {
  namespace: 'organization',

  state: {
    organizations: [],
    pagination: {
      total: 0,
      current: 1,
      pageSize: 10,
    },
    currentOrganization: {},
  },

  effects: {
    *getOrganization({ payload, callback }, { call }) {
      const response = yield call(getOrganization, payload);
      if (callback) {
        callback(response);
      }
    },
    *listOrganization({ payload, callback }, { call, put, select }) {
      const response = yield call(listOrganization, payload);
      const pagination = yield select(state => state.organization.pagination);
      const pageSize = payload ? payload.per_page || pagination.pageSize : pagination.pageSize;
      const current = payload ? payload.page || pagination.current : pagination.current;

      pagination.total = response.total;
      pagination.pageSize = pageSize;
      pagination.current = current;
      yield put({
        type: 'save',
        payload: {
          pagination,
          organizations: response.data.data,
        },
      });
      if (callback) {
        callback();
      }
    },
    *createOrganization({ payload, callback }, { call }) {
      const response = yield call(createOrganization, payload);
      if (callback) {
        callback({
          payload,
          ...response,
        });
      }
    },
    *updateOrganization({ payload, callback }, { call }) {
      const response = yield call(updateOrganization, payload);
      if (callback) {
        callback({
          payload,
          ...response,
        });
      }
    },
    *deleteOrganization({ payload, callback }, { call }) {
      const response = yield call(deleteOrganization, payload.id);
      if (callback) {
        callback({
          payload,
          ...response,
        });
      }
    },
  },
  reducers: {
    save(state, { payload }) {
      return {
        ...state,
        ...payload,
      };
    },
    clear() {
      return {
        organizations: [],
        pagination: {
          total: 0,
          current: 1,
          pageSize: 10,
        },
        currentOrganization: {},
      };
    },
  },
};
