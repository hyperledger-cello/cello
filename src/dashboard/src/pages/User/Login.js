/*
 SPDX-License-Identifier: Apache-2.0
*/
import React, { Component } from 'react';
import { connect, injectIntl } from 'umi';
import { Checkbox, Alert, Tabs, Tooltip } from 'antd';
import Login from '@/components/Login';
import styles from './Login.less';

const { Email, Password, Submit, OrgName } = Login;
const { TabPane } = Tabs;

@connect(({ login, loading }) => ({
  login,
  submitting: loading.effects['login/login'],
  registering: loading.effects['login/register'],
}))
class LoginPage extends Component {
  state = {
    type: 'account',
    autoLogin: true,
  };

  handleSubmit = (err, values) => {
    const { type } = this.state;
    if (!err) {
      const { dispatch } = this.props;
      dispatch({
        type: 'login/login',
        payload: {
          ...values,
          type,
        },
      });
    }
  };

  registerSubmit = (err, values) => {
    if (!err) {
      const { dispatch } = this.props;
      const { passwordAgain, ...newValues } = values;
      dispatch({
        type: 'login/register',
        payload: {
          ...newValues,
        },
      });
    }
  };

  changeAutoLogin = e => {
    this.setState({
      autoLogin: e.target.checked,
    });
  };

  renderMessage = content => (
    <Alert
      className={styles.alertText}
      style={{ marginBottom: 24 }}
      message={content.message}
      type={content.type}
      showIcon
    />
  );

  render() {
    const { login, submitting, intl, registering } = this.props;
    const { type, autoLogin } = this.state;
    const { success, registerMsg } = login.register;
    return (
      <div className={styles.main}>
        <Tabs defaultActiveKey="1" centered>
          <TabPane tab={`${intl.formatMessage({ id: 'app.login.login' })}`} key="1">
            <Login defaultActiveKey={type} onSubmit={this.handleSubmit}>
              {login.status === 'error' &&
                login.type === 'account' &&
                !submitting &&
                this.renderMessage(
                  intl.formatMessage({ id: 'app.login.message-invalid-credentials' })
                )}
              <Email
                name="email"
                placeholder={`${intl.formatMessage({ id: 'app.login.email' })}`}
                rules={[
                  {
                    required: true,
                    message: intl.formatMessage({ id: 'validation.email.required' }),
                  },
                  {
                    pattern: new RegExp('^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\\.[a-zA-Z0-9_-]+)+$'),
                    message: intl.formatMessage({ id: 'validation.email.wrong-format' }),
                  },
                ]}
              />
              <Password
                name="password"
                placeholder={`${intl.formatMessage({ id: 'app.login.password' })}: password`}
                rules={[
                  {
                    required: true,
                    message: intl.formatMessage({ id: 'validation.password.required' }),
                  },
                ]}
              />
              <div>
                <Checkbox checked={autoLogin} onChange={this.changeAutoLogin}>
                  {intl.formatMessage({
                    id: 'app.login.remember-me',
                  })}
                </Checkbox>
              </div>
              <Submit loading={submitting}>
                {intl.formatMessage({
                  id: 'app.login.login',
                })}
              </Submit>
            </Login>
          </TabPane>
          <TabPane tab={`${intl.formatMessage({ id: 'app.register.register' })}`} key="2">
            <Login defaultActiveKey={type} onSubmit={this.registerSubmit}>
              {!registering &&
                registerMsg !== '' &&
                this.renderMessage({ type: success ? 'success' : 'error', message: registerMsg })}
              <Alert
                message={intl.formatMessage({ id: 'app.register.info' })}
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <Tooltip
                title={intl.formatMessage({ id: 'app.register.orgName.example' })}
                placement="bottomLeft"
                text={intl.formatMessage({ id: 'app.register.orgName.example' })}
              >
                <OrgName
                  name="orgName"
                  placeholder={intl.formatMessage({ id: 'app.register.orgName' })}
                  rules={[
                    {
                      required: true,
                      message: intl.formatMessage({ id: 'validation.orgName.required' }),
                    },
                    {
                      pattern: new RegExp('^[a-z][\\da-z]{0,61}\\.[a-z\\d]{1,62}\\.[a-z]{1,6}$'),
                      message: intl.formatMessage({ id: 'validation.orgName.check' }),
                    },
                  ]}
                />
              </Tooltip>
              <Email
                name="email"
                placeholder={intl.formatMessage({ id: 'app.login.email' })}
                rules={[
                  {
                    required: true,
                    message: intl.formatMessage({ id: 'validation.email.required' }),
                  },
                  {
                    pattern: new RegExp('^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\\.[a-zA-Z0-9_-]+)+$'),
                    message: intl.formatMessage({ id: 'validation.email.wrong-format' }),
                  },
                ]}
              />
              <Password
                name="password"
                placeholder={`${intl.formatMessage({ id: 'app.login.password' })}`}
                rules={[
                  {
                    required: true,
                    message: intl.formatMessage({ id: 'validation.password.required' }),
                  },
                ]}
              />
              <Password
                name="passwordAgain"
                placeholder={`${intl.formatMessage({ id: 'app.register.passwordAgain' })}`}
                rules={[
                  ({ getFieldValue }) => ({
                    validator(role, value) {
                      if (value !== getFieldValue('password')) {
                        return Promise.reject(
                          intl.formatMessage({ id: 'validation.password.twice' })
                        );
                      }
                      return Promise.resolve();
                    },
                  }),
                ]}
              />
              <Submit loading={registering}>
                {intl.formatMessage({
                  id: 'app.register.register',
                })}
              </Submit>
            </Login>
          </TabPane>
        </Tabs>
      </div>
    );
  }
}

export default injectIntl(LoginPage);
