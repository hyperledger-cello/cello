import React from 'react';
import {
  UserOutlined,
  LockOutlined,
  MobileOutlined,
  MailOutlined,
  TeamOutlined,
  LinkOutlined,
} from '@ant-design/icons';
import styles from './index.less';

export default {
  UserName: {
    props: {
      size: 'large',
      prefix: <UserOutlined className={styles.prefixIcon} />,
      placeholder: 'admin',
    },
    rules: [
      {
        required: true,
        message: 'Please enter username!',
      },
    ],
  },
  Password: {
    props: {
      size: 'large',
      prefix: <LockOutlined className={styles.prefixIcon} />,
      type: 'password',
      placeholder: '888888',
    },
    rules: [
      {
        required: true,
        message: 'Please enter password!',
      },
    ],
  },
  Mobile: {
    props: {
      size: 'large',
      prefix: <MobileOutlined className={styles.prefixIcon} />,
      placeholder: 'mobile number',
    },
    rules: [
      {
        required: true,
        message: 'Please enter mobile number!',
      },
      {
        pattern: /^1\d{10}$/,
        message: 'Wrong mobile number format!',
      },
    ],
  },
  Captcha: {
    props: {
      size: 'large',
      prefix: <MailOutlined className={styles.prefixIcon} />,
      placeholder: 'captcha',
    },
    rules: [
      {
        required: true,
        message: 'Please enter Captcha!',
      },
    ],
  },
  OrgName: {
    props: {
      size: 'large',
      prefix: <TeamOutlined className={styles.prefixIcon} />,
      placeholder: 'org1',
    },
    rules: [
      {
        required: true,
        message: 'Please enter the name of organization!',
      },
    ],
  },
  Email: {
    props: {
      size: 'large',
      prefix: <MailOutlined className={styles.prefixIcon} />,
      placeholder: 'admin',
    },
    rules: [
      {
        required: true,
        message: 'Please enter username!',
      },
    ],
  },
  AgentUrl: {
    props: {
      size: 'large',
      prefix: <LinkOutlined className={styles.prefixIcon} />,
      placeholder: 'http://example.com',
    },
    rules: [
      {
        required: true,
        message: 'Please enter agent URL!',
      },
      {
        pattern: /^https?:\/\/.+/,
        message: 'Please enter a valid URL (http:// or https://)',
      },
    ],
  },
};
