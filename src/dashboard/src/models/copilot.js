/*
 SPDX-License-Identifier: Apache-2.0
 */
import { streamChat } from '@/services/copilot';

const makeId = () =>
  `${Date.now()}-${Math.random()
    .toString(36)
    .slice(2, 8)}`;

// Cannot yield put() from inside the onToken callback because the saga is
// suspended at yield call() when tokens arrive. Direct store dispatch is the
// standard dva workaround for streaming callbacks.
const dispatchAppend = text => {
  if (!text) return;
  try {
    // eslint-disable-next-line global-require
    const { getDvaApp } = require('umi');
    const app = getDvaApp();
    // eslint-disable-next-line no-underscore-dangle
    if (app && app._store) app._store.dispatch({ type: 'copilot/appendToken', payload: { text } });
  } catch (_) {
    // outside umi context (tests)
  }
};

export default {
  namespace: 'copilot',

  state: {
    messages: [],
    sending: false,
  },

  reducers: {
    addMessage(state, { payload }) {
      return { ...state, messages: [...state.messages, payload] };
    },
    appendToken(state, { payload }) {
      const text = payload?.text ?? '';
      if (!text) return state;
      const messages = [...state.messages];
      const last = messages[messages.length - 1];
      if (last && last.role === 'assistant' && !last.error) {
        messages[messages.length - 1] = { ...last, content: (last.content || '') + text };
      } else {
        messages.push({ id: makeId(), role: 'assistant', content: text });
      }
      return { ...state, messages };
    },
    failLast(state) {
      const messages = [...state.messages];
      const last = messages[messages.length - 1];
      if (last && last.role === 'assistant' && !last.content && !last.error) {
        messages[messages.length - 1] = { ...last, error: true };
        return { ...state, messages };
      }
      return {
        ...state,
        messages: [...messages, { id: makeId(), role: 'assistant', content: '', error: true }],
      };
    },
    setSending(state, { payload }) {
      return { ...state, sending: payload };
    },
    clear() {
      return { messages: [], sending: false };
    },
  },

  effects: {
    *sendMessage({ payload, callback }, { call, put, select }) {
      const text = (payload || '').trim();
      if (!text) {
        if (callback) callback({ status: 'ignored' });
        return;
      }

      yield put({ type: 'addMessage', payload: { id: makeId(), role: 'user', content: text } });
      yield put({ type: 'setSending', payload: true });
      yield put({ type: 'addMessage', payload: { id: makeId(), role: 'assistant', content: '' } });

      let streamErr = null;

      try {
        const history = yield select(s => s.copilot.messages);
        const messages = history
          .filter(m => !(m.role === 'assistant' && !m.content && !m.error))
          .map(m => ({ role: m.role, content: m.content }));

        const doneData = yield call(() =>
          streamChat({
            messages,
            onToken: data => {
              const chunk = typeof data === 'string' ? data : data?.text ?? '';
              dispatchAppend(chunk);
            },
            onError: data => {
              streamErr = data;
            },
          })
        );

        if (streamErr) throw new Error(streamErr.message || streamErr.msg || 'stream error');

        if (!doneData) throw new Error('stream closed without a done event');

        if (doneData.reply) {
          const cur = yield select(s => s.copilot);
          const last = cur.messages[cur.messages.length - 1];
          if (!last?.content) dispatchAppend(doneData.reply);
        }

        if (callback) callback({ status: 'successful', data: doneData });
      } catch (err) {
        yield put({ type: 'failLast' });
        if (callback) callback({ status: 'failed', error: err });
      } finally {
        yield put({ type: 'setSending', payload: false });
      }
    },
  },
};
