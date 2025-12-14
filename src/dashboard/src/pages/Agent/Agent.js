import React, { useCallback, useEffect } from 'react';
import { connect, useIntl } from 'umi';
import { Card, Button, message, List, Badge, Row, Col, Modal, Form, Select, Input } from 'antd';
import { PlusOutlined, DesktopOutlined } from '@ant-design/icons';
import moment from 'moment';
import PageHeaderWrapper from '@/components/PageHeaderWrapper';
import { getAuthority } from '@/utils/authority';
import { useDeleteConfirm, useModalForm, useTableManagement } from '@/hooks';
import styles from '../styles.less';

const FormItem = Form.Item;
const { Option } = Select;

const ApplyAgentForm = props => {
  const [form] = Form.useForm();
  const { visible, handleSubmit, handleModalVisible, confirmLoading, action, agentData } = props;
  const intl = useIntl();
  const onSubmit = () => {
    form.submit();
  };
  const onFinish = values => {
    if (action === 'update') {
      handleSubmit({ name: values.name, id: agentData.id }, action);
    } else {
      handleSubmit(values, action);
    }
  };
  const agentTypeValues = ['docker', 'kubernetes'];
  const agentTypeOptions = agentTypeValues.map(item => (
    <Option value={item} key={item}>
      <span style={{ color: '#8c8f88' }}>{item}</span>
    </Option>
  ));
  const width = { width: '120px' };
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
        id: 'app.applyAgent.title',
        defaultMessage: 'Apply for agent',
      })}
      visible={visible}
      confirmLoading={confirmLoading}
      width="45%"
      onOk={onSubmit}
      onCancel={() => handleModalVisible(false)}
    >
      <Form onFinish={onFinish} form={form} preserve={false}>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.newAgent.label.name',
            defaultMessage: 'Name',
          })}
          name="name"
          initialValue={action === 'create' ? '' : agentData.name}
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.agent.form.name.required',
                defaultMessage: 'Please input agent name',
              }),
            },
          ]}
        >
          <Input
            placeholder={intl.formatMessage({
              id: 'app.newAgent.label.name',
              defaultMessage: 'Name',
            })}
          />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.newAgent.label.ip',
            defaultMessage: 'Agent IP Address',
          })}
          name="urls"
          initialValue={action === 'create' ? '' : agentData.urls}
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.newAgent.required.ip',
                defaultMessage: 'Please input the ip address & port of the agent.',
              }),
            },
          ]}
        >
          <Input placeholder="http://192.168.0.10:5001" disabled={action === 'update'} />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.newAgent.label.type',
            defaultMessage: 'Type',
          })}
          name="type"
          initialValue={action === 'create' ? agentTypeValues[0] : agentData.type}
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.newAgent.required.type',
                defaultMessage: 'Please select a type.',
              }),
            },
          ]}
        >
          <Select defaultActiveFirstOption={false} style={width} disabled={action === 'update'}>
            {agentTypeOptions}
          </Select>
        </FormItem>
      </Form>
    </Modal>
  );
};

