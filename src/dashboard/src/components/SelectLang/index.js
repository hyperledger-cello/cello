import React, { useCallback } from 'react';
import { useIntl, setLocale } from 'umi';
import { GlobalOutlined } from '@ant-design/icons';
import classNames from 'classnames';
import HeaderDropdown from '../HeaderDropdown';
import styles from './index.less';

const locales = ['zh-CN', 'en-US'];
const languageLabels = {
  'zh-CN': '简体中文',
  'en-US': 'English',
};
const languageIcons = {
  'zh-CN': '🇨🇳',
  'en-US': '🇬🇧',
};

const SelectLang = ({ className }) => {
  const intl = useIntl();

  const changeLang = useCallback(({ key }) => {
    setLocale(key, false); // false = don't reload page
    localStorage.setItem('umi_locale', key);
  }, []);

  const langMenuItems = locales.map(locale => ({
    key: locale,
    label: (
      <span>
        {languageIcons[locale]} {languageLabels[locale]}
      </span>
    ),
    onClick: changeLang,
  }));

  return (
    <HeaderDropdown menu={{ items: langMenuItems }} placement="bottomRight">
      <span className={classNames(styles.dropDown, className)}>
        <GlobalOutlined />
        <span>{intl.formatMessage({ id: 'navBar.lang' })}</span>
      </span>
    </HeaderDropdown>
  );
};

export default SelectLang;
