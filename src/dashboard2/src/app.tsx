import type { HeaderProps } from '@ant-design/pro-layout';
import { ConfigProvider } from 'antd';

export async function getInitialState() {
  const token = "localStorage.getItem('token')";

  return {
    token,
  };
}

export const rootContainer = (container: React.ReactNode) => {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorBgLayout: '#20343e',

          colorTextSecondary: '#dfe6eb',
        },
      }}
    >
      {container}
    </ConfigProvider>
  );
};

export const layout = () => {
  return {
    logo: '/favicon.png',
    layout: 'mix',

    headerRender: (_props: HeaderProps, defaultDom: React.ReactNode) => {
      return (
        <div>
          {defaultDom}
        </div>
      );
    },
  };
};
