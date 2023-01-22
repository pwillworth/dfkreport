var BASE_SCRIPT_URL = '/';
var HARMONY_TOKENS = {
  '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F': 'Jewel',
  '0xA9cE83507D872C5e1273E745aBcfDa849DAA654F': 'xJewels',
  '0x985458E523dB3d53125813eD68c274899e9DfAb4': '1USDC',
  '0xcF664087a5bB0237a0BAd6742852ec6c8d69A27a': 'ONE',
  '0xb12c13e66AdE1F72f71834f2FC5082Db8C091358': 'wAVAX',
  '0x53BA62dDD5a9A6B6d97C7a496D7832D13A9218c4': 'rAVAX',
  '0xDA7fE71960cd1C19E1b86D6929efD36058F60a03': 'wLumen',
  '0x95CE547D730519A90dEF30d647F37D9E5359B6Ae': 'wLUNA',
  '0xFbdd194376de19a88118e84E279b977f165d01b8': 'wMATIC',
  '0x9b68BF4bF89c115c721105eaf6BD5164aFcc51E4': 'Freyala',
  '0x7BF379FcB16b4a6F648371cD72D9D443EF24168F': 'Amethyst',
  '0xD74433B187Cf0ba998Ad9Be3486B929c76815215': 'Artemis',
  '0x3cebA57a1AA15A35a4A29a9E067D4AE441dE779F': 'Babymis',
  '0xCf1709Ad76A79d5a60210F23e81cE2460542A836': 'Tranquil',
  '0xB4aA8c8e555b3A2F1BFd04234FF803C011760E59': 'xTranq',
  '0xB55106308974CEbe299A0f0505435C47b404b9a6': 'Eden',
  '0x0159ED2E06DDCD46a25E74eb8e159Ce666B28687': 'FOX',
  '0xED0B4b0F0E2c17646682fc98ACe09feB99aF3adE': 'RVRS',
  '0x17fDEdda058d43fF1615cdb72a40Ce8704C2479A': '1SUPERBID',
  '0x44aFdBe2Cb42cc18759159f7E383afb0Ca8E57aD': 'SmugDoge',
  '0xBCF532871415Bc6e3D147d777C6ad3e68E50cd92': 'PartyHat',
  '0x7ca9C1D0bb11F1b7C31ee5538D7a75aAF2d8E2FC': 'CryptoPigs',
  '0x8Eb03202275bD598AdC23678008eF88655544910': 'Radiant',
  '0x5903720f0132E8bd48530010d9b3192B25F51D8e': 'PASTA',
  '0x3E018675c0Ef63eB361b9EF4bfEa3A3294C74C7b': 'KuroShiba',
  '0xd009b07B4a65CC769379875Edc279961D710362d': 'RAIN',
  '0x1e05C8B69e4128949FcEf16811a819eF2f55D33E': 'SONIC',
  '0x224e64ec1BDce3870a6a6c777eDd450454068FEC': 'wUST',
  '0x3C2B8Be99c50593081EAA2A724F0B8285F5aba8f': '1USDT',
  '0xE176EBE47d621b984a73036B9DA5d834411ef734': 'Binance USD',
  '0xb1f6E61E1e113625593a22fa6aa94F8052bc39E0': 'bscBNB',
  '0x0aB43550A6915F9f67d0c454C2E90385E6497EaA': 'bscBUSD',
  '0x44cED87b9F1492Bf2DCf5c16004832569f7f6cBa': 'bscUSDC',
  '0x3F56e0c36d275367b8C502090EDF38289b3dEa0d': 'MAI',
  '0x6983D1E6DEf3690C4d616b13597A09e6193EA013': '1ETH',
  '0x3095c7557bCb296ccc6e363DE01b760bA031F2d9': 'wBTC',
  '0xdc54046c0451f9269FEe1840aeC808D36015697d': '1BTC',
  '0x735aBE48e8782948a37C7765ECb76b98CdE97B0F': 'Fantom',
  '0x39aB439897380eD10558666C4377fACB0322Ad48': '1FTM',
  '0x14A7B318fED66FfDcc80C1517C172c13852865De': '1AXS',
  '0xA5445d24E5dbF641f76058CD7a95b1c402Eb97b5': 'bscTLM',
  '0x2A719aF848bf365489E548BE5edbEC1D65858e59': 'Fira',
  '0x690f506C7FB8e76d61C077Ca75341a6F8AC37Ed5': 'sFira',
  '0x22D62b19b7039333ad773b7185BB61294F3AdC19': 'stONE',
  '0x892D81221484F690C0a97d3DD18B9144A3ECDFB7': 'MAGIC',
  '0xf390830DF829cf22c53c8840554B98eafC5dCBc2': 'anyJewel',
  '0x3405A1bd46B85c5C029483FbECf2F3E611026e45': 'anyMAI',
  '0x093956649D43f23fe4E7144fb1C3Ad01586cCf1e': 'Jewel LP Token AVAX/Jewel',
  '0xEb579ddcD49A7beb3f205c9fF6006Bb6390F138f': 'Jewel LP Token ONE/Jewel',
  '0xFdAB6B23053E22b74f21ed42834D7048491F8F32': 'Jewel LP Token ONE/xJewel',
  '0x66C17f5381d7821385974783BE34c9b31f75Eb78': 'Jewel LP Token ONE/1USDC',
  '0x3733062773B24F9bAfa1e8f2e5A352976f008A95': 'Jewel LP Token XYA/Jewel',
  '0xc74eaf04777F784A7854e8950daEb27559111b85': 'Jewel LP Token XYA/ONE',
  '0x61356C852632813f3d71D57559B06cdFf70E538B': 'Jewel LP Token ONE/UST',
  '0xb91A0dFA0178500FEDC526f26A89803C387772E8': 'Jewel LP Token Jewel/UST',
  '0xf0504847fDbe0AEFaB006EA002BfC1CFe20d8985': 'Jewel LP Token ONE/1USDT',
  '0xf33ee94922326d7C1d220298Cc9428A1Fd15dAea': 'Jewel LP Token LUMEN/Jewel',
  '0xB6e9754b90b338ccB2a74fA31de48ad89f65ec5e': 'Jewel LP Token Luna/Jewel',
  '0x7f89b5F33138C89FAd4092a7C079973C95362D53': 'Jewel LP Token Fantom/Jewel',
  '0x3E81154912E5E2Cc9B10Ad123BF14aeb93aE5318': 'Jewel LP Toekn wMatic/Jewel',
  '0x751606585FcAa73bf92Cf823b7b6D8A0398a1c99': 'Jewel LP Token MIS/Jewel',
  '0x60e0d939D4b0C71918088278bCf600470A6c8f26': 'Jewel LP Token ONE/MIS',
  '0xfB1b4457f78E4A5b985118D6b96626F9874F400c': 'Jewel LP Token ONE/bMIS',
  '0xC593893ED4b5F97CB64808c640E48B18A80E61Ff': 'Jewel LP Token MIS/COINKX',
  '0xE01502Db14929b7733e7112E173C3bCF566F996E': 'Jewel LP Token BUSD/Jewel',
  '0x0AcCE15D05B4BA4dBEdFD7AFD51EA4FA1592f75E': 'Jewel LP Token wBTC/Jewel',
  '0x997f00485B238c83f7e58C2Ea1866DFD79f04A4b': 'Jewel LP Token wBTC/1ETH',
  '0x864fcd9a42a5f6e0f76BC309Ee26c8fab473FC3e': 'Jewel LP Token 1ETH/ONE',
  '0xEaB84868f6c8569E14263a5326ECd62F5328a70f': 'Jewel LP Token 1ETH/Jewel',
  '0x3a0C4D87BdE442150779d63c1c695d003184dF52': 'Jewel LP Token BUSD/ONE',
  '0xE7d0116Dd1DBBBA2EFBAd58f097D1FFbbeDc4923': 'Jewel LP Token bscBNB/Jewel',
  '0x68a73f563ba14d51f070A6ddD073177FB794190A': 'Jewel LP Token Superbid/ONE',
  '0x95f2409a44a9B989F8C5601037C513890E90cd06': 'Jewel LP Token Superbid/Jewel',
  '0xd22AfC683130B7c899b701e86e546F19bc598167': 'Jewel LP Token AME/BUSD/ONE',
  '0xbBAE29799602437364d183fBD9272968cF5F6361': 'Jewel LP Token TRANQ/BUSD/ONE',
  '0x5d7c3e1Fa36BbEEDf77A45E69759c5bfA56570b8': 'Jewel LP Token ONE/EDEN',
  '0xC4Af332a1E154B0bfa8760Cd3F974cdB538455Bf': 'Jewel LP Token ONE/PHAT',
  '0xdfc122dfbcec9cb11da72a7314E373fE32100396': 'Jewel LP Token ONE/SMUG',
  '0x7f64A21c72590497208273Dadba0814a6762685e': 'Jewel LP Token ONE/FOX',
  '0x7Be40c6Ba2Ff1e254e4277de0178EC80a8B78204': 'Jewel LP Token ONE/PASTA',
  '0xA1221A5BBEa699f507CC00bDedeA05b5d2e32Eba': 'Jewel LP Token 1USDC/Jewel',
  '0xFD3AB633de7a747cEacAfDad6575df1D737D659E': 'Jewel LP Token MIS/LUMEN',
  '0xe9425769e13d3f928C483726de841999648e9CFd': 'Jewel LP Token MIS/FOX',
  '0xfA45e64Adf9BF3caDC65b737b2B0151C750f414C': 'Jewel LP Token MIS/Tranquil',
  '0x14eC453656Ce925C969eafFcD76d62ACA2468Eb6': 'Jewel LP Token MIS/RVRS',
  '0x6F8B3C45f582d8f0794A57fa6a467C591CED9CAD': 'Jewel LP Token wBTC/ONE',
  '0xD7Ef803Ad48654016890DdA9F12d709f87C79cD9': 'Jewel LP Token ONE',
  '0xC79245BA0248Abe8a385d588C0a9D3DB261B453c': 'Jewel LP Token DFKTEARS/Jewel',
  '0xE22297CC3452aae66cEE6ED1cb437e96219c3319': 'Jewel LP Token MIS/XYA',
  '0xF8a37164E8273cB89e631A76c53af8ad55e6Af4E': 'Jewel LP Token MIS/MAGIC',
  '0xA9Ae89Fc743891a7166a884F25abaC50615C9BaD': 'Jewel LP Token AME/FOX',
  '0xD147ac7ccEdCa0F6F34238d4b3D0CB737aC0cfB2': 'Jewel LP Token 1AXS/ONE',
  '0xC9D4786b600873EF0f4CBe60474563Fe55ec2320': 'Jewel LP Token BUSD/1FTM',
  '0x882cF21E4bf43B6d5658C27e07f5b2873DBE5718': 'Jewel LP Token AME/RAIN',
  '0xD74B9b22860b52d8d6bc666Cf8E7274D76Cd596d': 'Jewel LP Token bscTLM/Jewel',
  '0xa8589d575aeD9C6dc12C860867c5348791D2D097': 'Jewel LP Token KURO/Jewel',
  '0x500afc0C82DA45C618fbBfc2F6931Bc415d334ea': 'Jewel LP Token 1MATIC/Jewel',
  '0x321EafB0aeD358966a90513290De99763946A54b': 'Jewel LP Token DFKGold/Jewel',
  '0xB270556714136049B27485f1aA8089B10F6F7f57': 'Jewel LP Token Shvas/Jewel',
  '0x6574026Db45bA8d49529145080489C3da71a82DF': 'Venom LP Token ONE/UST',
  '0xF170016d63fb89e1d559e8F87a17BCC8B7CD9c00': 'Venom LP Token ONE/USDC',
  '0xA0E4f1f65e80A7aFb07cB43956DC8b91C7dBC640': 'Venom LP Token bscUSDC/1USDC',
  '0x3a4EDcf3312f44EF027acfd8c21382a5259936e7': 'DFK Gold',
  '0x24eA0D436d3c2602fbfEfBe6a16bBc304C963D04': 'Gaia\'s Tears',
  '0x66F5BfD910cd83d3766c4B39d13730C911b2D286': 'Shvas Rune',
  '0x8F655142104478724bbC72664042EA09EBbF7B38': 'Moksha Rune',
  '0x95d02C1Dc58F05A015275eB49E107137D9Ee81Dc': 'Grey Pet Egg',
  '0x6d605303e9Ac53C59A3Da1ecE36C9660c7A71da5': 'Green Pet Egg',
  '0x9678518e04Fe02FB30b55e2D0e554E26306d0892': 'Blue Pet Egg',
  '0x3dB1fd0Ad479A46216919758144FD15A21C3e93c': 'Yellow Pet Egg',
  '0x9edb3Da18be4B03857f3d39F83e5C6AAD67bc148': 'Golden Egg',
  '0x6e1bC01Cc52D165B357c42042cF608159A2B81c1': 'Ambertaffy',
  '0x68EA4640C5ce6cC0c9A1F17B7b882cB1cBEACcd7': 'Darkweed',
  '0x600541aD6Ce0a8b5dae68f086D46361534D20E80': 'Goldvein',
  '0x043F9bd9Bb17dFc90dE3D416422695Dd8fa44486': 'Ragweed',
  '0x094243DfABfBB3E6F71814618ace53f07362a84c': 'Redleaf',
  '0x6B10Ad6E3b99090De20bF9f95F960addC35eF3E2': 'Rockroot',
  '0xCdfFe898E687E941b124dfB7d24983266492eF1d': 'SwiftThistle',
  '0x78aED65A2Cc40C7D8B0dF1554Da60b38AD351432': 'Bloater',
  '0xe4Cfee5bF05CeF3418DA74CFB89727D8E4fEE9FA': 'Ironscale',
  '0x8Bf4A0888451C6b5412bCaD3D9dA3DCf5c6CA7BE': 'Lanterneye',
  '0xc5891912718ccFFcC9732D1942cCD98d5934C2e1': 'Redgill',
  '0xb80A07e13240C31ec6dc0B5D72Af79d461dA3A70': 'Sailfish',
  '0x372CaF681353758f985597A35266f7b330a2A44D': 'Shimmerskin',
  '0x2493cfDAcc0f9c07240B5B1C4BE08c62b8eEff69': 'Silverfin',
  '0xAC5c49Ff7E813dE1947DC74bbb1720c353079ac9': 'Blue Stem',
  '0xc0214b37FCD01511E6283Af5423CF24C96BB9808': 'Milkweed',
  '0x19B9F05cdE7A61ab7aae5b0ed91aA62FF51CF881': 'Spiderfruit',
  '0x17f3B5240C4A71a3BBF379710f6fA66B9b51f224': 'Bounty Hero Achievement',
  '0x0405f1b828C7C9462877cC70A9f266887FF55adA': 'DFK Raffle Tix',
  '0x909EF175d58d0e17d3Ceb005EeCF24C1E5C6F390': 'Eternal Story Page',
  '0x2789F04d22a845dC854145d3c289240517f2BcF0': 'Health Vial',
  '0x87361363A75c9A6303ce813D0B2656c34B68FF52': 'Full Health Potion',
  '0x19b020001AB0C12Ffa93e1FDeF90c7C37C8C71ef': 'Mana Vial',
  '0xDc2C698aF26Ff935cD1c50Eef3a4A933C62AF18D': 'Full Mana Potion',
  '0x959ba19508827d1ed2333B1b503Bd5ab006C710e': 'Stamina Vial',
  '0xA1f8b0E88c51a45E152934686270DDF4E3356278': 'Anti-poison Potion',
  '0x1771dEc8D9A29F30d82443dE0a69e7b6824e2F53': 'Anti-blinding Potion',
  '0x7e120334D9AFFc0982719A4eacC045F78BF41C68': 'Magic Resistance Potion',
  '0xFb03c364969a0bB572Ce62b8Cd616A7DDEb4c09A': 'Toughness Potion',
  '0x872dD1595544CE22ad1e0174449C7ECE6F0bb01b': 'Switftness Potion',
  '0x27dC6AaaD95580EdF25F8B9676f1B984e09e413d': 'Atonement Crystal',
  '0x1f3F655079b70190cb79cE5bc5AE5F19dAf2A6Cf': 'Atonement Crystal Lesser',
  '0x17f3B5240C4A71a3BBF379710f6fA66B9b51f224': 'Greater Atonement Crystal',
  '0xaB464901AFBc61bAC440a97Fa568aC42885Da58B': 'Lesser Might Crystal',
  '0xb368f69bE6eDa74700763672AEB2Ae63f3d20AE6': 'Might Crystal',
  '0xdFA5aE156AD4590A0061E9c4E8cc5bd60bc775c7': 'Greater Might Crystal',
  '0x39927A2CEE5580d63A163bc402946C7600300373': 'Lesser Finesse Crystal',
  '0xc6A58eFc320A7aFDB1cD662eaf6de10Ee17103F2': 'Finesse Crystal',
  '0xd1f789f6f8a3ee3fb94adBE3e82f43AAb51759Ee': 'Greater Finesse Crystal',
  '0xf5c26F2F34E9245C3A9ea0B0e7Ea7B33E6404Da0': 'Lesser Swiftness Crystal',
  '0x5d7f20e3B0f1406Bf038175218eA7e9B4838908c': 'Swiftness Crystal',
  '0x1e38e63227D52CBaDA2f0c11bE04feD64154ea37': 'Greater Swiftness Crystal',
  '0x0d8403E47445DB9E316E36F476dacD5827220Bdd': 'Lesser Vigor Crystal',
  '0xBbA50bD111DC586Fd1f2B1476B6eC505800A3FD0': 'Vigor Crystal',
  '0x5292dbce7eC2e10dd500984A163A5aE8abA585Ce': 'Greater Vigor Crystal',
  '0x3017609B9A59B77B708D783835B6fF94a3D9E337': 'Lesser Fortitude Crystal',
  '0x603919AEB55EB13F9CDE94274fC54ab2Bd2DecE7': 'Fortitude Crystal',
  '0xFE41BFf925eD88f688332b12746ef1Da68FD4CF2': 'Greater Fortitude Crystal',
  '0x17ff2016c9ecCFBF4Fc4DA6EF95Fe646D2c9104F': 'Lesser Wit Crystal',
  '0x3619fc2386FbBC19DDC39d29A72457e758CFAD69': 'Wit Crystal',
  '0xbaAb8dB69a2FdC0b88B2B3F6F75Fa8899680c43B': 'Greater Wit Crystal',
  '0xc63b76f710e9973b8989678eb16234CfADc8D9DB': 'Lesser Insight Crystal',
  '0x117E60775584CdfA4f414E22b075F31cC9c3207C': 'Insight Crystal',
  '0x90454DbF13846CF960abc0F583c319B06aB3F280': 'Greater Insight Crystal',
  '0x13AF184aEA970Fe79E3BB7A1B0B156B195fB1f40': 'Lesser Fortune Crystal',
  '0x6D777C64f0320d8A5b31BE0FdeB694007Fc3ed45': 'Fortune Crystal',
  '0x2bC1112337B90bF8c5b9422bC1e98193a9C3d1f4': 'Greater Fortune Crystal',
  '0xa509c34306AdF6168268A213Cc47D336630bf101': 'Lesser Chaos Crystal',
  '0x45B53E55b5c0A10fdd4fE2079a562d5702F3A033': 'Chaos Crystal',
  '0x423bbec25e4888967baeDB7B4EC5b0465Fa3B87D': 'Greater Chaos Crystal',
  '0xe4E7C0c693d8A7FC159776a993495378705464A7': 'Lesser Might Stone',
  '0x6382781FE94CAadC71027c0457c9CbEff06e204c': 'Might Stone',
  '0xE7F6ea1cE7BbEbC9F2Cf080010dd938d2D8D8B1b': 'Might Stone',
  '0x2bc05bf05E273a2276F19a8Bd6738e742A5685b3': 'Greater Might Stone',
  '0xbb5614D466b77d50DdEd994892DFe6F0ACA4eEbb': 'Lesser Finesse Stone',
  '0xD0B689Cb5DE0c15792Aa456C89D64038C1F2EedC': 'Finesse Stone',
  '0x20f10ef23Cdc11Fa55E6B3703d88f19A7B345D15': 'Greater Finesse Stone',
  '0xd9A8abC0Ce1ADC23F1c1813986c9a9C21C9e7510': 'Lesser Swiftness Stone',
  '0x08f362517aD4119d93bBCd20825c2E4119abB495': 'Swiftness Stone',
  '0xA1a56D20e4ba3fd2FB91c80f611ECa43c1311Afe': 'Greater Swiftness Stone',
  '0xB00CbF5Cd5e7b321436C2D3d8078773522D2F073': 'Lesser Vigor Stone',
  '0x9df75917aC9747B4A70fa033E4b0182d85B62857': 'Vigor Stone',
  '0x00a2E2F8Feb81FDB7205992B5Abd2a801b419394': 'Greater Vigor Stone',
  '0x1f57eb682377f5Ad6276b9315412920BdF9530f6': 'Lesser Fortitude Stone',
  '0x17Fa96ba9d9C29e4B96d29A7e89a4E7B240E3343': 'Fortitude Stone',
  '0x27AF2A00B42Dcc0084A6Dc99169efbFE98eb140C': 'Greater Fortitude Stone',
  '0x4Ff7A020ec1100D36d5C81F3D4815F2e9C704b59': 'Lesser Wit Stone',
  '0x939Ea05C81aAC48F7C10BdB08615082B82C80c63': 'Wit Stone',
  '0xa6e86F2b43Ae73cfB09A3bA779AeB8Fd48417ba0': 'Greater Wit Stone',
  '0x762b98B3758d0A5Eb95B3E4A1E2914Ce0A80D99c': 'Lesser Insight Stone',
  '0x9D71Bb9C781FC2eBdD3d6cb709438e3c71200149': 'Insight Stone',
  '0x40654Da5a038963fA9750AF352ae9d3b1da2baD0': 'Greater Insight Stone',
  '0x6D6eA1D2Dc1Df6Eaa2153f212d25Cf92d13Be628': 'Lesser Fortune Stone',
  '0x5da2EffE9857DcEcB786E13566Ff37B92e1E6862': 'Fortune Stone',
  '0x7f26CB2BBBcFCE8e5866cc02a887A591E1Adc02A': 'Greater Fortune Stone',
  '0x6D4f4bC32df561a35C05866051CbE9C92759Da29': 'Lesser Chaos Stone',
  '0x3633F956410163A98D58D2D928B38C64A488654e': 'Chaos Stone',
  '0x2fB31FF9E9945c5c1911386865cD666b2C5dfeB6': 'Greater Chaos Stone'
};
var DFKCHAIN_TOKENS = {
  '0x04b9dA42306B023f3572e106B11D82aAd9D32EBb': 'Crystal',
  '0xA11f52cd55900e7faf0daca7F2BA1DF8df30AdDd': 'xCrystalOld',
  '0x6E7185872BCDf3F7a6cBbE81356e50DAFFB002d2': 'xCrystal',
  '0xCCb93dABD71c8Dad03Fc4CE5559dC3D89F67a260': 'wJewel',
  '0x77f2656d04E158f915bC22f07B779D94c1DC47Ff': 'wxJewel',
  '0xB57B60DeBDB0b8172bb6316a9164bd3C695F133a': 'dfkAVAX',
  '0x3AD9DFE640E1A9Cc1D9B0948620820D975c3803a': 'USDC',
  '0xfBDF0E31808d0aa7b9509AA6aBC9754E48C58852': 'Ethereum',
  '0x7516EB8B8Edfa420f540a162335eACF3ea05a247': 'BTC.b',
  '0x97855Ba65aa7ed2F65Ed832a776537268158B78a': 'Klay',
  '0xD17a41Cd199edF1093A9Be4404EaDe52Ec19698e': 'Matic',
  '0x2Df041186C844F8a2e2b63F16145Bc6Ff7d23E25': 'Fantom',
  '0x576C260513204392F0eC0bc865450872025CB1cA': 'DFK Gold',
  '0x58E63A9bbb2047cd9Ba7E6bB4490C238d271c278': 'Gaia\'s Tears',
  '0x79fE1fCF16Cc0F7E28b4d7B97387452E3084b6dA': 'Gaia\'s Tears',
  '0x6AC38A4C112F125eac0eBDbaDBed0BC8F4575d0d': 'Crystal LP Token Jewel/xJewel',
  '0x48658E69D741024b4686C8f7b236D3F1D291f386': 'Crystal LP Token Jewel/Crystal',
  '0xF3EabeD6Bd905e0FcD68FC3dBCd6e3A4aEE55E98': 'Crystal LP Token Jewel/AVAX',
  '0xCF329b34049033dE26e4449aeBCb41f1992724D3': 'Crystal LP Token Jewel/USDC',
  '0x9f378F48d0c1328fd0C80d7Ae544C6CadB5Ba99E': 'Crystal LP Token Crystal/AVAX',
  '0x04Dec678825b8DfD2D0d9bD83B538bE3fbDA2926': 'Crystal LP Token Crystal/USDC',
  '0x78C893E262e2681Dbd6B6eBA6CCA2AaD45de19AD': 'Crystal LP Token Crystal/Ethereum',
  '0x7d4daa9eB74264b082A92F3f559ff167224484aC': 'Crystal LP Token Ethereum/USDC',
  '0x79724B6996502afc773feB3Ff8Bb3C23ADf2854B': 'Crystal LP Token Ethereum/Jewel',
  '0xaFC1fBc3F3fB517EB54Bb2472051A6f0b2105320': 'Crystal LP Token Klay/Crystal',
  '0x561091E2385C90d41b4c0dAef651A4b33E1a5CfE': 'Crystal LP Token Klay/Jewel',
  '0xfAa8507e822397bd56eFD4480Fb12ADC41ff940B': 'Crystal LP Token BTC.b/Jewel',
  '0x00BD81c9bAc29a3b6aea7ABc92d2C9a3366Bb4dD': 'Crystal LP Token BTC.b/Crystal',
  '0x59D642B471dd54207Cb1CDe2e7507b0Ce1b1a6a5': 'Crystal LP Token BTC.b/USDC',
  '0xE072a18f6a8f1eD4953361972edD1Eb34f3e7c4E': 'Crystal LP Token Crystal/Tears',
  '0x75E8D8676d774C9429FbB148b30E304b5542aC3d': 'Shvas Rune',
  '0xCd2192521BD8e33559b0CA24f3260fE6A26C28e4': 'Moksha Rune',
  '0x7E121418cC5080C96d967cf6A033B0E541935097': 'Grey Pet Egg',
  '0x8D2bC53106063A37bb3DDFCa8CfC1D262a9BDCeB': 'Green Pet Egg',
  '0xa61Bac689AD6867a605633520D70C49e1dCce853': 'Blue Pet Egg',
  '0x72F860bF73ffa3FC42B97BbcF43Ae80280CFcdc3': 'Yellow Pet Egg',
  '0xf2D479DaEdE7F9e270a90615F8b1C52F3C487bC7': 'Golden Egg',
  '0xB78d5580d6D897DE60E1A942A5C1dc07Bc716943': 'Ambertaffy',
  '0x848Ac8ddC199221Be3dD4e4124c462B806B6C4Fd': 'Darkweed',
  '0x0096ffda7A8f8E00e9F8Bbd1cF082c14FA9d642e': 'Goldvein',
  '0x137995beEEec688296B0118131C1052546475fF3': 'Ragweed',
  '0x473A41e71618dD0709Ba56518256793371427d79': 'Redleaf',
  '0x60170664b52c035Fcb32CF5c9694b22b47882e5F': 'Rockroot',
  '0x97b25DE9F61BBBA2aD51F1b706D4D7C04257f33A': 'Swift-Thistle',
  '0xe7a1B580942148451E47b92e95aEB8d31B0acA37': 'Frost Drum',
  '0xBcdD90034eB73e7Aec2598ea9082d381a285f63b': 'Knaproot',
  '0x80A42Dc2909C0873294c5E359e8DF49cf21c74E4': 'Shaggy Caps',
  '0xc6030Afa09EDec1fd8e63a1dE10fC00E0146DaF3': 'Skunk Shade',
  '0x268CC8248FFB72Cd5F3e73A9a20Fa2FF40EfbA61': 'Bloater',
  '0x04B43D632F34ba4D4D72B0Dc2DC4B30402e5Cf88': 'Ironscale',
  '0xc2Ff93228441Ff4DD904c60Ecbc1CfA2886C76eB': 'Lanterneye',
  '0x68eE50dD7F1573423EE0Ed9c66Fc1A696f937e81': 'Redgill',
  '0x7f46E45f6e0361e7B9304f338404DA85CB94E33D': 'Sailfish',
  '0xd44ee492889C078934662cfeEc790883DCe245f3': 'Shimmerskin',
  '0xA7CFd21223151700FB82684Cd9c693596267375D': 'Silverfin',
  '0x3bcb9A3DaB194C6D8D44B424AF383E7Db51C82BD': 'Frost Bloater',
  '0xE7CB27ad646C49dC1671Cb9207176D864922C431': 'Speckle Tail',
  '0x60A3810a3963f23Fa70591435bbe93BF8786E202': 'King Pincer',
  '0x6513757978E89e822772c16B60AE033781A29A4F': 'Three Eyed Eel',
  '0x0776b936344DE7bd58A4738306a6c76835ce5D3F': 'Blue Stem',
  '0xA2cef1763e59198025259d76Ce8F9E60d27B17B5': 'Milkweed',
  '0x3E022D84D397F18743a90155934aBAC421D5FA4C': 'Spiderfruit',
  '0xBbd7c4Be2e54fF5e013471162e1ABAD7AB74c3C3': 'DFK Raffle Tix CV',
  '0xA37851cCE4B2b65c0b290AA4cC2DFF00314ec85a': 'Eternal Story Page',
  '0xeC744dae4d68735d5AEA5FDB766FcE51D9A256a5': 'Duels Trophy S1 Solo',
  '0x4Aa517d7DAadD2e22d2b6d90F19a7BB01498116b': 'Duels Trophy S1 Wquad',
  '0x6EAD9B5d7Ae26c12CC40E393749999CB1707af5f': 'Duels Trophy S1 Warr',
  '0x591853e01EcFDcF1Bdc9f093423C197BfBBd1A4f': 'Health Vial',
  '0x5948dd8Df6afEFE05B033AD8f3ae513a9Cd4F1Dc': 'Full Health Potion',
  '0x240da5314B05E84392e868aC8f2b80ad6becadd4': 'Mana Vial',
  '0xf17FD21bDF6713a1Dfed668b97835b21e32651e8': 'Full Mana Potion',
  '0x242078edFDca25ef2A497C8D9f256Fd641472E5F': 'Stamina Vial',
  '0x449eB718e351a86718A090A1a8Db3FD561306d9b': 'Anti-Poison Potion',
  '0x5986045e7c221c8AD40A736B6434D82E29687aeB': 'Anti-Blind Potion',
  '0xFADCb72aAE2713975a890b59FF47231D1A552De3': 'Magic Resistance Potion',
  '0x2dfFf745d2c7ddCAD4E97b80DF33705B1a95A172': 'Toughness Potion',
  '0x84246Ce3988742D46fC00d9b8b2AFb5CDBDaE660': 'Swiftness Potion',
  '0xab2B495902f9A6652c382e5f289423929FFF2E65': 'Atonement Crystal',
  '0xbFa812214a16EcA7814e5F5c270d7f8F37A110B5': 'Atonement Crystal Lesser',
  '0x3A28E0D4eCF7558e1ba7357070032C5A6105B0C2': 'Greater Atonement Crystal',
  '0x5bAC3cAd961B01Ef9510C8e6c5402A2bB1542831': 'Lesser Might Crystal',
  '0x234dCf10Db6817185F5A3b430a8CAF2B4a35e9E9': 'Might Crystal',
  '0x438A4e0673b7084D6b2379a362627789D845399c': 'Greater Might Crystal',
  '0x9d9ef1Bf6A46b8413bf6b1b54F6A7aAb53c6b1b6': 'Lesser Finesse Crystal',
  '0xA9A8cc1AC7e7505a69cAca2E068716395CebE562': 'Finesse Crystal',
  '0xdA16b191D1431746b6661D428A223b72c178765A': 'Greater Finesse Crystal',
  '0x6BCA53314dADdA7f4De30A95413f75a93bfAfecF': 'Lesser Swiftness Crystal',
  '0x3e664eB15b35783B9D3EF06702044820F08bB45B': 'Swiftness Crystal',
  '0x1459c662F516D63216491DC34F7d9d35b00dF25A': 'Greater Swiftness Crystal',
  '0x5e4Cf6907CB5fBe2F642E399F6d07E567155d1F8': 'Lesser Vigor Crystal',
  '0xcD9201F50e5Be84ECE3D8F603dcd3e9DD5e88ea2': 'Vigor Crystal',
  '0x8780c4aa8bd0D15493D63C884bd9D427199Cf2cf': 'Greater Vigor Crystal',
  '0xbd2677c06C9448534A851bdD25dF045872b87cb1': 'Lesser Fortitude Crystal',
  '0xe9BfCc80800EB77a1eAF6881825936770aF83Eb6': 'Fortitude Crystal',
  '0x3e1c80c3B916C93748Ae642c885d4BFb5D6a6BFe': 'Greater Fortitude Crystal',
  '0xC989c916F189D2A2BE0322c020942d7c43aEa830': 'Lesser Wit Crystal',
  '0xAeb5b59c8B90D4F078046550Cc8F9f08dC127253': 'Wit Crystal',
  '0x9d1f44b0EC7BB80656FC8Fcd65152513f29a606D': 'Greater Wit Crystal',
  '0xbb5F97358F60cCBa262883A3Ff0C637393FE3aB8': 'Lesser Insight Crystal',
  '0x03e56Ded72C3a974295773355EadB38c0A85cF9D': 'Insight Crystal',
  '0xB3F5867E277798b50ba7A71C0b24FDcA03045eDF': 'Greater Insight Crystal',
  '0xE410b2BE2Ce1508E15009118567d02C6d7A7038e': 'Lesser Fortune Crystal',
  '0xe9BfCc80800EB77a1eAF6881825936770aF83Eb6': 'Fortune Crystal',
  '0x64C7D12D85050F5F0DcD075f038E5D616f30a404': 'Greater Fortune Crystal',
  '0xeEe5b16Cc49e7cef65391Fe7325cea17f787e245': 'Lesser Chaos Crystal',
  '0xC6b00B4005883C1Ff09fa1351B0f49027bCAB71a': 'Chaos Crystal',
  '0xb0155Fdb7B6972717C4774Fa2AEAEe9D6c0040b9': 'Greater Chaos Crystal',
  '0xf345b884eA45aEcb3E46CeEaEDB9CE993Ba3615a': 'Lesser Might Stone',
  '0x37bAa710391c1D6e22396E4B7F78477F0fF2fFA7': 'Might Stone',
  '0xA0851F6368AfA693a6654e9fdaf76CB6F160B837': 'Greater Might Stone',
  '0xF1D53fa23C562246B9d8EC591eEa12Ec0288a888': 'Lesser Finesse Stone',
  '0xe2C357ECB698C5ee97c49CCCfA8117c4b943C7B9': 'Finesse Stone',
  '0xF35D4f749C6ADCd4AEfE1720C5890cD38129d128': 'Greater Finesse Stone',
  '0xd37aCbAC3C25a543B30aa16208637cfa6EB97eDd': 'Lesser Swiftness Stone',
  '0x4F95D51fB8eF93704aF8C39A080c794cdA08f853': 'Swiftness Stone',
  '0x40D2c135a3E5a6f6546626795DEc67f818f0352a': 'Greater Swiftness Stone',
  '0x63891e0fcfEe0cEB12dE5fb96F43ADf9DbEC20a3': 'Lesser Vigor Stone',
  '0xA71a120931526fC98f1AcC9f769b6b0d690fB8f0': 'Vigor Stone',
  '0x0A5985574369EDE9Bd871fbdad61613D4C11Dac4': 'Greater Vigor Stone',
  '0xf599Ae2c925D3287a7fF64DC1b55C7Ea6EE3AA8f': 'Lesser Fortitude Stone',
  '0x05305c97e9A2FDC0F5Ea23824c1348DEeD9Aff04': 'Fortitude Stone',
  '0xc2eF7E4f659272ca2DaE9d3df05680783b299Cd0': 'Greater Fortitude Stone',
  '0xFC943eBd19112D6c6098412238E4E8319641B3d8': 'Lesser Wit Stone',
  '0x3971212Ec22147EE8808cB84F743DD852Be92f9C': 'Wit Stone',
  '0xa1BD7683fA348e256a2de8a9dDB55E5ea01eB048': 'Greater Wit Stone',
  '0x3D112747ff2463802Afa240B62ade8F1cc4a5c7d': 'Lesser Insight Stone',
  '0x74CFf096C9B027104fb1a0C2E0e265D123eA47De': 'Insight Stone',
  '0x3198f51A1c8cFC5f1FeaD58feaa19E6dFc8e9737': 'Greater Insight Stone',
  '0x934e3e2a433F37cC2D02855A43fD7Ed475EA7451': 'Lesser Fortune Stone',
  '0xd647D8b52981eDE13ac6a5B7Ad04e212Ac38fdFb': 'Fortune Stone',
  '0x8FfF0f5A660b4D38441DDF6127bca42D7a2755a9': 'Greater Fortune Stone',
  '0x7643ADB5AaF129A424390CB055d6e23231fFd690': 'Lesser Chaos Stone',
  '0x1ED1a6Ed588945C59227f7a0c622Ad564229d3d6': 'Chaos Stone',
  '0xEd4Bf3008afE47FE01CcC7a6648a24E326667eee': 'Greater Chaos Stone'
};
var KLAYTN_TOKENS = {
  '0x5819b6af194a78511c79c85ea68d2377a7e9335f': 'wKlay',
  '0xe4f05A66Ec68B54A58B17c22107b02e0232cC817': 'KLAY',
  '0x19Aac5f612f524B754CA7e7c41cbFa2E981A4432': 'wKlay',
  '0xB3F5867E277798b50ba7A71C0b24FDcA03045eDF': 'Jade',
  '0x30C103f8f5A3A732DFe2dCE1Cc9446f545527b43': 'Jewel',
  '0xcd8fe44a29db9159db36f96570d7a4d91986f528': 'Avax',
  '0x6270B58BE569a7c0b8f47594F191631Ae5b2C86C': 'synUSDC',
  '0xceE8FAF64bB97a73bb51E115Aa89C17FfA8dD167': 'oUSDT',
  '0x34d21b1e550D73cee41151c77F3c73359527a396': 'oETH',
  '0x16D0e1fBD024c600Ca0380A4C5D57Ee7a2eCBf9c': 'oWBTC',
  '0xaA8548665bCC12C202d5d0C700093123F2463EA6': 'sJewel',
  '0x6fc625D907b524475887524b11DE833feF460698': 'Jade LP Token oETH/Jade',
  '0x509d49AC90EF180363269E35b363E10b95c983AF': 'Jade LP Token oUSDT/Jade',
  '0x6CE5bb25A4E7aBF7214309F7b8D7cceCEF60867E': 'Jade LP Token Avax/Jewel',
  '0x63b67d4a0f553D436B0a511836A7A4bDF8Af376A': 'Jade LP Token Avax/Jade',
  '0x7828926761e7a6E1f9532914A282bf6631EA3C81': 'Jade LP Token Jewel/oWBTC',
  '0x50943e1E500D7D62cc4c6904FBB3957fAfaEbEd5': 'Jade LP Token Jade/oWBTC',
  '0xd08A937a67eb5613ccC8729C01605E0320f1B216': 'Jade LP Token Klay/Jade',
  '0xd3e2Fd9dB41Acea03f0E0c22d85D3076186f4f24': 'Jade LP Token Jewel/oETH',
  '0x0d9a7780ce1d680ec32c37d815e966304b09be9b': 'Jade LP Token Jade/Gaia Tears',
  '0xFab984b38039D3D4CbfeE8f274Fa6E193206a0EC': 'Jade LP Token Jewel/Gaia Tears',
  '0x0d9d200720021F9de5C8413244f81087ecB4AdcC': 'Jade LP Token Klay/Jewel',
  '0xe7a1B580942148451E47b92e95aEB8d31B0acA37': 'DFKGold',
  '0x8Be0cbA3c8c8F392408364ef21dfCF714A918234': 'Gaia\'s Tears',
  '0x907a98319AEB249e387246637149f4B2e7D21dB7': 'Shvas Rune',
  '0xd0223143057Eb44065e789b202E03A5869a6006C': 'Moksha Rune',
  '0xfd29ebdE0dd1331C19BBF54518df94b442ACb38C': 'Grey Pet Egg',
  '0xb1Ec534fBBfEBd4563A4B0055E744286CE490f26': 'Green Pet Egg',
  '0x29ADd7D022c591D56eb4aFd262075dA900C67ab1': 'Blue Pet Egg',
  '0x0A73aF98781bad9BCb80A71241F129EA877eF1b7': 'Yellow Pet Egg',
  '0xc9731BE04F217543E3010cCbf903E858EFde840f': 'Golden Egg',
  '0x75E8D8676d774C9429FbB148b30E304b5542aC3d': 'Ambertaffy',
  '0xEDFBe9EEf42FfAf8909EC9Ce0d79850BA0C232FE': 'Darkweed',
  '0xeaF833A0Ae97897f6F69a728C9c17916296cecCA': 'Goldvein',
  '0x4cD7025BD6e1b77105b90928362e6715101d0b5a': 'Ragweed',
  '0xadbF23Fe3B47857614940dF31B28179685aE9B0c': 'Redleaf',
  '0xf2D479DaEdE7F9e270a90615F8b1C52F3C487bC7': 'Rockroot',
  '0xCd2192521BD8e33559b0CA24f3260fE6A26C28e4': 'Swift-Thistle',
  '0xD69542aBE74413242e387Efb9e55BE6A4863ca10': 'Frost Drum',
  '0xFceFA4Abcb18a7053393526f75Ad33fac5F25dc9': 'Knaproot',
  '0xCe370D379f0CCf746B3426E3BD3923f3aDF0DC1a': 'Shaggy Caps',
  '0x874FC0015ece1d77ba3D5668F16c46ba72913239': 'Skunk Shade',
  '0x72F860bF73ffa3FC42B97BbcF43Ae80280CFcdc3': 'Bloater',
  '0xBcdD90034eB73e7Aec2598ea9082d381a285f63b': 'Ironscale',
  '0x80A42Dc2909C0873294c5E359e8DF49cf21c74E4': 'Lanterneye',
  '0x8D2bC53106063A37bb3DDFCa8CfC1D262a9BDCeB': 'Redgill',
  '0xc6030Afa09EDec1fd8e63a1dE10fC00E0146DaF3': 'Sailfish',
  '0xa61Bac689AD6867a605633520D70C49e1dCce853': 'Shimmerskin',
  '0x7E121418cC5080C96d967cf6A033B0E541935097': 'Silverfin',
  '0x18cB286EeCE992f79f601E49acde1D1F5dE32a30': 'Frost Bloater',
  '0x48d9fC80A47cee2d52DE950898Bc6aBF54223F81': 'Speckle Tail',
  '0xB4A516bf36e44c0CE9E3E6769D3BA87341Cd9959': 'King Pincer',
  '0x7E1298EBF3a8B259561df6E797Ff8561756E50EA': 'Three Eyed Eel',
  '0xDbd4fA2D2C62C6c60957a126970e412Ed6AC1bD6': 'Blue Stem',
  '0xE408814828f2b51649473c1a05B861495516B920': 'Milkweed',
  '0x08D93Db24B783F8eBb68D7604bF358F5027330A6': 'Spiderfruit',
  '0xa27C1429a676db902B9f0360686eDbB57d0A7B01': 'Health Vial',
  '0xf710244462431b9962706B46826AFB3B38376c7b': 'Full Health Potion',
  '0x8639d64A2088500EC4f20fB5C41A995fE4f1d85a': 'Mana Vial',
  '0x108D31E23bC6540878E6532F3376b3EC982e1C58': 'Full Mana Potion',
  '0x4546DBaAb48Bf1BF2ad7B56d04952d946Ab6e2a7': 'Stamina Vial',
  '0xE34a733fA92B41A1CA4241da9D2d5834Cc8D1011': 'Anti-Poison Potion',
  '0x5FB537aF1d929af7BDD7935C289158c940782ed6': 'Anti-Blind Potion',
  '0x9c8A0C6a7ad8Be153773070D434CDbeA5176D2ff': 'Magic Resistance Potion',
  '0xf757a7F4ffF29e7F7b4aCCe6Ffb04E59e91EFDA8': 'Toughness Potion',
  '0xcb7aA7cA9357DAF9F2b78D262A4f89cDfE5abC70': 'Swiftness Potion',
  '0x80Ab38fc9fA0a484b98d5600147e7C695627747D': 'Lesser Might Crystal',
  '0xa3907dEA6f16f1918B4BcDd178c2928c7e6A571D': 'Might Crystal',
  '0x1F93421DaE2f8de79C3Fd197a227ec5EE3Eef71b': 'Greater Might Crystal',
  '0xC3B36a02f360c3d18042bF3533be602cb775007A': 'Lesser Finesse Crystal',
  '0x15E77beB33D3B09aB7da529daB1E556b955fECf6': 'Finesse Crystal',
  '0x616df872971A3f31dffC9a2B55BF55C760B966bF': 'Greater Finesse Crystal',
  '0x32Cbbfd741EB7634818aa2e3E8502367cB6602BE': 'Lesser Swiftness Crystal',
  '0xc2Ff16F357b51E070c977501563A01a70F3B7BF5': 'Swiftness Crystal',
  '0xa5CC44e60F5a898e5c776952E66D1c9905077608': 'Greater Swiftness Crystal',
  '0x6C7AF7483b050a00b5fbC4241eD06944c5f0bD77': 'Lesser Vigor Crystal',
  '0x14a9D5a75799E4C6B4BfA65C8293a75e02DD5339': 'Vigor Crystal',
  '0x73286f76E05aAa7A73F896DE0Ebc745021Cb50F2': 'Greater Vigor Crystal',
  '0x1E672a8385b39E13267efA2Fb39f574a2a23AE9F': 'Lesser Fortitude Crystal',
  '0xA844059503289B781854aEdcA04E5bB13290bd86': 'Fortitude Crystal',
  '0x147b3263F1C4ca729B13Ca1D2A7148c32Aa1d8d0': 'Greater Fortitude Crystal',
  '0xf15035b5eD13Feb18f63D829ABc1c3139041e7C2': 'Lesser Wit Crystal',
  '0xf30214D43E55BE1cbaC712b49A75d4D3220302a7': 'Wit Crystal',
  '0x5F8A485ed5B4B13c1fc3c1C7fe82164E8e534060': 'Greater Wit Crystal',
  '0x5f967E325E91977B42D2591Fc2f57da75Ee4490B': 'Lesser Insight Crystal',
  '0xAd7fBD9EDDE05227964104Bb23Ff8d171D4c90C8': 'Insight Crystal',
  '0x17bb680872D7631e3056136d7e15eC5f6570976a': 'Greater Insight Crystal',
  '0x8baD15B5C531d119b328d0F716a6B9D90CeDa88A': 'Lesser Fortune Crystal',
  '0x02d27BC195E58498C687A82d96188A8EF282a1e1': 'Fortune Crystal',
  '0x0d2ea025007995e9Bb1815864CD4e7B98B47DF7c': 'Greater Fortune Crystal',
  '0x537E800b8fD22Dc76A438Af8b9923986A5487853': 'Lesser Chaos Crystal',
  '0xE078C782fF0cC1789D0608834A3cD5076896e4FC': 'Chaos Crystal',
  '0x9e185426354AA53aAC07De79c2fa1e0B50490fdd': 'Greater Chaos Crystal',
  '0xbb8ac0BB95E433204217b0478B3f6d815EcB2d8C': 'Lesser Might Stone',
  '0x532bce28c28616552a4BcDdb5D4B4126Dea35f66': 'Might Stone',
  '0x434619b18466dEAA26475f97467754135aB8f3AF': 'Greater Might Stone',
  '0x784bd01e3882b80aa837f6A3041Cd386eC54a501': 'Lesser Finesse Stone',
  '0x31eb3b534E29D10Db08109A1fa50ccB081d10816': 'Finesse Stone',
  '0xFE4ac39174C2637537711f0cb3112EaD47E77D37': 'Greater Finesse Stone',
  '0xAd51199B453075C73FA106aFcAAD59f705EF7872': 'Lesser Swiftness Stone',
  '0xf200597430eAc3e22B4566D1BCd70A3b63804B24': 'Swiftness Stone',
  '0x954296fd7563f737BD502e3DdbAdA3f5223F92f1': 'Greater Swiftness Stone',
  '0x50F683acefA41b226CEfAdc0dd2ea6fFBfED56A0': 'Lesser Vigor Stone',
  '0xA0c89fB3cbb115cf86EdcB4319578312D026A07a': 'Vigor Stone',
  '0x9A587bBD01D5B2745b20A89ddd9B83268129fEda': 'Greater Vigor Stone',
  '0xBC5248B4f50f4c7D2F9A67Be1f1d4b8be44ffc75': 'Lesser Fortitude Stone',
  '0x254787d3b87d8c21A300Ab8D5A06C01426CE40c0': 'Fortitude Stone',
  '0x3D0EA055081e62e40257fde3A2036a557af6Ff77': 'Greater Fortitude Stone',
  '0x5903F478e456DD4Ce5387caBE3984DfEf93D0A46': 'Lesser Wit Stone',
  '0x3BaEFAfF21Fa2F06Ad3899903B7A899a91B5915A': 'Wit Stone',
  '0x3C0B9C87b1747C47D0B73910f995A08D75D81Af1': 'Greater Wit Stone',
  '0xfC66cF68505F8E95C52C4F7f84936436DBd52e9B': 'Lesser Insight Stone',
  '0x22A92428605a3B5b66695A60e96b683E98a9a035': 'Insight Stone',
  '0xF861104131825320C3d0D9B7bd373Ea0549f0587': 'Greater Insight Stone',
  '0x816E22125021530535364390a3E2fA305a436247': 'Lesser Fortune Stone',
  '0xf0cBbd41652d9A93A899f070669186F0c8475F7D': 'Fortune Stone',
  '0x91aced74b0CEE03EF8902f13E97F6e308941E6Bd': 'Greater Fortune Stone',
  '0x38bDed7C399bbD214a19De35260766b130cAFd2F': 'Lesser Chaos Stone',
  '0x880cb941AAb394775f54F2b6468035bbdD0B81dF': 'Chaos Stone',
  '0x932049DF7f09DeE7cF5Aefe03f373810EBbdDDc7': 'Greater Chaos Stone',
  '0x26bdcB310313eFf8D580e43762e2020B23f3e728': 'Eternal Story Pages'
};
var AVALANCHE_TOKENS = {
  '0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7': 'AVAX',
  '0x4f60a160D8C2DDdaAfe16FCC57566dB84D674BD6': 'AVAX Jewel',
  '0xd586E7F844cEa2F87f50152665BCbc2C279D8d70': 'DAI',
  '0xA7D7079b0FEaD91F3e65f86E8915Cb59c1a4C664': 'USDC',
  '0x49D5c2BdFfac6CE2BFdB6640F4F80f226bc10bAB': 'wETH',
  '0x152b9d0fdc40c096757f570a51e494bd4b943e50': 'BTC.b',
  '0x60781C2586D68229fde47564546784ab3fACA982': 'PNG',
};
const JEWEL_ADDRESSES = {
  '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F': 'harmony',
  '0xCCb93dABD71c8Dad03Fc4CE5559dC3D89F67a260': 'dfkchain',
  '0x30C103f8f5A3A732DFe2dCE1Cc9446f545527b43': 'klaytn',
  '0x4f60a160D8C2DDdaAfe16FCC57566dB84D674BD6': 'avalanche'
};
const AIRDROP_ADDRESSES = {
  '0xa678d193fEcC677e137a00FEFb43a9ccffA53210': 'Airdrop',
  '0x8AbEbcDBF5AF9FC602814Eabf6Fbf952acF682A2': 'Airdrops',
  '0x2b12D9A2480D6Dd9F71DabAa366C87134195b679': 'Airdrop Payments Portal',
  '0x123165B3a30fdA3655B30cfC10135C1CA3C21bFC': 'Airdrop Crystalvale',
  '0x947873092dc57C1A70704033c41cB110f4462a8B': 'Airdrop Claim'
}
const LENDING_ADDRESSES = {
  '0x34B9aa82D89AE04f0f546Ca5eC9C93eFE1288940': 'TranqOneLending',
  '0x973f22036A0fF3A93654e7829444ec64CB37BD78': 'TranqStoneLending',
  '0xd9c0D8Ad06ABE10aB29655ff98DcAAA0E059184A': 'Tranq1WBTCLending',
  '0x481721B918c698ff5f253c56684bAC8dCa84346c': 'Tranq1BTCLending',
  '0xc63AB8c72e636C9961c5e9288b697eC5F0B8E1F7': 'Tranq1ETHLending',
  '0xCa3e902eFdb2a410C952Fd3e4ac38d7DBDCB8E96': 'Tranq1USDCLending',
  '0x7af2430eFa179dB0e76257E5208bCAf2407B2468': 'Tranq1USDTLending',
  '0x49d95736FE7f1F32E3ee5deFc26c95bA22834639': 'Tranq1DAILending',
}
crystalvale_rewards = ['0x04b9dA42306B023f3572e106B11D82aAd9D32EBb','0x576C260513204392F0eC0bc865450872025CB1cA','0x79fE1fCF16Cc0F7E28b4d7B97387452E3084b6dA','0x75E8D8676d774C9429FbB148b30E304b5542aC3d','0xCd2192521BD8e33559b0CA24f3260fE6A26C28e4','0x7E121418cC5080C96d967cf6A033B0E541935097','0x8D2bC53106063A37bb3DDFCa8CfC1D262a9BDCeB','0xa61Bac689AD6867a605633520D70C49e1dCce853','0x72F860bF73ffa3FC42B97BbcF43Ae80280CFcdc3','0xf2D479DaEdE7F9e270a90615F8b1C52F3C487bC7','0xB78d5580d6D897DE60E1A942A5C1dc07Bc716943','0x848Ac8ddC199221Be3dD4e4124c462B806B6C4Fd','0x0096ffda7A8f8E00e9F8Bbd1cF082c14FA9d642e','0x137995beEEec688296B0118131C1052546475fF3','0x473A41e71618dD0709Ba56518256793371427d79','0x60170664b52c035Fcb32CF5c9694b22b47882e5F','0x97b25DE9F61BBBA2aD51F1b706D4D7C04257f33A','0xe7a1B580942148451E47b92e95aEB8d31B0acA37','0xBcdD90034eB73e7Aec2598ea9082d381a285f63b','0x80A42Dc2909C0873294c5E359e8DF49cf21c74E4','0xc6030Afa09EDec1fd8e63a1dE10fC00E0146DaF3','0x268CC8248FFB72Cd5F3e73A9a20Fa2FF40EfbA61','0x04B43D632F34ba4D4D72B0Dc2DC4B30402e5Cf88','0xc2Ff93228441Ff4DD904c60Ecbc1CfA2886C76eB','0x68eE50dD7F1573423EE0Ed9c66Fc1A696f937e81','0x7f46E45f6e0361e7B9304f338404DA85CB94E33D','0xd44ee492889C078934662cfeEc790883DCe245f3','0xA7CFd21223151700FB82684Cd9c693596267375D','0x3bcb9A3DaB194C6D8D44B424AF383E7Db51C82BD','0xE7CB27ad646C49dC1671Cb9207176D864922C431','0x60A3810a3963f23Fa70591435bbe93BF8786E202','0x6513757978E89e822772c16B60AE033781A29A4F','0x0776b936344DE7bd58A4738306a6c76835ce5D3F','0xA2cef1763e59198025259d76Ce8F9E60d27B17B5','0x3E022D84D397F18743a90155934aBAC421D5FA4C','0xCCb93dABD71c8Dad03Fc4CE5559dC3D89F67a260','0x04b9dA42306B023f3572e106B11D82aAd9D32EBb'];
event_groups = ['tavern','swaps','liquidity','gardens','bank','alchemist','quests','wallet','airdrops','lending'];
paymentsTotal = 0;
paymentsTotalValue = 0;
var sid='';
var selectedAccount='';
const balanceOfABI = [
  {
      "constant": true,
      "inputs": [
          {
              "name": "_owner",
              "type": "address"
          }
      ],
      "name": "balanceOf",
      "outputs": [
          {
              "name": "balance",
              "type": "uint256"
          }
      ],
      "payable": false,
      "stateMutability": "view",
      "type": "function"
  },
];
let transferABI = [
   {
       'constant': false,
       'inputs': [
           {
               'name': '_to',
               'type': 'address'
           },
           {
               'name': '_value',
               'type': 'uint256'
           }
       ],
       'name': 'transfer',
       'outputs': [
           {
               'name': '',
               'type': 'bool'
           }
       ],
       'type': 'function'
   }
]

