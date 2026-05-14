import { FunctionOutlined } from '@ant-design/icons';
import { ProDescriptionsItemProps, PageContainer, ProTable } from "@ant-design/pro-components";
import { useIntl } from 'umi';
import styles from './index.less'
import { queryChaincodeList } from '@/services/chaincode/ChaincodeController';
import { useState } from 'react';
import { Button } from 'antd';
import CreateForm from './Components/CreateForm';

const ChaincodeList: React.FC = () => {
  const [createModalVisible, handleCreateModalVisible] = useState<boolean>(false);
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
      valueEnum: {
        'CREATED': {
          text: intl.formatMessage({id: 'app.chaincode.created',}),
          status: 'default',
        },
        'INSTALLED': {
          text: intl.formatMessage({id: 'app.chaincode.installed',}),
          status: 'processing',
        },
        'APPROVED': {
          text: intl.formatMessage({id: 'app.chaincode.approved',}),
          status: 'processing',
        },
        'COMMITTED': {
          text: intl.formatMessage({id: 'app.chaincode.committed',}),
          status: 'success'
        }
      },
    },
    {
      title: intl.formatMessage({id: 'header.approvals',}),
      dataIndex: 'approvals',
      valueType: 'text',
      render: (obj: any) => {
        const total = Object.keys(obj).length;
        const trueCount = Object.values(obj).filter(v => v).length;
        return `${total}/${trueCount}`;
      },
    },
    {
      title: intl.formatMessage({id: 'header.creation.timestamp',}),
      dataIndex: 'created_at',
      valueType: 'dateTime',
    },
    {
      title: intl.formatMessage({id: 'header.operations',}),
      valueType: 'option',
      render: (_, record) => {
        const status = record.status;
        if (status == 'COMMITTED') {
          return null;
        } else if (status == 'APPROVED') {
          return (
            <Button
              type='link'
            >
              {intl.formatMessage({id: 'app.chaincode.commit',})}
            </Button>
          );
        } else if (status == 'INSTALLED') {
          return (
            <Button>
              {intl.formatMessage({id: 'app.chaincode.approve',})}
            </Button>
          );
        } else {
          return (
            <Button>
              {intl.formatMessage({id: 'app.chaincode.install',})}
            </Button>
          );
        }
      },
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
      <ProTable<ChaincodeAPI.Info>
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
          const { data } = await queryChaincodeList({...params});
          return {
            data: data?.data || [],
          }
        }}
        toolBarRender={() => [
          <Button
            key="1"
            type="primary"
            onClick={() => handleCreateModalVisible(true)}
          >
            {intl.formatMessage({id: 'header.creation',})}
          </Button>,
        ]}
      />
      <CreateForm
        visible={createModalVisible}
        onCancel={() => handleCreateModalVisible(false)}
      />
    </PageContainer>
  );
};

export default ChaincodeList;
