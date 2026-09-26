/*
 SPDX-License-Identifier: Apache-2.0
 */
/* eslint-disable no-continue */

export const COPILOT_CHAT_URL = '/api/v1/copilot/chat';

const getToken = () => window.localStorage.getItem('cello-token') || '';

// Uses raw fetch instead of customRequest/umi-request because the SSE endpoint
// is a POST with a Bearer token — umi-request wraps XHR and cannot return a
// ReadableStream. Token is read from localStorage to match the rest of the dashboard.
export const streamChat = async ({
  messages,
  signal,
  onToken,
  onToolCall,
  onToolResult,
  onError,
  onDone,
}) => {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(COPILOT_CHAT_URL, {
    method: 'POST',
    headers,
    body: JSON.stringify({ messages }),
    signal,
  });

  if (!response.ok) {
    let body = null;
    try {
      body = await response.json();
    } catch (_) {
      body = { msg: response.statusText };
    }
    const msg = body?.msg || body?.message || body?.detail || response.statusText;
    const err = new Error(msg);
    err.status = response.status;
    err.body = body;
    throw err;
  }

  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('text/event-stream')) {
    // Non-streaming fallback: backend returned single JSON object
    const data = await response.json();
    if (onDone) onDone(data);
    return data;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let currentEvent = null;
  let currentData = null;

  let donePayload = null;

  const dispatch = (event, data) => {
    if (event === 'token' && onToken) onToken(data);
    else if (event === 'tool_call' && onToolCall) onToolCall(data);
    else if (event === 'tool_result' && onToolResult) onToolResult(data);
    else if (event === 'done') {
      donePayload = data;
      if (onDone) onDone(data);
    } else if (event === 'error' && onError) onError(data);
  };

  // eslint-disable-next-line no-await-in-loop
  for (;;) {
    const { value, done } = await reader.read(); // eslint-disable-line no-await-in-loop
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split('\n');
    buffer = parts.pop() || '';

    // eslint-disable-next-line no-restricted-syntax
    for (const line of parts) {
      if (!line) {
        if (currentEvent && currentData !== null) {
          try {
            dispatch(currentEvent, JSON.parse(currentData));
          } catch (_) {
            dispatch(currentEvent, currentData);
          }
        }
        currentEvent = null;
        currentData = null;
        continue;
      }
      if (line.startsWith(':')) continue;
      if (line.startsWith('event:')) {
        currentEvent = line.slice(6).trim();
        continue;
      }
      if (line.startsWith('data:')) currentData = line.slice(5).trim();
    }
  }

  if (currentEvent && currentData !== null) {
    try {
      dispatch(currentEvent, JSON.parse(currentData));
    } catch (_) {
      dispatch(currentEvent, currentData);
    }
  }
  return donePayload;
};
