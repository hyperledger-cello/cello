import React, { useState, useCallback, useEffect, useMemo } from 'react';
import { Table, Alert } from 'antd';
import { useIntl } from 'umi';
import styles from './index.less';

function initTotalList(columns) {
  const totalList = [];
  columns.forEach(column => {
    if (column.needTotal) {
      totalList.push({ ...column, total: 0 });
    }
  });
  return totalList;
}

const StandardTable = ({
  data = {},
  columns = [],
  selectedRows = [],
  disableSelect = false,
  rowKey = 'key',
  onSelectRow,
  onChange,
  ...rest
}) => {
  const intl = useIntl();
  const { list = [], pagination } = data;

  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [needTotalList, setNeedTotalList] = useState(() => initTotalList(columns));

  // Handle selectedRows changes from parent (equivalent to getDerivedStateFromProps)
  useEffect(() => {
    if (selectedRows.length === 0) {
      setSelectedRowKeys([]);
      setNeedTotalList(initTotalList(columns));
    }
  }, [selectedRows.length, columns]);

  const handleRowSelectChange = useCallback(
    (keys, rows) => {
      const updatedTotalList = needTotalList.map(item => ({
        ...item,
        total: rows.reduce((sum, val) => sum + parseFloat(val[item.dataIndex], 10), 0),
      }));

      setSelectedRowKeys(keys);
      setNeedTotalList(updatedTotalList);

      if (onSelectRow) {
        onSelectRow(rows);
      }
    },
    [needTotalList, onSelectRow]
  );

  const handleTableChange = useCallback(
    (paginationConfig, filters, sorter) => {
      if (onChange) {
        onChange(paginationConfig, filters, sorter);
      }
    },
    [onChange]
  );

  const cleanSelectedKeys = useCallback(() => {
    handleRowSelectChange([], []);
  }, [handleRowSelectChange]);

  const paginationProps = useMemo(
    () => ({
      showSizeChanger: true,
      showQuickJumper: true,
      showTotal: (total, range) =>
        intl.formatMessage(
          {
            id: 'component.standardTable.showTotal',
            defaultMessage: '{start}-{end} of {total} items',
          },
          {
            start: range[0],
            end: range[1],
            total,
          }
        ),
      ...pagination,
    }),
    [intl, pagination]
  );

  const rowSelection = useMemo(
    () => ({
      selectedRowKeys,
      onChange: handleRowSelectChange,
      getCheckboxProps: record => ({
        disabled: record.disabled,
      }),
    }),
    [selectedRowKeys, handleRowSelectChange]
  );

  return (
    <div className={styles.standardTable}>
      {!disableSelect && (
        <div className={styles.tableAlert}>
          <Alert
            message={
              <>
                {intl.formatMessage({
                  id: 'component.standardTable.selected',
                  defaultMessage: 'Selected',
                })}{' '}
                <a style={{ fontWeight: 600 }}>{selectedRowKeys.length}</a>{' '}
                {intl.formatMessage({
                  id: 'component.standardTable.item',
                  defaultMessage: 'Item',
                })}
                &nbsp;&nbsp;
                {needTotalList.map(item => (
                  <span style={{ marginLeft: 8 }} key={item.dataIndex}>
                    {item.title}
                    {intl.formatMessage({
                      id: 'component.standardTable.total',
                      defaultMessage: 'Total',
                    })}{' '}
                    &nbsp;
                    <span style={{ fontWeight: 600 }}>
                      {item.render ? item.render(item.total) : item.total}
                    </span>
                  </span>
                ))}
                <a onClick={cleanSelectedKeys} style={{ marginLeft: 24 }}>
                  {intl.formatMessage({
                    id: 'component.standardTable.clean',
                    defaultMessage: 'Clean',
                  })}
                </a>
              </>
            }
            type="info"
            showIcon
          />
        </div>
      )}
      <Table
        rowKey={rowKey}
        rowSelection={!disableSelect ? rowSelection : undefined}
        dataSource={list}
        pagination={paginationProps}
        onChange={handleTableChange}
        columns={columns}
        {...rest}
      />
    </div>
  );
};

export default StandardTable;
