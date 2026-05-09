declare namespace ChaincodeAPI {
  interface Info {
    id: string;
    name: string;
    version: string;
    sequence: number;
    init_required: boolean;
    signature_policy: string;
    package_id: string;
    label: string;
    language: string;
    created_at: string;
    description: string;
    status: string;
    approvals: string;
  }
}
