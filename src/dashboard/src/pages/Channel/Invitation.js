/*
 SPDX-License-Identifier: Apache-2.0
 */
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { connect, useIntl, history } from 'umi';
import { Card, Select, Button, Badge, Tooltip, Popconfirm, message } from 'antd';
import { PlusOutlined, DeploymentUnitOutlined } from '@ant-design/icons';
import PageHeaderWrapper from '@/components/PageHeaderWrapper';
import StandardTable from '@/components/StandardTable';
import { useTableManagement } from '@/hooks';
import CreateInvitationForm from './forms/CreateInvitationForm';
import styles from './styles.less';

const { Option } = Select;

const CANCELABLE_STATUSES = ['DRAFT', 'SIGNING', 'READY', 'FAILED'];

export const badgeStatusMap = {
  DRAFT: 'default',
  SIGNING: 'processing',
  READY: 'success',
  ACCEPTED: 'success',
  REJECTED: 'error',
  FAILED: 'error',
  CANCELED: 'default',
};

export const computeRecordFlags = (record, ctx) => {
  const { currentOrgId, isChannelMember } = ctx;
  const invitees = record.invitees || [];
  const isInviteePending = invitees.some(
    inv => inv.organization && inv.organization.id === currentOrgId && inv.status === 'PENDING'
  );
  const status = record.status;
  const cancelable = CANCELABLE_STATUSES.includes(status);
  return {
    canSign: isChannelMember && (status === 'DRAFT' || status === 'SIGNING'),
    canCancel: cancelable && (isChannelMember || isInviteePending),
    canAccept: isInviteePending && status === 'READY',
    canReject: isInviteePending && status === 'READY',
  };
};

