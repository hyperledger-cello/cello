import { PageContainer, ProDescriptionsItemProps, ProTable } from "@ant-design/pro-components";
import styles from './index.less';
import { useIntl } from 'umi';
import { queryChannelList } from "@/services/channel/ChannelController";
import { DeploymentUnitOutlined } from "@ant-design/icons";
import { useState } from "react";
import CreateForm from "./components/CreateForm";
import { Button } from "antd";

const ChannelList: React.FC = () => {
  const [createModalVisible, handleCreateModalVisible] = useState<boolean>(false);
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
      <ProTable<ChannelAPI.Info>
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
          const { data } = await queryChannelList({...params});
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

export default ChannelList;
