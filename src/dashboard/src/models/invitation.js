/*
 SPDX-License-Identifier: Apache-2.0
 */
import {
  listInvitation,
  getInvitation,
  createInvitation,
  signInvitation,
  acceptInvitation,
  rejectInvitation,
  cancelInvitation,
} from '@/services/invitation';
import { createModel, createListEffect, createSimpleEffect } from '@/utils/modelFactory';

export default createModel({
  namespace: 'invitation',

  state: {
    invitations: [],
    currentInvitation: {},
  },

  effects: {
    listInvitation: createListEffect({
      service: listInvitation,
      namespace: 'invitation',
      dataKey: 'invitations',
      getTotalFromResponse: response => response.data.total,
    }),

    getInvitation: createSimpleEffect(getInvitation, {
      saveKey: 'currentInvitation',
      includePayloadInCallback: false,
    }),

    createInvitation: createSimpleEffect(createInvitation, {
      includePayloadInCallback: false,
    }),

    signInvitation: createSimpleEffect(signInvitation, {
      includePayloadInCallback: false,
    }),

    acceptInvitation: createSimpleEffect(acceptInvitation, {
      includePayloadInCallback: false,
    }),

    rejectInvitation: createSimpleEffect(rejectInvitation, {
      includePayloadInCallback: false,
    }),

    cancelInvitation: createSimpleEffect(cancelInvitation, {
      includePayloadInCallback: false,
    }),
  },
});