function getTokenName(address, network) {
  result = address;
  if (network == 'dfkchain' && address in DFKCHAIN_TOKENS) {
    result = DFKCHAIN_TOKENS[address];
  }
  if (network == 'klaytn' && address in KLAYTN_TOKENS) {
    result = KLAYTN_TOKENS[address];
  }
  if (network == 'harmony' && address in HARMONY_TOKENS) {
    result = HARMONY_TOKENS[address];
  }
  if (network == 'avalanche' && address in AVALANCHE_TOKENS) {
    result = AVALANCHE_TOKENS[address];
  }
  return result;
}
function getAirdropName(address) {
  if (address in AIRDROP_ADDRESSES) {
    return AIRDROP_ADDRESSES[address];
  } else {
    return '';
  }
}
function getLendingName(address) {
  if (address in LENDING_ADDRESSES) {
    return LENDING_ADDRESSES[address];
  } else {
    return address;
  }
}

// Update running total summary of airdrop/payment income
function updatePaymentTotal(addAmount, addValue) {
  paymentsTotal += addAmount;
  paymentsTotalValue += addValue;
  $("#paymentsTotalValue").html(paymentsTotal.toFixed(3) + " Jewel (" + usdFormat.format(paymentsTotalValue) + ")");
  $("#paymentsTotal").show();
}

