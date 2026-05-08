import { defineConfig } from '@umijs/max';

export default defineConfig({
  antd: {},
  access: {},
  model: {},
  initialState: {},
  request: {},
  locale: {
    default: 'en-US',
    antd: true,
    baseNavigator: true,
  },
  layout: {
    title: 'Hyperledger Cello',
  },
  favicons: [
    '/favicon.png'
  ],
  routes: [
    {
      path: '/login',
      component: './Login',
      headerRender: false,
      menuRender: false,
    },
    {
      path: '/',
      component: './Home',
      access: 'isLogin',
    },
    {
      name: 'organization',
      path: '/organization',
      component: './Organization',
      access: 'isLogin',
      icon: 'Team',
      title: true
    },
    {
      name: 'node',
      path: '/node',
      component: './Node',
      access: 'isLogin',
      icon: 'NodeIndex',
      title: true
    },
    {
      name: 'channel',
      path: '/channel',
      component: './Channel',
      access: 'isLogin',
      icon: 'DeploymentUnit',
      title: true
    },
  ],
  npmClient: 'yarn',
  utoopack: {},
  define: {
    'process.env.API_BASE_URL': process.env.API_BASE_URL
  },
});

