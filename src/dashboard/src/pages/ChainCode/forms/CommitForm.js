import React, { useState, useEffect } from 'react';
import { injectIntl, useIntl } from 'umi';
import { Modal, message, Select, Form, Tag, Checkbox, Input } from 'antd';
import { listChannel } from '@/services/channel';
import styles from '../styles.less';

const FormItem = Form.Item;

const CommitForm = props => {
  const [form] = Form.useForm();
  const intl = useIntl();
  const [channels, setChannels] = useState();
  const {
    commitModalVisible,
    handleCommit,
    handleCommitModalVisible,
    committing,
    fetchChainCodes,
    initFlagChange,
  } = props;

  useEffect(() => {
    async function fetchData() {
      try {
        const response = await listChannel();
        const newChannels = Object.keys(response.data.data).map(item => ({
          label: response.data.data[item].name,
          value: response.data.data[item].name,
        }));
        setChannels(newChannels);
      } catch (error) {
        console.error('Failed to fetch data:', error);
      }
    }
    fetchData();
  }, []);

  const commitCallback = response => {
    if (response.status !== 'successful') {
      message.error(
        intl.formatMessage({
          id: 'app.operator.chainCode.form.commit.fail',
          defaultMessage: 'Commit chaincode failed',
        })
      );
    } else {
      message.success(
        intl.formatMessage({
          id: 'app.operator.chainCode.form.commit.success',
          defaultMessage: 'Commit chaincode succeed',
        })
      );
      form.resetFields();
      handleCommitModalVisible();
      fetchChainCodes();
    }
  };

  const onSubmit = () => {
    form.submit();
  };

  const onFinish = values => {
    handleCommit(values, commitCallback);
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
        id: 'app.operator.chainCode.form.commit.header.title',
        defaultMessage: 'Commit Chaincode',
      })}
      confirmLoading={committing}
      open={commitModalVisible}
      onOk={onSubmit}
      onCancel={() => handleCommitModalVisible(false)}
    >
      <Form
        onFinish={onFinish}
        form={form}
        preserve={false}
        initialValues={{
          initFlag: false,
        }}
      >
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.operator.chainCode.form.commit.channels',
            defaultMessage: 'Please select channel',
          })}
          name="channel"
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.operator.chainCode.form.commit.channels',
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

export default injectIntl(CommitForm);
