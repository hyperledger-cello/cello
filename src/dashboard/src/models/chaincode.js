/*
 SPDX-License-Identifier: Apache-2.0
*/
import {
  listChainCode,
  createChainCode,
  uploadChainCode,
  installChainCode,
  approveChainCode,
  commitChainCode,
} from '@/services/chaincode';
import { createModel, createListEffect, createSimpleEffect } from '@/utils/modelFactory';

export default createModel({
  namespace: 'chainCode',

  state: {
    chainCodes: [],
  },

  effects: {
    listChainCode: createListEffect({
      service: listChainCode,
      namespace: 'chainCode',
      dataKey: 'chainCodes',
      // ChainCode API returns total in response.data.total instead of response.total
      getTotalFromResponse: response => response.data.total,
    }),

    createChainCode: createSimpleEffect(createChainCode, {
      includePayloadInCallback: false,
    }),

    uploadChainCode: createSimpleEffect(uploadChainCode, {
      includePayloadInCallback: false,
    }),

    installChainCode: createSimpleEffect(installChainCode, {
      includePayloadInCallback: false,
    }),

    approveChainCode: createSimpleEffect(approveChainCode, {
      includePayloadInCallback: false,
    }),

    commitChainCode: createSimpleEffect(commitChainCode, {
      includePayloadInCallback: false,
    }),
  },
});
