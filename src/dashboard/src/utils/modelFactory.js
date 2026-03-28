/*
 SPDX-License-Identifier: Apache-2.0
*/

/**
 * Default pagination state used across all models
 */
export const DEFAULT_PAGINATION = {
  total: 0,
  current: 1,
  pageSize: 10,
};

/**
 * Creates default pagination state (returns a new object each time)
 * @returns {Object} Default pagination state
 */
export const createPagination = () => ({ ...DEFAULT_PAGINATION });

/**
 * Common reducers used across all models
 */
export const commonReducers = {
  /**
   * Generic save reducer - merges payload into state
   */
  save(state, { payload }) {
    return {
      ...state,
      ...payload,
    };
  },
};

/**
 * Creates a clear reducer that resets state to initial values
 * @param {Object} initialState - The initial state to reset to
 * @returns {Function} Clear reducer function
 */
export const createClearReducer = initialState => () => ({ ...initialState });

/**
 * Creates a paginated list effect for dva models
 *
 * @param {Object} config - Configuration object
 * @param {Function} config.service - The service function to call
 * @param {string} config.namespace - The model namespace
 * @param {string} config.dataKey - The key to store the list data (e.g., 'agents', 'nodes')
 * @param {Function} [config.getTotalFromResponse] - Custom function to extract total from response
 * @returns {GeneratorFunction} Dva effect generator function
 *
 * @example
 * effects: {
 *   listAgent: createListEffect({
 *     service: listAgent,
 *     namespace: 'agent',
 *     dataKey: 'agents',
 *   }),
 * }
 */
export function createListEffect({ service, namespace, dataKey, getTotalFromResponse }) {
  return function* listEffect({ payload, callback }, { call, put, select }) {
    const response = yield call(service, payload);
    const pagination = yield select(state => state[namespace].pagination);

    const pageSize = payload?.per_page || pagination.pageSize;
    const current = payload?.page || pagination.current;

    // Support custom total extraction (e.g., response.data.total vs response.total)
    const total = getTotalFromResponse ? getTotalFromResponse(response) : response.total;

    yield put({
      type: 'save',
      payload: {
        pagination: {
          total,
          pageSize,
          current,
        },
        [dataKey]: response.data.data,
      },
    });

    if (callback) {
      callback();
    }
  };
}

/**
 * Creates a simple effect that calls a service and invokes callback
 *
 * @param {Function} service - The service function to call
 * @param {Object} [options] - Configuration options
 * @param {boolean} [options.includePayloadInCallback=true] - Include payload in callback response
 * @param {Function} [options.getServiceParams] - Custom function to extract service params from payload
 * @param {string} [options.saveKey] - If provided, saves response to this state key
 * @returns {GeneratorFunction} Dva effect generator function
 *
 * @example
 * effects: {
 *   createAgent: createSimpleEffect(createAgent),
 *   deleteAgent: createSimpleEffect(deleteAgent, { includePayloadInCallback: true }),
 *   getAgent: createSimpleEffect(getAgent, { saveKey: 'agent' }),
 * }
 */
export function createSimpleEffect(service, options = {}) {
  const {
    includePayloadInCallback = true,
    getServiceParams = payload => payload,
    saveKey = null,
  } = options;

  return function* simpleEffect({ payload, callback }, { call, put }) {
    const serviceParams = getServiceParams(payload);
    const response = yield call(service, serviceParams);

    if (saveKey) {
      yield put({
        type: 'save',
        payload: {
          [saveKey]: response,
        },
      });
    }

    if (callback) {
      if (includePayloadInCallback) {
        callback({
          payload,
          ...response,
        });
      } else {
        callback(response);
      }
    }
  };
}

/**
 * Creates a complete dva model with common patterns
 *
 * @param {Object} config - Model configuration
 * @param {string} config.namespace - Model namespace
 * @param {Object} config.state - Additional state (pagination is auto-added)
 * @param {Object} config.effects - Model effects
 * @param {Object} [config.reducers] - Additional reducers (save and clear are auto-added)
 * @returns {Object} Complete dva model
 *
 * @example
 * export default createModel({
 *   namespace: 'agent',
 *   state: {
 *     agent: {},
 *     agents: [],
 *     currentAgent: {},
 *   },
 *   effects: {
 *     listAgent: createListEffect({ ... }),
 *     createAgent: createSimpleEffect(createAgent),
 *   },
 * });
 */
export function createModel({ namespace, state, effects, reducers = {} }) {
  const initialState = {
    ...state,
    pagination: createPagination(),
  };

  return {
    namespace,
    state: initialState,
    effects,
    reducers: {
      ...commonReducers,
      clear: createClearReducer(initialState),
      ...reducers,
    },
  };
}

export default createModel;
