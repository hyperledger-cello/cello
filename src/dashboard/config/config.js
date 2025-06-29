// https://umijs.org/config/
import pageRoutes from './router.config';
import webpackPlugin from './plugin.config';
import theme from './theme';

const PROXY = process.env.PROXY || 'http://127.0.0.1/engine';

export default {
  // add for transfer to umi
  dva: {},
  antd: {},
  locale: {
    default: 'en-US',
    antd: true,
    title: true,
    baseNavigator: false,
    baseSeparator: '-',
  },
  pwa: false,
  lessLoader: { javascriptEnabled: true },
  // devtool: false,
  // 路由配置
  routes: pageRoutes,
  // Theme for antd
  // https://ant.design/docs/react/customize-theme-cn
  theme,
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8080/',
      changeOrigin: true,
      //pathRewrite: { '^/api': '' },
    },
  },
  ignoreMomentLocale: true,
  dynamicImport: {
    loading: '@/components/PageLoading/index',
  },
  manifest: {
    basePath: '/',
  },

  chainWebpack: webpackPlugin,
  mock: {
    exclude: ['mock/**/_*.js', 'mock/_*/**/*.js'],
  },
  hash: true,
  history: {
    type: 'hash',
  },
};
