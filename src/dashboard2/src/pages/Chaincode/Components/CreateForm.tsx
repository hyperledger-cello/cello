import { ProForm, ProFormDigit, ProFormSelect, ProFormSwitch, ProFormText, ProFormUploadButton } from "@ant-design/pro-components";
import { useIntl } from 'umi';
import { Modal } from "antd";
import { PropsWithChildren } from 'react';
import { createChaincode } from "@/services/chaincode/ChaincodeController";
import { queryChannelList } from "@/services/channel/ChannelController";

interface Props {
  visible: boolean;
  onCancel: () => void;
}

const CreateForm: React.FC<PropsWithChildren<Props>> = (props) => {
  const { visible, onCancel } = props;
  const intl = useIntl();

  return (
    <Modal
      title={intl.formatMessage({id: 'header.creation',})}
      width={420}
      open={visible}
      onCancel={onCancel}
      footer={null}
    >
      <ProForm
        style={{
          background: '#31596e',
          paddingInline: '16px'
        }}
        onFinish={async (values) => {
          const success = await createChaincode(values);
          if (success) {
            onCancel();
          }
          return true;
        }}
      >
        <ProFormUploadButton
          name="package"
          label={intl.formatMessage({id: 'app.chaincode.package.label',})}
          title={intl.formatMessage({id: 'app.chaincode.package.title',})}
          max={1}
          rules={[
            { required: true },
          ]}
          fieldProps={{
            beforeUpload: () => false,
          }}
        />
        <ProFormText
          name="name"
          label={intl.formatMessage({id: 'header.name',})}
          rules={[
            { required: true },
          ]}
        />
        <ProFormText
          name="version"
          label={intl.formatMessage({id: 'app.chaincode.version',})}
          rules={[
            { required: true },
          ]}
        />
        <ProFormDigit
          name="sequence"
          label={intl.formatMessage({id: 'app.chaincode.sequence',})}
          rules={[
            { required: true },
          ]}
        />
        <ProFormSwitch
          name="init-required"
          label={intl.formatMessage({id: 'app.chaincode.init-required',})}
        />
        <ProFormText
          name="signature-policy"
          label={intl.formatMessage({id: 'app.chaincode.signature-policy',})}
        />
        <ProFormSelect
          name="channel"
          label={intl.formatMessage({id: 'app.chaincode.channel',})}
          request={async () => {
            const res = await queryChannelList({page: 1, per_page: 10}).then(r => r.data.data);
            return res.map((item: any) => ({
              label: item.name,
              value: item.id,
            }));
          }}
          rules={[
            { required: true },
          ]}
        />
        <ProFormText
          name="description"
          label={intl.formatMessage({id: 'app.chaincode.description',})}
        />
      </ProForm>
    </Modal>
  );
};

export default CreateForm;
