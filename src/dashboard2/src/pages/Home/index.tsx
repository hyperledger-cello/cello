import { PageContainer } from '@ant-design/pro-components';
import { useIntl } from 'umi';
import styles from './index.less';
import { Layout, Row, Typography } from 'antd';

const HomePage: React.FC = () => {
  const intl = useIntl();
  return (
    <PageContainer
      header={{
        title: '',
        ghost: true,
        breadcrumb: {
          items: [
            {
              path: '',
              title: intl.formatMessage({id: 'home.title',}),
            },
          ],
        },
      }}
    >
      <div className={styles.container}>
        <Layout>
          <Row>
            <Typography.Title level={3} className={styles.title}>
              <strong>{intl.formatMessage({id: 'home.welcome.message',})}</strong>
            </Typography.Title>
          </Row>
        </Layout>
      </div>
    </PageContainer>
  );
};

export default HomePage;
