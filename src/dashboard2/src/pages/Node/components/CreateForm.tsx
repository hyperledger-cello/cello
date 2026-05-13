import { ProDescriptionsItemProps, ProTable } from "@ant-design/pro-components";
import styles from '../index.less';
import { useIntl } from 'umi';
import { Modal } from "antd";
import { PropsWithChildren } from 'react';
import { createNode } from "@/services/node/NodeController";

interface Props {
  visible: boolean;
  onCancel: () => void;
}

const CreateForm: React.FC<PropsWithChildren<Props>> = (props) => {
  const { visible, onCancel } = props;
  const intl = useIntl();
  const columns: ProDescriptionsItemProps<NodeAPI.CreationPayload>[] = [
    {
      title: intl.formatMessage({id: 'header.type',}),
      dataIndex: 'type',
      valueType: 'select',
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
      title: intl.formatMessage({id: 'header.name',}),
      dataIndex: 'name',
      valueType: 'text',
    },
  ];

  return (
    <Modal
      title={intl.formatMessage({id: 'app.node.creation',})}
      width={420}
      open={visible}
      onCancel={onCancel}
      footer={null}
    >
      <ProTable<NodeAPI.CreationPayload>
        type="form"
        columns={columns}
        onSubmit={async (value) => {
          const success = await createNode(value);
          if (success) {
            onCancel();
          }
        }}
      />
    </Modal>
  );
};

export default CreateForm;
