/*
 SPDX-License-Identifier: Apache-2.0
 */
import React from 'react';

jest.mock('umi', () => ({
  connect: () => component => component,
  useIntl: () => ({ formatMessage: ({ defaultMessage }) => defaultMessage }),
  history: { push: jest.fn(), replace: jest.fn() },
}));

jest.mock('@/components/PageHeaderWrapper', () => ({ children }) => <>{children}</>);
jest.mock('@/components/StandardTable', () => {
  const FakeTable = () => null;
  return FakeTable;
});
jest.mock('@/hooks', () => ({
  useTableManagement: () => ({
    selectedRows: [],
    handleSelectRows: () => {},
    handleTableChange: () => {},
    refreshList: () => {},
  }),
}));
jest.mock('../../pages/Channel/forms/CreateInvitationForm', () => () => null);

const { badgeStatusMap, computeRecordFlags } = require('../../pages/Channel/Invitation');

describe('badgeStatusMap', () => {
  it('maps DRAFT to default', () => expect(badgeStatusMap.DRAFT).toBe('default'));
  it('maps SIGNING to processing', () => expect(badgeStatusMap.SIGNING).toBe('processing'));
  it('maps READY to success', () => expect(badgeStatusMap.READY).toBe('success'));
  it('maps ACCEPTED to success', () => expect(badgeStatusMap.ACCEPTED).toBe('success'));
  it('maps REJECTED to error', () => expect(badgeStatusMap.REJECTED).toBe('error'));
  it('maps FAILED to error', () => expect(badgeStatusMap.FAILED).toBe('error'));
  it('maps CANCELED to default', () => expect(badgeStatusMap.CANCELED).toBe('default'));
});

describe('computeRecordFlags', () => {
  const ctxBase = { currentOrgId: 'orgMe', isChannelMember: true };
  const recordBase = overrides => ({
    id: 'inv1',
    status: 'DRAFT',
    creator_organization: { id: 'orgMe' },
    invitees: [],
    signatures: [],
    ...overrides,
  });

  it('channel member can sign DRAFT', () => {
    expect(computeRecordFlags(recordBase({ status: 'DRAFT' }), ctxBase).canSign).toBe(true);
  });

  it('channel member can sign SIGNING', () => {
    expect(computeRecordFlags(recordBase({ status: 'SIGNING' }), ctxBase).canSign).toBe(true);
  });

  it('channel member cannot sign READY', () => {
    expect(computeRecordFlags(recordBase({ status: 'READY' }), ctxBase).canSign).toBe(false);
  });

  it('non-member cannot sign', () => {
    expect(computeRecordFlags(recordBase({}), { ...ctxBase, isChannelMember: false }).canSign).toBe(
      false
    );
  });

  it('channel member can cancel DRAFT/SIGNING/READY/FAILED', () => {
    ['DRAFT', 'SIGNING', 'READY', 'FAILED'].forEach(s =>
      expect(computeRecordFlags(recordBase({ status: s }), ctxBase).canCancel).toBe(true)
    );
  });

  it('channel member cannot cancel ACCEPTED/REJECTED/CANCELED', () => {
    ['ACCEPTED', 'REJECTED', 'CANCELED'].forEach(s =>
      expect(computeRecordFlags(recordBase({ status: s }), ctxBase).canCancel).toBe(false)
    );
  });

  it('pending invitee can cancel when READY', () => {
    const record = recordBase({
      status: 'READY',
      invitees: [{ organization: { id: 'orgMe' }, status: 'PENDING' }],
    });
    expect(
      computeRecordFlags(record, { currentOrgId: 'orgMe', isChannelMember: false }).canCancel
    ).toBe(true);
  });

  it('pending invitee can accept/reject only when READY', () => {
    const record = recordBase({
      status: 'READY',
      invitees: [{ organization: { id: 'orgMe' }, status: 'PENDING' }],
    });
    const flags = computeRecordFlags(record, {
      currentOrgId: 'orgMe',
      isChannelMember: false,
    });
    expect(flags.canAccept).toBe(true);
    expect(flags.canReject).toBe(true);
  });

  it('invitee cannot accept/reject before READY', () => {
    const record = recordBase({
      status: 'SIGNING',
      invitees: [{ organization: { id: 'orgMe' }, status: 'PENDING' }],
    });
    const flags = computeRecordFlags(record, ctxBase);
    expect(flags.canAccept).toBe(false);
    expect(flags.canReject).toBe(false);
  });

  it('non-pending invitee cannot accept again', () => {
    const record = recordBase({
      status: 'READY',
      invitees: [{ organization: { id: 'orgMe' }, status: 'ACCEPTED' }],
    });
    expect(computeRecordFlags(record, ctxBase).canAccept).toBe(false);
  });

  it('unrelated organization has no actions', () => {
    const record = recordBase({
      status: 'READY',
      invitees: [{ organization: { id: 'other' }, status: 'PENDING' }],
      creator_organization: { id: 'other' },
    });
    const flags = computeRecordFlags(record, {
      currentOrgId: 'bystander',
      isChannelMember: false,
    });
    expect(flags.canSign).toBe(false);
    expect(flags.canCancel).toBe(false);
    expect(flags.canAccept).toBe(false);
    expect(flags.canReject).toBe(false);
  });
});
