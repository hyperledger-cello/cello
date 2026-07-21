/*
 SPDX-License-Identifier: Apache-2.0
 */
import { stringify } from 'qs';

const mockCustomRequest = jest.fn();

jest.mock('../../utils/serviceFactory', () => ({
  customRequest: mockCustomRequest,
}));

const {
  listInvitation,
  getInvitation,
  createInvitation,
  signInvitation,
  acceptInvitation,
  rejectInvitation,
  cancelInvitation,
} = require('../../services/invitation');

describe('invitation service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('listInvitation builds a GET URL with channel id and pagination', () => {
    listInvitation({ channelId: 'c1', page: 1, per_page: 10 });
    expect(mockCustomRequest).toHaveBeenCalledTimes(1);
    expect(mockCustomRequest).toHaveBeenCalledWith(
      `/api/v1/channels/c1/invitations?${stringify({ page: 1, per_page: 10 })}`
    );
  });

  it('listInvitation omits undefined payload keys from the query string', () => {
    listInvitation({ channelId: 'c2' });
    expect(mockCustomRequest).toHaveBeenCalledWith('/api/v1/channels/c2/invitations?');
  });

  it('getInvitation builds a GET URL with channel and invitation id', () => {
    getInvitation({ channelId: 'c3', invitationId: 'i3' });
    expect(mockCustomRequest).toHaveBeenCalledWith('/api/v1/channels/c3/invitations/i3');
  });

  it('createInvitation issues a POST with body data', () => {
    createInvitation({
      channelId: 'c4',
      organization_names: ['org.a.example.com', 'org.b.example.com'],
      required_signatures: 2,
    });
    expect(mockCustomRequest).toHaveBeenCalledWith('/api/v1/channels/c4/invitations', {
      method: 'POST',
      data: {
        organization_names: ['org.a.example.com', 'org.b.example.com'],
        required_signatures: 2,
      },
    });
  });

  it('signInvitation targets the sign sub-path', () => {
    signInvitation({ channelId: 'c5', invitationId: 'i5' });
    expect(mockCustomRequest).toHaveBeenCalledWith('/api/v1/channels/c5/invitations/i5/sign', {
      method: 'POST',
    });
  });

  it('acceptInvitation targets the accept sub-path', () => {
    acceptInvitation({ channelId: 'c6', invitationId: 'i6' });
    expect(mockCustomRequest).toHaveBeenCalledWith('/api/v1/channels/c6/invitations/i6/accept', {
      method: 'POST',
    });
  });

  it('rejectInvitation targets the reject sub-path', () => {
    rejectInvitation({ channelId: 'c7', invitationId: 'i7' });
    expect(mockCustomRequest).toHaveBeenCalledWith('/api/v1/channels/c7/invitations/i7/reject', {
      method: 'POST',
    });
  });

  it('cancelInvitation targets the cancel sub-path', () => {
    cancelInvitation({ channelId: 'c8', invitationId: 'i8' });
    expect(mockCustomRequest).toHaveBeenCalledWith('/api/v1/channels/c8/invitations/i8/cancel', {
      method: 'POST',
    });
  });
});
