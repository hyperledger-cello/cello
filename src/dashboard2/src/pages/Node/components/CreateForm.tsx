import { ProDescriptionsItemProps, ProTable } from "@ant-design/pro-components";
import { useIntl } from 'umi';
import { Modal } from "antd";
import { PropsWithChildren, useState } from 'react';
import { createNode } from "@/services/node/NodeController";

interface Props {
  visible: boolean;
  onCancel: () => void;
}

const CreateForm: React.FC<PropsWithChildren<Props>> = (props) => {
  const [loading, handleLoading] = useState<boolean>(false);
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
      formItemProps: {
        rules: [
          {
            required: true,
            message: intl.formatMessage({id: 'validation.node.type.required',}),
          },
        ],
      },
    },
    {
      title: intl.formatMessage({id: 'header.name',}),
      dataIndex: 'name',
      valueType: 'text',
      formItemProps: {
        rules: [
          {
            required: true,
            message: intl.formatMessage({id: 'validation.node.name.required',}),
          },
        ],
      },
    },
  ];

  return (
    <Modal
      title={intl.formatMessage({id: 'header.creation',})}
      width={420}
      open={visible}
      onCancel={onCancel}
      footer={null}
    >
      <ProTable<NodeAPI.CreationPayload>
        type="form"
        loading={loading}
        columns={columns}
        onSubmit={async (value) => {
          handleLoading(true);
          const success = await createNode(value);
          handleLoading(false);
          if (success) {
            onCancel();
          }
        }}
      />
    </Modal>
  );
};

export default CreateForm;
