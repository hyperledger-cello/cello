import {
  listChainCode,
  uploadChainCode,
  installChainCode,
  approveChainCode,
} from '@/services/chaincode';

export default {
  namespace: 'chainCode',

  state: {
    chainCodes: [],
    pagination: {
      total: 0,
      current: 1,
      pageSize: 10,
    },
  },

  effects: {
    *listChainCode({ payload }, { call, put, select }) {
      const response = yield call(listChainCode, payload);
      const pagination = yield select(state => state.chainCode.pagination);
      const pageSize = payload ? payload.per_page || pagination.pageSize : pagination.pageSize;
      const current = payload ? payload.page || pagination.current : pagination.current;

      pagination.total = response.data.total;
      pagination.pageSize = pageSize;
      pagination.current = current;
      yield put({
        type: 'save',
        payload: {
          pagination,
          chainCodes: response.data.data,
        },
      });
    },
    *uploadChainCode({ payload, callback }, { call }) {
      const response = yield call(uploadChainCode, payload);
      if (callback) {
        callback(response);
      }
    },
    *installChainCode({ payload, callback }, { call }) {
      const response = yield call(installChainCode, payload);
      if (callback) {
        callback(response);
      }
    },
    *approveChainCode({ payload, callback }, { call }) {
      const response = yield call(approveChainCode, payload);
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
        chainCodes: [],
        pagination: {
          total: 0,
          current: 1,
          pageSize: 10,
        },
      };
    },
  },
};
