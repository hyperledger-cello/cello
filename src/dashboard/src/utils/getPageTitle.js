import { pathToRegexp } from 'path-to-regexp';
import isEqual from 'lodash/isEqual';
import memoizeOne from 'memoize-one';
import { menu, title } from '../defaultSettings';

export const matchParamsPath = (pathname, breadcrumbNameMap) => {
  const pathKey = Object.keys(breadcrumbNameMap).find(key => {
    const { regexp } = pathToRegexp(key);
    return regexp.test(pathname);
  });

  return breadcrumbNameMap[pathKey];
};

const getPageTitle = (pathname, breadcrumbNameMap, intl) => {
  const currRouterData = matchParamsPath(pathname, breadcrumbNameMap);
  if (!currRouterData) {
    return title;
  }

  // If intl is provided, use it for formatting; otherwise fall back to name
  const pageName =
    menu.disableLocal || !intl
      ? currRouterData.name
      : intl.formatMessage({
          id: currRouterData.locale || currRouterData.name,
          defaultMessage: currRouterData.name,
        });

  return `${pageName} - ${title}`;
};

export default memoizeOne(getPageTitle, isEqual);
