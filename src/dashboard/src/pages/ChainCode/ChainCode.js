/*
 SPDX-License-Identifier: Apache-2.0
*/
import React, { PureComponent, Fragment } from 'react';
import { connect, injectIntl } from 'umi';
import { Card, Button, Divider, Dropdown, Menu } from 'antd';
import { PlusOutlined, FunctionOutlined, DownOutlined } from '@ant-design/icons';
import PageHeaderWrapper from '@/components/PageHeaderWrapper';
import StandardTable from '@/components/StandardTable';
import UploadForm from '@/pages/ChainCode/forms/UploadForm';
import InstallForm from '@/pages/ChainCode/forms/InstallForm';
import ApproveForm from '@/pages/ChainCode/forms/ApproveForm';
import CommitForm from './forms/CommitForm';
import styles from './styles.less';

@connect(({ chainCode, loading }) => ({
  chainCode,
  loadingChainCodes: loading.effects['chainCode/listChainCode'],
  uploading: loading.effects['chainCode/uploadChainCode'],
  installing: loading.effects['chainCode/installChainCode'],
  approving: loading.effects['chainCode/approveChainCode'],
  committing: loading.effects['chainCode/commitChainCode'],
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
        chainCodeName: record.package_id,
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

  handleInstall = (values, callback) => {
    const { dispatch } = this.props;
    const formData = new FormData();

    Object.keys(values)
      .filter(key => !(key === 'description' && !values[key])) // filter out empty description
      .forEach(key => {
        formData.append(key, values[key]);
      });

    dispatch({
      type: 'chainCode/installChainCode',
      payload: formData,
      callback,
    });
  };

  handleApprove = (values, callback) => {
    const { dispatch } = this.props;

    const payload = {
      channel_name: values.channel,
      chaincode_name: values.name,
      chaincode_version: values.version,
      sequence: parseInt(values.sequence, 10),
      policy: values.policy,
      init_flag: !!values.initFlag,
    };

    dispatch({
      type: 'chainCode/approveChainCode',
      payload,
      callback,
    });
  };

  handleCommit = (values, callback) => {
    const { dispatch } = this.props;

    const payload = {
      channel_name: values.channel,
      chaincode_name: values.name,
      chaincode_version: values.version,
      sequence: parseInt(values.sequence, 10),
      policy: values.policy,
      init_flag: !!values.initFlag,
    };

    dispatch({
      type: 'chainCode/commitChainCode',
      payload,
      callback,
    });
  };

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
    } = this.props;

    const uploadFormProps = {
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
      handleInstall: this.handleInstall,
      installing,
      chainCodeName,
      nodes,
      intl,
    };

    const approveFormProps = {
      approveModalVisible,
      handleApproveModalVisible: this.handleApproveModalVisible,
      fetchChainCodes: this.fetchChainCodes,
      handleApprove: this.handleApprove,
      approving,
      selectedRows: [],
      initFlagChange: e => {
        // this can be used to handle the initFlag change, currently only for demo
        console.log('initFlag changed:', e.target.checked);
      },
      intl,
    };

    const commitFormProps = {
      commitModalVisible,
      handleCommitModalVisible: this.handleCommitModalVisible,
      handleCommit: this.handleCommit,
      fetchChainCodes: this.fetchChainCodes,
      committing,
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
              id: 'app.chainCode.table.operate.delete',
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
            id: 'app.node.table.operation.more',
            defaultMessage: 'More',
          })}{' '}
          <DownOutlined />
        </a>
      </Dropdown>
    );

    const columns = [
      {
        title: intl.formatMessage({
          id: 'app.chainCode.table.header.packageID',
          defaultMessage: 'PackageID',
        }),
        dataIndex: 'package_id',
        ellipsis: true,
      },
      {
        title: intl.formatMessage({
          id: 'app.chainCode.table.header.version',
          defaultMessage: 'Version',
        }),
        dataIndex: 'version',
      },
      {
        title: intl.formatMessage({
          id: 'app.chainCode.table.header.language',
          defaultMessage: 'Chaincode Language',
        }),
        dataIndex: 'language',
      },
      {
        title: intl.formatMessage({
          id: 'app.chainCode.table.header.description',
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
                id: 'app.chainCode.table.operate.install',
                defaultMessage: 'Install',
              })}
            </a>
            <Divider type="vertical" />
            <a onClick={() => this.handleApproveModalVisible(true)}>
              {intl.formatMessage({
                id: 'app.chainCode.table.operate.approve',
                defaultMessage: 'Approve',
              })}
            </a>
            <Divider type="vertical" />
            <a onClick={() => this.handleCommitModalVisible(true)}>
              {intl.formatMessage({
                id: 'app.chainCode.table.operate.commit',
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
    const dummyPagination = {
      total: 0,
      current: 1,
      pageSize: 10,
    };
    return (
      <PageHeaderWrapper
        title={
          <span>
            {<FunctionOutlined style={{ marginRight: 15 }} />}
            {intl.formatMessage({
              id: 'app.chainCode.title',
              defaultMessage: 'Chaincode Management',
            })}
          </span>
        }
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
                list: chainCodes,
                pagination: chainCodes.length !== 0 ? paginations : dummyPagination,
              }}
              columns={columns}
              onSelectRow={this.handleSelectRows}
              onChange={this.handleTableChange}
            />
          </div>
        </Card>
        <UploadForm {...uploadFormProps} />
        <InstallForm {...installFormProps} />
        <ApproveForm {...approveFormProps} />
        <CommitForm {...commitFormProps} />
      </PageHeaderWrapper>
    );
  }
}

export default injectIntl(ChainCode);