// Populates the transaction data that was generated into the page
function loadReport(results, contentType, eventGroup='all') {
  if (contentType == 'tax') {
    loadTaxes(results);
  } else {
    var eventResult = results.event_records;
    var progressIndex = event_groups.findIndex((element) => {element == eventGroup;});
    $("#mappingProgress").progressbar( "option", "value", (2000 / event_groups.length) + ((progressIndex+1) * (2000 / event_groups.length)));
    $("#mappingPercent").html("Loading " + eventGroup + " Events...");
    switch(eventGroup) {
      case 'tavern':
        loadTavernEvents(eventResult[eventGroup]);
        break;
      case 'swaps':
        loadSwapEvents(eventResult[eventGroup]);
        break;
      case 'liquidity':
        loadLiquidityEvents(eventResult[eventGroup]);
        break;
      case 'gardens':
        loadGardensEvents(eventResult[eventGroup]);
        break;
      case 'bank':
        loadBankEvents(eventResult[eventGroup]);
        break;
      case 'alchemist':
        loadAlchemistEvents(eventResult[eventGroup]);
        break;
      case 'airdrops':
        loadAirdropEvents(eventResult[eventGroup]);
        break;
      case 'lending':
        loadLendingEvents(eventResult[eventGroup]);
        break;
      case 'quests':
        loadQuestEvents(eventResult[eventGroup]);
        break;
      case 'wallet':
        loadWalletEvents(eventResult[eventGroup]);
        $("#mappingProgress").progressbar( "option", "value", 2000);
        $("#mappingPercent").html("Ready!");
        break;
      default:
        $("#mappingProgress").progressbar( "option", "value", 2000);
        $("#mappingPercent").html("Ready!");
    }
  }
}

