import type { HeaderProps } from '@ant-design/pro-layout';
import { history } from 'umi';
import { ConfigProvider, Menu, Modal, theme } from 'antd';
import HeaderRight from './components/HeaderRight/HeaderRight';
import { ApiOutlined, BookOutlined, GithubOutlined } from '@ant-design/icons';
import { useIntl } from 'umi';

export const rootContainer = (container: React.ReactNode) => {
  return (
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorBgLayout: '#20343e',
          colorBgBase: '#2d3f49',
          colorText: '#ffffff',
          colorTextSecondary: '#dfe6eb',
        },
      }}
    >
      {container}
    </ConfigProvider>
  );
};

const { useToken } = theme;

export const layout = () => {
  const { token } = useToken();
  return {
    logo: '/favicon.png',
    layout: 'mix',

    token: {
      header: {
        colorBgHeader: token.colorBgLayout,
      },

      sider: {
        colorMenuBackground: token.colorBgBase,
        colorTextMenu: token.colorText,
        colorTextMenuItemHover: '#5aaafa',
        colorTextMenuSelected: '#5aaafa',
        colorBgMenuItemSelected: '#121e35',
      },

      pageContainer: {
        colorBgPageContainer: token.colorBgLayout,
      },
    },

    actionsRender: (_props: HeaderProps, defaultDom: React.ReactNode) => {
      return <HeaderRight />;
    },

    menuFooterRender: () => {
      const intl = useIntl();
      return (
        <Menu
          mode="inline"
          selectable={false}
          inlineIndent={16}
          style={{
            background: token.colorBgLayout,
            borderTop: '1px solid rgba(112,204,254,0.27)',
            paddingBottom: 10
          }}
          items={[
            {
              key: 'api',
              icon: <ApiOutlined />,
              label: (
                <a
                  href={process.env.API_BASE_URL + '/api/v1/docs'}
                  target="_blank"
                >
                  REST API
                </a>
              ),
            },
            {
              key: 'github',
              icon: <GithubOutlined />,
              label: (
                <a
                  href='https://github.com/hyperledger-cello'
                  target="_blank"
                >
                  GitHub
                </a>
              ),
            },
            {
              key: 'docs',
              icon: <BookOutlined />,
              label: (
                <a
                  href='https://hyperledger-cello.readthedocs.io'
                  target="_blank"
                >
                  {intl.formatMessage({id: 'menu.docs'},)}
                </a>
              ),
            },
          ]}
        />
      );
    },

    onPageChange: () => {
      const { location } = history;
      const isLogin = !!localStorage.getItem('token');
      if (isLogin && location.pathname == '/login') {
        history.push('/');
      }
    },
  };
};

export const request = {
  requestInterceptors: [
    (url: string, options: any) => {
      options.baseURL = process.env.API_BASE_URL;
      return { url, options };
    },
  ],

  responseInterceptors: [[
    (response: any) => response,
    (error: any) => {
      if (error?.response?.status === 401) {
        if (document.querySelector('.token-expired-modal')) {
          return Promise.reject(error);
        }

        Modal.error({
          className: 'token-expired-modal',
          title: '登入已過期',
          content: '您的登入狀態已過期，請重新登入。',
          okText: '重新登入',
          onOk: () => {
            localStorage.removeItem('token');
            history.push('/login');
          },
        });
      }
      return Promise.reject(error);
    },
  ]],
};
