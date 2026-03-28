/*
 SPDX-License-Identifier: Apache-2.0
*/
import {
  listAgent,
  getAgent,
  createAgent,
  updateAgent,
  deleteAgent,
  applyAgent,
  releaseAgent,
} from '@/services/agent';
import { createModel, createListEffect, createSimpleEffect } from '@/utils/modelFactory';

export default createModel({
  namespace: 'agent',

  state: {
    agent: {},
    agents: [],
    currentAgent: {},
  },

  effects: {
    listAgent: createListEffect({
      service: listAgent,
      namespace: 'agent',
      dataKey: 'agents',
    }),

    getAgent: createSimpleEffect(getAgent, {
      saveKey: 'agent',
      includePayloadInCallback: false,
    }),

    createAgent: createSimpleEffect(createAgent, {
      getServiceParams: payload => payload.formData,
    }),

    applyAgent: createSimpleEffect(applyAgent, {
      getServiceParams: payload => payload.data,
    }),

    // Custom effect to include action in callback (original behavior)
    *updateAgent({ payload, callback }, { call }) {
      const response = yield call(updateAgent, payload.data);
      if (callback) {
        callback({
          action: payload.action,
          ...response,
        });
      }
    },

    deleteAgent: createSimpleEffect(deleteAgent),

    releaseAgent: createSimpleEffect(releaseAgent),
  },
});
