import { PageContainer, ProDescriptionsItemProps, ProTable } from "@ant-design/pro-components";
import styles from './index.less';
import { useIntl } from 'umi';
import { queryNodeList } from "@/services/node/NodeController";
import { NodeIndexOutlined } from "@ant-design/icons";
import { Button } from "antd";
import { useState } from "react";
import CreateForm from "./components/CreateForm";

const NodeList: React.FC = () => {
  const [createModalVisible, handleCreateModalVisible] = useState<boolean>(false);
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
      valueEnum: {
        'PEER': {
          text: 'Peer',
        },
        'ORDERER': {
          text: 'Orderer',
        },
      },
    },
    {
      title: intl.formatMessage({id: 'header.status',}),
      dataIndex: 'status',
      valueType: 'text',
      valueEnum: {
        'running': {
          text: intl.formatMessage({id: 'app.node.running',}),
          status: 'success',
        },
        'paused': {
          text: intl.formatMessage({id: 'app.node.paused',}),
          status: 'warning',
        },
        'restarting': {
          text: intl.formatMessage({id: 'app.node.restarting',}),
          status: 'error',
        },
      },
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
          icon: <NodeIndexOutlined />
        },
        title: intl.formatMessage({id: 'menu.node',}),
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
      <ProTable<NodeAPI.Info>
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
          const { data } = await queryNodeList({...params});
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

export default NodeList;
