/*
 SPDX-License-Identifier: Apache-2.0
*/
import { listNetwork, createNetwork, deleteNetwork } from '@/services/network';
import { createModel, createListEffect, createSimpleEffect } from '@/utils/modelFactory';

export default createModel({
  namespace: 'network',

  state: {
    networks: [],
    currentNetwork: {},
  },

  effects: {
    listNetwork: createListEffect({
      service: listNetwork,
      namespace: 'network',
      dataKey: 'networks',
    }),

    createNetwork: createSimpleEffect(createNetwork, {
      includePayloadInCallback: false,
    }),

    deleteNetwork: createSimpleEffect(deleteNetwork),
  },
});
