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
import InstallForm from '@/pages/ChainCode/forms/InstallForm';
import ApproveForm from '@/pages/ChainCode/forms/ApproveForm';
import CommitForm from './forms/CommitForm';
import { useDeleteConfirm, useTableManagement } from '@/hooks';
import styles from './styles.less';

const ChainCode = ({
  dispatch,
  chainCode = {},
  loadingChainCodes,
  uploading,
  installing,
  approving,
  committing,
}) => {
  const intl = useIntl();
  const { chainCodes = [], paginations = {}, nodes = {} } = chainCode;

  const { selectedRows, handleSelectRows, handleTableChange, refreshList } = useTableManagement({
    dispatch,
    listAction: 'chainCode/listChainCode',
  });
  const { showDeleteConfirm } = useDeleteConfirm({ dispatch, intl });

  const [modalVisible, setModalVisible] = useState(false);
  const [installModalVisible, setInstallModalVisible] = useState(false);
  const [approveModalVisible, setApproveModalVisible] = useState(false);
  const [commitModalVisible, setCommitModalVisible] = useState(false);
  const [chainCodeName, setChainCodeName] = useState('');
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

  const fetchNodes = useCallback(() => {
    dispatch({ type: 'node/listNode' });
  }, [dispatch]);

  const handleModalVisible = useCallback(visible => {
    setModalVisible(!!visible);
  }, []);

  const handleInstallModalVisible = useCallback(
    (visible, record = {}) => {
      if (visible) {
        fetchNodes();
        setChainCodeName(record.package_id);
      }
      setInstallModalVisible(!!visible);
    },
    [fetchNodes]
  );

  const handleApproveModalVisible = useCallback(visible => {
    setApproveModalVisible(!!visible);
  }, []);

  const handleCommitModalVisible = useCallback(visible => {
    setCommitModalVisible(!!visible);
  }, []);

  const handleInstall = useCallback(
    (values, callback) => {
      const formData = new FormData();
      Object.keys(values)
        .filter(key => !(key === 'description' && !values[key]))
        .forEach(key => {
          formData.append(key, values[key]);
        });
      dispatch({
        type: 'chainCode/installChainCode',
        payload: formData,
        callback,
      });
    },
    [dispatch]
  );

  const handleApprove = useCallback(
    (values, callback) => {
      const payload = {
        channel_name: values.channel,
        chaincode_name: values.name,
        chaincode_version: values.version,
        sequence: parseInt(values.sequence, 10),
        policy: values.policy,
        init_flag: !!values.initFlag,
      };
      dispatch({
        type: 'chainCode/approveChainCode',
        payload,
        callback,
      });
    },
    [dispatch]
  );

  const handleCommit = useCallback(
    (values, callback) => {
      const payload = {
        channel_name: values.channel,
        chaincode_name: values.name,
        chaincode_version: values.version,
        sequence: parseInt(values.sequence, 10),
        policy: values.policy,
        init_flag: !!values.initFlag,
      };
      dispatch({
        type: 'chainCode/commitChainCode',
        payload,
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

  const installFormProps = useMemo(
    () => ({
      installModalVisible,
      handleInstallModalVisible,
      fetchChainCodes,
      handleInstall,
      installing,
      chainCodeName,
      nodes,
      intl,
    }),
    [
      installModalVisible,
      handleInstallModalVisible,
      fetchChainCodes,
      handleInstall,
      installing,
      chainCodeName,
      nodes,
      intl,
    ]
  );

  const approveFormProps = useMemo(
    () => ({
      approveModalVisible,
      handleApproveModalVisible,
      fetchChainCodes,
      handleApprove,
      approving,
      selectedRows: [],
      initFlagChange: e => {
        // 保留原本示範行為
        // eslint-disable-next-line no-console
        console.log('initFlag changed:', e.target.checked);
      },
      intl,
    }),
    [
      approveModalVisible,
      handleApproveModalVisible,
      fetchChainCodes,
      handleApprove,
      approving,
      intl,
    ]
  );

  const commitFormProps = useMemo(
    () => ({
      commitModalVisible,
      handleCommitModalVisible,
      handleCommit,
      fetchChainCodes,
      committing,
      intl,
    }),
    [commitModalVisible, handleCommitModalVisible, handleCommit, fetchChainCodes, committing, intl]
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
          <a onClick={() => handleInstallModalVisible(true, record)}>
            {intl.formatMessage({
              id: 'app.chainCode.table.operate.install',
              defaultMessage: 'Install',
            })}
          </a>
          <Divider type="vertical" />
          <a onClick={() => handleApproveModalVisible(true)}>
            {intl.formatMessage({
              id: 'app.chainCode.table.operate.approve',
              defaultMessage: 'Approve',
            })}
          </a>
          <Divider type="vertical" />
          <a onClick={() => handleCommitModalVisible(true)}>
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
      <InstallForm {...installFormProps} />
      <ApproveForm {...approveFormProps} />
      <CommitForm {...commitFormProps} />
    </PageHeaderWrapper>
  );
};

export default connect(({ chainCode, loading }) => ({
  chainCode,
  loadingChainCodes: loading.effects['chainCode/listChainCode'],
  uploading: loading.effects['chainCode/uploadChainCode'],
  installing: loading.effects['chainCode/installChainCode'],
  approving: loading.effects['chainCode/approveChainCode'],
  committing: loading.effects['chainCode/commitChainCode'],
}))(ChainCode);
