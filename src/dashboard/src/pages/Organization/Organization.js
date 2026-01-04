/*
 SPDX-License-Identifier: Apache-2.0
*/
import { useEffect } from 'react';
import { connect, useIntl } from 'umi';
import { Card, Form, Modal, Input, message } from 'antd';
import { TeamOutlined } from '@ant-design/icons';
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
    if (data.id) {
      message.success(
        intl.formatMessage(
          {
            id: 'app.organization.create.success',
            defaultMessage: 'Create organization {name} success',
          },
          { name, id: data.id }
        )
      );
      closeModal();
      refreshList();
    } else {
      message.error(
        intl.formatMessage(
          {
            id: 'app.organization.create.fail',
            defaultMessage: 'Create organization {name} failed',
          },
          { name }
        )
      );
    }
  };

  const updateCallback = data => {
    const { code, payload } = data;
    const { name } = payload;
    if (code) {
      message.error(
        intl.formatMessage(
          {
            id: 'app.organization.update.fail',
            defaultMessage: 'Update organization {name} failed',
          },
          { name }
        )
      );
    } else {
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