function addTaxRow(recordCategory, description, acquiredDate, soldDate, proceeds, costs, gains, accountedString) {
  $('#tax_' + recordCategory + '_data').show();
  $('#tax_' + recordCategory + '_data').append(
    '<tr><td>' + description + '</td>' +
    '<td>' + acquiredDate + '</td>' +
    '<td>' + soldDate + '</td>' +
    '<td>' + usdFormat.format(proceeds) + '</td>' +
    '<td>' + usdFormat.format(costs) + accountedString + '</td>' +
    '<td>' + usdFormat.format(gains) + '</td></tr>'
  );
}

function loadTaxes(results) {
  var taxResult = results.tax_records;
  if (taxResult == undefined) {
    alert('No results - ' + results);
    return
  }
  $("#mappingProgress").progressbar( "option", "value", 200);
  $("#mappingPercent").html("Loading Tax Report...");

  // Populate the main Tax Report from response
  for (var i = 0; i < taxResult.length; i++) {
    recordCategory = taxResult[i].category;
    accountedString = '';
    if ( taxResult[i].amountNotAccounted > .01 ) {
      accountedString = '<img src="' + BASE_SCRIPT_URL + 'static/images/alertred.png" style="max-width:24px;float:right; title="Only found Partial Cost Basis for this item."/>';
    }

    setTimeout(addTaxRow, 50, recordCategory, taxResult[i].description, taxResult[i].acquiredDate, taxResult[i].soldDate, taxResult[i].proceeds, taxResult[i].costs, taxResult[i].gains, accountedString);
  }
  // some very small accounts may result in no tax generating records
  // switch to the transaction tab in this case as there may be something there
  if ( taxResult.length == 0 ) {
    switchView('transaction')
  }
}

