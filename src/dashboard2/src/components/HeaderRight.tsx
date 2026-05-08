import { GlobalOutlined } from '@ant-design/icons';
import { SelectLang } from '@umijs/max';
import { useIntl } from '@umijs/max';
import { Avatar } from 'antd';
import styles from './HeaderRight.less'

export default function HeaderRight() {
  const intl = useIntl();

  return (
    <>
      <Avatar
        className={styles.avatar}
        style={{
          backgroundColor: 'rgba(255,255,255,0.25)'
        }}
        src="/avatar.png"
      />
      <span className={styles.avatar}>email</span>
      <SelectLang
          icon={
              <>
                  <GlobalOutlined />
                  <span className="lang-text">{intl.formatMessage({id: 'navBar.lang',})}</span>
              </>
          }
          reload={false}
      />
    </>
  );
}
