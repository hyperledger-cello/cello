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
      name: '登入',
      path: '/login',
      component: './Login',
      layout: false
    },
    {
      path: '/',
      component: './Home',
      access: 'isLogin',
      icon: 'team',
    },
    {
      name: '組織管理',
      path: '/organization',
      component: './Organization',
      access: 'isLogin',
      icon: 'team',
    },
    {
      name: 'CRUD 示例',
      path: '/table',
      component: './Table',
      access: 'isLogin',
      icon: 'team',
    },
  ],
  npmClient: 'yarn',
  utoopack: {},
});