const Agent = ({ dispatch, agent = {}, loadingAgents, applyingAgent }) => {
  const intl = useIntl();
  const { agents = [], pagination = {} } = agent;
  const pageSize = pagination.pageSize || 10;
  const currentPage = pagination.current || 1;
  const userRole = getAuthority()[0];

  const { refreshList } = useTableManagement({
    dispatch,
    listAction: 'agent/listAgent',
  });
  const { showDeleteConfirm } = useDeleteConfirm({ dispatch, intl });
  const {
    modalVisible,
    modalMethod,
    currentRecord: agentData,
    openCreateModal,
    openUpdateModal,
    closeModal,
    handleModalVisible,
  } = useModalForm();

  const queryAgentList = useCallback(
    (page = currentPage, perPage = pageSize) => {
      refreshList({
        page,
        per_page: perPage,
      });
      if (userRole === 'admin') {
        dispatch({ type: 'organization/listOrganization' });
      }
    },
    [dispatch, refreshList, userRole, currentPage, pageSize]
  );

  useEffect(() => {
    queryAgentList();
    return () => {
      dispatch({ type: 'agent/clear' });
    };
  }, [dispatch, queryAgentList]);

  const submitCallback = useCallback(
    response => {
      if (response.status === 'successful') {
        if (response.action === 'create') {
          message.success(
            intl.formatMessage({
              id: 'app.applyAgent.success',
              defaultMessage: 'Successful application for agent.',
            })
          );
        } else {
          message.success(
            intl.formatMessage({
              id: 'app.updateAgent.success',
              defaultMessage: 'Successful application for agent.',
            })
          );
        }
        queryAgentList();
        closeModal();
      }
    },
    [closeModal, intl, queryAgentList]
  );

  const handleSubmit = useCallback(
    (values, action) => {
      const type = action === 'create' ? 'agent/applyAgent' : 'agent/updateAgent';
      dispatch({
        type,
        payload: { data: values, action },
        callback: submitCallback,
      });
    },
    [dispatch, submitCallback]
  );

  const handlePageChange = useCallback(
    (page, perPage) => {
      queryAgentList(page, perPage || pageSize);
    },
    [queryAgentList, pageSize]
  );

  const handleDelete = useCallback(
    agentItem => {
      const titleId =
        userRole === 'admin' ? 'app.agent.form.delete.title' : 'app.agent.form.release.title';
      const contentId =
        userRole === 'admin' ? 'app.agent.form.delete.content' : 'app.agent.form.release.content';
      const successId =
        userRole === 'admin' ? 'app.agent.delete.success' : 'app.agent.release.success';
      const failId = userRole === 'admin' ? 'app.agent.delete.fail' : 'app.agent.release.fail';

      showDeleteConfirm({
        record: agentItem,
        deleteAction: 'agent/deleteAgent',
        titleId,
        contentId,
        successId,
        failId,
        onSuccess: () => queryAgentList(),
      });
    },
    [queryAgentList, showDeleteConfirm, userRole]
  );

  const nodeList = useCallback(agentItem => agentItem, []);

  const badgeStatus = status => {
    let statusOfBadge = 'default';
    switch (status) {
      case 'active':
        statusOfBadge = 'success';
        break;
      case 'inactive':
        statusOfBadge = 'error';
        break;
      default:
        break;
    }
    return statusOfBadge;
  };

  const paginationProps = {
    showQuickJumper: true,
    total: pagination.total,
    pageSize,
    current: currentPage,
    onChange: handlePageChange,
  };

  const ListContent = ({ data: { type, created_at: createdAt, status } }) => (
    <div>
      <Row gutter={15} className={styles.ListContentRow}>
        <Col span={8}>
          <p>{intl.formatMessage({ id: 'app.agent.type', defaultMessage: 'Type' })}</p>
          <p>{type}</p>
        </Col>
        <Col span={10}>
          <p>
            {intl.formatMessage({
              id: 'app.agent.table.header.creationTime',
              defaultMessage: 'Creation Time',
            })}
          </p>
          <p>{moment(createdAt).format('YYYY-MM-DD HH:mm:ss')}</p>
        </Col>
        <Col span={6}>
          <Badge status={badgeStatus(status)} text={status} />
        </Col>
      </Row>
    </div>
  );

  const formProps = {
    visible: modalVisible,
    handleSubmit,
    handleModalVisible,
    confirmLoading: applyingAgent,
    action: modalMethod,
    agentData,
  };

  return (
    <PageHeaderWrapper
      title={
        <span>
          <DesktopOutlined style={{ marginRight: 15 }} />
          {intl.formatMessage({
            id: 'app.agent.title',
            defaultMessage: 'Agent Management',
          })}
        </span>
      }
    >
      <Card bordered={false}>
        <div className={styles.tableList}>
          <div className={styles.tableListOperator}>
            <Button className={styles.newAgentButton} type="dashed" onClick={openCreateModal}>
              <PlusOutlined />{' '}
              {intl.formatMessage({ id: 'form.button.new', defaultMessage: 'New' })}
            </Button>
          </div>
          <List
            size="large"
            rowKey="id"
            loading={loadingAgents}
            pagination={agents.length > 0 ? paginationProps : false}
            dataSource={agents}
            renderItem={item => (
              <List.Item
                actions={[
                  <a onClick={() => openUpdateModal(item)}>
                    {intl.formatMessage({
                      id: 'form.menu.item.update',
                      defaultMessage: 'Update',
                    })}
                  </a>,
                  <a onClick={() => nodeList(item)}>
                    {intl.formatMessage({ id: 'menu.node', defaultMessage: 'Node' })}
                  </a>,
                  <a onClick={() => handleDelete(item)}>
                    {intl.formatMessage({
                      id: 'form.menu.item.delete',
                      defaultMessage: 'Delete',
                    })}
                  </a>,
                ]}
              >
                <List.Item.Meta
                  title={<span className={styles.ListItemTitle}>{item.name}</span>}
                  description={
                    <div>
                      <p>{item.ip}</p>
                    </div>
                  }
                />
                <ListContent data={item} />
              </List.Item>
            )}
          />
        </div>
      </Card>
      <ApplyAgentForm {...formProps} />
    </PageHeaderWrapper>
  );
};

export default connect(({ agent, loading }) => ({
  agent,
  loadingAgents: loading.effects['agent/listAgent'],
  applyingAgent: loading.effects['agent/applyAgent'] || loading.effects['agent/updateAgent'],
}))(Agent);
