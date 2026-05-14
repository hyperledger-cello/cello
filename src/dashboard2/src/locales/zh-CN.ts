export default {
  // login page
  'navBar.lang': '语言',
  'navBar.logout': '注销',

  // message
  'message.error': '错误',
  'message.error.server': '伺服器错误。查看日志以获得更多资讯。',
  'message.success': '成功',
  'message.info': '说明',

  // login form
  'app.login.login': '登录',
  'app.login.email': '邮箱地址',
  'app.login.password': '密码',
  'app.login.error': '邮箱地址或密码错误',

  // register form
  'app.register.register': '注册组织',
  'app.register.orgName': '组织名称',
  'app.register.email': '管理员邮箱地址',
  'app.register.password': '管理员密码',
  'app.register.confirmPassword': '确认密码',
  'app.register.agentUrl': '代理地址',
  'app.register.error': '无效的组织信息',
  'app.register.success': '您已成功注册，请登入组织！',
  'app.register.info': '此注册功能仅用于创建新组织及其首位管理员账号。如果您的组织已完成注册，请联系组织管理员为您创建个人账号。',

  // validation
  'validation.email.required': '请输入邮箱地址！',
  'validation.password.required': '请输入密码！',
  'validation.orgName.required': '请输入组织名！',
  'validation.password.confirmed': '请确认密码！',
  'validation.password.different': '两次输入的密码不匹配！',
  'validation.agentUrl.required': '请输入代理地址！',
  'validation.agentUrl.format': '代理地址格式错误，必须以 http:// 或 https:// 开头！',

  // home page
  'home.welcome.message': '欢迎使用 Hyperledger Cello！',

  // page table
  'header.name': '名称',
  'header.creation.timestamp': '创建时间',
  'header.type': '类型',
  'header.status': '状态',
  'header.approvals': '通道组织批准数量',
  'header.creation': '新建',
  'header.operations': '操作',

  // side bar and title
  'menu.login': '登录',
  'menu.home': '首页',
  'menu.organization': '组织管理',
  'menu.node': '节点管理',
  'menu.channel': '通道管理',
  'menu.chaincode': '链码管理',
  'menu.docs': '线上文档',

  // node page
  'app.node.running': '运行中',
  'app.node.paused': '已停止',
  'app.node.restarting': '重启中',
  'app.node.exited': '未启动',
  'validation.node.type.required': '请输入节点类型！',
  'validation.node.name.required': '请输入节点名称!',

  // channel page
  'validation.channel.name.required': '请输入通道名称！',

  // chaincode page
  'app.chaincode.package.label': '链码包',
  'app.chaincode.package.title': '仅支持 .tar.gz 文件',
  'app.chaincode.version': '版本',
  'app.chaincode.sequence': '序列号',
  'app.chaincode.init-required': '是否需要初始化？',
  'app.chaincode.signature-policy': '签署政策',
  'app.chaincode.channel': '通道',
  'app.chaincode.description': '描述',
  'app.chaincode.created': '已建立',
  'app.chaincode.installed': '已安装',
  'app.chaincode.approved': '已批准',
  'app.chaincode.committed': '已提交',
  'app.chaincode.install': '安装',
  'app.chaincode.approve': '批准',
  'app.chaincode.commit': '提交',
};
