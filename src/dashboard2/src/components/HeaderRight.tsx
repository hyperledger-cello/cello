import { GlobalOutlined } from '@ant-design/icons';
import { SelectLang } from '@umijs/max';
import { useIntl } from '@umijs/max';

export default function HeaderRight() {
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
