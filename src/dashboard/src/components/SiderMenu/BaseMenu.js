import React, { PureComponent } from 'react';
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
import { Link } from 'umi';
import { urlToList } from '../_utils/pathTools';
import { getMenuMatches } from './SiderMenuUtils';

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
//   icon: 'setting',
//   icon: 'icon-geren' #For Iconfont ,
//   icon: 'http://demo.com/icon.png',
//   icon: <Icon type="setting" />,
const getIcon = icon => {
  if (typeof icon === 'string') {
    // if (isUrl(icon)) {
    //   return <Icon component={() => <img src={icon} alt="icon" className={styles.icon} />} />;
    // }
    // if (icon.startsWith('icon-')) {
    //   return <IconFont type={icon} />;
    // }
    return menus[icon];
  }
  return icon;
};

export default class BaseMenu extends PureComponent {
  /**
   * 获得菜单子节点
   * @memberof SiderMenu
   */
  getNavMenuItems = (menusData, isFromTop) => {
    if (!menusData) {
      return [];
    }
    const { isMobile, onCollapse, location } = this.props;
    return menusData
      .filter(item => item.name && !item.hideInMenu && isFromTop !== (item.isBottom ?? false))
      .map(item => {
        const itemNode = {
          key: item.path,
          icon: getIcon(item.icon),
          // label 可以是 ReactNode（Link / <a> / 字串）
          label: item.isExternal ? (
            <a href={this.conversionPath(item.path)} target={item.target}>
              <span>{item.name}</span>
            </a>
          ) : (
            <Link
              to={this.conversionPath(item.path)}
              target={item.target}
              replace={this.conversionPath(item.path) === location.pathname}
              onClick={
                isMobile
                  ? () => {
                      onCollapse(true);
                    }
                  : undefined
              }
            >
              <span>{item.name}</span>
            </Link>
          ),
        };

        // 如果有子節點且沒有 hideChildrenInMenu，遞迴產生 children
        if (item.children && !item.hideChildrenInMenu && item.children.some(c => c.name)) {
          itemNode.children = this.getNavMenuItems(item.children, isFromTop);
        }

        return itemNode;
      });
  };

  // Get the currently selected menu
  getSelectedMenuKeys = pathname => {
    const { flatMenuKeys } = this.props;
    return urlToList(pathname).map(itemPath => getMenuMatches(flatMenuKeys, itemPath).pop());
  };

  conversionPath = path => {
    if (path && path.indexOf('http') === 0) {
      return path;
    }
    return `/${path || ''}`.replace(/\/+/g, '/');
  };

  getPopupContainer = (fixedHeader, layout) => {
    if (fixedHeader && layout === 'topmenu') {
      return this.wrap;
    }
    return document.body;
  };

  getRef = ref => {
    this.wrap = ref;
  };

  render() {
    const {
      openKeys,
      theme,
      mode,
      location: { pathname },
      className,
      collapsed,
      fixedHeader,
      layout,
    } = this.props;
    // if pathname can't match, use the nearest parent's key
    let selectedKeys = this.getSelectedMenuKeys(pathname);
    if (!selectedKeys.length && openKeys) {
      selectedKeys = [openKeys[openKeys.length - 1]];
    }
    let props = {};
    if (openKeys && !collapsed) {
      props = {
        openKeys: openKeys.length === 0 ? [...selectedKeys] : openKeys,
      };
    }
    const { handleOpenChange, style, menuData } = this.props;
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
          {...props}
          getPopupContainer={() => this.getPopupContainer(fixedHeader, layout)}
          items={this.getNavMenuItems(menuData, true)}
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
          {...props}
          getPopupContainer={() => this.getPopupContainer(fixedHeader, layout)}
          items={this.getNavMenuItems(menuData, false)}
        />
        <div ref={this.getRef} />
      </div>
    );
  }
}
