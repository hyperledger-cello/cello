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
      icon: 'team',
    },
    {
      name: 'organization',
      path: '/organization',
      component: './Organization',
      access: 'isLogin',
      icon: 'team',
      title: true
    },
  ],
  npmClient: 'yarn',
  utoopack: {},
  define: {
    'process.env.API_BASE_URL': process.env.API_BASE_URL
  },
});

