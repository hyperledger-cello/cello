import React, { useState, useEffect } from 'react';
import { injectIntl, useIntl } from 'umi';
import { Modal, message, Select, Form, Tag, Input, Checkbox } from 'antd';
import { listChannel } from '@/services/channel';
import styles from '../styles.less';

const FormItem = Form.Item;

const ApproveForm = props => {
  const [form] = Form.useForm();
  const intl = useIntl();
  const [channels, setChannels] = useState([]);
  const {
    approveModalVisible,
    handleApprove,
    handleApproveModalVisible,
    approving,
    fetchChainCodes,
    initFlagChange,
  } = props;

  useEffect(() => {
    async function fetchData() {
      const response = await listChannel();
      const newChannels = Object.keys(response.data.data).map(item => ({
        label: response.data.data[item].name,
        value: response.data.data[item].name,
      }));
      setChannels(newChannels);
    }
    fetchData();
  }, []);

  const approveCallback = response => {
    if (response.status !== 'successful') {
      message.error(
        intl.formatMessage({
          id: 'app.chainCode.form.approve.fail',
          defaultMessage: 'Approve chaincode failed',
        })
      );
    } else {
      message.success(
        intl.formatMessage({
          id: 'app.chainCode.form.approve.success',
          defaultMessage: 'Approve chaincode succeed',
        })
      );
      form.resetFields();
      handleApproveModalVisible();
      fetchChainCodes();
    }
  };

  const onSubmit = () => {
    form.submit();
  };

  const onFinish = values => {
    handleApprove(values, approveCallback);
  };

  const formItemLayout = {
    labelCol: {
      xs: { span: 24 },
      sm: { span: 11 },
    },
    wrapperCol: {
      xs: { span: 24 },
      sm: { span: 12 },
      md: { span: 10 },
    },
  };

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
        id: 'app.chainCode.form.approve.header.title',
        defaultMessage: 'Approve Chaincode',
      })}
      confirmLoading={approving}
      open={approveModalVisible}
      onOk={onSubmit}
      onCancel={() => handleApproveModalVisible(false)}
    >
      <Form
        onFinish={onFinish}
        form={form}
        preserve={false}
        initialValues={{
          policy: '',
          initFlag: false,
        }}
      >
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.chainCode.form.approve.channel',
            defaultMessage: 'Please select channel',
          })}
          name="channel"
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.chainCode.form.approve.channel',
                defaultMessage: 'Please select channel',
              }),
            },
          ]}
        >
          <Select
            options={channels}
            tagRender={tagRender}
            dropdownClassName={styles.dropdownClassName}
          />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.chainCode.form.approve.specifyName',
            defaultMessage: 'Name for chaincode',
          })}
          name="name"
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.chainCode.form.approve.specifyName',
                defaultMessage: 'Name for chaincode',
              }),
            },
          ]}
        >
          <Input
            placeholder={intl.formatMessage({
              id: 'app.chainCode.form.approve.name',
              defaultMessage: 'Name',
            })}
          />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.chainCode.form.approve.version',
            defaultMessage: 'Version',
          })}
          name="version"
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.chainCode.form.approve.version.required',
                defaultMessage: 'Please input version',
              }),
            },
          ]}
        >
          <Input
            placeholder={intl.formatMessage({
              id: 'app.chainCode.form.approve.version.placeholder',
              defaultMessage: 'Version',
            })}
          />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.chainCode.form.approve.sequence',
            defaultMessage: 'Sequence',
          })}
          name="sequence"
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.chainCode.form.approve.sequence.required',
                defaultMessage: 'Please input sequence',
              }),
            },
          ]}
        >
          <Input
            placeholder={intl.formatMessage({
              id: 'app.chainCode.form.approve.sequence.placeholder',
              defaultMessage: 'Sequence',
            })}
          />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.chainCode.form.approve.endorsement_policy',
            defaultMessage: 'Endorsement Policy',
          })}
          name="policy"
        >
          <Input
            placeholder={intl.formatMessage({
              id: 'app.chainCode.form.approve.policy.placeholder',
              defaultMessage: 'Policy (optional)',
            })}
          />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.chainCode.form.initFlag',
            defaultMessage: '--init-required flag',
          })}
          name="initFlag"
        >
          <Checkbox onChange={initFlagChange} />
        </FormItem>
      </Form>
    </Modal>
  );
};

export default injectIntl(ApproveForm);
