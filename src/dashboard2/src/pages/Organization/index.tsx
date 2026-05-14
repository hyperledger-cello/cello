import { PageContainer, ProDescriptionsItemProps, ProTable } from "@ant-design/pro-components";
import styles from './index.less';
import { useIntl } from 'umi';
import { queryOrganizationList } from "@/services/organization/OrganizationController";
import { TeamOutlined } from "@ant-design/icons";

const OrganizationList: React.FC = () => {
  const intl = useIntl();
  const columns: ProDescriptionsItemProps<OrganizationAPI.Info>[] = [
    {
      title: intl.formatMessage({id: 'header.name',}),
      dataIndex: 'name',
      valueType: 'text',
    },
    {
      title: intl.formatMessage({id: 'header.creation.timestamp',}),
      dataIndex: 'created_at',
      valueType: 'dateTime',
    }
  ];

  return (
    <PageContainer
      header={{
        avatar: {
          icon: <TeamOutlined />
        },
        title: intl.formatMessage({id: 'menu.organization',}),
        breadcrumb: {
          items: [
            {
              title: intl.formatMessage({id: 'menu.home',}),
            },
            {
              title: intl.formatMessage({id: 'menu.organization',}),
            },
          ],
        },
      }}
    >
      <ProTable<OrganizationAPI.Info>
        className={styles.container}
        rowKey="id"
        search={false}
        columns={columns}
        request={async (
          params: {
            page?: number;
            per_page?: number;
          }, 
          sorter, 
          filter
        ) => {
          const { data } = await queryOrganizationList({...params});
          return {
            data: data?.data || [],
          }
        }}
      />
    </PageContainer>
  );
};

export default OrganizationList;
