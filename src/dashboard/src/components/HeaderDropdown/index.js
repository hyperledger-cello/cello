import React, { PureComponent } from 'react';
import { Dropdown } from 'antd';
import classNames from 'classnames';
import styles from './index.less';

export default class HeaderDropdown extends PureComponent {
  render() {
    const { className, ...props } = this.props;
    return (
      <Dropdown className={classNames(styles.container, className)} {...props} />
    );
  }
}
