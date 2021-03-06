one_hop_config = {
    0: ['D', 'D', 'U', 'U', 'U', 'D', 'D', 'U', 'U', 'U'],
    1: ['D', 'D', 'U', 'U', 'D', 'D', 'D', 'U', 'U', 'D'],
    2: ['D', 'D', 'U', 'D', 'D', 'D', 'D', 'U', 'D', 'D'],
    3: ['D', 'D', 'U', 'U', 'U', 'D', 'D', 'D', 'D', 'D'],
    4: ['D', 'D', 'U', 'U', 'D', 'D', 'D', 'D', 'D', 'D'],
    5: ['D', 'D', 'U', 'D', 'D', 'D', 'D', 'D', 'D', 'D'],
    6: ['D', 'D', 'U', 'U', 'U', 'D', 'D', 'U', 'U', 'D']
}

two_hop_config = {
    0: {
        'backhaul':['', '', '', '', 'D', '', '', '', 'U', ''],
        'access': one_hop_config[1]
    },
    1: {
        'backhaul': ['', '', '', 'U', '', '', '', '', '', 'D'],
        'access': one_hop_config[1]
    },
    2: {
        'backhaul': ['', '', '', '', 'D', '', '', '', 'U', 'D'],
        'access': one_hop_config[1]
    },
    3: {
        'backhaul': ['', '', '', 'U', 'D', '', '', '', '', 'D'],
        'access': one_hop_config[1]
    },
    4: {
        'backhaul': ['', '', '', 'U', 'D', '', '', '', 'U', 'D'],
        'access': one_hop_config[1]
    },
    5: {
        'backhaul': ['', '', 'U', '', '', '', '', '', 'D', ''],
        'access': one_hop_config[2]
    },
    6: {
        'backhaul': ['', '', '', 'D', '', '', '', 'U', '', ''],
        'access': one_hop_config[2]
    },
    7: {
        'backhaul': ['', '', 'U', '', 'D', '', '', '', 'D', ''],
        'access': one_hop_config[2]
    },
    8: {
        'backhaul': ['', '', '', 'D', '', '', '', 'U', '', 'D'],
        'access': one_hop_config[2]
    },
    9: {
        'backhaul': ['', '', 'U', 'D', 'D', '', '', '', 'D', ''],
        'access': one_hop_config[2]
    },
    10: {
        'backhaul': ['', '', '', 'D', '', '', '', 'U', 'D', 'D'],
        'access': one_hop_config[2]
    },
    11: {
        'backhaul': ['', '', '', 'U', '', '', '', 'D', '', 'D'],
        'access': one_hop_config[3]
    },
    12: {
        'backhaul': ['', '', '', 'U', '', '', '', 'D', 'D', 'D'],
        'access': one_hop_config[3]
    },
    13: {
        'backhaul': ['', '', '', 'U', '', '', '', '', '', 'D'],
        'access': one_hop_config[4]
    },
    14: {
        'backhaul': ['', '', '', 'U', '', '', '', 'D', '', 'D'],
        'access': one_hop_config[4]
    },
    15: {
        'backhaul': ['', '', '', 'U', '', '', '', '', 'D', 'D'],
        'access': one_hop_config[4]
    },
    16: {
        'backhaul': ['', '', '', 'U', '', '', '', 'D', 'D', 'D'],
        'access': one_hop_config[4]
    },
    17: {
        'backhaul': ['', '', '', 'U', 'D', '', '', 'D', 'D', 'D'],
        'access': one_hop_config[4]
    },
    18: {
        'backhaul': ['', '', '', '', 'U', '', '', '', '', 'D'],
        'access': one_hop_config[6]
    }
}