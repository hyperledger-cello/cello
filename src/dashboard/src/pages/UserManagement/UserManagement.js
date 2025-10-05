/*
 SPDX-License-Identifier: Apache-2.0
*/
import React, { PureComponent, Fragment } from 'react';
import { connect, injectIntl } from 'umi';
import {
  Card,
  Button,
  Form,
  Modal,
  Input,
  Select,
  message,
  Dropdown,
  Menu,
  AutoComplete,
} from 'antd';
import { DownOutlined, PlusOutlined, UserOutlined } from '@ant-design/icons';
import moment from 'moment';
import isEmail from 'validator/lib/isEmail';
import PageHeaderWrapper from '@/components/PageHeaderWrapper';
import StandardTable from '@/components/StandardTable';
import { getAuthority } from '@/utils/authority';
import styles from '../styles.less';

const FormItem = Form.Item;
const Option = Select.Option;
const AutoCompleteOption = AutoComplete.Option;

const CreateUpdateForm = props => {
  const {
    visible,
    method,
    handleSubmit,
    handleModalVisible,
    confirmLoading,
    user,
    organizations,
    onSearchOrganization,
    intl,
  } = props;
  const [form] = Form.useForm();
  const userRole = getAuthority()[0];
  let orgID = '';
  const onSubmit = () => {
    form.submit();
  };

  const onFinish = values => {
    handleSubmit(
      method,
      {
        ...values,
        organization: orgID,
      },
      user
    );
  };
  const validateEmail = async (rule, value) => {
    if (value && !isEmail(value)) {
      throw new Error(
        intl.formatMessage({
          id: 'app.user.form.email.noValid',
          defaultMessage: 'Please input valid email',
        })
      );
    }
  };
  const organizationOptions = organizations.map(org => (
    <AutoCompleteOption key={org.id} value={org.name}>
      {org.name}
    </AutoCompleteOption>
  ));
  const onSelectOrganization = (value, option) => {
    form.setFieldsValue({
      organization: value,
    });
    orgID = option.key;
  };

  const validatePasswordConfirm = async (rule, value) => {
    if (value && form.getFieldValue('password') !== value) {
      throw new Error(
        intl.formatMessage({
          id: 'app.user.form.passwordConfirm.noValid',
          defaultMessage: 'Inconsistent password input twice',
        })
      );
    }
  };

  return (
    <Modal
      destroyOnClose
      title={intl.formatMessage({
        id: `app.user.form.${method === 'create' ? 'new' : 'update'}.title`,
        defaultMessage: 'New User',
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
          role: method === 'create' ? 'user' : user.role,
          email: method === 'create' ? '' : user.email,
        }}
      >
        <FormItem
          labelCol={{ span: 5 }}
          wrapperCol={{ span: 15 }}
          label={intl.formatMessage({
            id: 'app.user.form.name.label',
            defaultMessage: 'User Name',
          })}
          name="username"
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.user.form.name.required',
                defaultMessage: 'Please input user name',
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
            id: 'app.user.form.role.label',
            defaultMessage: 'User Role',
          })}
          name="role"
        >
          <Select>
            <Option value="user">
              {intl.formatMessage({
                id: 'app.user.role.user',
                defaultMessage: 'User',
              })}
            </Option>
            <Option value="administrator">
              {intl.formatMessage({
                id: 'app.user.role.administrator',
                defaultMessage: 'Administrator',
              })}
            </Option>
          </Select>
        </FormItem>
        <FormItem
          labelCol={{ span: 5 }}
          wrapperCol={{ span: 15 }}
          label={intl.formatMessage({
            id: 'app.user.form.email.label',
            defaultMessage: 'Email',
          })}
          name="email"
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.user.form.email.required',
                defaultMessage: 'Please input email',
              }),
            },
            {
              validator: validateEmail,
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
            id: 'app.user.form.password.label',
            defaultMessage: 'Password',
          })}
          name="password"
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.user.form.password.required',
                defaultMessage: 'Please input password',
              }),
            },
          ]}
        >
          <Input.Password
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
            id: 'app.user.form.passwordConfirm.label',
            defaultMessage: 'Password Confirm',
          })}
          name="passwordConfirm"
          rules={[
            {
              required: true,
              message: intl.formatMessage({
                id: 'app.user.form.password.required',
                defaultMessage: 'Please input password',
              }),
            },
            {
              validator: validatePasswordConfirm,
            },
          ]}
        >
          <Input.Password
            placeholder={intl.formatMessage({
              id: 'form.input.placeholder',
              defaultMessage: 'Please input',
            })}
          />
        </FormItem>
        {userRole === 'operator' && (
          <Form.Item
            labelCol={{ span: 5 }}
            wrapperCol={{ span: 15 }}
            label={intl.formatMessage({
              id: 'app.user.form.organization.label',
              defaultMessage: 'Organization',
            })}
            name="organization"
          >
            <AutoComplete
              onSearch={onSearchOrganization}
              onSelect={onSelectOrganization}
              placeholder={intl.formatMessage({
                id: 'form.input.placeholder',
                defaultMessage: 'Please input',
              })}
            >
              {organizationOptions}
            </AutoComplete>
          </Form.Item>
        )}
      </Form>
    </Modal>
  );
};

