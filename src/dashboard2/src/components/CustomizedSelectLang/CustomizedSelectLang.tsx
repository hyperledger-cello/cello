import { GlobalOutlined } from "@ant-design/icons";
import styles from './CustomizedSelectLang.less'
import { SelectLang, useIntl } from '@umijs/max';
import { Button } from "antd";

export default function CustomizedSelectLang() {
  const intl = useIntl();

  return (
    <SelectLang
      icon={
        <Button
          className={styles.dropdown}
          type="text"
        >
          <GlobalOutlined />
          <span className="lang-text">{intl.formatMessage({id: 'navBar.lang',})}</span>
        </Button>
      }
      reload={false}
    />
  );
}
