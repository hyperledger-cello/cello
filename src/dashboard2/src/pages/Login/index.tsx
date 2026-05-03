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
            message: '请输入邮箱地址!',
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
            message: '请输入密码!',
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
            message: '请输入组织名称!',
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
            message: '请输入邮箱地址!',
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
            message: '请输入密码!',
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
            message: '请再次输入密码!',
          },
          ({ getFieldValue }) => ({
            validator(role, value) {
              if (value !== getFieldValue('password')) {
                return Promise.reject('两次密码必须相同!');
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
            message: '请输入代理地址!',
          },
          {
            pattern: /^https?:\/\/.+/,
            message: '代理地址格式错误，必须以 http:// 或 https:// 开头!',
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
