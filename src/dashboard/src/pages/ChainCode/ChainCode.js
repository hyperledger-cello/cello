/*
 SPDX-License-Identifier: Apache-2.0
*/
import { useCallback, useEffect, useMemo, useState } from 'react';
import { connect, useIntl } from 'umi';
import { Card, Button, Badge } from 'antd';
import { PlusOutlined, FunctionOutlined } from '@ant-design/icons';
import PageHeaderWrapper from '@/components/PageHeaderWrapper';
import StandardTable from '@/components/StandardTable';
import UploadForm from '@/pages/ChainCode/forms/UploadForm';
import { useTableManagement } from '@/hooks';
import styles from './styles.less';

const ChainCode = ({ dispatch, chainCode = {}, loadingChainCodes, uploading }) => {
  const intl = useIntl();
  const { chainCodes = [], paginations = {} } = chainCode;

  const { selectedRows, handleSelectRows, handleTableChange, refreshList } = useTableManagement({
    dispatch,
    listAction: 'chainCode/listChainCode',
  });

  const [modalVisible, setModalVisible] = useState(false);
  const [newFile, setFile] = useState(null);
  const [operatingId, setOperatingId] = useState(null);
  const [operationType, setOperationType] = useState(null);

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
      setOperatingId(values.id);
      setOperationType('install');
      dispatch({
        type: 'chainCode/installChainCode',
        payload: { id: values.id },
        callback: () => {
          setOperatingId(null);
          setOperationType(null);
          if (callback) callback();
        },
      });
    },
    [dispatch]
  );

  const handleApprove = useCallback(
    (values, callback) => {
      setOperatingId(values.id);
      setOperationType('approve');
      dispatch({
        type: 'chainCode/approveChainCode',
        payload: { id: values.id },
        callback: () => {
          setOperatingId(null);
          setOperationType(null);
          if (callback) callback();
        },
      });
    },
    [dispatch]
  );

  const handleCommit = useCallback(
    (values, callback) => {
      setOperatingId(values.id);
      setOperationType('commit');
      dispatch({
        type: 'chainCode/commitChainCode',
        payload: { id: values.id },
        callback: () => {
          setOperatingId(null);
          setOperationType(null);
          if (callback) callback();
        },
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

  const getStatusBadge = status => {
    const statusMap = {
      CREATED: 'default',
      INSTALLED: 'success',
      APPROVED: 'success',
      COMMITTED: 'success',
    };
    return statusMap[status] || 'default';
  };

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
        id: 'app.chainCode.table.header.status',
        defaultMessage: 'Status',
      }),
      dataIndex: 'status',
      render: status => {
        const statusIdMap = {
          CREATED: 'app.chainCode.status.created',
          INSTALLED: 'app.chainCode.status.installed',
          APPROVED: 'app.chainCode.status.approved',
          COMMITTED: 'app.chainCode.status.committed',
        };
        const statusDefaultMap = {
          CREATED: 'Created',
          INSTALLED: 'Installed',
          APPROVED: 'Approved',
          COMMITTED: 'Committed',
        };
        return (
          <Badge
            status={getStatusBadge(status)}
            text={intl.formatMessage({
              id: statusIdMap[status] || 'app.chainCode.status.unknown',
              defaultMessage: statusDefaultMap[status] || status,
            })}
          />
        );
      },
    },
    {
      title: intl.formatMessage({
        id: 'app.chainCode.table.header.approvals',
        defaultMessage: 'Approvals',
      }),
      dataIndex: 'approvals',
      render: approvals => {
        if (!approvals || typeof approvals !== 'object') {
          return '0/0';
        }
        const keys = Object.keys(approvals);
        const total = keys.length;
        const approved = keys.filter(key => approvals[key] === true).length;
        return `${approved}/${total}`;
      },
    },
    {
      title: intl.formatMessage({
        id: 'form.table.header.operation',
        defaultMessage: 'Operation',
      }),
      render: (text, record) => {
        const isInstallingThis = operatingId === record.id && operationType === 'install';
        const isApprovingThis = operatingId === record.id && operationType === 'approve';
        const isCommittingThis = operatingId === record.id && operationType === 'commit';

        // 根据状态决定显示哪个按钮
        if (record.status === 'CREATED') {
          return (
            <a
              onClick={() =>
                !isInstallingThis && handleInstall({ id: record.id }, () => fetchChainCodes())
              }
              style={
                isInstallingThis ? { opacity: 0.6, cursor: 'not-allowed' } : { cursor: 'pointer' }
              }
            >
              {isInstallingThis
                ? intl.formatMessage({
                    id: 'app.chainCode.table.operate.installing',
                    defaultMessage: 'Installing...',
                  })
                : intl.formatMessage({
                    id: 'app.chainCode.table.operate.install',
                    defaultMessage: 'Install',
                  })}
            </a>
          );
        }

        if (record.status === 'INSTALLED') {
          return (
            <a
              onClick={() =>
                !isApprovingThis && handleApprove({ id: record.id }, () => fetchChainCodes())
              }
              style={
                isApprovingThis ? { opacity: 0.6, cursor: 'not-allowed' } : { cursor: 'pointer' }
              }
            >
              {isApprovingThis
                ? intl.formatMessage({
                    id: 'app.chainCode.table.operate.approving',
                    defaultMessage: 'Approving...',
                  })
                : intl.formatMessage({
                    id: 'app.chainCode.table.operate.approve',
                    defaultMessage: 'Approve',
                  })}
            </a>
          );
        }

        if (record.status === 'APPROVED') {
          return (
            <a
              onClick={() =>
                !isCommittingThis && handleCommit({ id: record.id }, () => fetchChainCodes())
              }
              style={
                isCommittingThis ? { opacity: 0.6, cursor: 'not-allowed' } : { cursor: 'pointer' }
              }
            >
              {isCommittingThis
                ? intl.formatMessage({
                    id: 'app.chainCode.table.operate.committing',
                    defaultMessage: 'Committing...',
                  })
                : intl.formatMessage({
                    id: 'app.chainCode.table.operate.commit',
                    defaultMessage: 'Commit',
                  })}
            </a>
          );
        }

        // COMMITTED 或其他状态不显示按钮
        return null;
      },
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
