export const dva = {
  config: {
    onError(err) {
      err.preventDefault();
    },
  },
};

export function render(oldRender) {
  oldRender();
  // runtime 自動註冊 models（支援使用 createModel(...) 的檔案）
  // umi 提供 getDvaApp 與 require.context（webpack）
  // eslint-disable-next-line global-require
  const { getDvaApp } = require('umi');
  const app = typeof getDvaApp === 'function' ? getDvaApp() : null;

  if (!app) {
    // dva 尚未就緒或 plugin 未啟用
    return;
  }

  // 使用 webpack 的 require.context 來載入 src/models 下的所有 .js/.ts/.tsx 檔案
  let req;
  try {
    req = require.context('./models', true, /\.(j|t)sx?$/);
  } catch (e) {
    // 若環境不支援 require.context（極少見），直接結束
    return;
  }

  req.keys().forEach(key => {
    const mod = req(key);
    const m = mod && (mod.default || mod); // 支援 default export 或 module.exports
    if (!m || !m.namespace) {
      // skip 非 model 檔或未正確 export 的檔案
      return;
    }

    // eslint-disable-next-line no-underscore-dangle
    const exists = (app._models || []).some(mm => mm.namespace === m.namespace);
    if (!exists) {
      app.model(m);
    }
  });
}
