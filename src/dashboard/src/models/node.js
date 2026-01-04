/*
 SPDX-License-Identifier: Apache-2.0
*/
import {
  listNode,
  getNode,
  registerUserToNode,
  deleteNode,
  operateNode,
  createNode,
  downloadNodeConfig,
  uploadNodeConfig,
  nodeJoinChannel,
} from '@/services/node';
import { createModel, createListEffect, createSimpleEffect } from '@/utils/modelFactory';

export default createModel({
  namespace: 'node',

  state: {
    node: {},
    nodes: [],
  },

  effects: {
    listNode: createListEffect({
      service: listNode,
      namespace: 'node',
      dataKey: 'nodes',
    }),

    createNode: createSimpleEffect(createNode, {
      includePayloadInCallback: false,
    }),

    getNode: createSimpleEffect(getNode, {
      saveKey: 'node',
      includePayloadInCallback: false,
    }),

    registerUserToNode: createSimpleEffect(registerUserToNode),

    deleteNode: createSimpleEffect(deleteNode, {
      includePayloadInCallback: false,
    }),

    operateNode: createSimpleEffect(operateNode),

    downloadNodeConfig: createSimpleEffect(downloadNodeConfig, {
      includePayloadInCallback: false,
    }),

    uploadNodeConfig: createSimpleEffect(uploadNodeConfig),

    nodeJoinChannel: createSimpleEffect(nodeJoinChannel),
  },
});
