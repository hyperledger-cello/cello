/*
 SPDX-License-Identifier: Apache-2.0
 */
import { listChannel, createChannel } from '@/services/channel';
import { listNode } from '@/services/node';
import { createModel, createListEffect, createSimpleEffect } from '@/utils/modelFactory';

export default createModel({
  namespace: 'channel',

  state: {
    channels: [],
    nodeCounts: { peer: 0, orderer: 0 },
    loadingNodeCounts: false,
  },

  effects: {
    listChannel: createListEffect({
      service: listChannel,
      namespace: 'channel',
      dataKey: 'channels',
    }),

    createChannel: createSimpleEffect(createChannel, {
      includePayloadInCallback: false,
    }),

    *fetchNodeCounts(_, { call, put }) {
      yield put({ type: 'save', payload: { loadingNodeCounts: true } });
      const response = yield call(listNode);
      yield put({ type: 'save', payload: { loadingNodeCounts: false } });
      if (response && response.data) {
        const nodes = response.data.data || [];
        const counts = nodes.reduce(
          (acc, n) => {
            if (n.type === 'PEER') acc.peer += 1;
            if (n.type === 'ORDERER') acc.orderer += 1;
            return acc;
          },
          { peer: 0, orderer: 0 }
        );
        yield put({ type: 'save', payload: { nodeCounts: counts } });
      }
    },

    *listChannelWithNodes({ payload }, { call, put }) {
      yield put({ type: 'fetchNodeCounts' });
      const response = yield call(listChannel, payload);
      if (response) {
        yield put({
          type: 'save',
          payload: { channels: response.data.data || [] },
        });
      }
    },
  },
});
