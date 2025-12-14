import React, { PureComponent } from 'react';
import { injectIntl } from 'umi';
import PageHeaderWrapper from '@/components/PageHeaderWrapper';

class Index extends PureComponent {
  render() {
    const { intl } = this.props;
    return (
      <PageHeaderWrapper>
        {intl.formatMessage({
          id: 'overview.title',
          defaultMessage: 'User Overview',
        })}
        <h1 style={{ textAlign: 'center' }}>
          {intl.formatMessage({
            id: 'overview.welcome.message',
            defaultMessage: 'Welcome!',
          })}
        </h1>
      </PageHeaderWrapper>);
  }
}

export default injectIntl(Index);
