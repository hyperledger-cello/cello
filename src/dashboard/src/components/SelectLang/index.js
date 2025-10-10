import React, { PureComponent } from 'react';
import { injectIntl, setLocale } from 'umi';
import { GlobalOutlined } from '@ant-design/icons';
import classNames from 'classnames';
import HeaderDropdown from '../HeaderDropdown';
import styles from './index.less';

class SelectLang extends PureComponent {
  changeLang = ({ key }) => {
    setLocale(key);
    localStorage.setItem('umi_locale', key);
  };

  render() {
    const { className, intl } = this.props;
    const locales = ['zh-CN', 'en-US'];
    const languageLabels = {
      'zh-CN': '简体中文',
      'en-US': 'English',
    };
    const languageIcons = {
      'zh-CN': '🇨🇳',
      'en-US': '🇬🇧',
    };
    const langMenuItems = locales.map(locale => ({
      key: locale,
      label: (
        <span>
          {languageIcons[locale]} {languageLabels[locale]}
        </span>
      ),
      onClick: this.changeLang,
    }));
    return (
      <HeaderDropdown menu={{ items: langMenuItems }} placement="bottomRight">
        <span className={classNames(styles.dropDown, className)}>
          <GlobalOutlined />
          <span>{intl.formatMessage({ id: 'navBar.lang' })}</span>
        </span>
      </HeaderDropdown>
    );
  }
}

export default injectIntl(SelectLang);
