/*
 SPDX-License-Identifier: Apache-2.0
*/
import {
  getOrganization,
  listOrganization,
  createOrganization,
  updateOrganization,
  deleteOrganization,
} from '@/services/organization';
import { createModel, createListEffect, createSimpleEffect } from '@/utils/modelFactory';

export default createModel({
  namespace: 'organization',

  state: {
    organizations: [],
    currentOrganization: {},
  },

  effects: {
    listOrganization: createListEffect({
      service: listOrganization,
      namespace: 'organization',
      dataKey: 'organizations',
    }),

    getOrganization: createSimpleEffect(getOrganization, {
      includePayloadInCallback: false,
    }),

    createOrganization: createSimpleEffect(createOrganization),

    updateOrganization: createSimpleEffect(updateOrganization),

    deleteOrganization: createSimpleEffect(deleteOrganization, {
      getServiceParams: payload => payload.id,
    }),
  },
});
