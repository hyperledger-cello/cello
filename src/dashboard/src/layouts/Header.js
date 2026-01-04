import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Layout, message } from 'antd';
import Animate from 'rc-animate';
import { connect, useIntl, history } from 'umi';
import GlobalHeader from '@/components/GlobalHeader';
import TopNavHeader from '@/components/TopNavHeader';
import styles from './Header.less';

const { Header } = Layout;

const HeaderView = props => {
  const { isMobile, handleMenuCollapse, setting, dispatch, autoHideHeader, collapsed } = props;
  const { navTheme, layout, fixedHeader } = setting;
  const intl = useIntl();

  const [visible, setVisible] = useState(true);
  const oldScrollTopRef = useRef(0);
  const tickingRef = useRef(false);

  // Handle autoHideHeader state sync
  useEffect(() => {
    if (!autoHideHeader && !visible) {
      setVisible(true);
    }
  }, [autoHideHeader, visible]);

  // Scroll handler
  const handScroll = useCallback(() => {
    if (!autoHideHeader) {
      return;
    }
    const scrollTop = document.body.scrollTop + document.documentElement.scrollTop;
    if (!tickingRef.current) {
      tickingRef.current = true;
      requestAnimationFrame(() => {
        if (oldScrollTopRef.current > scrollTop) {
          setVisible(true);
        } else if (scrollTop > 300 && visible) {
          setVisible(false);
        } else if (scrollTop < 300 && !visible) {
          setVisible(true);
        }
        oldScrollTopRef.current = scrollTop;
        tickingRef.current = false;
      });
    }
  }, [autoHideHeader, visible]);

  // Add/remove scroll listener
  useEffect(() => {
    document.addEventListener('scroll', handScroll, { passive: true });
    return () => {
      document.removeEventListener('scroll', handScroll);
    };
  }, [handScroll]);

  const getHeadWidth = useCallback(() => {
    if (isMobile || !fixedHeader || layout === 'topmenu') {
      return '100%';
    }
    return collapsed ? 'calc(100% - 80px)' : 'calc(100% - 256px)';
  }, [isMobile, fixedHeader, layout, collapsed]);

  const handleNoticeClear = useCallback(
    type => {
      message.success(
        `${intl.formatMessage({ id: 'component.noticeIcon.cleared' })} ${intl.formatMessage({
          id: `component.globalHeader.${type}`,
        })}`
      );
      dispatch({
        type: 'global/clearNotices',
        payload: type,
      });
    },
    [dispatch, intl]
  );

  const handleMenuClick = useCallback(
    ({ key }) => {
      if (key === 'userCenter') {
        history.push('/account/center');
        return;
      }
      if (key === 'triggerError') {
        history.push('/exception/trigger');
        return;
      }
      if (key === 'userinfo') {
        history.push('/account/settings/base');
        return;
      }
      if (key === 'logout') {
        dispatch({
          type: 'login/logout',
        });
      }
    },
    [dispatch]
  );

  const handleNoticeVisibleChange = useCallback(
    visibleState => {
      if (visibleState) {
        dispatch({
          type: 'global/fetchNotices',
        });
      }
    },
    [dispatch]
  );

  const isTop = layout === 'topmenu';
  const width = getHeadWidth();

  const HeaderDom = visible ? (
    <Header
      style={{ padding: 0, width, zIndex: 2 }}
      className={fixedHeader ? styles.fixedHeader : ''}
    >
      {isTop && !isMobile ? (
        <TopNavHeader
          theme={navTheme}
          mode="horizontal"
          onCollapse={handleMenuCollapse}
          onNoticeClear={handleNoticeClear}
          onMenuClick={handleMenuClick}
          onNoticeVisibleChange={handleNoticeVisibleChange}
          {...props}
        />
      ) : (
        <GlobalHeader
          onCollapse={handleMenuCollapse}
          onNoticeClear={handleNoticeClear}
          onMenuClick={handleMenuClick}
          onNoticeVisibleChange={handleNoticeVisibleChange}
          {...props}
        />
      )}
    </Header>
  ) : null;

  return (
    <Animate component="" transitionName="fade">
      {HeaderDom}
    </Animate>
  );
};

export default connect(({ user, global, setting, loading }) => ({
  currentUser: user.currentUser,
  collapsed: global.collapsed,
  fetchingMoreNotices: loading.effects['global/fetchMoreNotices'],
  fetchingNotices: loading.effects['global/fetchNotices'],
  notices: global.notices,
  setting,
}))(HeaderView);