function addTavernRow(seller, eventDate, itemType, itemID, event, coinType, coinCost, fiatAmount, network) {
  $('#tx_tavern_data').show();
  $('#tx_tavern_data').append(
    '<tr title="' + seller + '"><td>' + eventDate.toUTCString() + '</td>' +
    '<td>' + itemType + '</td>' +
    '<td>' + itemID + '</td>' +
    '<td>' + event + '</td>' +
    '<td>' + getTokenName(coinType, network) + '</td>' +
    '<td>' + coinCost + '</td>' +
    '<td>' + usdFormat.format(fiatAmount) + '</td></tr>'
  );
}

function loadTavernEvents(tavernEvents) {
  // Populate the Transaction list with Hero Data
  var tavernTotals = {}
  var tavernCosts = {}
  $("#tx_tavern_data").html('<tr><th>Block Date</th><th>Item Type</th><th>Item ID</th><th>Event</th><th>Coin</th><th>Coin Amt</th><th>USD Amount</th></tr>');
  for (var i = 0; i < tavernEvents.length; i++) {
    var eventDate = new Date(tavernEvents[i].timestamp * 1000);
    var coinCost = tavernEvents[i].coinCost;
    var fiatAmount = tavernEvents[i].fiatAmount;

    if (tavernEvents[i].coinCost['py/reduce'] != undefined) {
      coinCost = tavernEvents[i].coinCost['py/reduce'][1]['py/tuple'][0];
    }
    coinCost = Number(coinCost)
    if (tavernEvents[i].fiatAmount['py/reduce'] != undefined) {
      fiatAmount = tavernEvents[i].fiatAmount['py/reduce'][1]['py/tuple'][0];
    }

    setTimeout(addTavernRow, 50, tavernEvents[i].seller, eventDate, tavernEvents[i].itemType, tavernEvents[i].itemID, tavernEvents[i].event, tavernEvents[i].coinType, coinCost, fiatAmount, tavernEvents[i].network);

    if ( tavernEvents[i].event in tavernTotals ) {
      tavernTotals[tavernEvents[i].event] += 1;
      tavernCosts[tavernEvents[i].event] += coinCost
    } else {
      tavernTotals[tavernEvents[i].event] = 1;
      tavernCosts[tavernEvents[i].event] = coinCost
    }
    $('#tx_tavern_count').html(' (' + (i + 1) + ')');
  }
  // Add summary data for each event
  var tavernTable = '<table><tr><th>Event</th><th>Count</th><th>Total Token Amt</th></tr>';
  for (let k in tavernTotals) {
    tavernTable = tavernTable + '<tr><td>' + k + 's</td><td>' + tavernTotals[k] + '</td><td>' + tavernCosts[k].toFixed(1) + '</td></tr>';
  }
  $("#smy_tavern_data").html(tavernTable + '</table>');
}

