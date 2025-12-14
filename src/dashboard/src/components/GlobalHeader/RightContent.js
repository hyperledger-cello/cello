import React, { PureComponent } from 'react';
import { injectIntl } from 'umi';
import { Spin, Avatar } from 'antd';
import { LogoutOutlined } from '@ant-design/icons';
import HeaderDropdown from '../HeaderDropdown';
import SelectLang from '../SelectLang';
import styles from './index.less';

class GlobalHeaderRight extends PureComponent {
  render() {
    const { currentUser, onMenuClick, intl } = this.props;
    const menuItems = [
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: (
          <span>
            {intl.formatMessage({
              id: 'menu.account.logout',
              defaultMessage: 'logout',
            })}
          </span>
        ),
        onClick: onMenuClick,
      },
    ];
    const className = styles.right;

    return (
      <div className={className}>
        {currentUser.id ? (
          <HeaderDropdown menu={{ items: menuItems }}>
            <span className={`${styles.action} ${styles.account}`}>
              <Avatar size="small" className={styles.avatar} src="/avatar.png" alt="avatar" />
              <span className={styles.name}>{currentUser.email}</span>
            </span>
          </HeaderDropdown>
        ) : (
          <Spin size="small" style={{ marginLeft: 8, marginRight: 8 }} />
        )}
        <SelectLang className={styles.action} />
      </div>
    );
  }
}

export default injectIntl(GlobalHeaderRight);
