import { useState, useEffect } from 'react';
import { injectIntl, useIntl } from 'umi';
import { Button, Modal, Input, Upload, message, Switch, Select, InputNumber, Tag } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { Form } from 'antd/lib/index';
import { listNode } from '@/services/node';
import { listChannel } from '@/services/channel';
import styles from '../styles.less';

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

const UploadForm = props => {
  const [form] = Form.useForm();
  const intl = useIntl();
  const [nodes, setNodes] = useState();
  const [channels, setChannels] = useState();
  const {
    modalVisible,
    handleUpload,
    handleModalVisible,
    uploading,
    fetchChainCodes,
    newFile,
    setFile,
  } = props;

  useEffect(() => {
    async function fecthData() {
      const responseNodes = await listNode();
      const responseChannels = await listChannel();
      const nodeOptions = responseNodes.data.data
        .filter(node => node.type.toLowerCase() === 'peer')
        .map(node => ({
          label: node.name,
          value: node.id,
        }));
      const channelOptions = responseChannels.data.data.map(channel => ({
        label: channel.name,
        value: channel.id,
      }));
      setNodes(nodeOptions);
      setChannels(channelOptions);
    }
    fecthData();
  }, []);

  const uploadCallback = response => {
    if (response.status.toLowerCase() !== 'successful') {
      message.error(
        intl.formatMessage({
          id: 'app.chainCode.form.create.fail',
          defaultMessage: 'Upload chaincode failed',
        })
      );
    } else {
      message.success(
        intl.formatMessage({
          id: 'app.chainCode.form.create.success',
          defaultMessage: 'Upload chaincode succeed',
        })
      );
      form.resetFields();
      handleModalVisible();
      fetchChainCodes();
      setFile(null);
    }
  };

  const onSubmit = () => {
    form.submit();
  };

  const onFinish = values => {
    handleUpload(values, uploadCallback);
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

  const uploadProps = {
    onRemove: () => {
      setFile(null);
    },
    beforeUpload: file => {
      setFile(file);
      return false;
    },
  };

  const normFile = e => {
    if (Array.isArray(e)) {
      return e;
    }
    return newFile;
  };

  return (
    <Modal
      destroyOnClose
      title={intl.formatMessage({
        id: 'app.chainCode.form.create.header.title',
        defaultMessage: 'Upload chaincode',
      })}
      confirmLoading={uploading}
      open={modalVisible}
      onOk={onSubmit}
      onCancel={() => handleModalVisible(false)}
    >
      <Form onFinish={onFinish} form={form} preserve={false}>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.chainCode.form.create.file',
            defaultMessage: 'Package',
          })}
          name="package"
          getValueFromEvent={normFile}
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.chainCode.form.create.fileSelect',
                defaultMessage: 'Please select the chaincode package',
              }),
            },
          ]}
          extra="Only tar.gz file is supported"
        >
          <Upload {...uploadProps}>
            <Button disabled={!!newFile}>
              <UploadOutlined />
              {intl.formatMessage({
                id: 'app.chainCode.form.create.fileSelect',
                defaultMessage: 'Please select the chaincode package',
              })}
            </Button>
          </Upload>
        </FormItem>
        <FormItem
          {...formItemLayout}
          label="name"
          name="name"
          rules={[
            {
              required: true,
            },
          ]}
        >
          <Input placeholder="Chaincode name" />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label="version"
          name="version"
          rules={[
            {
              required: true,
            },
          ]}
        >
          <Input placeholder="Chaincode version" />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label="sequence"
          name="sequence"
          rules={[
            {
              required: true,
            },
          ]}
        >
          <InputNumber
            min={1}
            precision={0}
            step={1}
            placeholder="Chaincode Sequence"
            style={{ width: '100%' }}
          />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label="initRequired"
          name="init_required"
          initialValue={false}
          valuePropName="checked"
        >
          <Switch />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label="SignaturePolicy"
          name="signature_policy"
          initialValue=""
          rules={[
            {
              required: false,
            },
          ]}
        >
          <Input placeholder="Chaincode Signature Policy" />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label="Channel"
          name="channel"
          rules={[
            {
              required: true,
            },
          ]}
        >
          <Select
            options={channels}
            tagRender={tagRender}
            popupClassName={styles.dropdownClassName}
            style={{ width: '100%' }}
          />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.chainCode.form.install.nodes',
            defaultMessage: 'Please select node',
          })}
          name="peers"
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
          <Select mode="multiple" options={nodes} tagRender={tagRender} style={{ width: '100%' }} />
        </FormItem>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.chainCode.form.create.description',
            defaultMessage: 'Description',
          })}
          name="description"
          initialValue=""
          rules={[
            {
              required: false,
            },
          ]}
        >
          <Input
            placeholder={intl.formatMessage({
              id: 'app.chainCode.form.create.description',
              defaultMessage: 'Chaincode Description',
            })}
          />
        </FormItem>
      </Form>
    </Modal>
  );
};

export default injectIntl(UploadForm);
