/*
 SPDX-License-Identifier: Apache-2.0
*/
import { useEffect } from 'react';
import { connect, useIntl } from 'umi';
import { Card, Form, Modal, Input, Button, message } from 'antd';
import { PlusOutlined, TeamOutlined } from '@ant-design/icons';
import moment from 'moment';
import PageHeaderWrapper from '@/components/PageHeaderWrapper';
import StandardTable from '@/components/StandardTable';
import { useTableManagement, useModalForm } from '@/hooks';
import styles from '../styles.less';

const FormItem = Form.Item;

// Separate form component for create/update
const CreateUpdateForm = ({
  visible,
  method,
  handleSubmit,
  handleModalVisible,
  confirmLoading,
  organization,
  intl,
}) => {
  const [form] = Form.useForm();

  const onSubmit = () => {
    form.submit();
  };

  const onFinish = values => {
    handleSubmit(method, values, organization);
  };

  return (
    <Modal
      destroyOnClose
      title={intl.formatMessage({
        id: `app.organization.form.${method === 'create' ? 'new' : 'update'}.title`,
        defaultMessage: 'New Organization',
      })}
      visible={visible}
      confirmLoading={confirmLoading}
      width="50%"
      onOk={onSubmit}
      onCancel={() => handleModalVisible()}
    >
      <Form
        form={form}
        onFinish={onFinish}
        initialValues={{
          name: method === 'create' ? '' : organization.name,
          agent_url: method === 'create' ? '' : organization.agent_url,
          msp_id: method === 'create' ? '' : organization.msp_id,
        }}
      >
        <FormItem
          labelCol={{ span: 5 }}
          wrapperCol={{ span: 15 }}
          label={intl.formatMessage({
            id: 'app.organization.form.name.label',
            defaultMessage: 'Organization Name',
          })}
          name="name"
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.organization.form.name.required',
                defaultMessage: 'Please input organization name',
              }),
              min: 1,
            },
          ]}
        >
          <Input
            placeholder={intl.formatMessage({
              id: 'form.input.placeholder',
              defaultMessage: 'Please input',
            })}
          />
        </FormItem>
        <FormItem
          labelCol={{ span: 5 }}
          wrapperCol={{ span: 15 }}
          label={intl.formatMessage({
            id: 'app.organization.form.agent_url.label',
            defaultMessage: 'Agent URL',
          })}
          name="agent_url"
          extra={intl.formatMessage({
            id: 'app.organization.form.agent_url.extra',
            defaultMessage: 'Leave as default for local development',
          })}
        >
          <Input
            placeholder={intl.formatMessage({
              id: 'app.organization.form.agent_url.placeholder',
              defaultMessage: 'http://cello-docker-agent:8080/api/v1/',
            })}
          />
        </FormItem>
        <FormItem
          labelCol={{ span: 5 }}
          wrapperCol={{ span: 15 }}
          label={intl.formatMessage({
            id: 'app.organization.form.msp_id.label',
            defaultMessage: 'MSP ID',
          })}
          name="msp_id"
        >
          <Input
            placeholder={intl.formatMessage({
              id: 'app.organization.form.msp_id.placeholder',
              defaultMessage: 'Auto-generated if blank',
            })}
          />
        </FormItem>
      </Form>
    </Modal>
  );
};

const Organization = ({
  dispatch,
  organization = {},
  loadingOrganizations,
  creatingOrganization,
}) => {
  const intl = useIntl();
  const { organizations = [], pagination = {} } = organization;

  // Use custom hooks
  const { selectedRows, handleSelectRows, handleTableChange, refreshList } = useTableManagement({
    dispatch,
    listAction: 'organization/listOrganization',
  });

  const {
    modalVisible,
    modalMethod,
    currentRecord: currentOrganization,
    closeModal,
    handleModalVisible,
  } = useModalForm();

  // Load data on mount, clear on unmount
  useEffect(() => {
    dispatch({ type: 'organization/listOrganization' });
    return () => {
      dispatch({ type: 'organization/clear' });
    };
  }, [dispatch]);

  // Callbacks for create/update/delete
  const createCallback = data => {
    const { name } = data.payload;
    const responseData = data.data;
    if (responseData && responseData.id) {
      message.success(
        intl.formatMessage(
          {
            id: 'app.organization.create.success',
            defaultMessage: 'Create organization {name} success',
          },
          { name, id: responseData.id }
        )
      );
      closeModal();
      refreshList();
    } else {
      const msg = data.msg || '';
      message.error(
        `${intl.formatMessage(
          {
            id: 'app.organization.create.fail',
            defaultMessage: 'Create organization {name} failed',
          },
          { name }
        )}${msg ? `: ${msg}` : ''}`
      );
    }
  };

  const updateCallback = data => {
    const { name } = data.payload;
    const responseData = data.data;
    if (responseData && responseData.id) {
      message.success(
        intl.formatMessage(
          {
            id: 'app.organization.update.success',
            defaultMessage: 'Update organization {name} success',
          },
          { name }
        )
      );
      closeModal();
      refreshList();
    } else {
      message.error(
        intl.formatMessage(
          {
            id: 'app.organization.update.fail',
            defaultMessage: 'Update organization {name} failed',
          },
          { name }
        )
      );
    }
  };

  // Handle form submit
  const handleSubmit = (method, values, record) => {
    switch (method) {
      case 'create':
        dispatch({
          type: 'organization/createOrganization',
          payload: values,
          callback: createCallback,
        });
        break;
      case 'update':
        dispatch({
          type: 'organization/updateOrganization',
          payload: {
            ...values,
            id: record.id,
          },
          callback: updateCallback,
        });
        break;
      default:
        break;
    }
  };

  // Table columns
  const columns = [
    {
      title: intl.formatMessage({
        id: 'app.organization.table.header.name',
        defaultMessage: 'Organization Name',
      }),
      dataIndex: 'name',
    },
    {
      title: intl.formatMessage({
        id: 'app.organization.table.header.createTime',
        defaultMessage: 'Create Time',
      }),
      dataIndex: 'created_at',
      render: text => <span>{moment(text).format('YYYY-MM-DD HH:mm:ss')}</span>,
    },
    // Operation column is commented out in original, keeping it that way
  ];

  // Form props
  const formProps = {
    visible: modalVisible,
    method: modalMethod,
    organization: currentOrganization,
    handleSubmit,
    handleModalVisible,
    confirmLoading: creatingOrganization,
    intl,
  };

  return (
    <PageHeaderWrapper
      title={
        <span>
          <TeamOutlined style={{ marginRight: 15 }} />
          {intl.formatMessage({
            id: 'app.organization.title',
            defaultMessage: 'Organization Management',
          })}
        </span>
      }
    >
      <Card bordered={false}>
        <div className={styles.tableList}>
          <div className={styles.tableListOperator}>
            <Button type="primary" onClick={() => handleModalVisible(true, 'create')}>
              <PlusOutlined />
              {intl.formatMessage({ id: 'form.button.new', defaultMessage: 'New' })}
            </Button>
          </div>
          <StandardTable
            selectedRows={selectedRows}
            loading={loadingOrganizations}
            rowKey="id"
            data={{
              list: organizations,
              pagination,
            }}
            columns={columns}
            onSelectRow={handleSelectRows}
            onChange={handleTableChange}
          />
        </div>
      </Card>
      <CreateUpdateForm {...formProps} />
    </PageHeaderWrapper>
  );
};

export default connect(({ organization, loading }) => ({
  organization,
  loadingOrganizations: loading.effects['organization/listOrganization'],
  creatingOrganization: loading.effects['organization/createOrganization'],
}))(Organization);
