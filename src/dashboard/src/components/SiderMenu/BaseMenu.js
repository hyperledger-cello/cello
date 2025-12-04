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
// import { isUrl } from '@/utils/utils';
// import styles from './index.less';
// import IconFont from '@/components/IdocsconFont';

const { SubMenu } = Menu;
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
    return menusData
      .filter(item => item.name && !item.hideInMenu && isFromTop !== (item.isBottom ?? false))
      .map(item => this.getSubMenuOrItem(item))
      .filter(item => item);
  };

  // Get the currently selected menu
  getSelectedMenuKeys = pathname => {
    const { flatMenuKeys } = this.props;
    return urlToList(pathname).map(itemPath => getMenuMatches(flatMenuKeys, itemPath).pop());
  };

  /**
   * get SubMenu or Item
   */
  getSubMenuOrItem = item => {
    // doc: add hideChildrenInMenu
    if (item.children && !item.hideChildrenInMenu && item.children.some(child => child.name)) {
      const { name } = item;
      return (
        <SubMenu
          title={
            item.icon ? (
              <span>
                {getIcon(item.icon)}
                <span>{name}</span>
              </span>
            ) : (
              name
            )
          }
          key={item.path}
        >
          {this.getNavMenuItems(item.children)}
        </SubMenu>
      );
    }
    return <Menu.Item key={item.path}>{this.getMenuItemPath(item)}</Menu.Item>;
  };

  /**
   * 判断是否是http链接.返回 Link 或 a
   * Judge whether it is http link.return a or Link
   * @memberof SiderMenu
   */
  getMenuItemPath = item => {
    const itemPath = this.conversionPath(item.path);
    const icon = getIcon(item.icon);
    const { name, target, isExternal } = item;
    // Is it a http link
    if (isExternal) {
      return (
        <a href={itemPath} target={target}>
          {icon}
          <span>{name}</span>
        </a>
      );
    }
    const { location, isMobile, onCollapse } = this.props;
    return (
      <Link
        to={itemPath}
        target={target}
        replace={itemPath === location.pathname}
        onClick={
          isMobile
            ? () => {
                onCollapse(true);
              }
            : undefined
        }
      >
        {icon}
        <span>{name}</span>
      </Link>
    );
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
        >
          {this.getNavMenuItems(menuData, true)}
        </Menu>
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
        >
          {this.getNavMenuItems(menuData, false)}
        </Menu>
        <div ref={this.getRef} />
      </div>
    );
  }
}
