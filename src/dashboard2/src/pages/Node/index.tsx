import { PageContainer, ProDescriptionsItemProps, ProTable } from "@ant-design/pro-components";
import styles from './index.less';
import { useIntl } from 'umi';
import { queryNodeList } from "@/services/node/NodeController";

const NodeList: React.FC = () => {
  const intl = useIntl();
  const columns: ProDescriptionsItemProps<NodeAPI.Info>[] = [
    {
      title: intl.formatMessage({id: 'header.name',}),
      dataIndex: 'name',
      valueType: 'text',
    },
    {
      title: intl.formatMessage({id: 'header.type',}),
      dataIndex: 'type',
      valueType: 'text',
    },
    {
      title: intl.formatMessage({id: 'header.status',}),
      dataIndex: 'status',
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
        title: intl.formatMessage({id: 'menu.node',}),
        ghost: true,
        breadcrumb: {
          items: [
            {
              title: intl.formatMessage({id: 'home.title',}),
            },
            {
              title: intl.formatMessage({id: 'menu.node',}),
            },
          ],
        },
      }}
    >
      <div className={styles.container}>
        <ProTable<NodeAPI.Info>
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
            const { data } = await queryNodeList({...params});
            return {
              data: data?.data || [],
            }
          }}
        />
      </div>
    </PageContainer>
  );
};

export default NodeList;