function addSwapRow(eventDate, swapType, swapAmount, receiveType, receiveAmount, fiatSwapValue, fiatReceiveValue, network) {
  $('#tx_swaps_data').show();
  $('#tx_swaps_data').append(
    '<tr><td>' + eventDate.toUTCString() + '</td>' +
    '<td>' + getTokenName(swapType, network) + '</td>' +
    '<td>' + Number(swapAmount).toFixed(3) + '</td>' +
    '<td>' + getTokenName(receiveType, network) + '</td>' +
    '<td>' + Number(receiveAmount).toFixed(3) + '</td>' +
    '<td>' + usdFormat.format(fiatSwapValue) + '</td>' +
    '<td>' + usdFormat.format(fiatReceiveValue) + '</td></tr>'
  );
}

function loadSwapEvents(swapEvents) {
  // Populate the Transaction list with Swaps Data
  var swapTotals = {}
  $("#tx_swaps_data").html('<tr><th>Block Date</th><th>Swap Type</th><th>Swap Amount</th><th>Receive Type</th><th>Receive Amount</th><th>Swap USD Amount</th><th>Receive USD Amount</th></tr>');
  for (var i = 0; i < swapEvents.length; i++) {
    var eventDate = new Date(swapEvents[i].timestamp * 1000);
    var fiatReceiveValue = swapEvents[i].fiatReceiveValue;
    var fiatSwapValue = swapEvents[i].fiatSwapValue;

    if (swapEvents[i].fiatReceiveValue['py/reduce'] != undefined) {
      fiatReceiveValue = swapEvents[i].fiatReceiveValue['py/reduce'][1]['py/tuple'][0];
    }
    if (swapEvents[i].fiatSwapValue['py/reduce'] != undefined) {
      fiatSwapValue = swapEvents[i].fiatSwapValue['py/reduce'][1]['py/tuple'][0];
    }

    setTimeout(addSwapRow, 50, eventDate, swapEvents[i].swapType, swapEvents[i].swapAmount['py/reduce'][1]['py/tuple'][0], swapEvents[i].receiveType, swapEvents[i].receiveAmount['py/reduce'][1]['py/tuple'][0], fiatSwapValue, fiatReceiveValue, swapEvents[i].network);

    swapName = getTokenName(swapEvents[i].swapType, swapEvents[i].network);
    rcvdName = getTokenName(swapEvents[i].receiveType, swapEvents[i].network);
    if ( swapName in swapTotals ) {
      swapTotals[swapName][0] += parseInt(swapEvents[i].swapAmount['py/reduce'][1]['py/tuple'][0]);
    } else {
      swapTotals[swapName] = [parseInt(swapEvents[i].swapAmount['py/reduce'][1]['py/tuple'][0]), 0];
    }
    if ( rcvdName in swapTotals ) {
      swapTotals[rcvdName][1] += parseInt(swapEvents[i].receiveAmount['py/reduce'][1]['py/tuple'][0]);
    } else {
      swapTotals[rcvdName] = [0, parseInt(swapEvents[i].receiveAmount['py/reduce'][1]['py/tuple'][0])];
    }
    $('#tx_swaps_count').html(' (' + (i + 1) + ')');
  }
  // Add summary data for each coin type swapped
  var swapTable = '<table><tr><th>Coin Type</th><th>Total Sent</th><th>Total Rcvd</th></tr>';
  for (let k in swapTotals) {
    swapTable = swapTable + '<tr><td>' + k + '</td><td>' + swapTotals[k][0].toFixed(0) + '</td><td>' + swapTotals[k][1].toFixed(0) + '</td></tr>';
  }
  $("#smy_swaps_data").html(swapTable + '</table>');
}

function addLiquidityRow(eventDate, action, poolName, poolAmount, coin1Amount, coin2Amount, coin1FiatValue, coin2FiatValue) {
  $('#tx_liquidity_data').show();
  $('#tx_liquidity_data').append(
    '<tr><td>' + eventDate.toUTCString() + '</td>' +
    '<td>' + action + ' ' + poolName + '</td>' +
    '<td>' + Number(poolAmount).toFixed(5) + '</td>' +
    '<td>' + Number(coin1Amount).toFixed(3) + '</td>' +
    '<td>' + Number(coin2Amount).toFixed(3) + '</td>' +
    '<td>' + usdFormat.format(coin1FiatValue) + '</td>' +
    '<td>' + usdFormat.format(coin2FiatValue) + '</td></tr>'
  );
}

function loadLiquidityEvents(liquidityEvents) {
  // Populate the Transaction list with Liquidity Pool events
  var liquidityTotals = {};
  $("#tx_liquidity_data").html('<tr><th>Block Date</th><th>Pool Action</th><th>LP Tokens</th><th>Coin 1 Amount</th><th>Coin 2 Amount</th><th>Coin 1 USD Value</th><th>Coin 2 USD Value</th></tr>');
  for (var i = 0; i < liquidityEvents.length; i++) {
    var eventDate = new Date(liquidityEvents[i].timestamp * 1000);
    var coin1FiatValue = liquidityEvents[i].coin1FiatValue;
    var coin2FiatValue = liquidityEvents[i].coin2FiatValue;
    var poolName = getTokenName(liquidityEvents[i].coin1Type, liquidityEvents[i].network) + '/' + getTokenName(liquidityEvents[i].coin2Type, liquidityEvents[i].network);
    if (liquidityEvents[i].coin1FiatValue['py/reduce'] != undefined) {
      coin1FiatValue = Number(liquidityEvents[i].coin1FiatValue['py/reduce'][1]['py/tuple'][0]);
    }
    if (liquidityEvents[i].coin2FiatValue['py/reduce'] != undefined) {
      coin2FiatValue = Number(liquidityEvents[i].coin2FiatValue['py/reduce'][1]['py/tuple'][0]);
    }

    setTimeout(addLiquidityRow, 50, eventDate, liquidityEvents[i].action, poolName, liquidityEvents[i].poolAmount['py/reduce'][1]['py/tuple'][0], liquidityEvents[i].coin1Amount['py/reduce'][1]['py/tuple'][0], liquidityEvents[i].coin2Amount['py/reduce'][1]['py/tuple'][0], coin1FiatValue, coin2FiatValue);

    if ( poolName in liquidityTotals ) {
      if (liquidityEvents[i].action == 'withdraw') {
        liquidityTotals[poolName][0] += (coin1FiatValue + coin2FiatValue);
      } else {
        liquidityTotals[poolName][1] += (coin1FiatValue + coin2FiatValue);
      }
    } else {
      if (liquidityEvents[i].action == 'withdraw') {
        liquidityTotals[poolName] = [coin1FiatValue + coin2FiatValue, 0];
      } else {
        liquidityTotals[poolName] = [0, coin1FiatValue + coin2FiatValue];
      }
    }
    $('#tx_liquidity_count').html(' (' + (i + 1) + ')');
  }
  // Add summary data for each pool
  var liquidityTable = '<table><tr><th>LP</th><th>Total Out</th><th>Total In</th></tr>';
  for (let k in liquidityTotals) {
    liquidityTable = liquidityTable + '<tr><td>' + k + '</td><td>' + usdFormat.format(liquidityTotals[k][0]) + '</td><td>' + usdFormat.format(liquidityTotals[k][1]) + '</td></tr>';
  }
  $("#smy_liquidity_data").html(liquidityTable + '</table>');
}

function addGardensRow(eventDate, location, event, coinType, coinAmount, fiatValue, network) {
  $('#tx_gardens_data').show();
  $('#tx_gardens_data').append(
    '<tr><td>' + eventDate.toUTCString() + '</td>' +
    '<td>' + location + '</td>' +
    '<td>' + event + '</td>' +
    '<td>' + getTokenName(coinType, network) + '</td>' +
    '<td>' + Number(coinAmount).toFixed(5) + '</td>' +
    '<td>' + usdFormat.format(fiatValue) + '</td></tr>'
  );
}

function loadGardensEvents(gardensEvents) {
  // Populate the Transaction list with Jewel rewards events from Gardens LPs
  var gardensTotals = {};
  $("#tx_gardens_data").html('<tr><th>Block Date</th><th>Location</th><th>Event</th><th>Coin Type</th><th>Coin Amount</th><th>Coin USD Value</th></tr>');
  for (var i = 0; i < gardensEvents.length; i++) {
    var eventDate = new Date(gardensEvents[i].timestamp * 1000)
    var coinAmount = gardensEvents[i].coinAmount
    var fiatValue = gardensEvents[i].fiatValue;
    if (gardensEvents[i].coinAmount['py/reduce'] != undefined) {
      coinAmount = gardensEvents[i].coinAmount['py/reduce'][1]['py/tuple'][0];
    }
    if (gardensEvents[i].fiatValue['py/reduce'] != undefined) {
      fiatValue = gardensEvents[i].fiatValue['py/reduce'][1]['py/tuple'][0];
    }
    var location = 'Farms'
    var lpName = String(getTokenName(gardensEvents[i].coinType, gardensEvents[i].network))
    if (lpName.includes('Jewel LP')) {
      location = 'Serendale'
    }
    if (lpName.includes('Venom LP')) {
      location = 'ViperSwap'
    }
    if (lpName.includes('Tranquil LP')) {
      location = 'Tranquil Finance'
    }
    if (lpName.includes('Crystal LP')) {
      location = 'Crystalvale'
    }
    if (lpName.includes('Pangolin LP')) {
      location = 'Pangolin'
    }

    setTimeout(addGardensRow, 50, eventDate, location, gardensEvents[i].event, gardensEvents[i].coinType, coinAmount, fiatValue, gardensEvents[i].network);

    if ( lpName + ' ' + gardensEvents[i].event in gardensTotals ) {
      gardensTotals[lpName + ' ' + gardensEvents[i].event] += Number(coinAmount);
    } else {
      gardensTotals[lpName + ' ' + gardensEvents[i].event] = Number(coinAmount);
    }
    // Maintain header total of Jewel income
    if (fiatValue > 0 && gardensEvents[i].coinType in JEWEL_ADDRESSES) {
      updatePaymentTotal(Number(coinAmount), Number(fiatValue));
    }
    $('#tx_gardens_count').html(' (' + (i + 1) + ')');
  }
  // Add summary data for each event
  var gardensTable = '';
  for (let k in gardensTotals) {
    gardensTable = gardensTable + '<tr><td>' + k + '</td><td>' + gardensTotals[k].toFixed(3) + '</td></tr>';
  }
  $("#smy_gardens_data").html('<table>' + gardensTable + '</table>');
}

function addBankRow(eventDate, bankLocation, action, xRate, coinType, coinAmount, fiatValue, network) {
  $('#tx_bank_data').show();
  $('#tx_bank_data').append(
    '<tr><td>' + eventDate.toUTCString() + '</td>' +
    '<td>' + bankLocation + '</td>' +
    '<td>' + action + '</td>' +
    '<td>' + Number(xRate).toFixed(4) + '</td>' +
    '<td>' + getTokenName(coinType, network) + '</td>' +
    '<td>' + Number(coinAmount).toFixed(5) + '</td>' +
    '<td>' + usdFormat.format(fiatValue) + '</td></tr>'
  );
}

