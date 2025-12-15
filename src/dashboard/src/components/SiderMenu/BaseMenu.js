import React, { useCallback, useRef } from 'react';
import classNames from 'classnames';
import { Menu } from 'antd';
import {
  EyeOutlined,
  DashboardFilled,
  TeamOutlined,
  DesktopOutlined,
  NodeIndexOutlined,
  ApartmentOutlined,
  DeploymentUnitOutlined,
  FunctionOutlined,
  UserOutlined,
  BookOutlined,
  GithubOutlined,
  ApiOutlined,
} from '@ant-design/icons';
import { Link, useIntl } from 'umi';
import { urlToList } from '../_utils/pathTools';
import { getMenuMatches } from './SiderMenuUtils';
import { menu as menuConfig } from '../../defaultSettings';

const menus = {
  eye: <EyeOutlined />,
  dashboard: <DashboardFilled />,
  team: <TeamOutlined />,
  node: <NodeIndexOutlined />,
  network: <ApartmentOutlined />,
  channel: <DeploymentUnitOutlined />,
  chaincode: <FunctionOutlined />,
  user: <UserOutlined />,
  agent: <DesktopOutlined />,
  docs: <BookOutlined />,
  github: <GithubOutlined />,
  api: <ApiOutlined />,
};

// Allow menu.js config icon as string or ReactNode
const getIcon = icon => {
  if (typeof icon === 'string') {
    return menus[icon];
  }
  return icon;
};

const BaseMenu = props => {
  const {
    openKeys,
    theme,
    mode,
    location,
    className,
    collapsed,
    fixedHeader,
    layout,
    handleOpenChange,
    style,
    menuData,
    flatMenuKeys,
    isMobile,
    onCollapse,
  } = props;

  const intl = useIntl();
  const wrapRef = useRef(null);

  // Translate menu item name
  const translateName = useCallback(
    item => {
      if (menuConfig.disableLocal || !item.locale) {
        return item.name;
      }
      return intl.formatMessage({ id: item.locale, defaultMessage: item.name });
    },
    [intl]
  );

  // Convert path
  const conversionPath = useCallback(path => {
    if (path && path.indexOf('http') === 0) {
      return path;
    }
    return `/${path || ''}`.replace(/\/+/g, '/');
  }, []);

  // Get nav menu items
  const getNavMenuItems = useCallback(
    (menusData, isFromTop) => {
      if (!menusData) {
        return [];
      }
      return menusData
        .filter(item => item.name && !item.hideInMenu && isFromTop !== (item.isBottom ?? false))
        .map(item => {
          const translatedName = translateName(item);
          const itemNode = {
            key: item.path,
            icon: getIcon(item.icon),
            label: item.isExternal ? (
              <a href={conversionPath(item.path)} target={item.target}>
                <span>{translatedName}</span>
              </a>
            ) : (
              <Link
                to={conversionPath(item.path)}
                target={item.target}
                replace={conversionPath(item.path) === location.pathname}
                onClick={
                  isMobile
                    ? () => {
                        onCollapse(true);
                      }
                    : undefined
                }
              >
                <span>{translatedName}</span>
              </Link>
            ),
          };

          // 如果有子節點且沒有 hideChildrenInMenu，遞迴產生 children
          if (item.children && !item.hideChildrenInMenu && item.children.some(c => c.name)) {
            itemNode.children = getNavMenuItems(item.children, isFromTop);
          }

          return itemNode;
        });
    },
    [conversionPath, isMobile, location.pathname, onCollapse, translateName]
  );

  // Get the currently selected menu keys
  const getSelectedMenuKeys = useCallback(
    pathname => {
      return urlToList(pathname).map(itemPath => getMenuMatches(flatMenuKeys, itemPath).pop());
    },
    [flatMenuKeys]
  );

  // Get popup container
  const getPopupContainer = useCallback(() => {
    if (fixedHeader && layout === 'topmenu') {
      return wrapRef.current;
    }
    return document.body;
  }, [fixedHeader, layout]);

  const { pathname } = location;
  // if pathname can't match, use the nearest parent's key
  let selectedKeys = getSelectedMenuKeys(pathname);
  if (!selectedKeys.length && openKeys) {
    selectedKeys = [openKeys[openKeys.length - 1]];
  }

  let menuProps = {};
  if (openKeys && !collapsed) {
    menuProps = {
      openKeys: openKeys.length === 0 ? [...selectedKeys] : openKeys,
    };
  }

  const cls = classNames(className, {
    'top-nav-menu': mode === 'horizontal',
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 64px)' }}>
      <Menu
        key="Upper Menu"
        mode={mode}
        theme={theme}
        onOpenChange={handleOpenChange}
        selectedKeys={selectedKeys}
        style={style}
        className={cls}
        {...menuProps}
        getPopupContainer={getPopupContainer}
        items={getNavMenuItems(menuData, true)}
      />
      <div style={{ flexGrow: 1 }} />
      <Menu
        key="Lower Menu"
        mode={mode}
        theme={theme}
        onOpenChange={handleOpenChange}
        selectedKeys={selectedKeys}
        style={style}
        className={cls}
        {...menuProps}
        getPopupContainer={getPopupContainer}
        items={getNavMenuItems(menuData, false)}
      />
      <div ref={wrapRef} />
    </div>
  );
};

export default BaseMenu;
