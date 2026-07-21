/*
 SPDX-License-Identifier: Apache-2.0
 */
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { connect, useIntl, history } from 'umi';
import { Card, Button, Modal, message, Input, Form, Alert } from 'antd';
import { PlusOutlined, DeploymentUnitOutlined } from '@ant-design/icons';
import PageHeaderWrapper from '@/components/PageHeaderWrapper';
import StandardTable from '@/components/StandardTable';
import { useTableManagement } from '@/hooks';
import styles from './styles.less';

const FormItem = Form.Item;

const CreateChannel = props => {
  const [form] = Form.useForm();
  const intl = useIntl();
  const {
    modalVisible,
    handleCreate,
    handleModalVisible,
    creating,
    fetchChannels,
    nodeCounts,
    loadingNodeCounts,
  } = props;

  const hasPeer = nodeCounts.peer > 0;
  const hasOrderer = nodeCounts.orderer > 0;
  const canCreate = hasPeer && hasOrderer;
  const showWarning = !canCreate && !loadingNodeCounts;

  const createCallback = response => {
    if (response.status.toLowerCase() !== 'successful') {
      message.error(
        intl.formatMessage({
          id: 'app.channel.form.create.fail',
          defaultMessage: 'Create channel failed',
        })
      );
    } else {
      message.success(
        intl.formatMessage({
          id: 'app.channel.form.create.success',
          defaultMessage: 'Create channel succeed',
        })
      );
      form.resetFields();
      handleModalVisible();
      fetchChannels();
    }
  };

  const onSubmit = () => {
    form.submit();
  };

  const onFinish = values => {
    handleCreate(values, createCallback);
  };

  const formItemLayout = {
    labelCol: {
      xs: { span: 24 },
      sm: { span: 7 },
    },
    wrapperCol: {
      xs: { span: 24 },
      sm: { span: 12 },
      md: { span: 10 },
    },
  };

  return (
    <Modal
      destroyOnClose
      title={intl.formatMessage({
        id: 'app.channel.form.create.header.title',
        defaultMessage: 'Create Channel',
      })}
      confirmLoading={creating}
      open={modalVisible}
      onOk={onSubmit}
      onCancel={() => handleModalVisible(false)}
    >
      <Form onFinish={onFinish} form={form} preserve={false}>
        {showWarning && (
          <Alert
            message={intl.formatMessage({
              id: 'app.channel.form.create.warning.title',
              defaultMessage: 'Cannot create channel',
            })}
            description={
              <div>
                <p>
                  {intl.formatMessage({
                    id: 'app.channel.form.create.warning.desc',
                    defaultMessage:
                      'Your organization needs at least 1 Peer and 1 Orderer before creating a channel.',
                  })}
                </p>
                <p>
                  {intl.formatMessage(
                    {
                      id: 'app.channel.form.create.warning.current',
                      defaultMessage: 'Current: {peer} Peer(s), {orderer} Orderer(s)',
                    },
                    { peer: nodeCounts.peer, orderer: nodeCounts.orderer }
                  )}
                </p>
                <Button type="link" onClick={() => history.push('/node/new')}>
                  {intl.formatMessage({
                    id: 'app.channel.form.create.warning.action',
                    defaultMessage: 'Create Nodes Now →',
                  })}
                </Button>
              </div>
            }
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.channel.form.create.name',
            defaultMessage: 'Name',
          })}
          name="name"
          initialValue=""
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.channel.form.create.checkName',
                defaultMessage: 'Please enter the channel name',
              }),
            },
          ]}
        >
          <Input
            placeholder={intl.formatMessage({
              id: 'app.channel.form.create.name',
              defaultMessage: canCreate ? 'Name' : 'Create nodes first',
            })}
            disabled={!canCreate}
          />
        </FormItem>
      </Form>
    </Modal>
  );
};

const Channel = ({
  dispatch,
  channel = {},
  loadingChannels,
  creating,
  nodeCounts,
  loadingNodeCounts,
}) => {
  const intl = useIntl();
  const { channels = [], pagination = {} } = channel;

  const { selectedRows, handleSelectRows, handleTableChange, refreshList } = useTableManagement({
    dispatch,
    listAction: 'channel/listChannel',
  });

  const [modalVisible, setModalVisible] = useState(false);

  useEffect(() => {
    dispatch({ type: 'channel/listChannelWithNodes' });
    return () => {
      dispatch({ type: 'channel/clear' });
    };
  }, [dispatch]);

  const fetchChannels = useCallback(() => {
    refreshList();
  }, [refreshList]);

  const handleModalVisible = useCallback(visible => {
    setModalVisible(!!visible);
  }, []);

  const onCreateChannel = useCallback(() => {
    handleModalVisible(true);
  }, [handleModalVisible]);

  const handleCreate = useCallback(
    (values, callback) => {
      dispatch({
        type: 'channel/createChannel',
        payload: values,
        callback,
      });
    },
    [dispatch]
  );

  const formProps = useMemo(
    () => ({
      modalVisible,
      handleCreate,
      handleModalVisible,
      fetchChannels,
      creating,
      intl,
      nodeCounts,
      loadingNodeCounts,
    }),
    [
      modalVisible,
      handleCreate,
      handleModalVisible,
      fetchChannels,
      creating,
      intl,
      nodeCounts,
      loadingNodeCounts,
    ]
  );

  const columns = [
    {
      title: intl.formatMessage({
        id: 'app.channel.table.header.name',
        defaultMessage: 'Channel Name',
      }),
      dataIndex: 'name',
    },
    {
      title: intl.formatMessage({
        id: 'form.table.header.operation',
        defaultMessage: 'Operation',
      }),
      render: (text, record) => (
        <a
          onClick={() => history.push(`/channel/invitation?channel=${record.id}`)}
          style={{ cursor: 'pointer' }}
        >
          {intl.formatMessage({
            id: 'app.channel.table.row.invitations',
            defaultMessage: 'Invitations',
          })}
        </a>
      ),
    },
  ];

  return (
    <PageHeaderWrapper
      title={
        <span>
          <DeploymentUnitOutlined style={{ marginRight: 15 }} />
          {intl.formatMessage({
            id: 'app.channel.title',
            defaultMessage: 'Channel Management',
          })}
        </span>
      }
    >
      <Card bordered={false}>
        <div className={styles.tableList}>
          <div className={styles.tableListOperator}>
            <Button type="primary" onClick={onCreateChannel}>
              <PlusOutlined />
              {intl.formatMessage({ id: 'form.button.new', defaultMessage: 'New' })}
            </Button>
          </div>
          <StandardTable
            selectedRows={selectedRows}
            loading={loadingChannels}
            rowKey="id"
            data={{
              list: channels,
              pagination,
            }}
            columns={columns}
            onSelectRow={handleSelectRows}
            onChange={handleTableChange}
          />
        </div>
      </Card>
      <CreateChannel {...formProps} />
    </PageHeaderWrapper>
  );
};

export default connect(({ channel, loading }) => ({
  channel,
  nodeCounts: channel.nodeCounts,
  loadingNodeCounts: channel.loadingNodeCounts,
  loadingChannels: loading.effects['channel/listChannel'],
  creating: loading.effects['channel/createChannel'],
}))(Channel);