function loadBankEvents(bankEvents) {
  // Populate the transaction list with Bank deposit/withdrawal events
  var bankTotals = {};
  $("#tx_bank_data").html('<tr><th>Block Date</th><th>Location</th><th>Action</th><th>xJewel Ratio/cJewel</th><th>Coin Type</th><th>Coin Amount</th><th>Coin USD Value</th></tr>');
  for (var i = 0; i < bankEvents.length; i++) {
    var eventDate = new Date(bankEvents[i].timestamp * 1000)
    var bankLocation = 'Serendale';
    if (['0x04b9dA42306B023f3572e106B11D82aAd9D32EBb','0x9ed2c155632C042CB8bC20634571fF1CA26f5742','0xCCb93dABD71c8Dad03Fc4CE5559dC3D89F67a260'].includes(bankEvents[i].coinType)) {
      bankLocation = 'Crystalvale';
    }
    var xRate = bankEvents[i].xRate;
    if (bankEvents[i].xRate['py/reduce'] != undefined) {
      xRate = bankEvents[i].xRate['py/reduce'][1]['py/tuple'][0];
    }
    var coinAmount = bankEvents[i].coinAmount;
    if (bankEvents[i].coinAmount['py/reduce'] != undefined) {
      coinAmount = bankEvents[i].coinAmount['py/reduce'][1]['py/tuple'][0];
    }
    var fiatValue = bankEvents[i].fiatValue;
    if (bankEvents[i].fiatValue['py/reduce'] != undefined) {
      fiatValue = bankEvents[i].fiatValue['py/reduce'][1]['py/tuple'][0];
    }
    setTimeout(addBankRow, 50, eventDate, bankLocation, bankEvents[i].action, xRate, bankEvents[i].coinType, coinAmount, fiatValue, bankEvents[i].network);

    coinName = getTokenName(bankEvents[i].coinType, bankEvents[i].network)
    if ( coinName in bankTotals ) {
      if ( bankEvents[i].action == 'withdraw' ) {
        bankTotals[coinName][0] += Number(bankEvents[i].coinAmount['py/reduce'][1]['py/tuple'][0]);
      }
      if ( bankEvents[i].action == 'deposit' ) {
        bankTotals[coinName][1] += Number(bankEvents[i].coinAmount['py/reduce'][1]['py/tuple'][0]);
      }
    } else {
      if ( bankEvents[i].action == 'withdraw' ) {
        bankTotals[coinName] = [Number(bankEvents[i].coinAmount['py/reduce'][1]['py/tuple'][0]), 0];
      }
      if ( bankEvents[i].action == 'deposit' ) {
        bankTotals[coinName] = [0, Number(bankEvents[i].coinAmount['py/reduce'][1]['py/tuple'][0])];
      }
    }
    $('#tx_bank_count').html(' (' + (i + 1) + ')');
  }
  // Add summary data for each event
  var bankTable = '<table><tr><th>token</th><th>total withdraws</th><th>total deposits</th></tr>';
  for (let k in bankTotals) {
    bankTable = bankTable + '<tr><td>' + k + '</td><td>' + bankTotals[k][0].toFixed(3) + '</td><td>' + bankTotals[k][1].toFixed(3) + '</td></tr>';
  }
  $("#smy_bank_data").html(bankTable + '</table>');
}

function addAlchemistRow(eventDate, craftingType, craftedAmount, craftingCosts, fiatCraftedValue, fiatIngredientsValue, network) {
  $('#tx_alchemist_data').show();
  $('#tx_alchemist_data').append(
    '<tr><td>' + eventDate.toUTCString() + '</td>' +
    '<td>' + getTokenName(craftingType, network) + 'x' + craftedAmount + '</td>' +
    '<td>' + craftingCosts + '</td>' +
    '<td>' + usdFormat.format(fiatCraftedValue) + '</td>' +
    '<td>' + usdFormat.format(fiatIngredientsValue) + '</td></tr>'
  );
}

function loadAlchemistEvents(alchemistEvents) {
  // Populate the Transaction list with Alchemist Data
  var craftingTotals = {}
  $("#tx_alchemist_data").html('<tr><th>Block Date</th><th>Item Type</th><th>Crafting Costs</th><th>Item Fiat Value</th><th>Ingredients Fiat Value</th></tr>');
  for (var i = 0; i < alchemistEvents.length; i++) {
    var eventDate = new Date(alchemistEvents[i].timestamp * 1000);
    var craftedAmount = alchemistEvents[i].craftingAmount;
    var fiatCraftedValue = alchemistEvents[i].fiatValue;
    var fiatIngredientsValue = alchemistEvents[i].costsFiatValue;

    if (alchemistEvents[i].craftingAmount['py/reduce'] != undefined) {
      craftedAmount = alchemistEvents[i].craftingAmount['py/reduce'][1]['py/tuple'][0];
    }
    if (alchemistEvents[i].fiatValue['py/reduce'] != undefined) {
      fiatCraftedValue = alchemistEvents[i].fiatValue['py/reduce'][1]['py/tuple'][0];
    }
    if (alchemistEvents[i].costsFiatValue['py/reduce'] != undefined) {
      fiatIngredientsValue = alchemistEvents[i].costsFiatValue['py/reduce'][1]['py/tuple'][0];
    }

    setTimeout(addAlchemistRow, 50, eventDate, alchemistEvents[i].craftingType, craftedAmount, alchemistEvents[i].craftingCosts, fiatCraftedValue, fiatIngredientsValue, alchemistEvents[i].network);

    craftedName = getTokenName(alchemistEvents[i].craftingType, alchemistEvents[i].network)
    if ( craftedName in craftingTotals ) {
      craftingTotals[craftedName][0] += parseInt(craftedAmount);
      craftingTotals[craftedName][1] += fiatCraftedValue;
      craftingTotals[craftedName][2] += fiatIngredientsValue;
    } else {
      craftingTotals[craftedName] = [parseInt(craftedAmount), fiatCraftedValue, fiatIngredientsValue];
    }
    $('#tx_alchemist_count').html(' (' + (i + 1) + ')');
  }
  // Add summary data for each craft type
  var craftingTable = '<table><tr><th>Item</th><th>Total Crafted</th><th>Total Value</th><th>Total Ingredient Value</th></tr>';
  for (let k in craftingTotals) {
    craftingTable = craftingTable + '<tr><td>' + k + '</td><td>' + craftingTotals[k][0].toFixed(0) + '</td><td>' + usdFormat.format(craftingTotals[k][1]) + '</td><td>' + usdFormat.format(craftingTotals[k][2]) + '</td></tr>';
  }
  $("#smy_alchemist_data").html(craftingTable + '</table>');
}

function addAirdropRow(eventDate, location, tokenReceived, tokenAmount, fiatValue, network) {
  $('#tx_airdrops_data').show();
  $('#tx_airdrops_data').append(
    '<tr><td>' + eventDate.toUTCString() + '</td>' +
    '<td>' + location + '</td>' +
    '<td>' + getTokenName(tokenReceived, network) + '</td>' +
    '<td>' + tokenAmount + '</td>' +
    '<td>' + usdFormat.format(fiatValue) + '</td></tr>'
  );
}

function loadAirdropEvents(airdropEvents) {
  // Populate the transaction list with Airdrop events
  var airdropTotals = {};
  var airdropValues = {};
  $("#tx_airdrops_data").html('<tr><th>Block Date</th><th>Location</th><th>Token Type</th><th>Token Amount</th><th>Token USD Value</th></tr>');
  for (var i = 0; i < airdropEvents.length; i++) {
    var eventDate = new Date(airdropEvents[i].timestamp * 1000)
    var tokenAmount = airdropEvents[i].tokenAmount;
    var fiatValue = airdropEvents[i].fiatValue
    if (airdropEvents[i].tokenAmount['py/reduce'] != undefined) {
      tokenAmount = Number(airdropEvents[i].tokenAmount['py/reduce'][1]['py/tuple'][0]);
    }
    if (airdropEvents[i].fiatValue['py/reduce'] != undefined) {
      fiatValue = airdropEvents[i].fiatValue['py/reduce'][1]['py/tuple'][0];
    }
    var location = 'Airdrop';
    var airdropName = getAirdropName(airdropEvents[i].address);
    if (airdropName != '') {
      location = airdropName;
    }

    setTimeout(addAirdropRow, 50, eventDate, location, airdropEvents[i].tokenReceived, tokenAmount, fiatValue, airdropEvents[i].network);

    rcvdName = getTokenName(airdropEvents[i].tokenReceived, airdropEvents[i].network);
    if ( rcvdName in airdropTotals ) {
      airdropTotals[rcvdName] += Number(tokenAmount);
    } else {
      airdropTotals[rcvdName] = Number(tokenAmount);
    }
    if ( rcvdName in airdropValues ) {
      airdropValues[rcvdName] += Number(fiatValue);
    } else {
      airdropValues[rcvdName] = Number(fiatValue);
    }
    // Maintain header total of Jewel income
    if (fiatValue > 0 && airdropEvents[i].tokenReceived in JEWEL_ADDRESSES) {
      updatePaymentTotal(Number(tokenAmount), Number(fiatValue));
    }
    $('#tx_airdrops_count').html(' (' + (i + 1) + ')');
  }
  // Add summary data for each coin
  var airdropTable = '<table><tr><th>token</th><th>Total of Airdrops</th><th>USD Value</th></tr>';
  for (let k in airdropTotals) {
    airdropTable = airdropTable + '<tr><td>' + k + '</td><td>' + airdropTotals[k].toFixed(3) + '</td><td>' + usdFormat.format(airdropValues[k]) + '</td></tr>';
  }
  $("#smy_airdrops_data").html(airdropTable + '</table>');
}

function addLendingRow(eventDate, address, event, coinType, tokenAmount, fiatValue, network) {
  $('#tx_lending_data').show();
  $('#tx_lending_data').append(
    '<tr><td>' + eventDate.toUTCString() + '</td>' +
    '<td>' + getLendingName(address) + '</td>' +
    '<td>' + event + '</td>' +
    '<td>' + getTokenName(coinType, network) + '</td>' +
    '<td>' + Number(tokenAmount).toFixed(5) + '</td>' +
    '<td>' + usdFormat.format(fiatValue) + '</td></tr>'
  );
}

function loadLendingEvents(lendingEvents) {
  // Populate the transaction list with lending borrow/repay events
  var lendingTotals = {};
  $("#tx_lending_data").html('<tr><th>Block Date</th><th>Location</th><th>Action</th><th>Coin Type</th><th>Coin Amount</th><th>Coin USD Value</th></tr>');
  for (var i = 0; i < lendingEvents.length; i++) {
    var eventDate = new Date(lendingEvents[i].timestamp * 1000)
    var tokenAmount = lendingEvents[i].coinAmount;
    var fiatValue = lendingEvents[i].fiatValue;
    if (lendingEvents[i].coinAmount['py/reduce'] != undefined) {
      tokenAmount = Number(lendingEvents[i].coinAmount['py/reduce'][1]['py/tuple'][0]);
    }
    if (lendingEvents[i].fiatValue['py/reduce'] != undefined) {
      fiatValue = Number(lendingEvents[i].fiatValue['py/reduce'][1]['py/tuple'][0]);
    }

    setTimeout(addLendingRow, 50, eventDate, lendingEvents[i].address, lendingEvents[i].event, lendingEvents[i].coinType, tokenAmount, fiatValue, lendingEvents[i].network);

    switch (lendingEvents[i].event) {
      case 'lend':
        aIndex = 0;
        break;
      case 'redeem':
        aIndex = 1;
        break;
      case 'borrow':
        aIndex = 2;
        break;
      case 'repay':
        aIndex = 3;
        break;
      case 'liquidate':
        aIndex = 4;
        break;
      default:
        aIndex = 5;
    }
    var coinName = getTokenName(lendingEvents[i].coinType, lendingEvents[i].network);
    if ( coinName in lendingTotals ) {
      lendingTotals[coinName][aIndex] += tokenAmount;
    } else {
      aArray = [];
      for (e=0; e<6; e++) {
        if (e == aIndex) {
          aArray.push(tokenAmount);
        } else {
          aArray.push(0);
        }
      }
      lendingTotals[coinName] = aArray;
    }
    $('#tx_lending_count').html(' (' + (i + 1) + ')');
  }
  // Add summary data for each coin type
  var lendingTable = '<table><tr><th>Coin Type</th><th>Lent</th><th>Redeemed</th><th>Borrowed</th><th>Repaid</th><th>Liquidated</th></tr>';
  for (let k in lendingTotals) {
    lendingTable = lendingTable + '<tr><td>' + k + '</td><td>' + lendingTotals[k][0].toFixed(2) + '</td><td>' + lendingTotals[k][1].toFixed(2) + '</td><td>' + lendingTotals[k][2].toFixed(2) + '</td><td>' + lendingTotals[k][3].toFixed(2) + '</td><td>' + lendingTotals[k][4].toFixed(2) + '</td></tr>';
  }
  $("#smy_lending_data").html(lendingTable + '</table>');
}

