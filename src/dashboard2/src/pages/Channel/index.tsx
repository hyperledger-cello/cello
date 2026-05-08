import { PageContainer, ProDescriptionsItemProps, ProTable } from "@ant-design/pro-components";
import styles from './index.less';
import { useIntl } from 'umi';
import { queryChannelList } from "@/services/channel/ChannelController";
import { DeploymentUnitOutlined } from "@ant-design/icons";

const ChannelList: React.FC = () => {
  const intl = useIntl();
  const columns: ProDescriptionsItemProps<ChannelAPI.Info>[] = [
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
          icon: <DeploymentUnitOutlined />
        },
        title: intl.formatMessage({id: 'menu.channel',}),
        breadcrumb: {
          items: [
            {
              title: intl.formatMessage({id: 'home.title',}),
            },
            {
              title: intl.formatMessage({id: 'menu.channel',}),
            },
          ],
        },
      }}
    >
      <div className={styles.container}>
        <ProTable<ChannelAPI.Info>
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
            const { data } = await queryChannelList({...params});
            return {
              data: data?.data || [],
            }
          }}
        />
      </div>
    </PageContainer>
  );
};

export default ChannelList;
