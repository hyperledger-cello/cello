import { Component, Fragment } from 'react';
import { Link, connect } from 'umi';
import { Helmet } from 'react-helmet';
import GlobalFooter from '@/components/GlobalFooter';
import SelectLang from '@/components/SelectLang';
import getPageTitle from '@/utils/getPageTitle';
import styles from './UserLayout.less';

const links = [];

const copyright = <Fragment>Cello</Fragment>;

class UserLayout extends Component {
  componentDidMount() {
    const {
      dispatch,
      route: { routes, authority },
    } = this.props;
    dispatch({
      type: 'menu/getMenuData',
      payload: { routes, authority },
    });
  }

  render() {
    const {
      children,
      location: { pathname },
      breadcrumbNameMap,
    } = this.props;
    return (
      <>
        <Helmet>
          <title>{getPageTitle(pathname, breadcrumbNameMap)}</title>
        </Helmet>
        <div className={styles.container}>
          <div className={styles.lang}>
            <SelectLang />
          </div>
          <div className={styles.content}>
            <div className={styles.top}>
              <div className={styles.header}>
                <Link to="/">
                  <span className={styles.title}>Cello Dashboard</span>
                </Link>
              </div>
              <div className={styles.desc}>Dashboard for management cello service</div>
            </div>
            {children}
          </div>
          <GlobalFooter links={links} copyright={copyright} />
        </div>
      </>
    );
  }
}

export default connect(({ menu: menuModel }) => ({
  menuData: menuModel.menuData,
  breadcrumbNameMap: menuModel.breadcrumbNameMap,
}))(UserLayout);
