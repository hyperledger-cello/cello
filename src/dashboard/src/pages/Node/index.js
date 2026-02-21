/*
 SPDX-License-Identifier: Apache-2.0
*/
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { connect, useIntl } from 'umi';
import { Card, Button, Modal, message, Form, Input, Select, Badge } from 'antd';
import { PlusOutlined, NodeIndexOutlined } from '@ant-design/icons';
import moment from 'moment';
import PageHeaderWrapper from '@/components/PageHeaderWrapper';
import StandardTable from '@/components/StandardTable';
import { getAuthority } from '@/utils/authority';
import { useTableManagement } from '@/hooks';
import styles from '../styles.less';

const FormItem = Form.Item;
const { Option } = Select;

const RegisterUserForm = props => {
  const {
    registerUserFormVisible,
    handleSubmit,
    handleModalVisible,
    registeringUser,
    targetNodeId,
    intl,
  } = props;
  const [form] = Form.useForm();
  const onFinish = values => {
    if (values.attrs === '') {
      // eslint-disable-next-line no-param-reassign
      delete values.attrs;
    }
    const body = {
      id: targetNodeId,
      message: values,
    };
    handleSubmit(body);
  };
  const onSubmit = () => {
    form.submit();
  };
  const userTypeValues = ['peer', 'orderer', 'user'];
  const userTypeOptions = userTypeValues.map(item => (
    <Option value={item} key={item}>
      <span>{item}</span>
    </Option>
  ));
  const formItemLayout = {
    labelCol: {
      xs: { span: 24 },
      sm: { span: 8 },
    },
    wrapperCol: {
      xs: { span: 24 },
      sm: { span: 16 },
      md: { span: 10 },
    },
  };

  return (
    <Modal
      destroyOnClose
      title={intl.formatMessage({
        id: 'app.node.table.operation.registerUser',
        defaultMessage: 'Register User',
      })}
      visible={registerUserFormVisible}
      confirmLoading={registeringUser}
      width="30%"
      onOk={onSubmit}
      onCancel={() => handleModalVisible()}
    >
      <Form
        form={form}
        onFinish={onFinish}
        initialValues={{
          name: '',
        }}
      >
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.node.modal.label.name',
            defaultMessage: 'User name',
          })}
          name="name"
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.node.modal.required.name',
                defaultMessage: 'Please input user name.',
              }),
            },
          ]}
        >
          <Input
            placeholder={intl.formatMessage({
              id: 'app.node.modal.label.name',
              defaultMessage: 'User name',
            })}
          />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.node.modal.label.secret',
            defaultMessage: 'Password',
          })}
          name="secret"
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.node.modal.required.secret',
                defaultMessage: 'Please input password.',
              }),
            },
          ]}
        >
          <Input
            placeholder={intl.formatMessage({
              id: 'app.node.modal.label.secret',
              defaultMessage: 'Password',
            })}
          />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.node.modal.label.type',
            defaultMessage: 'Type',
          })}
          name="user_type"
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.node.modal.required.type',
                defaultMessage: 'Please select a type.',
              }),
            },
          ]}
        >
          <Select style={{ width: '100%' }}>{userTypeOptions}</Select>
        </FormItem>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.node.modal.label.attributes',
            defaultMessage: 'Attributes',
          })}
          name="attr"
        >
          <Input
            placeholder={intl.formatMessage({
              id: 'app.node.modal.label.attributes',
              defaultMessage: 'Attributes',
            })}
          />
        </FormItem>
      </Form>
    </Modal>
  );
};

const CreateNode = props => {
  const [form] = Form.useForm();
  const intl = useIntl();
  const { createModalVisible, handleCreate, handleModalVisible, creating, queryNodeList } = props;

  const createCallback = response => {
    if (response.status.toLowerCase() !== 'successful') {
      message.error(
        intl.formatMessage({
          id: 'app.node.new.createFail',
          defaultMessage: 'Create node failed',
        })
      );
    } else {
      message.success(
        intl.formatMessage({
          id: 'app.node.new.createSuccess',
          defaultMessage: 'Create node succeed',
        })
      );
      form.resetFields();
      handleModalVisible();
      queryNodeList();
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

  const types = ['ORDERER', 'PEER'];
  const typeOptions = types.map(item => (
    <Option value={item} key={item}>
      <span style={{ color: '#8c8f88' }}>{item}</span>
    </Option>
  ));

  return (
    <Modal
      destroyOnClose
      title={intl.formatMessage({
        id: 'app.node.new.title',
        defaultMessage: 'Create Node',
      })}
      confirmLoading={creating}
      visible={createModalVisible}
      onOk={onSubmit}
      onCancel={() => handleModalVisible(false)}
    >
      <Form onFinish={onFinish} form={form} preserve={false}>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.node.new.name',
            defaultMessage: 'Name',
          })}
          name="name"
          initialValue=""
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.node.new.nameCheck',
                defaultMessage: 'Please enter node name',
              }),
            },
          ]}
        >
          <Input
            placeholder={intl.formatMessage({
              id: 'app.node.new.name',
              defaultMessage: 'Name',
            })}
          />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.node.new.type',
            defaultMessage: 'Type',
          })}
          name="type"
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.node.new.typeCheck',
                defaultMessage: 'Please select a type',
              }),
            },
          ]}
        >
          <Select defaultActiveFirstOption={false}>{typeOptions}</Select>
        </FormItem>
      </Form>
    </Modal>
  );
};

