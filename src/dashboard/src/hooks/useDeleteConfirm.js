/*
 SPDX-License-Identifier: Apache-2.0
*/
import { useCallback } from 'react';
import { Modal, message } from 'antd';

/**
 * Hook for handling delete confirmation dialog
 *
 * @param {Object} options - Configuration options
 * @param {Function} options.dispatch - Dva dispatch function
 * @param {Object} options.intl - react-intl instance for i18n
 * @returns {Object} Delete confirmation handlers
 *
 * @example
 * const { showDeleteConfirm } = useDeleteConfirm({ dispatch, intl });
 *
 * showDeleteConfirm({
 *   record: agent,
 *   nameField: 'name',
 *   deleteAction: 'agent/deleteAgent',
 *   titleId: 'app.agent.form.delete.title',
 *   contentId: 'app.agent.form.delete.content',
 *   successId: 'app.agent.delete.success',
 *   failId: 'app.agent.delete.fail',
 *   onSuccess: () => refreshList(),
 * });
 */
export function useDeleteConfirm({ dispatch, intl }) {
  /**
   * Show delete confirmation dialog
   */
  const showDeleteConfirm = useCallback(
    ({
      record,
      nameField = 'name',
      deleteAction,
      titleId,
      titleDefault = 'Delete',
      contentId,
      contentDefault = 'Confirm to delete {name}?',
      successId,
      successDefault = 'Delete success',
      failId,
      failDefault = 'Delete failed',
      getPayload = r => r.id,
      onSuccess,
      onFail,
    }) => {
      const name = record[nameField];

      Modal.confirm({
        title: intl.formatMessage({
          id: titleId,
          defaultMessage: titleDefault,
        }),
        content: intl.formatMessage(
          {
            id: contentId,
            defaultMessage: contentDefault,
          },
          { name }
        ),
        okText: intl.formatMessage({ id: 'form.button.confirm', defaultMessage: 'Confirm' }),
        cancelText: intl.formatMessage({ id: 'form.button.cancel', defaultMessage: 'Cancel' }),
        onOk() {
          dispatch({
            type: deleteAction,
            payload: getPayload(record),
            callback: response => {
              if (response.status === 'successful' || !response.code) {
                message.success(
                  intl.formatMessage(
                    {
                      id: successId,
                      defaultMessage: successDefault,
                    },
                    { name }
                  )
                );
                if (onSuccess) onSuccess(response);
              } else {
                message.error(
                  intl.formatMessage(
                    {
                      id: failId,
                      defaultMessage: failDefault,
                    },
                    { name }
                  )
                );
                if (onFail) onFail(response);
              }
            },
          });
        },
      });
    },
    [dispatch, intl]
  );

  return {
    showDeleteConfirm,
  };
}

export default useDeleteConfirm;
