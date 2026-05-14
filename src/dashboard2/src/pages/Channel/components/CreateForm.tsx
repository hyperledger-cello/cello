import { ProDescriptionsItemProps, ProTable } from "@ant-design/pro-components";
import { useIntl } from 'umi';
import { Modal } from "antd";
import { PropsWithChildren, useState } from 'react';
import { createChannel } from "@/services/channel/ChannelController";

interface Props {
  visible: boolean;
  onCancel: () => void;
}

const CreateForm: React.FC<PropsWithChildren<Props>> = (props) => {
  const [loading, handleLoading] = useState<boolean>(false);
  const { visible, onCancel } = props;
  const intl = useIntl();
  const columns: ProDescriptionsItemProps<ChannelAPI.CreationPayload>[] = [
    {
      title: intl.formatMessage({id: 'header.name',}),
      dataIndex: 'name',
      valueType: 'text',
      formItemProps: {
        rules: [
          {
            required: true,
            message: intl.formatMessage({id: 'validation.channel.name.required',}),
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
      <ProTable<ChannelAPI.CreationPayload>
        type="form"
        loading={loading}
        columns={columns}
        onSubmit={async (value) => {
          handleLoading(true);
          const success = await createChannel(value);
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
