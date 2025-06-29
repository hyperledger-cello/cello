/*
 SPDX-License-Identifier: Apache-2.0
*/
import exception from './zh-CN/exception';
import globalHeader from './zh-CN/globalHeader';
import login from './zh-CN/login';
import menu from './zh-CN/menu';
import pwa from './zh-CN/pwa';
import component from './zh-CN/component';
import Organization from './zh-CN/Organization';
import operatorUser from './zh-CN/operatorUser';
import form from './zh-CN/form';
import Agent from './zh-CN/Agent';
import Node from './zh-CN/Node';
import fabricCa from './zh-CN/fabric/ca';
import Network from './zh-CN/Network';
import Channel from './zh-CN/Channel';
import ChainCode from './zh-CN/Chaincode';

export default {
  'navBar.lang': '语言',
  'layout.user.link.help': '帮助',
  'layout.user.link.privacy': '隐私',
  'layout.user.link.terms': '条款',
  'app.home.introduce': '介绍',
  'app.forms.basic.title': '基础表单',
  'app.forms.basic.description':
    '表单页用于向用户收集或验证信息，基础表单常见于数据项较少的表单场景。',

  // Error messages
  'error.request.200': '服务器成功返回请求的数据。',
  'error.request.201': '新建或修改数据成功。',
  'error.request.202': '一个请求已经进入后台排队（异步任务）。',
  'error.request.204': '删除数据成功。',
  'error.request.400': '发出的请求有错误，服务器没有进行新建或修改数据的操作。',
  'error.request.401': '用户没有权限（令牌、用户名、密码错误）。',
  'error.request.403': '用户得到授权，但是访问是被禁止的。',
  'error.request.404': '发出的请求针对的是不存在的记录，服务器没有进行操作。',
  'error.request.406': '请求的格式不可得。',
  'error.request.410': '请求的资源被永久删除，且不会再得到的。',
  'error.request.422': '当创建一个对象时，发生一个验证错误。',
  'error.request.500': '服务器发生错误，请检查服务器。',
  'error.request.502': '网关错误。',
  'error.request.503': '服务不可用，服务器暂时过载或维护。',
  'error.request.504': '网关超时。',
  'error.network': '网络错误，请检查您的网络连接。',
  'error.login.invalidCredentials': '用户名或密码错误。',
  'error.login.expired': '未登录或登录已过期，请重新登录。',
  'error.register.duplicate': '邮箱地址或组织名已存在。',
  'error.request.generic': '请求错误：{status}',

  ...exception,
  ...globalHeader,
  ...login,
  ...menu,
  ...pwa,
  ...component,
  ...Organization,
  ...Agent,
  ...operatorUser,
  ...form,
  ...Node,
  ...fabricCa,
  ...Network,
  ...Channel,
  ...ChainCode,
};
