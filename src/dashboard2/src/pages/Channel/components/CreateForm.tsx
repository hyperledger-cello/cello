import { ProDescriptionsItemProps, ProTable } from "@ant-design/pro-components";
import { useIntl } from 'umi';
import { Modal } from "antd";
import { PropsWithChildren } from 'react';
import { createChannel } from "@/services/channel/ChannelController";

interface Props {
  visible: boolean;
  onCancel: () => void;
}

const CreateForm: React.FC<PropsWithChildren<Props>> = (props) => {
  const { visible, onCancel } = props;
  const intl = useIntl();
  const columns: ProDescriptionsItemProps<ChannelAPI.CreationPayload>[] = [
    {
      title: intl.formatMessage({id: 'header.name',}),
      dataIndex: 'name',
      valueType: 'text',
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
      <ProTable<ChannelAPI.CreationPayload>
        type="form"
        columns={columns}
        onSubmit={async (value) => {
          const success = await createChannel(value);
          if (success) {
            onCancel();
          }
        }}
      />
    </Modal>
  );
};

export default CreateForm;
