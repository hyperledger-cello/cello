/*
 SPDX-License-Identifier: Apache-2.0
*/
import React, { PureComponent, Fragment } from 'react';
import { connect, injectIntl, useIntl } from 'umi';
import { Card, Button, Modal, Input, Upload, Divider, message, Dropdown, Menu } from 'antd';
import { PlusOutlined, UploadOutlined, DownOutlined } from '@ant-design/icons';
import PageHeaderWrapper from '@/components/PageHeaderWrapper';
import StandardTable from '@/components/StandardTable';
import { Form } from 'antd/lib/index';
import InstallForm from '@/pages/Operator/ChainCode/forms/InstallForm';
import ApproveForm from '@/pages/Operator/ChainCode/forms/ApproveForm';
import styles from './styles.less';
import CommitForm from './forms/CommitForm';

const FormItem = Form.Item;

const UploadChainCode = props => {
  const [form] = Form.useForm();
  const intl = useIntl();
  const {
    modalVisible,
    handleUpload,
    handleModalVisible,
    uploading,
    fetchChainCodes,
    newFile,
    setFile,
  } = props;

  const uploadCallback = response => {
    if (response.status !== 'successful') {
      message.error(
        intl.formatMessage({
          id: 'app.operator.chainCode.form.create.fail',
          defaultMessage: 'Upload chaincode failed',
        })
      );
    } else {
      message.success(
        intl.formatMessage({
          id: 'app.operator.chainCode.form.create.success',
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
      sm: { span: 7 },
    },
    wrapperCol: {
      xs: { span: 24 },
      sm: { span: 12 },
      md: { span: 10 },
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
        id: 'app.operator.chainCode.form.create.header.title',
        defaultMessage: 'Upload Chaincode',
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
            id: 'app.operator.chainCode.form.create.file',
            defaultMessage: 'Chaincode Package',
          })}
          name="chaincodePackage"
          getValueFromEvent={normFile}
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.operator.chainCode.form.create.fileSelect',
                defaultMessage: 'Please select the chaincode package file',
              }),
            },
          ]}
          extra="Only tar.gz file is supported"
        >
          <Upload {...uploadProps}>
            <Button disabled={!!newFile}>
              <UploadOutlined />
              {intl.formatMessage({
                id: 'app.operator.chainCode.form.create.fileSelect',
                defaultMessage: 'Please select the chaincode package file',
              })}
            </Button>
          </Upload>
        </FormItem>
        <FormItem
          {...formItemLayout}
          label={intl.formatMessage({
            id: 'app.operator.chainCode.form.create.description',
            defaultMessage: 'Chaincode Description',
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
              id: 'app.operator.chainCode.form.create.description',
              defaultMessage: 'Chaincode Description',
            })}
          />
        </FormItem>
      </Form>
    </Modal>
  );
};

@connect(({ chainCode, loading }) => ({
  chainCode,
  loadingChainCodes: loading.effects['chainCode/listChainCode'],
  uploading: loading.effects['chainCode/uploadChainCode'],
  installing: loading.effects['chainCode/installChainCode'],
  approving: loading.effects['chainCode/approveChainCode'],
  committing: loading.effects['chainCode/commitChainCode'],
  loadingOrgs: loading.effects['chainCode/listOrgs'],
}))
class ChainCode extends PureComponent {
  state = {
    selectedRows: [],
    formValues: {},
    newFile: '',
    modalVisible: false,
    installModalVisible: false,
    approveModalVisible: false,
    commitModalVisible: false,
    chainCodeName: '',
  };

  componentDidMount() {
    this.fetchChainCodes();
  }

  componentWillUnmount() {
    const { dispatch } = this.props;

    dispatch({
      type: 'chainCode/clear',
    });
  }

  fetchChainCodes = () => {
    const { dispatch } = this.props;

    dispatch({
      type: 'chainCode/listChainCode',
    });
  };

  fetchNodes = () => {
    const { dispatch } = this.props;

    dispatch({
      type: 'chainCode/listNode',
    });
  };

  handleTableChange = pagination => {
    const { dispatch } = this.props;
    const { formValues } = this.state;
    const { current, pageSize } = pagination;
    const params = {
      page: current,
      per_page: pageSize,
      ...formValues,
    };
    dispatch({
      type: 'chainCode/listChainCode',
      payload: params,
    });
  };

  handleModalVisible = visible => {
    this.setState({
      modalVisible: !!visible,
    });
  };

  handleInstallModalVisible = (visible, record) => {
    if (visible) {
      this.fetchNodes();
      this.setState({
        chainCodeName: record.packageID,
      });
    }
    this.setState({
      installModalVisible: !!visible,
    });
  };

  handleApproveModalVisible = visible => {
    this.setState({
      approveModalVisible: !!visible,
    });
  };

  handleCommitModalVisible = visible => {
    this.setState({
      commitModalVisible: !!visible,
    });
  };

  // TODO: Delete the chaincode
  // handleDeleteChaincode = record => {};

  handleUpload = (values, callback) => {
    const { dispatch } = this.props;
    const formData = new FormData();
    Object.keys(values)
      .filter(key => !(key === 'description' && !values[key])) // filter out empty description
      .forEach(key => {
        formData.append(key, values[key]);
      });

    dispatch({
      type: 'chainCode/uploadChainCode',
      payload: formData,
      callback,
    });
  };

  onUploadChainCode = () => {
    this.handleModalVisible(true);
  };

  setFile = file => {
    this.setState({ newFile: file });
  };

