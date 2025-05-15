/*
 SPDX-License-Identifier: Apache-2.0
*/
import exception from './en-US/exception';
import globalHeader from './en-US/globalHeader';
import login from './en-US/login';
import menu from './en-US/menu';
import pwa from './en-US/pwa';
import component from './en-US/component';
import Organization from './en-US/Organization';
import User from './en-US/operatorUser';
import form from './en-US/form';
import Agent from './en-US/Agent';
import Node from './en-US/Node';
import fabricCa from './en-US/fabric/ca';
import Network from './en-US/Network';
import Channel from './en-US/Channel';
import ChainCode from './en-US/Chaincode';

export default {
  'navBar.lang': 'Languages',
  'layout.user.link.help': 'Help',
  'layout.user.link.privacy': 'Privacy',
  'layout.user.link.terms': 'Terms',
  'app.home.introduce': 'introduce',
  'app.forms.basic.title': 'Basic form',
  'app.forms.basic.description':
    'Form pages are used to collect or verify information to users, and basic forms are common in scenarios where there are fewer data items.',

  // Error messages
  'error.request.200': 'Server successfully returned requested data.',
  'error.request.201': 'Created or modified data successfully.',
  'error.request.202': 'A request has entered the background queue.',
  'error.request.204': 'Data deleted successfully.',
  'error.request.400': 'Bad request, server did not create or modify data.',
  'error.request.401': 'User does not have permission (token, username, password error).',
  'error.request.403': 'User is authorized but access is forbidden.',
  'error.request.404': 'Request made to non-existent record, server did not operate.',
  'error.request.406': 'Requested format not available.',
  'error.request.410': 'Requested resource permanently deleted and will not be available again.',
  'error.request.422': 'Validation error occurred while creating an object.',
  'error.request.500': 'Server error, please check server.',
  'error.request.502': 'Gateway error.',
  'error.request.503': 'Service unavailable, server temporarily overloaded or maintaining.',
  'error.request.504': 'Gateway timeout.',
  'error.network': 'Network error, please check your connection.',
  'error.login.invalidCredentials': 'Invalid username or password.',
  'error.login.expired': 'Not logged in or session expired. Please log in again.',
  'error.register.duplicate': 'Email address or organization name already exists.',
  'error.request.generic': 'Request error: {status}',

  ...exception,
  ...globalHeader,
  ...login,
  ...menu,
  ...pwa,
  ...component,
  ...Organization,
  ...Agent,
  ...User,
  ...form,
  ...Node,
  ...fabricCa,
  ...Network,
  ...Channel,
  ...ChainCode,
};
