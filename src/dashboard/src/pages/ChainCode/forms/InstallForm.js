/*
 * SPDX-License-Identifier: Apache-2.0
 */
import React, { useState, useEffect } from 'react';
import { injectIntl, useIntl } from 'umi';
import { Modal, message, Select, Form, Tag, Input } from 'antd';
import { listNode } from '@/services/node';
import styles from '../styles.less';

const FormItem = Form.Item;

const InstallForm = props => {
  const [form] = Form.useForm();
  const intl = useIntl();
  const [nodes, setNodes] = useState();

  const {
    installModalVisible,
    handleInstallModalVisible,
    installing,
    fetchChainCodes,
    handleInstall,
    chainCodeName,
  } = props;

  useEffect(() => {
    async function fecthData() {
      const response = await listNode();
      // Filter out orderer nodes, only allow peer nodes for chaincode installation
      setNodes(
        response.data.data
          .filter(node => node.type === 'peer')
          .map(node => ({
            label: node.name,
            value: node.id,
          }))
      );
    }
    fecthData();
  }, []);

  const installCallback = response => {
    if (response.status !== 'successful') {
      message.error(
        intl.formatMessage({
          id: 'app.chainCode.form.install.fail',
          defaultMessage: 'Install chaincode failed',
        })
      );
    } else {
      message.success(
        intl.formatMessage({
          id: 'app.chainCode.form.install.success',
          defaultMessage: 'Install chaincode succeed',
        })
      );
      form.resetFields();
      handleInstallModalVisible(false);
      fetchChainCodes();
    }
  };

  const onSubmit = () => {
    form.submit();
  };

  const onFinish = values => {
    handleInstall(values, installCallback);
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
        id: 'app.chainCode.form.install.header.title',
        defaultMessage: 'Install Chaincode',
      })}
      confirmLoading={installing}
      open={installModalVisible}
      onOk={onSubmit}
      onCancel={() => handleInstallModalVisible(false)}
    >
      <Form onFinish={onFinish} form={form} preserve={false}>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.chainCode.form.install.chainCodeName',
            defaultMessage: 'Chaincode name:',
          })}
          name="id"
          initialValue={chainCodeName}
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.chainCode.form.install.chainCodeName',
                defaultMessage: 'Chaincode name:',
              }),
            },
          ]}
        >
          <Input disabled />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.chainCode.form.install.nodes',
            defaultMessage: 'Please select node',
          })}
          name="node"
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.chainCode.form.install.nodes',
                defaultMessage: 'Please select node',
              }),
            },
          ]}
        >
          <Select
            options={nodes}
            tagRender={tagRender}
            initialvalues={[]}
            popupClassName={styles.dropdownClassName}
          />
        </FormItem>
      </Form>
    </Modal>
  );
};

export default injectIntl(InstallForm);
