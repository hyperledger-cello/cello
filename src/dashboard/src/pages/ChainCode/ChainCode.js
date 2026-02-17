/*
 SPDX-License-Identifier: Apache-2.0
*/
import React, { Fragment, useCallback, useEffect, useMemo, useState } from 'react';
import { connect, useIntl } from 'umi';
import { Card, Button, Divider, Dropdown, Menu } from 'antd';
import { PlusOutlined, FunctionOutlined, DownOutlined } from '@ant-design/icons';
import PageHeaderWrapper from '@/components/PageHeaderWrapper';
import StandardTable from '@/components/StandardTable';
import UploadForm from '@/pages/ChainCode/forms/UploadForm';
import { useDeleteConfirm, useTableManagement } from '@/hooks';
import styles from './styles.less';

const ChainCode = ({ dispatch, chainCode = {}, loadingChainCodes, uploading }) => {
  const intl = useIntl();
  const { chainCodes = [], paginations = {} } = chainCode;

  const { selectedRows, handleSelectRows, handleTableChange, refreshList } = useTableManagement({
    dispatch,
    listAction: 'chainCode/listChainCode',
  });
  const { showDeleteConfirm } = useDeleteConfirm({ dispatch, intl });

  const [modalVisible, setModalVisible] = useState(false);
  const [newFile, setFile] = useState(null);

  useEffect(() => {
    dispatch({ type: 'chainCode/listChainCode' });
    return () => {
      dispatch({ type: 'chainCode/clear' });
    };
  }, [dispatch]);

  const fetchChainCodes = useCallback(() => {
    refreshList();
  }, [refreshList]);

  const handleModalVisible = useCallback(visible => {
    setModalVisible(!!visible);
  }, []);

  const handleInstall = useCallback(
    (values, callback) => {
      dispatch({
        type: 'chainCode/installChainCode',
        payload: { id: values.id },
        callback,
      });
    },
    [dispatch]
  );

  const handleApprove = useCallback(
    (values, callback) => {
      dispatch({
        type: 'chainCode/approveChainCode',
        payload: { id: values.id },
        callback,
      });
    },
    [dispatch]
  );

  const handleCommit = useCallback(
    (values, callback) => {
      dispatch({
        type: 'chainCode/commitChainCode',
        payload: { id: values.id },
        callback,
      });
    },
    [dispatch]
  );

  const handleUpload = useCallback(
    (values, callback) => {
      const formData = new FormData();
      Object.keys(values).forEach(key => {
        formData.append(key, values[key]);
      });
      dispatch({
        type: 'chainCode/createChainCode',
        payload: formData,
        callback,
      });
    },
    [dispatch]
  );

  const onUploadChainCode = useCallback(() => {
    handleModalVisible(true);
  }, [handleModalVisible]);

  const handleDeleteChaincode = useCallback(
    record => {
      showDeleteConfirm({
        record,
        deleteAction: 'chainCode/deleteChainCode',
        titleId: 'app.chainCode.table.operate.delete',
        contentId: 'app.chainCode.table.operate.delete',
        successId: 'app.chainCode.delete.success',
        failId: 'app.chainCode.delete.fail',
        getPayload: r => r.id,
        onSuccess: () => refreshList(),
      });
    },
    [refreshList, showDeleteConfirm]
  );

  const uploadFormProps = useMemo(
    () => ({
      modalVisible,
      handleUpload,
      handleModalVisible,
      fetchChainCodes,
      uploading,
      newFile,
      setFile,
      intl,
    }),
    [modalVisible, handleUpload, handleModalVisible, fetchChainCodes, uploading, newFile, intl]
  );

  const menu = record => (
    <Menu>
      <Menu.Item>
        <a
          onClick={() => {
            handleDeleteChaincode(record);
          }}
        >
          {intl.formatMessage({
            id: 'app.chainCode.table.operate.delete',
            defaultMessage: 'Delete',
          })}
        </a>
      </Menu.Item>
    </Menu>
  );

  const MoreBtn = record => (
    <Dropdown overlay={menu(record)}>
      <a>
        {intl.formatMessage({
          id: 'app.node.table.operation.more',
          defaultMessage: 'More',
        })}{' '}
        <DownOutlined />
      </a>
    </Dropdown>
  );

  const columns = [
    {
      title: intl.formatMessage({
        id: 'app.chainCode.table.header.packageID',
        defaultMessage: 'PackageID',
      }),
      dataIndex: 'package_id',
      ellipsis: true,
    },
    {
      title: intl.formatMessage({
        id: 'app.chainCode.table.header.version',
        defaultMessage: 'Version',
      }),
      dataIndex: 'version',
    },
    {
      title: intl.formatMessage({
        id: 'app.chainCode.table.header.language',
        defaultMessage: 'Chaincode Language',
      }),
      dataIndex: 'language',
    },
    {
      title: intl.formatMessage({
        id: 'app.chainCode.table.header.description',
        defaultMessage: 'Description',
      }),
      dataIndex: 'description',
    },
    {
      title: intl.formatMessage({
        id: 'form.table.header.operation',
        defaultMessage: 'Operation',
      }),
      render: (text, record) => (
        <Fragment>
          <a onClick={() => handleInstall({ id: record.id }, () => fetchChainCodes())}>
            {intl.formatMessage({
              id: 'app.chainCode.table.operate.install',
              defaultMessage: 'Install',
            })}
          </a>
          <Divider type="vertical" />
          <a onClick={() => handleApprove({ id: record.id }, () => fetchChainCodes())}>
            {intl.formatMessage({
              id: 'app.chainCode.table.operate.approve',
              defaultMessage: 'Approve',
            })}
          </a>
          <Divider type="vertical" />
          <a onClick={() => handleCommit({ id: record.id }, () => fetchChainCodes())}>
            {intl.formatMessage({
              id: 'app.chainCode.table.operate.commit',
              defaultMessage: 'Commit',
            })}
          </a>
          <Divider type="vertical" />
          <MoreBtn {...record} />
        </Fragment>
      ),
    },
  ];

  const dummyPagination = {
    total: 0,
    current: 1,
    pageSize: 10,
  };

  return (
    <PageHeaderWrapper
      title={
        <span>
          <FunctionOutlined style={{ marginRight: 15 }} />
          {intl.formatMessage({
            id: 'app.chainCode.title',
            defaultMessage: 'Chaincode Management',
          })}
        </span>
      }
    >
      <Card bordered={false}>
        <div className={styles.tableList}>
          <div className={styles.tableListOperator}>
            <Button type="primary" onClick={onUploadChainCode}>
              <PlusOutlined />
              {intl.formatMessage({ id: 'form.button.new', defaultMessage: 'New' })}
            </Button>
          </div>
          <StandardTable
            selectedRows={selectedRows}
            loading={loadingChainCodes}
            rowKey="id"
            data={{
              list: chainCodes,
              pagination: chainCodes.length !== 0 ? paginations : dummyPagination,
            }}
            columns={columns}
            onSelectRow={handleSelectRows}
            onChange={handleTableChange}
          />
        </div>
      </Card>
      <UploadForm {...uploadFormProps} />
    </PageHeaderWrapper>
  );
};

export default connect(({ chainCode, loading }) => ({
  chainCode,
  loadingChainCodes: loading.effects['chainCode/listChainCode'],
  uploading: loading.effects['chainCode/uploadChainCode'],
}))(ChainCode);
