import { listChannel, createChannel, getNodeConfig, updateChannelConfig } from '@/services/channel';

export default {
  namespace: 'channel',

  state: {
    channels: [],
    pagination: {
      total: 0,
      current: 1,
      pageSize: 10,
    },
    currentChannel: {},
  },

  effects: {
    *listChannel({ payload }, { call, put, select }) {
      const response = yield call(listChannel, payload);
      const pagination = yield select(state => state.channel.pagination);
      const pageSize = payload ? payload.per_page || pagination.pageSize : pagination.pageSize;
      const current = payload ? payload.page || pagination.current : pagination.current;

      pagination.total = response.total;
      pagination.pageSize = pageSize;
      pagination.current = current;
      yield put({
        type: 'save',
        payload: {
          pagination,
          channels: response.data.data,
        },
      });
    },
    *createChannel({ payload, callback }, { call }) {
      const response = yield call(createChannel, payload);
      if (callback) {
        callback(response);
      }
    },
    *getNodeConfig({ payload, callback }, { call }) {
      const response = yield call(getNodeConfig, payload);
      if (callback) {
        callback(response);
      }
    },
    *updateChannel({ id, payload, callback }, { call }) {
      const response = yield call(updateChannelConfig, id, payload);
      if (callback) {
        callback(response);
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
        channels: [],
        pagination: {
          total: 0,
          current: 1,
          pageSize: 10,
        },
        currentChannel: {},
      };
    },
  },
};