function addQuestRow(eventDate, questLocation, rewardType, rewardAmount, fiatValue, network) {
  $('#tx_quests_data').show();
  $('#tx_quests_data').append(
    '<tr><td>' + eventDate.toUTCString() + '</td>' +
    '<td>' + questLocation + '</td>' +
    '<td>' + getTokenName(rewardType, network) + '</td>' +
    '<td>' + rewardAmount + '</td>' +
    '<td>' + usdFormat.format(fiatValue) + '</td></tr>'
  );
}

function loadQuestEvents(questEvents) {
  // Populate the transaction list with Quest reward receipts
  var questTotals = {};
  $("#tx_quests_data").html('<tr><th>Block Date</th><th>Location</th><th>Reward Type</th><th>Reward Amount</th><th>Reward USD Value</th></tr>');
  for (var i = 0; i < questEvents.length; i++) {
    var eventDate = new Date(questEvents[i].timestamp * 1000)
    var rewardAmount = questEvents[i].rewardAmount;
    var fiatValue = questEvents[i].fiatValue
    if (questEvents[i].rewardAmount['py/reduce'] != undefined) {
      rewardAmount = Number(questEvents[i].rewardAmount['py/reduce'][1]['py/tuple'][0]);
    }
    if (questEvents[i].fiatValue['py/reduce'] != undefined) {
      fiatValue = questEvents[i].fiatValue['py/reduce'][1]['py/tuple'][0];
    }
    var questLocation = 'Serendale';
    if (crystalvale_rewards.includes(questEvents[i].rewardType)) {
      questLocation = 'Crystalvale';
    }

    setTimeout(addQuestRow, 50, eventDate, questLocation, questEvents[i].rewardType, rewardAmount, fiatValue, questEvents[i].network);

    var rewardName = getTokenName(questEvents[i].rewardType, questEvents[i].network)
    if ( rewardName in questTotals ) {
      questTotals[rewardName] += rewardAmount;
    } else {
      questTotals[rewardName] = rewardAmount;
    }
    // Maintain header total of Jewel income
    if (fiatValue > 0 && questEvents[i].rewardType in JEWEL_ADDRESSES) {
      updatePaymentTotal(Number(rewardAmount), Number(fiatValue));
    }
    $('#tx_quests_count').html(' (' + (i + 1) + ')');
  }
  // Add summary data for each reward type
  var questTable = '<table><tr><th>Reward</th><th>total gained</th></tr>';
  for (let k in questTotals) {
    questTable = questTable + '<tr><td>' + k + '</td><td>' + questTotals[k].toFixed(3) + '</td></tr>';
  }
  $("#smy_quests_data").html(questTable + '</table>');
}

function addWalletRow(eventDate, action, address, coinType, coinAmount, fiatValue, network) {
  $('#tx_wallet_data').show();
  $('#tx_wallet_data').append(
    '<tr><td>' + eventDate.toUTCString() + '</td>' +
    '<td>' + action + '</td>' +
    '<td>' + address + '</td>' +
    '<td>' + getTokenName(coinType, network) + '</td>' +
    '<td>' + coinAmount + '</td>' +
    '<td>' + usdFormat.format(fiatValue) + '</td></tr>'
  );
}

function loadWalletEvents(walletEvents) {
  // Populate the transaction list with basic wallet in/out transfers
  var walletTotals = {};
  $("#tx_wallet_data").html('<tr><th>Block Date</th><th>Action</th><th>Address</th><th>Coin Type</th><th>Coin Amount</th><th>Coin USD Value</th></tr>');
  for (var i = 0; i < walletEvents.length; i++) {
    var eventDate = new Date(walletEvents[i].timestamp * 1000)
    var coinAmount = walletEvents[i].coinAmount;
    var fiatValue = walletEvents[i].fiatValue
    if (walletEvents[i].coinAmount['py/reduce'] != undefined) {
      coinAmount = Number(walletEvents[i].coinAmount['py/reduce'][1]['py/tuple'][0]);
    }
    if (walletEvents[i].fiatValue['py/reduce'] != undefined) {
      fiatValue = walletEvents[i].fiatValue['py/reduce'][1]['py/tuple'][0];
    }

    setTimeout(addWalletRow, 50, eventDate, walletEvents[i].action, walletEvents[i].address, walletEvents[i].coinType, coinAmount, fiatValue, walletEvents[i].network);

    var coinName = getTokenName(walletEvents[i].coinType, walletEvents[i].network);
    if ( coinName in walletTotals ) {
      if ( walletEvents[i].action == 'withdraw' ) {
        walletTotals[coinName][0] += coinAmount;
      } else {
        walletTotals[coinName][1] += coinAmount;
      }
    } else {
      if ( walletEvents[i].action == 'withdraw' ) {
        walletTotals[coinName] = [coinAmount, 0];
      } else {
        walletTotals[coinName] = [0, coinAmount];
      }
    }
    // Maintain header total of jewel income
    if (walletEvents[i].action == 'payment' && walletEvents[i].coinType in JEWEL_ADDRESSES && fiatValue > 0) {
      updatePaymentTotal(Number(coinAmount), Number(fiatValue));
    }
    $('#tx_wallet_count').html(' (' + (i + 1) + ')');
  }
  // Add summary data for each coin type
  var walletTable = '<table><tr><th>Coin Type</th><th>Total Out</th><th>Total In</th></tr>';
  for (let k in walletTotals) {
    walletTable = walletTable + '<tr><td>' + k + '</td><td>' + walletTotals[k][0].toFixed(0) + '</td><td>' + walletTotals[k][1].toFixed(0) + '</td></tr>';
  }
  $("#smy_wallet_data").html(walletTable + '</table>');
}
function docHeight() {
  var body = document.body,
  html = document.documentElement;

  return Math.max( body.scrollHeight, body.offsetHeight, 
    html.clientHeight, html.scrollHeight, html.offsetHeight );
}
function docWidth() {
  var body = document.body,
  html = document.documentElement;

  return Math.max( body.scrollWidth, body.offsetWidth, 
    html.clientWidth, html.scrollWidth, html.offsetWidth );
}
function showWindow(winId) {
  var maskHeight = docHeight();
  var maskWidth = docWidth();
  var maskElm = document.getElementById('mask');
  maskElm.style.width = maskWidth;
  maskElm.style.height = maskHeight;
  maskElm.style.display = 'block';
  winElm = document.getElementById(winId);
  let winH = window.innerHeight;
  let winW = window.innerWidth;
  winElm.style.top = (winH/2-winElm.offsetHeight/2) + window.scrollY;
  winElm.style.left = winW/2-winElm.offsetWidth/2;
  winElm.style.display = 'block';
}
function hideWindow(winId) {
  maskElm = document.getElementById('mask');
  maskElm.style.display = 'none';
  winElm = document.getElementById(winId);
  winElm.style.display = 'none';
}
function getQueryVar(qsvar) {
  var query = window.location.search.substring(1);
  var vars = query.split("&");
  for (var i=0;i<vars.length;i++) {
    var pair = vars[i].split("=");
    if (pair[0] == qsvar) {
      return pair[1];
    }
  }
  return -1;
}
function getCookie(cName, defaultValue) {
  if (document.cookie.length>0) {
    let dc = decodeURIComponent(document.cookie);
    cStart = dc.indexOf(cName + "=");
    if (cStart != -1) {
        cStart = cStart + cName.length+1;
        cEnd = dc.indexOf(";",cStart);
        if (cEnd == -1) cEnd = dc.length;
        return dc.substring(cStart,cEnd);
    } else {
      return defaultValue;
    }
  }
  return defaultValue;
}
function setCookie(cName, value, expireDays) {
    var exdate = new Date();
    exdate.setDate(exdate.getDate()+expireDays);
    document.cookie=cName + "=" + value+((expireDays==null) ? "" : ";expires="+exdate.toUTCString()) + ";path=/";
}
async function isConnected() {
  const accounts = await ethereum.request({method: 'eth_accounts'});
  if (accounts.length) {
    console.log(`You're connected to: ${accounts[0]}`);
    handleAccountsChanged(accounts);
    return true;
  } else {
    console.log("Metamask is not connected");
    return false;
  }
}
/* To connect using MetaMask */
async function connect() {
  if (window.ethereum) {
    console.log("requesting wallet connection");
    ethereum
      .request({ method: 'eth_requestAccounts' })
      .then(handleAccountsChanged)
      .catch((err) => {
        if (err.code === 4001) {
          console.log('connection rejected');
        } else {
          console.error(err);
        }
      });
  }
}

function handleAccountsChanged(accounts) {
  if (accounts.length === 0) {
    console.log('unlock and/or connect wallet');
  } else if (accounts[0] !== selectedAccount) {
    selectedAccount = accounts[0];
    sid = getCookie(`sid-${selectedAccount}`, '');
    setCookie('selectedAccount', selectedAccount, 180);
    console.log(`Wallet: ${selectedAccount}`);
    var addr = selectedAccount.substring(0, 6) + '...' + selectedAccount.substring(38, 42);
    document.getElementById("member").innerHTML = addr;
    document.getElementById('connectWallet').style.display = 'none';
    document.getElementById('loginButton').style.display = 'block';
    if (sid != '') {
      login();
    }
    refreshLists();
  }
}
function handleAuth(wAddress, signature) {
  var request = new XMLHttpRequest();
  request.open('GET', `${BASE_SCRIPT_URL}auth.py?account=${wAddress}&signature=${signature}`, true);
  console.log(`loading ${BASE_SCRIPT_URL}auth.py?account=${wAddress}&signature=${signature}`);
  request.onload = function() {
    console.log('load completed');
    if (!request.status || (request.status >= 400)) {
      alert('authentication failed.');
    } else {
      var resp = JSON.parse(request.responseText);
      console.log('loaded session '+resp['sid']);
      sid = resp['sid'];
      setCookie(`sid-${selectedAccount}`, sid, 180);
      setCookie('selectedAccount', selectedAccount, 180);
      document.getElementById('loginButton').style.display = 'none';
      document.getElementById('logoutButton').style.display = 'block';
      location.reload();
    }
  };
  request.send();
}
function handleLoginSignature(nonce) {
  window.web3 = new Web3(window.ethereum);
  const wAddress = selectedAccount;
  web3.eth.personal.sign(
    web3.utils.utf8ToHex(`Lilas Ledger login uses no transaction or gas fees.\n\nClick Sign to verify you own this wallet and login.\n\nIf you have cookies enabled, your session can persist for up to 6 months or until you logout.\n\nnonce: ${nonce}`),
    wAddress,
    (err, signature) => {
      if (err) {
        console.log(`error: ${err.message}`);
        return;
      }
      return handleAuth(wAddress, signature);
    }
  );
}
async function login(sign=false) {
  if (!isConnected()) {
    alert('you need to connect a wallet first!');
    return;
  }
  const wAddress = selectedAccount;
  var request = new XMLHttpRequest();
  request.open('GET', `${BASE_SCRIPT_URL}login.py?account=${wAddress}&sid=${sid}`, true);
  console.log(`loading: ${BASE_SCRIPT_URL}login.py?account=${wAddress}&sid=${sid}`);
  request.onload = function() {
    console.log('load completed');
    if (!request.status || (request.status >= 400)) {
      alert('Failed to login.');
    } else {
      var resp = JSON.parse(request.responseText);
      if ('sid' in resp) {
        sid = resp['sid']
        document.getElementById('loginButton').style.display = 'none';
        document.getElementById('logoutButton').style.display = 'block';
        refreshLists();
        return;
      }
      if ('nonce' in resp && sign) {
        console.log(`loaded nonce ${resp['nonce']}`);
        handleLoginSignature(resp['nonce']);
      }
      if ('error' in resp) {
        alert(resp['error']);
      }
    }
  };
  request.send();
}
async function logout() {
  if (!isConnected()) {
    alert('you need to connect a wallet first!');
    return;
  }
  const wAddress = selectedAccount;
  var request = new XMLHttpRequest();
  request.open('GET', `${BASE_SCRIPT_URL}logout.py?account=${wAddress}&sid=${sid}`, true);
  console.log(`loading: ${BASE_SCRIPT_URL}logout.py?account=${wAddress}&sid=${sid}`);
  request.onload = function() {
    console.log('load completed');
    if (!request.status || (request.status >= 400)) {
      alert('Failed to logout, server error.');
    } else {
      var resp = JSON.parse(request.responseText);
      if (resp['result'].indexOf("Error:") > -1) {
        alert(resp['result']);
      } else {
        sid = '';
        setCookie(`sid-${selectedAccount}`,'',-1);
        document.getElementById('loginButton').style.display = 'block';
        document.getElementById('logoutButton').style.display = 'none';
        location.reload();
      }
    }
  };
  request.send();
}
function resetConnection() {
  document.getElementById("member").innerHTML = '';
  document.getElementById('connectWallet').style.display = 'block';
  document.getElementById('loginButton').style.display = 'none';
  document.getElementById('logoutButton').style.display = 'none';
}
