/*
 SPDX-License-Identifier: Apache-2.0
*/
import { useState, useCallback } from 'react';

/**
 * Hook for managing modal form state (visibility, method, current record)
 *
 * @param {Object} options - Configuration options
 * @param {Object} [options.defaultRecord={}] - Default record when creating new item
 * @returns {Object} Modal form state and handlers
 *
 * @example
 * const {
 *   modalVisible,
 *   modalMethod,
 *   currentRecord,
 *   openCreateModal,
 *   openUpdateModal,
 *   closeModal,
 * } = useModalForm();
 *
 * // Open for creating
 * <Button onClick={openCreateModal}>New</Button>
 *
 * // Open for updating
 * <a onClick={() => openUpdateModal(record)}>Edit</a>
 *
 * // Modal component
 * <MyFormModal
 *   visible={modalVisible}
 *   method={modalMethod}
 *   record={currentRecord}
 *   onCancel={closeModal}
 * />
 */
export function useModalForm(options = {}) {
  const { defaultRecord = {} } = options;

  const [modalVisible, setModalVisible] = useState(false);
  const [modalMethod, setModalMethod] = useState('create');
  const [currentRecord, setCurrentRecord] = useState(defaultRecord);

  /**
   * Open modal for creating new item
   */
  const openCreateModal = useCallback(() => {
    setCurrentRecord(defaultRecord);
    setModalMethod('create');
    setModalVisible(true);
  }, [defaultRecord]);

  /**
   * Open modal for updating existing item
   */
  const openUpdateModal = useCallback(record => {
    setCurrentRecord(record);
    setModalMethod('update');
    setModalVisible(true);
  }, []);

  /**
   * Close modal and reset state
   */
  const closeModal = useCallback(() => {
    setModalVisible(false);
    // Reset after modal close animation
    setTimeout(() => {
      setModalMethod('create');
      setCurrentRecord(defaultRecord);
    }, 300);
  }, [defaultRecord]);

  /**
   * Toggle modal visibility (legacy support for handleModalVisible pattern)
   */
  const handleModalVisible = useCallback(
    (visible, method, record) => {
      if (visible) {
        setModalMethod(method || 'create');
        setCurrentRecord(record || defaultRecord);
      }
      setModalVisible(!!visible);
    },
    [defaultRecord]
  );

  return {
    // State
    modalVisible,
    modalMethod,
    currentRecord,

    // Setters
    setModalVisible,
    setModalMethod,
    setCurrentRecord,

    // Handlers
    openCreateModal,
    openUpdateModal,
    closeModal,
    handleModalVisible, // Legacy support
  };
}

export default useModalForm;
