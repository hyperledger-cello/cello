/*
 SPDX-License-Identifier: Apache-2.0
*/
export default [
  // user
  {
    path: '/user',
    component: '../layouts/UserLayout',
    routes: [
      { path: '/user', redirect: '/user/login' },
      { path: '/user/login', name: 'login', component: './User/Login' },
      {
        component: '404',
      },
    ],
  },
  // app
  {
    path: '/',
    component: '../layouts/SecurityLayout',
    routes: [
      {
        path: '/',
        component: '../layouts/BasicLayout',
        authority: ['admin', 'member'],
        routes: [
          { path: '/', redirect: '/overview' },
          {
            path: '/overview',
            name: 'overview',
            icon: 'dashboard',
            component: './Overview/index',
          },
          {
            path: '/organization',
            authority: ['admin'],
            name: 'organization',
            icon: 'team',
            component: './Organization/Organization',
          },
          // {
          //   path: '/agent',
          //   name: 'agent',
          //   icon: 'agent',
          //   component: './Agent/Agent',
          // },
          // {
          //   path: '/agent/newAgent',
          //   name: 'newAgent',
          //   component: './Agent/newAgent',
          //   hideInMenu: true,
          // },
          // {
          //   path: '/agent/editAgent',
          //   name: 'editAgent',
          //   component: './Agent/newAgent',
          //   hideInMenu: true,
          // },
          {
            path: '/node',
            name: 'node',
            icon: 'node',
            component: './Node/index',
          },
          {
            path: '/node/new',
            name: 'newNode',
            hideInMenu: true,
            component: './Node/New/index',
            routes: [
              {
                path: '/node/new',
                redirect: '/node/new/basic-info',
              },
              {
                path: '/node/new/basic-info',
                name: 'basicInfo',
                component: './Node/New/basicInfo',
              },
              {
                path: '/node/new/node-info',
                name: 'nodeInfo',
                component: './Node/New/nodeInfo',
              },
            ],
          },
          // {
          //   path: '/network',
          //   name: 'network',
          //   icon: 'network',
          //   component: './Network/Network',
          // },
          // {
          //   path: '/network/newNetwork',
          //   name: 'newNetwork',
          //   component: './Network/newNetwork',
          //   hideInMenu: true,
          // },
          {
            path: '/channel',
            name: 'channel',
            icon: 'channel',
            component: './Channel/Channel',
          },
          {
            path: '/chaincode',
            name: 'chaincode',
            icon: 'chaincode',
            component: './ChainCode/ChainCode',
          },
          {
            path: '/userManagement',
            name: 'userManagement',
            icon: 'user',
            component: './UserManagement/UserManagement',
          },
          {
            path: 'https://hyperledger-cello.readthedocs.io',
            name: 'docs',
            icon: 'docs',
            isExternal: true,
            isBottom: true,
          },
        ],
      },
      {
        component: '404',
      },
    ],
  },
];
