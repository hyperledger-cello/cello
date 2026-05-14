import { useIntl } from '@umijs/max';
import { Avatar } from 'antd';
import styles from './HeaderRight.less'
import CustomizedSelectLang from '../CustomizedSelectLang/CustomizedSelectLang';
import { quereyUserProfile } from '@/services/user/UserController';
import { useRequest } from '@umijs/max';

export default function HeaderRight() {
  const intl = useIntl();
  const { data, loading, error } = useRequest(quereyUserProfile);
  let content = '';

  if (loading) {
    content = 'loading...'
  } else if (data) {
    console.log(data);
    content = data.email;
  }

  return (
    <>
      <Avatar
        className={styles.avatar}
        style={{
          backgroundColor: 'rgba(255,255,255,0.25)'
        }}
        src="/avatar.png"
      />
      <span className={styles.avatar}>{content}</span>
      <CustomizedSelectLang/>
    </>
  );
}