@connect(({ user, organization, loading }) => ({
  user,
  organization,
  loadingUsers: loading.effects['user/fetch'],
  creatingUser: loading.effects['user/createUser'],
}))
class UserManagement extends PureComponent {
  state = {
    modalVisible: false,
    modalMethod: 'create',
    selectedRows: [],
    // formValues: {},
  };

  componentDidMount() {
    const { dispatch } = this.props;

    dispatch({
      type: 'user/fetch',
    });
  }

  handleModalVisible = visible => {
    this.setState({
      modalVisible: !!visible,
    });
  };

  handleSelectRows = rows => {
    this.setState({
      selectedRows: rows,
    });
  };

  createCallback = data => {
    const { intl } = this.props;
    if (data.id) {
      message.success(
        intl.formatMessage(
          {
            id: 'app.user.create.success',
            defaultMessage: 'Create user {name} success',
          },
          {
            name: data.username,
          }
        )
      );
      this.handleModalVisible();
      this.handleFormReset();
    } else {
      message.success(
        intl.formatMessage(
          {
            id: 'app.user.create.fail',
            defaultMessage: 'Create user {name} failed',
          },
          {
            name: data.username,
          }
        )
      );
    }
  };

  deleteCallback = data => {
    const { code, payload } = data;
    const { intl } = this.props;
    const { username } = payload;
    if (code) {
      message.error(
        intl.formatMessage(
          {
            id: 'app.user.delete.fail',
            defaultMessage: 'Delete user {name} failed',
          },
          {
            name: username,
          }
        )
      );
    } else {
      message.success(
        intl.formatMessage(
          {
            id: 'app.user.delete.success',
            defaultMessage: 'Delete user {name} success',
          },
          {
            name: username,
          }
        )
      );
      this.handleFormReset();
    }
  };

  deleteUser = (record, callback = this.deleteCallback) => {
    const { dispatch } = this.props;
    dispatch({
      type: 'user/deleteUser',
      payload: {
        ...record,
      },
      callback,
    });
  };

  handleDelete = record => {
    const { intl } = this.props;
    Modal.confirm({
      title: intl.formatMessage({
        id: 'app.user.form.delete.title',
        defaultMessage: 'Delete User',
      }),
      content: intl.formatMessage(
        {
          id: 'app.user.form.delete.content',
          defaultMessage: 'Confirm to delete user {name}',
        },
        {
          name: record.username,
        }
      ),
      okText: intl.formatMessage({ id: 'form.button.confirm', defaultMessage: 'Confirm' }),
      cancelText: intl.formatMessage({ id: 'form.button.cancel', defaultMessage: 'Cancel' }),
      onOk: () => this.deleteUser(record),
    });
  };

  handleFormReset = () => {
    const { dispatch } = this.props;
    // this.setState({
    //   formValues: {},
    // });
    dispatch({
      type: 'user/fetch',
    });
  };

  handleSubmit = (method, values) => {
    const {
      dispatch,
      user: {
        currentUser: { organization = {} },
      },
    } = this.props;
    const userRole = getAuthority()[0];

    // eslint-disable-next-line no-param-reassign
    delete values.passwordConfirm;
    if (userRole === 'administrator' && organization.id) {
      // eslint-disable-next-line no-param-reassign
      values.organization = organization.id;
    }
    switch (method) {
      case 'create':
        dispatch({
          type: 'user/createUser',
          payload: values,
          callback: this.createCallback,
        });
        break;
      default:
        break;
    }
  };