const Index = ({ dispatch, node = {}, loadingNodes, registeringUser, creating }) => {
  const intl = useIntl();
  const { nodes = [], pagination = {} } = node;
  const userRole = getAuthority()[0];

  const { selectedRows, handleSelectRows, handleTableChange, refreshList } = useTableManagement({
    dispatch,
    listAction: 'node/listNode',
  });

  const [registerUserFormVisible, setRegisterUserFormVisible] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);

  const queryNodeList = useCallback(
    (extra = {}) => {
      refreshList({
        per_page: pagination.pageSize,
        page: pagination.current,
        ...extra,
      });
    },
    [pagination, refreshList]
  );

  useEffect(() => {
    queryNodeList();
    return () => {
      dispatch({ type: 'node/clear' });
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const registerUserCallback = useCallback(() => {
    message.success(
      intl.formatMessage({
        id: 'app.node.modal.success',
        defaultMessage: 'Registered User Successful.',
      })
    );
    setRegisterUserFormVisible(false);
  }, [intl]);

  const handleSubmit = useCallback(
    values => {
      dispatch({
        type: 'node/registerUserToNode',
        payload: values,
        callback: registerUserCallback,
      });
    },
    [dispatch, registerUserCallback]
  );

  const handleCreateModalVisible = useCallback(visible => {
    setCreateModalVisible(!!visible);
  }, []);

  const handleCreate = useCallback(
    (values, callback) => {
      dispatch({
        type: 'node/createNode',
        payload: values,
        callback,
      });
    },
    [dispatch]
  );

  const formProps = useMemo(
    () => ({
      registerUserFormVisible,
      handleSubmit,
      handleModalVisible: () => setRegisterUserFormVisible(false),
      registeringUser,
      targetNodeId: '',
      intl,
    }),
    [registerUserFormVisible, handleSubmit, registeringUser, intl]
  );

  const createFormProps = useMemo(
    () => ({
      createModalVisible,
      handleCreate,
      handleModalVisible: handleCreateModalVisible,
      creating,
      intl,
      queryNodeList,
    }),
    [createModalVisible, handleCreate, handleCreateModalVisible, creating, intl, queryNodeList]
  );

  const badgeStatus = status => {
    let statusOfBadge = 'default';
    switch (status) {
      case 'running':
        statusOfBadge = 'success';
        break;
      case 'paused':
        statusOfBadge = 'warning';
        break;
      case 'restarting':
        statusOfBadge = 'error';
        break;
      default:
        break;
    }
    return statusOfBadge;
  };

  const columns = [
    {
      title: intl.formatMessage({
        id: 'app.node.table.header.name',
        defaultMessage: 'Name',
      }),
      dataIndex: 'name',
    },
    {
      title: intl.formatMessage({
        id: 'app.node.table.header.type',
        defaultMessage: 'Type',
      }),
      dataIndex: 'type',
      render: text => text.toLowerCase(),
    },
    {
      title: intl.formatMessage({
        id: 'app.node.table.header.creationTime',
        defaultMessage: 'Creation Time',
      }),
      dataIndex: 'created_at',
      render: text => <span>{moment(text).format('YYYY-MM-DD HH:mm:ss')}</span>,
    },
    {
      title: intl.formatMessage({
        id: 'app.node.table.header.status',
        defaultMessage: 'Status',
      }),
      dataIndex: 'status',
      render: text => <Badge status={badgeStatus(text.toLowerCase())} text={text.toLowerCase()} />,
    },
    {
      title: intl.formatMessage({
        id: 'form.table.header.operation',
        defaultMessage: 'Operation',
      }),
      render: () => null,
    },
  ];

  return (
    <PageHeaderWrapper
      title={
        <span>
          <NodeIndexOutlined style={{ marginRight: 15 }} />
          {intl.formatMessage({
            id: 'app.node.title',
            defaultMessage: 'Node Management',
          })}
        </span>
      }
    >
      <Card bordered={false}>
        <div className={styles.tableList}>
          <div className={styles.tableListOperator}>
            {userRole !== 'operator' && (
              <Button type="primary" onClick={() => handleCreateModalVisible(true)}>
                <PlusOutlined />
                {intl.formatMessage({ id: 'form.button.new', defaultMessage: 'New' })}
              </Button>
            )}
          </div>
          <StandardTable
            selectedRows={selectedRows}
            loading={loadingNodes}
            rowKey="id"
            data={{
              list: nodes,
              pagination,
            }}
            columns={columns}
            onSelectRow={handleSelectRows}
            onChange={handleTableChange}
          />
        </div>
      </Card>
      <RegisterUserForm {...formProps} />
      <CreateNode {...createFormProps} />
    </PageHeaderWrapper>
  );
};

export default connect(({ node, loading }) => ({
  node,
  loadingNodes: loading.effects['node/listNode'],
  registeringUser: loading.effects['node/registerUserToNode'],
  creating: loading.effects['node/createNode'],
}))(Index);
