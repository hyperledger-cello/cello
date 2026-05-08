import { GlobalOutlined } from "@ant-design/icons";
import { SelectLang, useIntl } from '@umijs/max';

export default function CustomizedSelectLang() {
  const intl = useIntl();

  return (
    <SelectLang
      icon={
        <>
          <GlobalOutlined />
          <span className="lang-text">{intl.formatMessage({id: 'navBar.lang',})}</span>
        </>
      }
      reload={false}
    />
  );
}
