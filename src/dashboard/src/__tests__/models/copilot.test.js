/*
 SPDX-License-Identifier: Apache-2.0
 */
// eslint-disable-next-line import/no-extraneous-dependencies
import { call, put, select } from 'redux-saga/effects';

import model from '../../models/copilot';

const { effects, reducers } = model;
const CTX = { call, put, select };

describe('copilot model', () => {
  beforeEach(() => jest.clearAllMocks());

  it('has correct namespace and state shape', () => {
    expect(model.namespace).toBe('copilot');
    expect(model.state.messages).toEqual([]);
    expect(model.state.sending).toBe(false);
  });

  it('addMessage appends to the conversation', () => {
    const next = reducers.addMessage(model.state, {
      payload: { id: 'm1', role: 'user', content: 'hi' },
    });
    expect(next.messages).toEqual([{ id: 'm1', role: 'user', content: 'hi' }]);
  });

  it('appendToken creates assistant bubble when last is not assistant', () => {
    const next = reducers.appendToken(
      { messages: [], sending: false },
      { payload: { text: 'hi' } }
    );
    expect(next.messages[0].content).toBe('hi');
  });

  it('appendToken appends to last assistant bubble', () => {
    const state = { messages: [{ id: 'a1', role: 'assistant', content: 'hel' }], sending: true };
    const next = reducers.appendToken(state, { payload: { text: 'lo' } });
    expect(next.messages[0].content).toBe('hello');
  });

  it('failLast marks empty assistant as error', () => {
    const state = { messages: [{ id: 'a1', role: 'assistant', content: '' }], sending: true };
    const next = reducers.failLast(state);
    expect(next.messages[0].error).toBe(true);
  });

  it('setSending toggles the flag', () => {
    const next = reducers.setSending(model.state, { payload: true });
    expect(next.sending).toBe(true);
  });

  it('clear resets state', () => {
    const dirty = { messages: [{ id: 'm1' }], sending: true };
    expect(reducers.clear(dirty)).toEqual({ messages: [], sending: false });
  });

  it('sendMessage with empty text is a no-op callback', () => {
    const callback = jest.fn();
    const saga = effects.sendMessage({ payload: '   ', callback }, CTX);
    saga.next();
    expect(callback).toHaveBeenCalledWith({ status: 'ignored' });
    expect(saga.next().done).toBe(true);
  });

  it('sendMessagehappy path: user bubble, empty assistant, stream, done', () => {
    const callback = jest.fn();
    const saga = effects.sendMessage({ payload: 'list nodes', callback }, CTX);

    expect(saga.next().value.PUT.action.type).toBe('addMessage');
    expect(saga.next().value.PUT.action.type).toBe('setSending');
    expect(saga.next().value.PUT.action.type).toBe('addMessage');

    const selectStep = saga.next();
    expect('SELECT' in selectStep.value).toBe(true);

    const callStep = saga.next([
      { id: 'u1', role: 'user', content: 'list nodes' },
      { id: 'a1', role: 'assistant', content: '' },
    ]);
    expect('CALL' in callStep.value).toBe(true);

    // streamChat returns doneData — inject it via saga.next; saga checks doneData.reply
    const donePayload = { reply: 'Three peers found.', stop_reason: 'stop', tool_calls: [] };
    // doneData.reply exists so saga does a second SELECT to check last message content
    const selectStep2 = saga.next(donePayload);
    expect('SELECT' in selectStep2.value).toBe(true);

    // last message has content (tokens arrived), so dispatchAppend is skipped; callback fires, then finally put
    const afterStream = saga.next({
      messages: [{ role: 'assistant', content: 'Three peers found.' }],
    });
    expect(afterStream.value.PUT.action.type).toBe('setSending');
    expect(afterStream.value.PUT.action.payload).toBe(false);

    saga.next();
    expect(callback).toHaveBeenCalledWith(expect.objectContaining({ status: 'successful' }));
  });

  it('sendMessage failure marks error and clears sending', () => {
    const callback = jest.fn();
    const saga = effects.sendMessage({ payload: 'boom', callback }, CTX);

    saga.next();
    saga.next();
    saga.next();
    saga.next();

    const boom = new Error('upstream down');
    const failPut = saga.throw(boom);
    expect(failPut.value.PUT.action.type).toBe('failLast');

    const donePut = saga.next({ messages: [{ role: 'assistant', content: '' }] });
    expect(donePut.value.PUT.action.type).toBe('setSending');
    expect(donePut.value.PUT.action.payload).toBe(false);

    saga.next();
    expect(callback).toHaveBeenCalledWith(expect.objectContaining({ status: 'failed' }));
  });
});