  handleMenuClick = e => {
    const { selectedRows } = this.state;
    const { intl } = this.props;
    let names = [];

    switch (e.key) {
      case 'remove':
        names = selectedRows.map(item => item.username);
        Modal.confirm({
          title: intl.formatMessage({
            id: 'app.user.form.delete.title',
            defaultMessage: 'Delete User',
          }),
          content: intl.formatMessage(
            {
              id: 'app.user.form.delete.content',
              defaultMessage: 'Confirm to delete user {name}',
            },
            {
              name: names.join(', '),
            }
          ),
          okText: intl.formatMessage({ id: 'form.button.confirm', defaultMessage: 'Confirm' }),
          cancelText: intl.formatMessage({ id: 'form.button.cancel', defaultMessage: 'Cancel' }),
          onOk: () => {
            selectedRows.map(user => this.deleteUser(user));
            this.setState({
              selectedRows: [],
            });
            Modal.destroyAll();
          },
        });
        break;
      default:
        break;
    }
  };

  render() {
    const { modalVisible, modalMethod, selectedRows } = this.state;
    const {
      user: { users, pagination },
      organization: { organizations },
      loadingUsers,
      creatingUser,
      dispatch,
      intl,
    } = this.props;
    const columns = [
      {
        title: intl.formatMessage({
          id: 'app.user.table.header.name',
          defaultMessage: 'User Name',
        }),
        dataIndex: 'email',
      },
      {
        title: intl.formatMessage({
          id: 'app.user.table.header.role',
          defaultMessage: 'User Role',
        }),
        dataIndex: 'role',
        render: text =>
          intl.formatMessage({
            id: `app.user.role.${text.toLowerCase()}`,
            defaultMessage: 'User',
          }),
      },
      {
        title: intl.formatMessage({
          id: 'app.user.table.header.organization',
          defaultMessage: 'Organization',
        }),
        dataIndex: 'organization',
        render: text => (text ? text.name : ''),
      },
      {
        title: intl.formatMessage({
          id: 'app.organization.table.header.createTime',
          defaultMessage: 'Create Time',
        }),
        dataIndex: 'created_at',
        render: text => <span>{moment(text).format('YYYY-MM-DD HH:mm:ss')}</span>,
      },
      {
        title: intl.formatMessage({
          id: 'form.table.header.operation',
          defaultMessage: 'Operation',
        }),
        render: (text, record) => (
          <Fragment>
            <a className={styles.danger} onClick={() => this.handleDelete(record)}>
              {intl.formatMessage({
                id: 'form.menu.item.delete',
                defaultMessage: 'Delete',
              })}
            </a>
          </Fragment>
        ),
      },
    ];

    const formProps = {
      intl,
      visible: modalVisible,
      method: modalMethod,
      handleModalVisible: this.handleModalVisible,
      handleSubmit: this.handleSubmit,
      confirmLoading: creatingUser,
      organizations,
      onSearchOrganization(value) {
        dispatch({
          type: 'organization/listOrganization',
          payload: {
            name: value,
          },
        });
      },
    };
    const menu = (
      <Menu onClick={this.handleMenuClick} selectedKeys={[]}>
        <Menu.Item key="remove">
          {intl.formatMessage({
            id: 'form.menu.item.delete',
            defaultMessage: 'Delete',
          })}
        </Menu.Item>
      </Menu>
    );
    return (
      <PageHeaderWrapper
        title={
          <span>
            {<UserOutlined style={{ marginRight: 15 }} />}
            {intl.formatMessage({
              id: 'app.user.title',
              defaultMessage: 'User Management',
            })}
          </span>
        }
      >
        <Card bordered={false}>
          <div className={styles.tableList}>
            <div className={styles.tableListOperator}>
              <Button type="primary" onClick={() => this.handleModalVisible(true)}>
                <PlusOutlined />
                {intl.formatMessage({
                  id: 'form.button.new',
                  defaultMessage: 'New',
                })}
              </Button>
              {selectedRows.length > 0 && (
                <span>
                  <Dropdown overlay={menu}>
                    <Button>
                      {intl.formatMessage({
                        id: 'form.button.moreActions',
                        defaultMessage: 'More Actions',
                      })}{' '}
                      <DownOutlined />
                    </Button>
                  </Dropdown>
                </span>
              )}
            </div>
            <StandardTable
              selectedRows={selectedRows}
              loading={loadingUsers}
              rowKey="id"
              data={{
                list: users.data,
                pagination,
              }}
              columns={columns}
              onSelectRow={this.handleSelectRows}
              onChange={this.handleTableChange}
            />
          </div>
        </Card>
        <CreateUpdateForm {...formProps} />
      </PageHeaderWrapper>
    );
  }
}

export default injectIntl(UserManagement);
