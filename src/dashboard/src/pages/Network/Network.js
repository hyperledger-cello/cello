/*
 SPDX-License-Identifier: Apache-2.0
*/
import React, { Fragment, useEffect } from 'react';
import { connect, history, useIntl } from 'umi';
import { Card, Button, Divider } from 'antd';
import { PlusOutlined, ApartmentOutlined } from '@ant-design/icons';
import moment from 'moment';
import PageHeaderWrapper from '@/components/PageHeaderWrapper';
import StandardTable from '@/components/StandardTable';
import { useDeleteConfirm, useTableManagement } from '@/hooks';
import styles from './styles.less';

const Network = ({ dispatch, network = {}, loadingNetworks }) => {
  const intl = useIntl();
  const { networks = [], pagination = {} } = network;

  const {
    selectedRows,
    handleSelectRows,
    handleTableChange,
    refreshList,
    clearSelectedRows,
  } = useTableManagement({
    dispatch,
    listAction: 'network/listNetwork',
  });
  const { showDeleteConfirm } = useDeleteConfirm({ dispatch, intl });

  useEffect(() => {
    dispatch({ type: 'network/listNetwork' });
    // Preserve original unmount behavior (re-query on unmount)
    return () => {
      dispatch({ type: 'network/listNetwork' });
    };
  }, [dispatch]);

  const newNetwork = () => {
    history.push('/network/newNetwork');
  };

  const handleDeleteNetwork = record => {
    showDeleteConfirm({
      record,
      deleteAction: 'network/deleteNetwork',
      titleId: 'app.network.form.delete.title',
      contentId: 'app.network.form.delete.content',
      successId: 'app.network.delete.success',
      failId: 'app.network.delete.fail',
      onSuccess: () => {
        clearSelectedRows();
        refreshList();
      },
    });
  };

  const columns = [
    {
      title: intl.formatMessage({
        id: 'app.network.table.header.name',
        defaultMessage: 'Network Name',
      }),
      dataIndex: 'name',
    },
    {
      title: intl.formatMessage({
        id: 'app.network.table.header.creationTime',
        defaultMessage: 'Create Time',
      }),
      dataIndex: 'created_at',
      render: text => <span>{moment(text).format('YYYY-MM-DD HH:mm:ss')}</span>,
    },
    {
      title: intl.formatMessage({
        id: 'form.table.header.operation',
        defaultMessage: 'Operation',
      }),
      render: (text, record) => (
        <Fragment>
          <a>{intl.formatMessage({ id: 'form.menu.item.update', defaultMessage: 'Update' })}</a>
          <Divider type="vertical" />
          <a className={styles.danger} onClick={() => handleDeleteNetwork(record)}>
            {intl.formatMessage({ id: 'form.menu.item.delete', defaultMessage: 'Delete' })}
          </a>
        </Fragment>
      ),
    },
  ];

  return (
    <PageHeaderWrapper
      title={
        <span>
          <ApartmentOutlined style={{ marginRight: 15 }} />
          {intl.formatMessage({
            id: 'app.network.title',
            defaultMessage: 'Network Management',
          })}
        </span>
      }
    >
      <Card bordered={false}>
        <div className={styles.tableList}>
          <div className={styles.tableListOperator}>
            <Button type="primary" onClick={newNetwork}>
              <PlusOutlined />
              {intl.formatMessage({ id: 'form.button.new', defaultMessage: 'New' })}
            </Button>
          </div>
          <StandardTable
            selectedRows={selectedRows}
            loading={loadingNetworks}
            rowKey="id"
            data={{
              list: networks,
              pagination,
            }}
            columns={columns}
            onSelectRow={handleSelectRows}
            onChange={handleTableChange}
          />
        </div>
      </Card>
    </PageHeaderWrapper>
  );
};

export default connect(({ network, loading }) => ({
  network,
  loadingNetworks: loading.effects['network/listNetwork'],
}))(Network);
