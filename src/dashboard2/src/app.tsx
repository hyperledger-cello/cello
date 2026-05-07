import type { HeaderProps } from '@ant-design/pro-layout';
import { history, SelectLang } from 'umi';
import { ConfigProvider, theme } from 'antd';
import HeaderRight from './components/HeaderRight';

export async function getInitialState() {
  const token = localStorage.getItem('token');

  return {
    token,
  };
}

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

export const layout = (initialState: any) => {
  return {
    logo: '/favicon.png',
    layout: 'mix',

    token: {
      header: {
        colorBgHeader: '#20343e',
        colorHeaderTitle: '#ffffff',
        colorTextMenuSecondary: '#ffffff',
      },

      sider: {
        colorMenuBackground: '#2d3f49',
        colorTextMenu: '#ffffff',
        colorTextMenuItemHover: '#5aaafa',
        colorTextMenuSelected: '#5aaafa',
        colorBgMenuItemSelected: '#121e35'
      },

      pageContainer: {
        colorBgPageContainer: '#20343e',
      },
    },

    rightContentRender: (_props: HeaderProps, defaultDom: React.ReactNode) => {
      return <HeaderRight />;
    },

    onPageChange: () => {
      const { location } = history;
      if (!initialState.initialState.token && location.pathname != 'login') {
        history.push('/login');
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
};
