import { FunctionOutlined } from '@ant-design/icons';
import { ProDescriptionsItemProps, PageContainer, ProTable } from "@ant-design/pro-components";
import { useIntl } from 'umi';
import styles from './index.less'
import { queryChaincodeList } from '@/services/chaincode/ChaincodeController';

const ChaincodeList: React.FC = () => {
  const intl = useIntl();
  const columns: ProDescriptionsItemProps<ChaincodeAPI.Info>[] = [
    {
      title: intl.formatMessage({id: 'header.name',}),
      dataIndex: 'name',
      valueType: 'text',
    },
    {
      title: intl.formatMessage({id: 'header.status',}),
      dataIndex: 'status',
      valueType: 'text',
    },
    {
      title: intl.formatMessage({id: 'header.approvals',}),
      dataIndex: 'approvals',
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
          icon: <FunctionOutlined />
        },
        title: intl.formatMessage({id: 'menu.chaincode',}),
        breadcrumb: {
          items: [
            {
              title: intl.formatMessage({id: 'home.title',}),
            },
            {
              title: intl.formatMessage({id: 'menu.chaincode',}),
            },
          ],
        },
      }}
    >
      <div className={styles.container}>
        <ProTable<ChaincodeAPI.Info>
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
            const { data } = await queryChaincodeList({...params});
            return {
              data: data?.data || [],
            }
          }}
        />
      </div>
    </PageContainer>
  );
};

export default ChaincodeList;
