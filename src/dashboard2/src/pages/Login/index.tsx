import { GlobalOutlined, LinkOutlined, LockOutlined, MailOutlined, TeamOutlined } from '@ant-design/icons';
import { LoginForm, ProFormText } from '@ant-design/pro-components';
import { Tabs, theme } from 'antd';
import { Helmet, SelectLang } from '@umijs/max';
import { useState } from 'react';
import { useIntl } from 'umi';


type ActionType = 'login' | 'register';

const AccessPage: React.FC = () => {
  const { token } = theme.useToken();
  const [actionType, setActionType] = useState<ActionType>('login');
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
        name="orgName"
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
        name="agentUrl"
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

  return (
    <>
      <Helmet>
        <title>{intl.formatMessage({id: 'app.login.login',}) + " - Cello Dashboard"}</title>
      </Helmet>
      <div
        style={{
          height: "100vh",
          background: token.colorBgLayout,
          backgroundImage: "url('https://gw.alipayobjects.com/zos/rmsportal/TVYTbAXWheQpRcWDaDMu.svg')",
          display: "flex",
          justifyContent: "center",
          alignItems: "center", 
        }}
      >
        <div style={{ position: "absolute", top: 20, right: 20 }}>
          <SelectLang
            icon={
              <>
                <GlobalOutlined />
                <span className="lang-text">{intl.formatMessage({id: 'navBar.lang',})}</span>
              </>
            }
            reload={false}
          />
        </div>
        <div>
          <LoginForm
            logo="/favicon.png"
            title="Cello Dashboard"
            subTitle="Dashboard for management cello service"
          >
            <Tabs
              centered
              activeKey={actionType}
              onChange={(activeKey) => setActionType(activeKey as ActionType)}
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
