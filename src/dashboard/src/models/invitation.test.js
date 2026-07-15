/*
 SPDX-License-Identifier: Apache-2.0
 */
// redux-saga is a transitive dependency of dva — available at runtime
// eslint-disable-next-line import/no-extraneous-dependencies
import { call, put, select } from 'redux-saga/effects';

import model from './invitation';

const { effects, reducers } = model;
const CTX = { call, put, select };

describe('invitation model', () => {
  beforeEach(() => jest.clearAllMocks());

  it('has correct namespace and state shape', () => {
    expect(model.namespace).toBe('invitation');
    expect(model.state.invitations).toEqual([]);
    expect(model.state.currentInvitation).toEqual({});
    expect(model.state.pagination).toBeDefined();
  });

  it('reducer save merges payload into state', () => {
    const initial = model.state;
    const next = reducers.save(initial, { payload: { invitations: [{ id: 'x' }] } });
    expect(next.invitations).toEqual([{ id: 'x' }]);
    expect(next.currentInvitation).toEqual({});
  });

  it('reducer clear resets state to initial', () => {
    const initial = model.state;
    const next = reducers.clear(initial);
    expect(next.invitations).toEqual([]);
    expect(next.currentInvitation).toEqual({});
  });

  it('listInvitation yields call(listInvitationService, payload) then select then put then callback', () => {
    const callback = jest.fn();
    const saga = effects.listInvitation({ payload: { channelId: 'c1' }, callback }, CTX);

    const callStep = saga.next();
    expect('CALL' in callStep.value).toBe(true);

    const selectStep = saga.next({ data: { total: 5, data: [{ id: 'inv1' }] } });
    expect('SELECT' in selectStep.value).toBe(true);

    const putStep = saga.next({ current: 1, pageSize: 10 });
    expect('PUT' in putStep.value).toBe(true);
    expect(putStep.value.PUT.action.payload.invitations).toEqual([{ id: 'inv1' }]);
    expect(putStep.value.PUT.action.payload.pagination).toMatchObject({ total: 5 });

    const final = saga.next();
    expect(callback).toHaveBeenCalled();
    expect(final.done).toBe(true);
  });

  it('createInvitation yields call(createInvitationService, payload) then callback', () => {
    const callback = jest.fn();
    const payload = { channelId: 'c3', organization_ids: ['o1'], required_signatures: 1 };
    const saga = effects.createInvitation({ payload, callback }, CTX);

    const callStep = saga.next();
    expect('CALL' in callStep.value).toBe(true);

    saga.next({ status: 'successful' });
    expect(callback).toHaveBeenCalledWith({ status: 'successful' });
  });

  it('signInvitation yields call then callback', () => {
    const callback = jest.fn();
    const saga = effects.signInvitation(
      { payload: { channelId: 'c4', invitationId: 'i4' }, callback },
      CTX
    );
    expect('CALL' in saga.next().value).toBe(true);
    saga.next({ status: 'successful' });
    expect(callback).toHaveBeenCalledWith({ status: 'successful' });
  });

  it('acceptInvitation yields call then callback', () => {
    const callback = jest.fn();
    const saga = effects.acceptInvitation(
      { payload: { channelId: 'c5', invitationId: 'i5' }, callback },
      CTX
    );
    expect('CALL' in saga.next().value).toBe(true);
    saga.next({ status: 'successful' });
    expect(callback).toHaveBeenCalledWith({ status: 'successful' });
  });

  it('rejectInvitation yields call then callback', () => {
    const callback = jest.fn();
    const saga = effects.rejectInvitation(
      { payload: { channelId: 'c6', invitationId: 'i6' }, callback },
      CTX
    );
    expect('CALL' in saga.next().value).toBe(true);
    saga.next({ status: 'successful' });
    expect(callback).toHaveBeenCalledWith({ status: 'successful' });
  });

  it('cancelInvitation yields call then callback', () => {
    const callback = jest.fn();
    const saga = effects.cancelInvitation(
      { payload: { channelId: 'c7', invitationId: 'i7' }, callback },
      CTX
    );
    expect('CALL' in saga.next().value).toBe(true);
    saga.next({ status: 'successful' });
    expect(callback).toHaveBeenCalledWith({ status: 'successful' });
  });
});
