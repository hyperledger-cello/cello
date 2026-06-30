const networkTypes = [{ name: 'Fabric', value: 'fabric' }];
const agentTypes = [{ name: 'Kubernetes', value: 'kubernetes' }];
const fabricVersions = [
  { name: '2.5.14', value: '2.5.14' },
  { name: '1.4.2', value: '1.4.2' },
];
const fabricNodeTypes = [
  { name: 'CA', value: 'ca' },
  { name: 'Peer', value: 'peer' },
  { name: 'Orderer', value: 'orderer' },
];

module.exports = {
  networkTypes,
  agentTypes,
  fabricVersions,
  fabricNodeTypes,
};
