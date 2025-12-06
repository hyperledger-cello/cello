/*
 SPDX-License-Identifier: Apache-2.0
*/
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { connect, useIntl } from 'umi';
import { Card, Button, Modal, message, Input, Select, Form, Tag, Upload } from 'antd';
import { PlusOutlined, UploadOutlined, DeploymentUnitOutlined } from '@ant-design/icons';
import PageHeaderWrapper from '@/components/PageHeaderWrapper';
import StandardTable from '@/components/StandardTable';
import { useTableManagement } from '@/hooks';
import styles from './styles.less';

const FormItem = Form.Item;
const { Option } = Select;

const CreateChannel = props => {
  const [form] = Form.useForm();
  const intl = useIntl();
  const { modalVisible, handleCreate, handleModalVisible, nodes, creating, fetchChannels } = props;

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

  const peers = [];
  const orderers = [];

  Object.keys(nodes).forEach(item => {
    if (nodes[item].type.toLowerCase() === 'peer') {
      peers.push({ label: nodes[item].name, value: nodes[item].id });
    } else {
      orderers.push({ label: nodes[item].name, value: nodes[item].id });
    }
  });

  // eslint-disable-next-line no-shadow
  const tagRender = props => {
    const { label, closable, onClose } = props;
    const onPreventMouseDown = event => {
      event.preventDefault();
      event.stopPropagation();
    };
    return (
      <Tag
        color="cyan"
        onMouseDown={onPreventMouseDown}
        closable={closable}
        onClose={onClose}
        style={{ marginRight: 3 }}
      >
        {label}
      </Tag>
    );
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
              defaultMessage: 'Name',
            })}
          />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.channel.form.create.orderer',
            defaultMessage: 'Please select orderer',
          })}
          name="orderer_ids"
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.channel.form.create.checkOrderer',
                defaultMessage: 'Please select orderer',
              }),
            },
          ]}
        >
          <Select
            mode="multiple"
            options={orderers}
            tagRender={tagRender}
            dropdownClassName={styles.dropdownClassName}
          />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.channel.form.create.peer',
            defaultMessage: 'Peer',
          })}
          name="peer_ids"
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.channel.form.create.checkPeer',
                defaultMessage: 'Please select peer',
              }),
            },
          ]}
        >
          <Select
            mode="multiple"
            options={peers}
            tagRender={tagRender}
            dropdownClassName={styles.dropdownClassName}
          />
        </FormItem>
      </Form>
    </Modal>
  );
};

const UpdateChannel = props => {
  const [form] = Form.useForm();
  const intl = useIntl();
  const {
    updateModalVisible,
    handleUpdate,
    handleModalVisible,
    updating,
    fetchChannels,
    channelData,
    newFile,
    setFile,
  } = props;

  const updateCallback = response => {
    if (response.status === 'successful') {
      message.success(
        intl.formatMessage({
          id: 'app.channel.form.update.success',
          defaultMessage: 'Update channel succeed',
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
    handleUpdate(channelData.id, values, updateCallback);
  };

  const normFile = e => {
    if (Array.isArray(e)) {
      return e;
    }
    return newFile;
  };

  const uploadProps = {
    onRemove: () => {
      setFile(null);
    },
    beforeUpload: file => {
      setFile(file);
      return false;
    },
  };

  const orgTypes = ['Application', 'Orderer'];
  const orgTypeOptions = orgTypes.map(item => (
    <Option value={item} key={item}>
      <span>{item}</span>
    </Option>
  ));

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
        id: 'app.channel.form.update.header.title',
        defaultMessage: 'Update Channel',
      })}
      confirmLoading={updating}
      open={updateModalVisible}
      onOk={onSubmit}
      onCancel={() => handleModalVisible(false)}
    >
      <Form onFinish={onFinish} form={form} preserve={false}>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.channel.form.update.mspId',
            defaultMessage: 'MSP ID',
          })}
          name="msp_id"
          initialValue=""
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.channel.form.update.checkMSPId',
                defaultMessage: 'Please enter the MSP id',
              }),
            },
          ]}
        >
          <Input
            placeholder={intl.formatMessage({
              id: 'app.channel.form.update.mspId',
              defaultMessage: 'MSP id',
            })}
          />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.channel.form.update.orgType',
            defaultMessage: 'Org Type',
          })}
          name="org_type"
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.channel.form.update.required.orgType',
                defaultMessage: 'Please select Org type.',
              }),
            },
          ]}
        >
          <Select>{orgTypeOptions}</Select>
        </FormItem>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.channel.form.update.file',
            defaultMessage: 'Channel config file',
          })}
          name="data"
          getValueFromEvent={normFile}
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.channel.form.update.fileSelect',
                defaultMessage: 'Please select the channel config file',
              }),
            },
          ]}
        >
          <Upload {...uploadProps}>
            <Button disabled={!!newFile}>
              <UploadOutlined />
              {intl.formatMessage({
                id: 'app.channel.form.update.fileSelect',
                defaultMessage: 'Please select the channel config file',
              })}
            </Button>
          </Upload>
        </FormItem>
      </Form>
    </Modal>
  );
};

const Channel = ({ dispatch, channel = {}, node = {}, loadingChannels, creating, updating }) => {
  const intl = useIntl();
  const { channels = [], pagination = {} } = channel;
  const { nodes = {} } = node;

  const { selectedRows, handleSelectRows, handleTableChange, refreshList } = useTableManagement({
    dispatch,
    listAction: 'channel/listChannel',
  });

  const [modalVisible, setModalVisible] = useState(false);
  const [updateModalVisible, setUpdateModalVisible] = useState(false);
  const [channelData, setChannelData] = useState({});
  const [newFile, setFile] = useState(null);

  useEffect(() => {
    dispatch({ type: 'channel/listChannel' });
    dispatch({ type: 'node/listNode' });
    return () => {
      dispatch({ type: 'channel/clear' });
    };
  }, [dispatch]);

  const fetchChannels = useCallback(() => {
    refreshList();
    dispatch({ type: 'node/listNode' });
  }, [dispatch, refreshList]);

  const handleModalVisible = useCallback(visible => {
    setModalVisible(!!visible);
  }, []);

  const handleUpdateModalVisible = useCallback((visible, record) => {
    setUpdateModalVisible(!!visible);
    setChannelData(record || {});
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

  const handleUpdate = useCallback(
    (id, values, callback) => {
      const formData = new FormData();
      Object.keys(values).forEach(key => {
        formData.append(key, values[key]);
      });
      dispatch({
        type: 'channel/updateChannel',
        id,
        payload: formData,
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
      nodes,
    }),
    [modalVisible, handleCreate, handleModalVisible, fetchChannels, creating, intl, nodes]
  );

  const updateFormProps = useMemo(
    () => ({
      updateModalVisible,
      handleUpdate,
      handleModalVisible: handleUpdateModalVisible,
      fetchChannels,
      updating,
      channelData,
      newFile,
      setFile,
      intl,
    }),
    [
      updateModalVisible,
      handleUpdate,
      handleUpdateModalVisible,
      fetchChannels,
      updating,
      channelData,
      newFile,
      intl,
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
      <UpdateChannel {...updateFormProps} />
    </PageHeaderWrapper>
  );
};

export default connect(({ channel, node, loading }) => ({
  channel,
  node,
  loadingChannels: loading.effects['channel/listChannel'],
  creating: loading.effects['channel/createChannel'],
  updating: loading.effects['channel/updateChannel'],
}))(Channel);
