/*
 SPDX-License-Identifier: Apache-2.0
 */
import React, { useEffect, useMemo } from 'react';
import { connect, useIntl, history } from 'umi';
import { Card, Row, Col, List, Button, Empty } from 'antd';
import { DeploymentUnitOutlined, MailOutlined, EditOutlined } from '@ant-design/icons';
import PageHeaderWrapper from '@/components/PageHeaderWrapper';

const StatCard = ({ icon, title, value, color, onClick }) => (
  <Card hoverable={!!onClick} onClick={onClick} bodyStyle={{ padding: 20 }}>
    <div style={{ display: 'flex', alignItems: 'center' }}>
      <div
        style={{
          width: 48,
          height: 48,
          borderRadius: 8,
          background: color || '#1890ff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginRight: 16,
          fontSize: 22,
          color: '#fff',
        }}
      >
        {icon}
      </div>
      <div>
        <div style={{ fontSize: 14, color: '#8c8c8c' }}>{title}</div>
        <div style={{ fontSize: 28, fontWeight: 600 }}>{value}</div>
      </div>
    </div>
  </Card>
);

const Overview = ({ dispatch, channel = {}, user = {} }) => {
  const intl = useIntl();
  const { channels = [] } = channel;
  const { currentUser = {} } = user;

  useEffect(() => {
    dispatch({ type: 'channel/listChannel' });
    dispatch({ type: 'user/fetchCurrent' });
  }, [dispatch]);

  const currentOrgName =
    currentUser && currentUser.organization ? currentUser.organization.name : '';

  const channelCount = channels.length;

  const greeting = useMemo(() => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  }, []);

  return (
    <PageHeaderWrapper
      title={intl.formatMessage({
        id: 'overview.title',
        defaultMessage: 'User Overview',
      })}
    >
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ marginBottom: 4 }}>
          {greeting}, {currentUser.username || currentUser.email || 'User'}
        </h2>
        <span style={{ color: '#8c8c8c' }}>
          {currentOrgName && `Organization: ${currentOrgName}`}
          {currentUser.role && ` · Role: ${currentUser.role}`}
        </span>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            icon={<DeploymentUnitOutlined />}
            title={intl.formatMessage({
              id: 'overview.stat.channels',
              defaultMessage: 'Channels',
            })}
            value={channelCount}
            color="#1890ff"
            onClick={() => history.push('/channel')}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            icon={<MailOutlined />}
            title={intl.formatMessage({
              id: 'overview.stat.invitations',
              defaultMessage: 'Invitations',
            })}
            value={intl.formatMessage({
              id: 'overview.stat.invitations.manage',
              defaultMessage: 'Manage',
            })}
            color="#722ed1"
            onClick={() => history.push('/channel/invitation')}
          />
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={12}>
          <Card
            title={
              <span>
                <DeploymentUnitOutlined style={{ marginRight: 8 }} />
                {intl.formatMessage({
                  id: 'overview.channels.title',
                  defaultMessage: 'Your Channels',
                })}
              </span>
            }
            extra={
              <a onClick={() => history.push('/channel')}>
                {intl.formatMessage({
                  id: 'overview.channels.viewAll',
                  defaultMessage: 'View All',
                })}
              </a>
            }
          >
            {channels.length === 0 ? (
              <Empty
                description={intl.formatMessage({
                  id: 'overview.channels.empty',
                  defaultMessage: 'No channels yet',
                })}
              />
            ) : (
              <List
                size="small"
                dataSource={channels.slice(0, 5)}
                renderItem={ch => (
                  <List.Item
                    actions={[
                      <a
                        key="inv"
                        onClick={() => history.push(`/channel/invitation?channel=${ch.id}`)}
                      >
                        {intl.formatMessage({
                          id: 'app.channel.table.row.invitations',
                          defaultMessage: 'Invitations',
                        })}
                      </a>,
                    ]}
                  >
                    <List.Item.Meta
                      avatar={<DeploymentUnitOutlined style={{ fontSize: 20, color: '#1890ff' }} />}
                      title={ch.name}
                      description={`${(ch.organizations || []).length} member(s)`}
                    />
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card
            title={
              <span>
                <EditOutlined style={{ marginRight: 8 }} />
                {intl.formatMessage({
                  id: 'overview.quickActions.title',
                  defaultMessage: 'Quick Actions',
                })}
              </span>
            }
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <Button
                type="default"
                icon={<MailOutlined />}
                block
                onClick={() => history.push('/channel/invitation')}
              >
                {intl.formatMessage({
                  id: 'overview.quickActions.manageInvitations',
                  defaultMessage: 'Manage Channel Invitations',
                })}
              </Button>
              <Button
                type="default"
                icon={<DeploymentUnitOutlined />}
                block
                onClick={() => history.push('/channel')}
              >
                {intl.formatMessage({
                  id: 'overview.quickActions.viewChannels',
                  defaultMessage: 'View Channels',
                })}
              </Button>
            </div>
          </Card>
        </Col>
      </Row>
    </PageHeaderWrapper>
  );
};

export default connect(({ channel, user }) => ({
  channel,
  user,
}))(Overview);
