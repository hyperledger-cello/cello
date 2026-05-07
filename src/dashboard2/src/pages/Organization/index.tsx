import { PageContainer, ProDescriptionsItemProps, ProTable } from "@ant-design/pro-components";
import styles from './index.less';
import { useIntl } from 'umi';
import { queryOrganizationList } from "@/services/organization/OrganizationController";

const OrganizationList: React.FC = () => {
  const intl = useIntl();
  const columns: ProDescriptionsItemProps<OrganizationAPI.Info>[] = [
    {
      title: 'Name',
      dataIndex: 'name',
      valueType: 'text',
    }
  ];


  return (
    <PageContainer
      header={{
        title: intl.formatMessage({id: 'menu.organization',}),
        ghost: true,
        breadcrumb: {
          items: [
            {
              path: '',
              title: intl.formatMessage({id: 'home.title',}),
            },
            {
              path: 'organization',
              title: intl.formatMessage({id: 'menu.organization',}),
            },
          ],
        },
      }}
    >
      <div className={styles.container}>
        <ProTable<OrganizationAPI.Info>
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
      </div>
    </PageContainer>
  );
};

export default OrganizationList;