  render() {
    const {
      selectedRows,
      modalVisible,
      newFile,
      installModalVisible,
      approveModalVisible,
      commitModalVisible,
      chainCodeName,
    } = this.state;

    const {
      chainCode: { chainCodes, paginations, nodes },
      loadingChainCodes,
      intl,
      uploading,
      installing,
      approving,
      committing,
      loadingOrgs,
    } = this.props;

    const formProps = {
      modalVisible,
      handleUpload: this.handleUpload,
      handleModalVisible: this.handleModalVisible,
      fetchChainCodes: this.fetchChainCodes,
      uploading,
      newFile,
      setFile: this.setFile,
      intl,
    };

    const installFormProps = {
      installModalVisible,
      handleInstallModalVisible: this.handleInstallModalVisible,
      fetchChainCodes: this.fetchChainCodes,
      installing,
      chainCodeName,
      nodes,
      intl,
    };

    const approveFormProps = {
      approveModalVisible,
      handleApproveModalVisible: this.handleApproveModalVisible,
      fetchChainCodes: this.fetchChainCodes,
      approving,
      selectedRows: [],
      intl,
    };

    const commitFormProps = {
      commitModalVisible,
      handleCommitModalVisible: this.handleCommitModalVisible,
      fetchChainCodes: this.fetchChainCodes,
      committing,
      loadingOrgs,
      selectedRows: [],
      intl,
    };

    const menu = record => (
      <Menu>
        <Menu.Item>
          <a
            onClick={() => {
              this.handleDeleteChaincode(record);
            }}
          >
            {intl.formatMessage({
              id: 'app.operator.chainCode.table.operate.delete',
              defaultMessage: 'Delete',
            })}
          </a>
        </Menu.Item>
      </Menu>
    );

    const MoreBtn = () => (
      <Dropdown overlay={menu}>
        <a>
          {intl.formatMessage({
            id: 'app.operator.node.table.operation.more',
            defaultMessage: 'More',
          })}{' '}
          <DownOutlined />
        </a>
      </Dropdown>
    );

    const columns = [
      {
        title: intl.formatMessage({
          id: 'app.operator.chainCode.table.header.packageID',
          defaultMessage: 'PackageID',
        }),
        dataIndex: 'packageID',
      },
      {
        title: intl.formatMessage({
          id: 'app.operator.chainCode.table.header.version',
          defaultMessage: 'Version',
        }),
        dataIndex: 'version',
      },
      {
        title: intl.formatMessage({
          id: 'app.operator.chainCode.table.header.language',
          defaultMessage: 'Chaincode Language',
        }),
        dataIndex: 'language',
      },
      {
        title: intl.formatMessage({
          id: 'app.operator.chainCode.table.header.description',
          defaultMessage: 'Description',
        }),
        dataIndex: 'description',
      },
      {
        title: intl.formatMessage({
          id: 'form.table.header.operation',
          defaultMessage: 'Operation',
        }),
        // eslint-disable-next-line no-unused-vars
        render: (text, record) => (
          <Fragment>
            <a onClick={() => this.handleInstallModalVisible(true, record)}>
              {intl.formatMessage({
                id: 'app.operator.chainCode.table.operate.install',
                defaultMessage: 'Install',
              })}
            </a>
            <Divider type="vertical" />
            <a onClick={() => this.handleApproveModalVisible(true)}>
              {intl.formatMessage({
                id: 'app.operator.chainCode.table.operate.approve',
                defaultMessage: 'Approve',
              })}
            </a>
            <Divider type="vertical" />
            <a onClick={() => this.handleCommitModalVisible(true)}>
              {intl.formatMessage({
                id: 'app.operator.chainCode.table.operate.commit',
                defaultMessage: 'Commit',
              })}
            </a>
            <Divider type="vertical" />
            <MoreBtn />
          </Fragment>
        ),
      },
    ];
    // TODO: remove dummy data after API is connected
    const dummyList = [
      {
        packageID: 'cc1v1:cc7bb5f50a53c207f68d37e9423c32f968083282e5ffac00d41ffc5768dc1873',
        description: 'chaincode demo',
        version: 'v1',
        language: 'golang',
        approve: false,
      },
    ];
    const dummyPagination = {
      total: 0,
      current: 1,
      pageSize: 10,
    };
    return (
      <PageHeaderWrapper
        title={intl.formatMessage({
          id: 'app.operator.chainCode.title',
          defaultMessage: 'Chaincode management',
        })}
      >
        <Card bordered={false}>
          <div className={styles.tableList}>
            <div className={styles.tableListOperator}>
              <Button type="primary" onClick={this.onUploadChainCode}>
                <PlusOutlined />
                {intl.formatMessage({ id: 'form.button.new', defaultMessage: 'New' })}
              </Button>
            </div>
            <StandardTable
              selectedRows={selectedRows}
              loading={loadingChainCodes}
              rowKey="id"
              // TODO: remove length check after API is connected
              data={{
                list: chainCodes.length !== 0 ? chainCodes : dummyList,
                pagination: chainCodes.length !== 0 ? paginations : dummyPagination,
              }}
              columns={columns}
              onSelectRow={this.handleSelectRows}
              onChange={this.handleTableChange}
            />
          </div>
        </Card>
        <UploadChainCode {...formProps} />
        <InstallForm {...installFormProps} />
        <ApproveForm {...approveFormProps} />
        <CommitForm {...commitFormProps} />
      </PageHeaderWrapper>
    );
  }
}

export default injectIntl(ChainCode);
