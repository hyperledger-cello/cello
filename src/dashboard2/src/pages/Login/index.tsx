import { LinkOutlined, LockOutlined, MailOutlined, TeamOutlined } from '@ant-design/icons';
import { LoginForm, ProFormText } from '@ant-design/pro-components';
import { Alert, Tabs } from 'antd';
import { history } from '@umijs/max';
import { useState } from 'react';
import { useIntl } from 'umi';
import { login, register } from '@/services/auth/AuthController';
import CustomizedSelectLang from '@/components/CustomizedSelectLang/CustomizedSelectLang';


type ActionType = 'login' | 'register';

const AccessPage: React.FC = () => {
  const [actionType, setActionType] = useState<ActionType>('login');
  const [success, handleSuccess] = useState<boolean>(false);
  const [error, handleError] = useState<any>(null);
  const intl = useIntl();

  const loginForm = (
    <>
      <ProFormText
        name="email"
        fieldProps={{
          size: 'large',
          prefix: <MailOutlined className={'prefixIcon'} />,
        }}
        placeholder={intl.formatMessage({id: 'app.login.email',})}
        rules={[
          {
            required: true,
            message: intl.formatMessage({id: 'validation.email.required',}),
          },
        ]}
      />
      <ProFormText.Password
        name="password"
        fieldProps={{
          size: 'large',
          prefix: <LockOutlined className={'prefixIcon'} />,
        }}
        placeholder={intl.formatMessage({id: 'app.login.password',})}
        rules={[
          {
            required: true,
            message: intl.formatMessage({id: 'validation.password.required',}),
          },
        ]}
      />
    </>
  );

  const registerForm = (
    <>
      <ProFormText
        name="org_name"
        fieldProps={{
          size: 'large',
          prefix: <TeamOutlined className={'prefixIcon'} />,
        }}
        placeholder={intl.formatMessage({id: 'app.register.orgName',})}
        rules={[
          {
            required: true,
            message: intl.formatMessage({id: 'validation.orgName.required',}),
          },
        ]}
      />
      <ProFormText
        name="email"
        fieldProps={{
          size: 'large',
          prefix: <MailOutlined className={'prefixIcon'} />,
        }}
        placeholder={intl.formatMessage({id: 'app.register.email',})}
        rules={[
          {
            required: true,
            message: intl.formatMessage({id: 'validation.email.required',}),
          },
        ]}
      />
      <ProFormText.Password
        name="password"
        fieldProps={{
          size: 'large',
          prefix: <LockOutlined className={'prefixIcon'} />,
        }}
        placeholder={intl.formatMessage({id: 'app.register.password',})}
        rules={[
          {
            required: true,
            message: intl.formatMessage({id: 'validation.password.required',}),
          },
        ]}
      />
      <ProFormText.Password
        name="confirmPassword"
        fieldProps={{
          size: 'large',
          prefix: <LockOutlined className={'prefixIcon'} />,
        }}
        placeholder={intl.formatMessage({id: 'app.register.confirmPassword'})}
        rules={[
          {
            required: true,
            message: intl.formatMessage({id: 'validation.password.confirmed',}),
          },
          ({ getFieldValue }) => ({
            validator(role, value) {
              if (value !== getFieldValue('password')) {
                return Promise.reject(intl.formatMessage({id: 'validation.password.different',}));
              }
              return Promise.resolve();
            },
          }),
        ]}
      />
      <ProFormText
        name="agent_url"
        fieldProps={{
          size: 'large',
          prefix: <LinkOutlined className={'prefixIcon'} />,
        }}
        placeholder={intl.formatMessage({id: 'app.register.agentUrl'})}
        rules={[
          {
            required: true,
            message: intl.formatMessage({id: 'validation.agentUrl.required'}),
          },
          {
            pattern: /^https?:\/\/.+/,
            message: intl.formatMessage({id: 'validation.agentUrl.format'}),
          },
        ]}
      />
    </>
  );

  let message = null;
  if (error) {
    const status = error.response.status;
    if (status > 499) {
      message = <Alert
        message={intl.formatMessage({id: 'message.error'})}
        description={intl.formatMessage({id: 'message.error.server'})}
        type='warning'
        showIcon
      >
      </Alert>;
    } else if (actionType == 'login') {
      message = <Alert
        message={intl.formatMessage({id: 'message.error'})}
        description={intl.formatMessage({id: 'app.login.error'})}
        type='error'
        showIcon
      >
      </Alert>;
    } else {
      message = <Alert
        message={intl.formatMessage({id: 'message.error'})}
        description={intl.formatMessage({id: 'app.register.error'})}
        type='error'
        showIcon
      >
      </Alert>;
    }
  } else if (success) {
    message = <Alert
      message={intl.formatMessage({id: 'message.success'})}
      description={intl.formatMessage({id: 'app.register.success'})}
      type='success'
      showIcon
    >
    </Alert>;
  } else if (actionType == 'register') {
    message = <Alert
      message={intl.formatMessage({id: 'message.info'})}
      description={intl.formatMessage({id: 'app.register.info'})}
      type='info'
      showIcon
    >
    </Alert>;
  }

  return (
    <>
      <div
        style={{
          height: "100vh",
          background: '#20343e',
          backgroundImage: "url('https://gw.alipayobjects.com/zos/rmsportal/TVYTbAXWheQpRcWDaDMu.svg')",
          display: "flex",
          justifyContent: "center",
          alignItems: "center", 
        }}
      >
        <div style={{ position: "absolute", top: 20, right: 20 }}>
          <CustomizedSelectLang />
        </div>
        <div>
          <LoginForm
            logo="/favicon.png"
            title="Cello Dashboard"
            subTitle={
              <span style={{ color: '#dfe6eb' }}>
                Dashboard for management cello service
              </span>
            }
            message={message}
            onFinish={async (values: any) => {
              if (actionType == 'login') {
                try {
                  const response = await login(values);
                  localStorage.setItem('token', response.data.token);
                  history.push('/');
                  handleError(null);
                } catch (error) {
                  handleError(error);
                  handleSuccess(false);
                }
              } else {
                try {
                  await register(values);
                  setActionType('login');
                  handleError(null);
                  handleSuccess(true);
                } catch (error) {
                  handleError(error);
                  handleSuccess(false);
                }
              }
            }}
            submitter={{
              searchConfig: {
                submitText: actionType == 'login' ?
                  intl.formatMessage({id: 'app.login.login',}) :
                  intl.formatMessage({id: 'app.register.register',}),
              },
            }}
          >
            <Tabs
              centered
              activeKey={actionType}
              onChange={(activeKey) => {
                handleSuccess(false);
                handleError(null);
                setActionType(activeKey as ActionType);
              }}
              items={[
                { key: 'login', label: intl.formatMessage({id: 'app.login.login',}) },
                { key: 'register', label: intl.formatMessage({id: 'app.register.register',}) },
              ]}
            />
            { actionType == 'login' ? loginForm : registerForm }
          </LoginForm>
        </div>
      </div>
    </>
  );
};

export default AccessPage;
