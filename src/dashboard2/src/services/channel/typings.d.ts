declare namespace ChannelAPI {
  interface Info {
    id: string;
    name: string;
    created_at: string;
  }

  interface CreationPayload {
    name: string;
  }
}
