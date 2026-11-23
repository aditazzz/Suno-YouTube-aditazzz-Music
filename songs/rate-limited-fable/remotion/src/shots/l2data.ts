// lane L2 (rl_l2_act): her acting plates + the quads the shots pin in code (stage px). Written by workers/rl_l2_act/prep_l2.py; do not hand-edit.
export type L2Plate = { src: string; final: boolean; fg?: string; hair?: string; clean?: string; pop1?: string; pop2?: string; pop3?: string };
export const L2P: Record<string, L2Plate> = {
 "6C": {
  "src": "l2/6C.jpg",
  "final": true
 },
 "7D_smile": {
  "src": "l2/7D_smile.jpg",
  "final": true
 },
 "7D_frozen": {
  "src": "l2/7D_frozen.jpg",
  "final": true
 },
 "9A": {
  "src": "l2/9A.jpg",
  "final": true,
  "fg": "l2/9A_fg.png",
  "hair": "l2/9A_hair.png",
  "clean": "l2/9A_clean.jpg"
 },
 "9A_squat": {
  "src": "l2/9A_squat.jpg",
  "final": true,
  "fg": "l2/9A_squat_fg.png",
  "hair": "l2/9A_squat_hair.png",
  "clean": "l2/9A_squat_clean.jpg"
 },
 "9C": {
  "src": "l2/9C.jpg",
  "final": false
 },
 "9E_bail": {
  "src": "l2/9E_bail.jpg",
  "final": true,
  "fg": "l2/9E_bail_fg.png",
  "hair": "l2/9E_bail_hair.png",
  "clean": "l2/9E_bail_clean.jpg"
 },
 "9E_w2": {
  "src": "l2/9E_w2.jpg",
  "final": true
 },
 "9G": {
  "src": "l2/9G.jpg",
  "final": true,
  "pop1": "l2/9G_pop1.jpg",
  "pop2": "l2/9G_pop2.jpg",
  "pop3": "l2/9G_pop3.jpg"
 },
 "12A_on": {
  "src": "l2/12A_on.jpg",
  "final": true
 },
 "12A_back": {
  "src": "l2/12A_back.jpg",
  "final": true
 },
 "12B_w2": {
  "src": "l2/12B_w2.jpg",
  "final": true
 },
 "12B_tree": {
  "src": "l2/12B_tree.jpg",
  "final": true
 },
 "12B_baby": {
  "src": "l2/12B_baby.jpg",
  "final": true
 },
 "12B_child": {
  "src": "l2/12B_child.jpg",
  "final": true
 },
 "12C_cat": {
  "src": "l2/12C_cat.jpg",
  "final": true
 },
 "12C_coop": {
  "src": "l2/12C_coop.jpg",
  "final": true
 },
 "12C_her": {
  "src": "l2/12C_her.jpg",
  "final": true
 },
 "12D_sway": {
  "src": "l2/12D_sway.jpg",
  "final": true
 },
 "12D_flop": {
  "src": "l2/12D_flop.jpg",
  "final": true
 },
 "12E_stare": {
  "src": "l2/12E_stare.jpg",
  "final": true
 },
 "12E_blow": {
  "src": "l2/12E_blow.jpg",
  "final": false
 },
 "12F": {
  "src": "l2/12F.jpg",
  "final": true
 },
 "12G": {
  "src": "l2/12G.jpg",
  "final": false
 },
 "13A_held": {
  "src": "l2/13A_held.jpg",
  "final": true
 },
 "13A_joy": {
  "src": "l2/13A_joy.jpg",
  "final": true
 },
 "13B_open": {
  "src": "l2/13B_open.jpg",
  "final": true
 },
 "13B_run": {
  "src": "l2/13B_run.jpg",
  "final": true
 },
 "13C": {
  "src": "l2/13C.jpg",
  "final": true
 }
};
export const L2Q: Record<string, Record<string, any>> = {
 "6C": {
  "dial": [
   [
    1431.5,
    904.9
   ],
   [
    1342.8,
    612.0
   ],
   [
    1635.3,
    523.7
   ],
   [
    1724.8,
    816.4
   ]
  ],
  "head": [
   -257.8,
   756.1
  ],
  "dial_c": [
   1533.5,
   714.0
  ]
 },
 "7D_smile": {
  "head": [
   1213.0,
   538.3
  ]
 },
 "7D_frozen": {
  "head": [
   1213.0,
   538.3
  ]
 },
 "9A": {
  "tv": [
   [
    1017.3,
    375.3
   ],
   [
    1680.3,
    399.4
   ],
   [
    1678.6,
    769.2
   ],
   [
    1018.6,
    777.5
   ]
  ],
  "head": [
   1622.0,
   218.8
  ]
 },
 "9A_squat": {
  "tv": [
   [
    1017.3,
    375.3
   ],
   [
    1680.3,
    399.4
   ],
   [
    1678.6,
    769.2
   ],
   [
    1018.6,
    777.5
   ]
  ],
  "head": [
   1618.5,
   523.6
  ]
 },
 "9C": {
  "tv": [
   [
    177.0,
    -89.1
   ],
   [
    1498.3,
    -21.1
   ],
   [
    1487.3,
    642.7
   ],
   [
    243.7,
    710.0
   ]
  ],
  "phone": [
   [
    1158.1,
    723.6
   ],
   [
    1352.3,
    723.3
   ],
   [
    1352.0,
    1141.5
   ],
   [
    1160.1,
    1142.2
   ]
  ],
  "head": [
   1293.9,
   331.2
  ]
 },
 "9E_bail": {
  "tv": [
   [
    1017.3,
    375.3
   ],
   [
    1680.3,
    399.4
   ],
   [
    1678.6,
    769.2
   ],
   [
    1018.6,
    777.5
   ]
  ],
  "head": [
   1646.6,
   254.8
  ]
 },
 "9E_w2": {
  "head": [
   802.4,
   302.2
  ]
 },
 "9G": {
  "head": [
   786.4,
   117.2
  ]
 },
 "12A_on": {
  "head": [
   1377.9,
   300.6
  ]
 },
 "12A_back": {
  "head": [
   1377.9,
   300.6
  ]
 },
 "12B_w2": {
  "head": [
   802.4,
   302.2
  ]
 },
 "12B_tree": {
  "head": [
   987.4,
   250.0
  ]
 },
 "12B_baby": {
  "head": [
   1778.3,
   1042.8
  ]
 },
 "12B_child": {
  "head": [
   1056.4,
   770.8
  ]
 },
 "12C_cat": {
  "head": [
   1077.3,
   1000.2
  ]
 },
 "12C_coop": {
  "head": [
   1077.3,
   1000.2
  ]
 },
 "12C_her": {
  "head": [
   1059.4,
   996.9
  ]
 },
 "12D_sway": {
  "head": [
   990.8,
   270.8
  ]
 },
 "12D_flop": {
  "head": [
   1181.0,
   512.8
  ]
 },
 "12E_stare": {
  "head": [
   1084.3,
   780.8
  ]
 },
 "12E_blow": {
  "head": [
   1016.1,
   852.0
  ]
 },
 "12F": {
  "dial": [
   [
    1345.1,
    1264.6
   ],
   [
    1176.0,
    1325.0
   ],
   [
    1186.3,
    1146.6
   ],
   [
    1345.9,
    1082.8
   ]
  ],
  "head": [
   1298.8,
   220.4
  ]
 },
 "12G": {
  "laptop": [
   [
    1082.6,
    762.0
   ],
   [
    640.5,
    762.4
   ],
   [
    673.4,
    1011.0
   ],
   [
    1091.6,
    1010.0
   ]
  ],
  "head": [
   953.7,
   404.6
  ]
 },
 "13A_held": {
  "head": [
   1280.0,
   345.2
  ]
 },
 "13A_joy": {
  "head": [
   1306.1,
   344.2
  ]
 },
 "13B_open": {
  "head": [
   1231.0,
   386.1
  ]
 },
 "13B_run": {
  "head": [
   1331.4,
   338.8
  ]
 },
 "13C": {
  "head": [
   786.8,
   217.4
  ]
 }
};
export const L2E: Record<string, any> = {
 "T29a": {
  "src": "l2/13E/T29a.jpg",
  "final": true
 },
 "T29f": {
  "src": "l2/13E/T29f.jpg",
  "final": true
 },
 "T29s": {
  "src": "l2/13E/T29s.jpg",
  "final": true
 },
 "T29c": {
  "src": "l2/13E/T29c.jpg",
  "final": true
 },
 "screen_corners": [
  [
   962.0,
   491.0
  ],
  [
   1505.4,
   473.0
  ],
  [
   1522.9,
   803.0
  ],
  [
   980.2,
   835.8
  ]
 ],
 "sticker_c": [
  [
   1175.3,
   908.2
  ],
  [
   1447.0,
   894.1
  ],
  [
   1475.6,
   931.5
  ],
  [
   1190.3,
   946.9
  ]
 ],
 "cat_a_box": [
  794.7,
  134.2,
  1621.3,
  931.6
 ],
 "cat_f_box": [
  794.7,
  202.7,
  1619.6,
  928.9
 ],
 "cat_c_box": [
  928.9,
  553.8,
  1596.4,
  935.1
 ],
 "T29e": {
  "src": "l2/13E/T29e.jpg",
  "final": true
 },
 "sticker": [
  [
   975.6,
   845.8
  ],
  [
   1600.9,
   874.8
  ],
  [
   1598.8,
   1141.2
  ],
  [
   947.1,
   1109.6
  ]
 ],
 "cat_box": [
  471.1,
  0.0,
  2046.2,
  891.6
 ],
 "cat_a": "l2/13E/cat_a.png",
 "cat_f": "l2/13E/cat_f.png"
};
