/*
 SPDX-License-Identifier: Apache-2.0
 */
import React, { useEffect, useState } from 'react';
import { useIntl } from 'umi';
import { Modal, Form, Select, InputNumber, Tag, message } from 'antd';
import { listOrganization } from '@/services/organization';

const FormItem = Form.Item;

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

const CreateInvitationForm = props => {
  const [form] = Form.useForm();
  const intl = useIntl();
  const [organizations, setOrganizations] = useState([]);

  const {
    modalVisible,
    handleCreate,
    handleModalVisible,
    fetchInvitations,
    creating,
    channelId,
    memberOrgIds = [],
  } = props;

  useEffect(() => {
    async function fetchData() {
      const response = await listOrganization();
      const options = (response.data.data || [])
        .filter(org => !memberOrgIds.includes(org.id))
        .map(org => ({
          label: org.name,
          value: org.name,
        }));
      setOrganizations(options);
    }
    fetchData();
  }, [memberOrgIds]);

  const createCallback = response => {
    if (!response || (response.status && response.status.toLowerCase() !== 'successful')) {
      message.error(
        intl.formatMessage({
          id: 'app.channel.invitation.form.create.fail',
          defaultMessage: 'Create invitation failed',
        })
      );
    } else {
      message.success(
        intl.formatMessage({
          id: 'app.channel.invitation.form.create.success',
          defaultMessage: 'Create invitation succeed',
        })
      );
      form.resetFields();
      handleModalVisible();
      fetchInvitations();
    }
  };

  const onSubmit = () => {
    form.submit();
  };

  const onFinish = values => {
    handleCreate(
      {
        channelId,
        organization_names: values.organization_names,
        required_signatures: values.required_signatures,
      },
      createCallback
    );
  };

  const formItemLayout = {
    labelCol: {
      xs: { span: 24 },
      sm: { span: 8 },
    },
    wrapperCol: {
      xs: { span: 24 },
      sm: { span: 14 },
      md: { span: 12 },
    },
  };

  return (
    <Modal
      destroyOnClose
      title={intl.formatMessage({
        id: 'app.channel.invitation.form.create.header.title',
        defaultMessage: 'Invite Organizations',
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
            id: 'app.channel.invitation.form.create.organizations',
            defaultMessage: 'Organizations',
          })}
          name="organization_names"
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.channel.invitation.form.create.required.organizations',
                defaultMessage: 'Please enter at least one organization name',
              }),
            },
          ]}
        >
          <Select
            mode="multiple"
            showSearch
            tagRender={tagRender}
            options={organizations}
            optionFilterProp="label"
            placeholder={intl.formatMessage({
              id: 'app.channel.invitation.form.create.organizationsPlaceholder',
              defaultMessage: 'Type or select organization names to invite',
            })}
          />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.channel.invitation.form.create.requiredSignatures',
            defaultMessage: 'Required Signatures',
          })}
          name="required_signatures"
          extra={intl.formatMessage({
            id: 'app.channel.invitation.form.create.requiredSignaturesExtra',
            defaultMessage: 'Defaults to a majority of current channel members',
          })}
        >
          <InputNumber min={1} precision={0} step={1} style={{ width: '100%' }} />
        </FormItem>
      </Form>
    </Modal>
  );
};

export default CreateInvitationForm;
