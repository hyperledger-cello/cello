import { useIntl, history, useRequest } from '@umijs/max';
import { Avatar, Button, Dropdown } from 'antd';
import styles from './HeaderRight.less'
import CustomizedSelectLang from '../CustomizedSelectLang/CustomizedSelectLang';
import { quereyUserProfile } from '@/services/user/UserController';

export default function HeaderRight() {
  const intl = useIntl();
  let content = '';
  if (location.pathname != '/login') {
    const { data, loading, error } = useRequest(quereyUserProfile);
    if (loading) {
      content = 'loading...'
    } else if (data) {
      content = data.email;
    }
  }

  return (
    <>
      <CustomizedSelectLang/>
      <Dropdown
        className={styles.dropdown}
        trigger={['hover']}
        menu={{
          items: [
            { key: 'logout', label: intl.formatMessage({id: 'navBar.logout'}) },
          ],
          onClick: (_) => {
            localStorage.removeItem('token');
            history.push('/login');
          }
        }}
      >
        <Button
          type='text'
        >
          <Avatar
            style={{
              backgroundColor: 'rgba(255,255,255,0.25)'
            }}
            src='/avatar.png'
          />
          <span>{content}</span>
        </Button>
      </Dropdown>
    </>
  );
}
