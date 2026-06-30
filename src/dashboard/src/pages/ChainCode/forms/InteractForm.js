/*
 SPDX-License-Identifier: Apache-2.0
*/
import { useState, useEffect } from 'react';
import { injectIntl, useIntl } from 'umi';
import { Modal, Form, Select, Input, Button, Card } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';

const FormItem = Form.Item;
const { Option } = Select;
const { TextArea } = Input;

const InteractForm = props => {
  const [form] = Form.useForm();
  const intl = useIntl();
  const [result, setResult] = useState('');

  const { modalVisible, handleTransact, handleModalVisible, transacting, record } = props;

  useEffect(() => {
    if (modalVisible) {
      setResult('');
      form.resetFields();
    }
  }, [modalVisible, form]);

  const onSubmit = () => {
    form.submit();
  };

  const transactCallback = response => {
    if (response && response.status === 'successful') {
      const output = response.data?.result;
      setResult(
        typeof output === 'object' ? JSON.stringify(output, null, 2) : String(output || '')
      );
    }
  };

  const onFinish = values => {
    // Arguments could be undefined if empty, default to empty array
    const args = values.arguments
      ? values.arguments.filter(arg => arg !== undefined && arg !== null)
      : [];
    handleTransact(
      {
        id: record.id,
        action: values.action,
        function: values.function,
        arguments: args,
      },
      transactCallback
    );
  };

  const formItemLayout = {
    labelCol: {
      xs: { span: 24 },
      sm: { span: 6 },
    },
    wrapperCol: {
      xs: { span: 24 },
      sm: { span: 16 },
    },
  };

  const tailFormItemLayout = {
    wrapperCol: {
      xs: { span: 24, offset: 0 },
      sm: { span: 16, offset: 6 },
    },
  };

  return (
    <Modal
      destroyOnClose
      title={`${intl.formatMessage({
        id: 'app.chainCode.form.transact.header.title',
        defaultMessage: 'Interact with Chaincode',
      })}: ${record ? record.name : ''}`}
      confirmLoading={transacting}
      open={modalVisible}
      onOk={onSubmit}
      onCancel={() => handleModalVisible(false)}
      width={640}
      okText={intl.formatMessage({
        id: 'app.chainCode.form.transact.execute',
        defaultMessage: 'Execute',
      })}
    >
      <Form onFinish={onFinish} form={form} preserve={false} initialValues={{ action: 'SUBMIT' }}>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.chainCode.form.transact.action',
            defaultMessage: 'Action Type',
          })}
          name="action"
          rules={[{ required: true }]}
        >
          <Select style={{ width: '100%' }}>
            <Option value="SUBMIT">SUBMIT (Invoke/Write)</Option>
            <Option value="EVALUATE">EVALUATE (Query/Read)</Option>
          </Select>
        </FormItem>

        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.chainCode.form.transact.function',
            defaultMessage: 'Function Name',
          })}
          name="function"
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.chainCode.form.transact.checkFunction',
                defaultMessage: 'Please enter the function name',
              }),
            },
          ]}
        >
          <Input placeholder="e.g. CreateAsset, ReadAsset, TransferAsset" />
        </FormItem>

        <Form.List name="arguments">
          {(fields, { add, remove }) => (
            <>
              {fields.map((field, index) => (
                <FormItem
                  {...(index === 0 ? formItemLayout : tailFormItemLayout)}
                  label={
                    index === 0
                      ? intl.formatMessage({
                          id: 'app.chainCode.form.transact.arguments',
                          defaultMessage: 'Arguments',
                        })
                      : ''
                  }
                  required={false}
                  key={field.key}
                >
                  <div style={{ display: 'flex', alignItems: 'center' }}>
                    <FormItem
                      {...field}
                      validateTrigger={['onChange', 'onBlur']}
                      rules={[
                        {
                          required: true,
                          whitespace: true,
                          message: intl.formatMessage({
                            id: 'app.chainCode.form.transact.checkArgument',
                            defaultMessage: 'Please input argument or delete this field',
                          }),
                        },
                      ]}
                      noStyle
                    >
                      <Input placeholder={`Argument #${index + 1}`} style={{ flex: 1 }} />
                    </FormItem>
                    <DeleteOutlined
                      className="dynamic-delete-button"
                      style={{ margin: '0 8px', color: '#ff4d4f', cursor: 'pointer' }}
                      onClick={() => remove(field.name)}
                    />
                  </div>
                </FormItem>
              ))}
              <FormItem {...tailFormItemLayout}>
                <Button
                  type="dashed"
                  onClick={() => add()}
                  style={{ width: '100%' }}
                  icon={<PlusOutlined />}
                >
                  {intl.formatMessage({
                    id: 'app.chainCode.form.transact.addArgument',
                    defaultMessage: 'Add Argument',
                  })}
                </Button>
              </FormItem>
            </>
          )}
        </Form.List>

        {result && (
          <Card
            title={intl.formatMessage({
              id: 'app.chainCode.form.transact.result',
              defaultMessage: 'Execution Result',
            })}
            size="small"
            style={{ marginTop: 24, background: '#f5f5f5', border: '1px solid #d9d9d9' }}
          >
            <TextArea
              value={result}
              readOnly
              style={{
                fontFamily: 'monospace',
                backgroundColor: '#ffffff',
                color: '#333333',
                border: 'none',
                height: 200,
                resize: 'none',
              }}
            />
          </Card>
        )}
      </Form>
    </Modal>
  );
};

export default injectIntl(InteractForm);
