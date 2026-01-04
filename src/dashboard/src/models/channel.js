/*
 SPDX-License-Identifier: Apache-2.0
*/
import { listChannel, createChannel, getNodeConfig, updateChannelConfig } from '@/services/channel';
import { createModel, createListEffect, createSimpleEffect } from '@/utils/modelFactory';

export default createModel({
  namespace: 'channel',

  state: {
    channels: [],
    currentChannel: {},
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

    getNodeConfig: createSimpleEffect(getNodeConfig, {
      includePayloadInCallback: false,
    }),

    // Custom effect for updateChannel with special parameter structure
    *updateChannel({ id, payload, callback }, { call }) {
      const response = yield call(updateChannelConfig, id, payload);
      if (callback) {
        callback(response);
      }
    },
  },
});
