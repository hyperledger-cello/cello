import { useIntl } from '@umijs/max';
import { Avatar } from 'antd';
import styles from './HeaderRight.less'
import CustomizedSelectLang from '../CustomizedSelectLang/CustomizedSelectLang';

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
      <CustomizedSelectLang/>
    </>
  );
}
