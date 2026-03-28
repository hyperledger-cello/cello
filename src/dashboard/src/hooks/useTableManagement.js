/*
 SPDX-License-Identifier: Apache-2.0
*/
import { useState, useCallback } from 'react';

/**
 * Hook for managing table state (selected rows, pagination, filters)
 *
 * @param {Object} options - Configuration options
 * @param {Function} options.dispatch - Dva dispatch function
 * @param {string} options.listAction - The action type to dispatch for listing (e.g., 'agent/listAgent')
 * @returns {Object} Table management state and handlers
 *
 * @example
 * const {
 *   selectedRows,
 *   formValues,
 *   handleSelectRows,
 *   handleTableChange,
 *   handleFormReset,
 *   setFormValues,
 * } = useTableManagement({
 *   dispatch,
 *   listAction: 'agent/listAgent',
 * });
 */
export function useTableManagement({ dispatch, listAction }) {
  const [selectedRows, setSelectedRows] = useState([]);
  const [formValues, setFormValues] = useState({});

  /**
   * Handle row selection in table
   */
  const handleSelectRows = useCallback(rows => {
    setSelectedRows(rows);
  }, []);

  /**
   * Clear selected rows
   */
  const clearSelectedRows = useCallback(() => {
    setSelectedRows([]);
  }, []);

  /**
   * Handle table pagination/sorting/filtering changes
   */
  const handleTableChange = useCallback(
    (pagination, filters = {}, sorter = {}) => {
      const { current, pageSize } = pagination;
      const params = {
        page: current,
        per_page: pageSize,
        ...formValues,
        ...filters,
      };

      // Add sorting if present
      if (sorter.field) {
        params.sortField = sorter.field;
        params.sortOrder = sorter.order;
      }

      dispatch({
        type: listAction,
        payload: params,
      });
    },
    [dispatch, listAction, formValues]
  );

  /**
   * Reset form filters and refresh list
   */
  const handleFormReset = useCallback(() => {
    setFormValues({});
    dispatch({
      type: listAction,
    });
  }, [dispatch, listAction]);

  /**
   * Refresh list with current filters
   */
  const refreshList = useCallback(
    (extraParams = {}) => {
      dispatch({
        type: listAction,
        payload: {
          ...formValues,
          ...extraParams,
        },
      });
    },
    [dispatch, listAction, formValues]
  );

  return {
    // State
    selectedRows,
    formValues,

    // Setters
    setSelectedRows,
    setFormValues,

    // Handlers
    handleSelectRows,
    handleTableChange,
    handleFormReset,
    clearSelectedRows,
    refreshList,
  };
}

export default useTableManagement;