const Invitation = ({
  dispatch,
  invitation = {},
  channel = {},
  user = {},
  loadingInvitations,
  creating,
}) => {
  const intl = useIntl();
  const { invitations = [], pagination = {} } = invitation;
  const { channels = [] } = channel;
  const { currentUser = {} } = user;

  const { selectedRows, handleSelectRows, handleTableChange, refreshList } = useTableManagement({
    dispatch,
    listAction: 'invitation/listInvitation',
  });

  const [channelId, setChannelId] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [operatingId, setOperatingId] = useState(null);
  const [operationType, setOperationType] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.hash.split('?')[1] || '');
    const q = params.get('channel');
    if (q) setChannelId(q);
  }, []);

  useEffect(() => {
    dispatch({ type: 'channel/listChannel' });
    dispatch({ type: 'user/fetchCurrent' });
    return () => {
      dispatch({ type: 'invitation/clear' });
    };
  }, [dispatch]);

  useEffect(() => {
    if (channelId) {
      dispatch({
        type: 'invitation/listInvitation',
        payload: { channelId },
      });
    }
  }, [channelId, dispatch]);

  const fetchInvitations = useCallback(() => {
    if (channelId) {
      refreshList({ channelId });
    }
  }, [channelId, refreshList]);

  const currentOrgId = currentUser && currentUser.organization ? currentUser.organization.id : null;

  const selectedChannel = useMemo(() => channels.find(c => c.id === channelId) || {}, [
    channels,
    channelId,
  ]);

  const memberOrgIds = useMemo(() => (selectedChannel.organizations || []).map(o => o.id), [
    selectedChannel,
  ]);

  const isChannelMember = useMemo(() => !!currentOrgId && memberOrgIds.includes(currentOrgId), [
    currentOrgId,
    memberOrgIds,
  ]);

  const canInvite = isChannelMember;

  const handleModalVisible = useCallback(visible => {
    setModalVisible(!!visible);
  }, []);

  const onCreate = useCallback(() => {
    setModalVisible(true);
  }, []);

  const handleCreate = useCallback(
    (values, callback) => {
      dispatch({
        type: 'invitation/createInvitation',
        payload: values,
        callback,
      });
    },
    [dispatch]
  );

  const runAction = useCallback(
    (actionType, record, successMsgId, successDefault, failMsgId, failDefault) => {
      setOperatingId(record.id);
      setOperationType(actionType);
      dispatch({
        type: `invitation/${actionType}Invitation`,
        payload: { channelId, invitationId: record.id },
        callback: response => {
          setOperatingId(null);
          setOperationType(null);
          const okStatus =
            response && response.status && response.status.toLowerCase() === 'successful';
          if (okStatus) {
            message.success(
              intl.formatMessage({ id: successMsgId, defaultMessage: successDefault })
            );
            fetchInvitations();
          } else {
            message.error(intl.formatMessage({ id: failMsgId, defaultMessage: failDefault }));
          }
        },
      });
    },
    [channelId, dispatch, fetchInvitations, intl]
  );

  const handleSign = useCallback(
    record =>
      runAction(
        'sign',
        record,
        'app.channel.invitation.action.sign.success',
        'Sign invitation succeed',
        'app.channel.invitation.action.sign.fail',
        'Sign invitation failed'
      ),
    [runAction]
  );

  const handleAccept = useCallback(
    record =>
      runAction(
        'accept',
        record,
        'app.channel.invitation.action.accept.success',
        'Accept invitation succeed',
        'app.channel.invitation.action.accept.fail',
        'Accept invitation failed'
      ),
    [runAction]
  );

  const handleReject = useCallback(
    record =>
      runAction(
        'reject',
        record,
        'app.channel.invitation.action.reject.success',
        'Reject invitation succeed',
        'app.channel.invitation.action.reject.fail',
        'Reject invitation failed'
      ),
    [runAction]
  );

  const handleCancel = useCallback(
    record =>
      runAction(
        'cancel',
        record,
        'app.channel.invitation.action.cancel.success',
        'Cancel invitation succeed',
        'app.channel.invitation.action.cancel.fail',
        'Cancel invitation failed'
      ),
    [runAction]
  );

  const recordFlags = useCallback(
    record =>
      computeRecordFlags(record, {
        currentOrgId,
        isChannelMember,
      }),
    [currentOrgId, isChannelMember]
  );

  const columns = [
    {
      title: intl.formatMessage({
        id: 'app.channel.invitation.table.header.channel',
        defaultMessage: 'Channel',
      }),
      dataIndex: ['channel', 'id'],
      render: channelIdVal => {
        const ch = channels.find(c => c.id === channelIdVal);
        return ch ? ch.name : channelIdVal;
      },
    },
    {
      title: intl.formatMessage({
        id: 'app.channel.invitation.table.header.status',
        defaultMessage: 'Status',
      }),
      dataIndex: 'status',
      render: status => {
        const badgeStatus = badgeStatusMap[status] || 'default';
        const statusId = `app.channel.invitation.status.${status.toLowerCase()}`;
        const statusDefault = status.charAt(0) + status.slice(1).toLowerCase();
        return (
          <Badge
            status={badgeStatus}
            text={intl.formatMessage({
              id: statusId,
              defaultMessage: statusDefault,
            })}
          />
        );
      },
    },
    {
      title: intl.formatMessage({
        id: 'app.channel.invitation.table.header.signatures',
        defaultMessage: 'Signatures',
      }),
      render: (text, record) => {
        const signed = (record.signatures || []).length;
        const required = record.required_signatures || 0;
        if (signed === 0) {
          return `${signed}/${required}`;
        }
        const signerNames = record.signatures.map(s => s.organization.name).join(', ');
        return (
          <Tooltip title={signerNames}>
            <span>
              {signed}/{required}
            </span>
          </Tooltip>
        );
      },
    },
    {
      title: intl.formatMessage({
        id: 'app.channel.invitation.table.header.invitees',
        defaultMessage: 'Invitees',
      }),
      render: (text, record) => {
        const invitees = record.invitees || [];
        if (invitees.length === 0) {
          return 0;
        }
        const inviteeInfo = invitees
          .map(inv => `${inv.organization.name} (${inv.status.toLowerCase()})`)
          .join(', ');
        return (
          <Tooltip title={inviteeInfo}>
            <span>{invitees.length}</span>
          </Tooltip>
        );
      },
    },
    {
      title: intl.formatMessage({
        id: 'app.channel.invitation.table.header.created',
        defaultMessage: 'Created',
      }),
      dataIndex: 'created_at',
      render: ts => (ts ? new Date(ts).toLocaleString() : '-'),
    },
    {
      title: intl.formatMessage({
        id: 'form.table.header.operation',
        defaultMessage: 'Operation',
      }),
      render: (text, record) => {
        const flags = recordFlags(record);
        const isOperating = operatingId === record.id;

        return (
          <div>
            {flags.canSign && (
              <a
                onClick={() => !isOperating && handleSign(record)}
                style={
                  isOperating && operationType === 'sign'
                    ? { opacity: 0.6, cursor: 'not-allowed', marginRight: 8 }
                    : { cursor: 'pointer', marginRight: 8 }
                }
              >
                {isOperating && operationType === 'sign'
                  ? intl.formatMessage({
                      id: 'app.channel.invitation.action.sign.progress',
                      defaultMessage: 'Signing...',
                    })
                  : intl.formatMessage({
                      id: 'app.channel.invitation.action.sign',
                      defaultMessage: 'Sign',
                    })}
              </a>
            )}
            {flags.canAccept && (
              <a
                onClick={() => !isOperating && handleAccept(record)}
                style={
                  isOperating && operationType === 'accept'
                    ? { opacity: 0.6, cursor: 'not-allowed', marginRight: 8 }
                    : { cursor: 'pointer', marginRight: 8 }
                }
              >
                {isOperating && operationType === 'accept'
                  ? intl.formatMessage({
                      id: 'app.channel.invitation.action.accept.progress',
                      defaultMessage: 'Accepting...',
                    })
                  : intl.formatMessage({
                      id: 'app.channel.invitation.action.accept',
                      defaultMessage: 'Accept',
                    })}
              </a>
            )}
            {flags.canReject && (
              <a
                style={{ marginRight: 8, color: '#ff4d4f' }}
                onClick={() => !isOperating && handleReject(record)}
              >
                {intl.formatMessage({
                  id: 'app.channel.invitation.action.reject',
                  defaultMessage: 'Reject',
                })}
              </a>
            )}
            {flags.canCancel && (
              <Popconfirm
                title={intl.formatMessage({
                  id: 'app.channel.invitation.action.cancel.confirm',
                  defaultMessage: 'Cancel this invitation?',
                })}
                onConfirm={() => !isOperating && handleCancel(record)}
              >
                <a style={{ color: '#ff4d4f' }}>
                  {isOperating && operationType === 'cancel'
                    ? intl.formatMessage({
                        id: 'app.channel.invitation.action.cancel.progress',
                        defaultMessage: 'Canceling...',
                      })
                    : intl.formatMessage({
                        id: 'app.channel.invitation.action.cancel',
                        defaultMessage: 'Cancel',
                      })}
                </a>
              </Popconfirm>
            )}
            {record.status === 'FAILED' && record.error_message && (
              <Tooltip title={record.error_message}>
                <a style={{ marginLeft: 8, color: '#faad14' }}>
                  {intl.formatMessage({
                    id: 'app.channel.invitation.action.errorInfo',
                    defaultMessage: 'Error',
                  })}
                </a>
              </Tooltip>
            )}
            {!flags.canSign &&
              !flags.canAccept &&
              !flags.canReject &&
              !flags.canCancel &&
              record.status !== 'FAILED' && <span style={{ color: '#bbb' }}>-</span>}
          </div>
        );
      },
    },
  ];

  const formProps = useMemo(
    () => ({
      modalVisible,
      handleCreate,
      handleModalVisible,
      fetchInvitations,
      creating,
      channelId,
      memberOrgIds,
    }),
    [
      modalVisible,
      handleCreate,
      handleModalVisible,
      fetchInvitations,
      creating,
      channelId,
      memberOrgIds,
    ]
  );

  return (
    <PageHeaderWrapper
      title={
        <span>
          <DeploymentUnitOutlined style={{ marginRight: 15 }} />
          {intl.formatMessage({
            id: 'app.channel.invitation.title',
            defaultMessage: 'Channel Invitations',
          })}
        </span>
      }
    >
      <Card bordered={false}>
        <div className={styles.tableList}>
          <div className={styles.tableListOperator}>
            <span style={{ marginRight: 16 }}>
              {intl.formatMessage({
                id: 'app.channel.invitation.selectChannel',
                defaultMessage: 'Channel',
              })}
              :
            </span>
            <Select
              style={{ width: 240, marginRight: 16 }}
              placeholder={intl.formatMessage({
                id: 'app.channel.invitation.selectChannelPlaceholder',
                defaultMessage: 'Select a channel',
              })}
              value={channelId || undefined}
              onChange={v => {
                setChannelId(v);
                history.push(`/channel/invitation?channel=${v}`);
              }}
              showSearch
              optionFilterProp="children"
            >
              {channels.map(c => (
                <Option value={c.id} key={c.id}>
                  {c.name}
                </Option>
              ))}
            </Select>
            {canInvite && (
              <Button type="primary" onClick={onCreate} disabled={!channelId}>
                <PlusOutlined />
                {intl.formatMessage({
                  id: 'app.channel.invitation.button.invite',
                  defaultMessage: 'Invite',
                })}
              </Button>
            )}
          </div>
          <StandardTable
            selectedRows={selectedRows}
            loading={loadingInvitations}
            rowKey="id"
            data={{
              list: invitations,
              pagination,
            }}
            columns={columns}
            onSelectRow={handleSelectRows}
            onChange={handleTableChange}
          />
        </div>
      </Card>
      <CreateInvitationForm {...formProps} />
    </PageHeaderWrapper>
  );
};

export default connect(({ invitation, channel, user, loading }) => ({
  invitation,
  channel,
  user,
  loadingInvitations: loading.effects['invitation/listInvitation'],
  creating: loading.effects['invitation/createInvitation'],
}))(Invitation);
