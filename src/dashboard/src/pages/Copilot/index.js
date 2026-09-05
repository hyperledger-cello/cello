/*
 SPDX-License-Identifier: Apache-2.0
 */
import React, { useEffect, useRef, useState } from 'react';
import { connect, useIntl } from 'umi';
import { Card, Input, Button, Spin } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import PageHeaderWrapper from '@/components/PageHeaderWrapper';
import styles from './styles.less';

const Copilot = ({ dispatch, copilot = {} }) => {
  const intl = useIntl();
  const { messages = [], sending } = copilot;
  const [text, setText] = useState('');
  const listRef = useRef(null);

  useEffect(() => {
    if (listRef.current) {
      // eslint-disable-next-line no-param-reassign
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages.length, sending]);

  useEffect(() => () => dispatch({ type: 'copilot/clear' }), [dispatch]);

  const send = () => {
    if (!text.trim() || sending) return;
    dispatch({
      type: 'copilot/sendMessage',
      payload: text,
      callback: () => setText(''),
    });
  };

  const handleKeyDown = e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <PageHeaderWrapper
      title={intl.formatMessage({ id: 'copilot.title' })}
      content={intl.formatMessage({ id: 'copilot.subtitle' })}
    >
      <Card bordered={false} bodyStyle={{ padding: 0 }}>
        <div className={styles.panel}>
          <div className={styles.messages} ref={listRef}>
            {messages.length === 0 && !sending && (
              <div className={styles.empty}>
                <p className={styles.emptyTitle}>
                  {intl.formatMessage({ id: 'copilot.empty.title' })}
                </p>
                <p className={styles.emptyHint}>
                  {intl.formatMessage({ id: 'copilot.empty.hint' })}
                </p>
              </div>
            )}
            {messages.map(item => {
              if (item.role === 'assistant' && !item.content && !item.error && sending) return null;
              return (
                <div key={item.id} className={`${styles.row} ${styles[item.role]}`}>
                  <div
                    className={`${styles.bubble} ${styles[item.role]} ${
                      item.error ? styles.error : ''
                    }`}
                  >
                    {item.error ? intl.formatMessage({ id: 'copilot.error' }) : item.content}
                  </div>
                </div>
              );
            })}
            {sending && !messages[messages.length - 1]?.content && (
              <div className={`${styles.row} ${styles.assistant}`}>
                <div className={styles.bubble}>
                  <Spin size="small" />
                  <span className={styles.thinking}>
                    {intl.formatMessage({ id: 'copilot.thinking' })}
                  </span>
                </div>
              </div>
            )}
          </div>
          <div className={styles.inputRow}>
            <Input.TextArea
              value={text}
              onChange={e => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={intl.formatMessage({ id: 'copilot.input.placeholder' })}
              autoSize={{ minRows: 1, maxRows: 4 }}
              disabled={sending}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={send}
              loading={sending}
              disabled={!text.trim()}
            >
              {intl.formatMessage({ id: 'copilot.send' })}
            </Button>
          </div>
        </div>
      </Card>
    </PageHeaderWrapper>
  );
};

export default connect(({ copilot }) => ({ copilot }))(Copilot);
