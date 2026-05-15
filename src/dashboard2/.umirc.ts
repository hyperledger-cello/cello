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
      name: 'login',
      path: '/login',
      component: './Login',
      headerRender: false,
      menuRender: false,
      hideInMenu: true,
    },
    {
      name: 'home',
      path: '/',
      component: './Home',
      hideInMenu: true,
    },
    {
      name: 'organization',
      path: '/organization',
      component: './Organization',
      
      icon: 'Team',
      title: true
    },
    {
      name: 'node',
      path: '/node',
      component: './Node',
      icon: 'NodeIndex',
      title: true
    },
    {
      name: 'channel',
      path: '/channel',
      component: './Channel',
      icon: 'DeploymentUnit',
      title: true
    },
    {
      name: 'chaincode',
      path: '/chaincode',
      component: './Chaincode',
      icon: 'Function',
      title: true
    },
  ],
  npmClient: 'yarn',
  utoopack: {},
  define: {
    'process.env.API_BASE_URL': process.env.API_BASE_URL
  },
});

