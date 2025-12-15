/*
 SPDX-License-Identifier: Apache-2.0
*/
import React, { useEffect, useCallback, useMemo } from 'react';
import { Layout } from 'antd';
import { Helmet } from 'react-helmet';
import { connect, useIntl } from 'umi';
import { ContainerQuery } from 'react-container-query';
import classNames from 'classnames';
import Media from 'react-media';
import SiderMenu from '@/components/SiderMenu';
import getPageTitle from '@/utils/getPageTitle';
import logo from '../assets/logo.svg';
import Footer from './Footer';
import Header from './Header';
import Context from './MenuContext';
import styles from './BasicLayout.less';

const { Content } = Layout;

const query = {
  'screen-xs': {
    maxWidth: 575,
  },
  'screen-sm': {
    minWidth: 576,
    maxWidth: 767,
  },
  'screen-md': {
    minWidth: 768,
    maxWidth: 991,
  },
  'screen-lg': {
    minWidth: 992,
    maxWidth: 1199,
  },
  'screen-xl': {
    minWidth: 1200,
    maxWidth: 1599,
  },
  'screen-xxl': {
    minWidth: 1600,
  },
};

const BasicLayout = props => {
  const {
    dispatch,
    route: { routes, path, authority },
    navTheme,
    layout: propsLayout,
    children,
    location,
    location: { pathname },
    isMobile,
    menuData,
    breadcrumbNameMap,
    fixedHeader,
    fixSiderbar,
    collapsed,
  } = props;

  // Subscribe to locale changes - this ensures the component re-renders when language switches
  const intl = useIntl();

  // Initialize on mount (equivalent to componentDidMount)
  useEffect(() => {
    dispatch({
      type: 'setting/getSetting',
    });
    dispatch({
      type: 'menu/getMenuData',
      payload: { routes, path, authority },
    });
  }, [dispatch, routes, path, authority]);

  // Memoized context value
  const contextValue = useMemo(
    () => ({
      location,
      breadcrumbNameMap,
    }),
    [location, breadcrumbNameMap]
  );

  // Calculate layout style
  const layoutStyle = useMemo(() => {
    if (fixSiderbar && propsLayout !== 'topmenu' && !isMobile) {
      return {
        paddingLeft: collapsed ? '80px' : '256px',
      };
    }
    return null;
  }, [fixSiderbar, propsLayout, isMobile, collapsed]);

  // Handle menu collapse
  const handleMenuCollapse = useCallback(
    collapsedState => {
      dispatch({
        type: 'global/changeLayoutCollapsed',
        payload: collapsedState,
      });
    },
    [dispatch]
  );

  const isTop = propsLayout === 'topmenu';
  const contentStyle = !fixedHeader ? { paddingTop: 0 } : {};

  const layoutContent = (
    <Layout>
      {isTop && !isMobile ? null : (
        <SiderMenu
          logo={logo}
          theme={navTheme}
          onCollapse={handleMenuCollapse}
          menuData={menuData}
          isMobile={isMobile}
          {...props}
        />
      )}
      <Layout
        style={{
          ...layoutStyle,
          minHeight: '100vh',
        }}
      >
        <Header
          menuData={menuData}
          handleMenuCollapse={handleMenuCollapse}
          logo={logo}
          isMobile={isMobile}
          {...props}
        />
        <Content className={styles.content} style={contentStyle}>
          {children}
        </Content>
        <Footer />
      </Layout>
    </Layout>
  );

  return (
    <>
      <Helmet>
        <title>{getPageTitle(pathname, breadcrumbNameMap, intl)}</title>
      </Helmet>

      <ContainerQuery query={query}>
        {params => (
          <Context.Provider value={contextValue}>
            <div className={classNames(params)}>{layoutContent}</div>
          </Context.Provider>
        )}
      </ContainerQuery>
    </>
  );
};

export default connect(({ global, setting, menu: menuModel }) => ({
  collapsed: global.collapsed,
  layout: setting.layout,
  menuData: menuModel.menuData,
  breadcrumbNameMap: menuModel.breadcrumbNameMap,
  ...setting,
}))(props => (
  <Media query="(max-width: 599px)">
    {isMobile => <BasicLayout {...props} isMobile={isMobile} />}
  </Media>
));
