import React, { PureComponent, Fragment } from 'react';
import { Table, Alert } from 'antd';
import { injectIntl } from 'umi';
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

class StandardTable extends PureComponent {
  constructor(props) {
    super(props);
    const { columns } = props;
    const needTotalList = initTotalList(columns);

    this.state = {
      selectedRowKeys: [],
      needTotalList,
    };
  }

  static getDerivedStateFromProps(nextProps) {
    // clean state
    if (nextProps.selectedRows.length === 0) {
      const needTotalList = initTotalList(nextProps.columns);
      return {
        selectedRowKeys: [],
        needTotalList,
      };
    }
    return null;
  }

  handleRowSelectChange = (selectedRowKeys, selectedRows) => {
    let { needTotalList } = this.state;
    needTotalList = needTotalList.map(item => ({
      ...item,
      total: selectedRows.reduce((sum, val) => sum + parseFloat(val[item.dataIndex], 10), 0),
    }));
    const { onSelectRow } = this.props;
    if (onSelectRow) {
      onSelectRow(selectedRows);
    }

    this.setState({ selectedRowKeys, needTotalList });
  };

  handleTableChange = (pagination, filters, sorter) => {
    const { onChange } = this.props;
    if (onChange) {
      onChange(pagination, filters, sorter);
    }
  };

  cleanSelectedKeys = () => {
    this.handleRowSelectChange([], []);
  };

  render() {
    const { selectedRowKeys, needTotalList } = this.state;
    const { data = {}, disableSelect = false, rowKey, intl, ...rest } = this.props;
    const { list = [], pagination } = data;

    const paginationProps = {
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
    };

    const rowSelection = {
      selectedRowKeys,
      onChange: this.handleRowSelectChange,
      getCheckboxProps: record => ({
        disabled: record.disabled,
      }),
    };

    return (
      <div className={styles.standardTable}>
        {!disableSelect && (
          <div className={styles.tableAlert}>
            <Alert
              message={
                <Fragment>
                  {intl.formatMessage({
                    id: 'component.standardTable.selected',
                    defaultMessage: 'Selected',
                  })}
                  {' '}<a style={{ fontWeight: 600 }}>{selectedRowKeys.length}</a>{' '}
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
                  <a onClick={this.cleanSelectedKeys} style={{ marginLeft: 24 }}>
                    {intl.formatMessage({
                      id: 'component.standardTable.clean',
                      defaultMessage: 'Clean',
                    })}
                  </a>
                </Fragment>
              }
              type="info"
              showIcon
            />
          </div>
        )}
        <Table
          rowKey={rowKey || 'key'}
          rowSelection={!disableSelect && rowSelection}
          dataSource={list}
          pagination={paginationProps}
          onChange={this.handleTableChange}
          {...rest}
        />
      </div>
    );
  }
}

export default injectIntl(StandardTable);
