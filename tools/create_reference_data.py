"""Build human-auditable transcriptions from Tour de gross arXiv:2506.03094v1.
This script contains only reference data; it does not generate physical circuits.
"""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def paths(text): return [line.split() for line in text.strip().splitlines()]
base={"source":"arXiv:2506.03094v1, PDF equations 27--64; Figure 5; Table 6", "convention":"X check at (i,j) has L support (i,j)+A and R support (i,j)+B; Z check has L support (i,j)-B and R support (i,j)-A. Coordinates reduced modulo ell,m.", "ell":12, "A":[[0,0],[0,1],[3,-1]],"B":[[0,0],[1,0],[-1,-3]],"dual_shift":[1,1]}
gross={**base,"name":"gross","m":6,"n":144,"k":12,"code_distance_published":12,"cycles_reference":10,
"p": [[4,0],[5,0],[6,1],[4,2],[5,4],[6,5]],
"q": [[3,0],[4,0],[3,1],[3,2],[4,2],[3,5]],
"r": [[0,0],[8,0],[1,1],[9,1],[3,4],[11,4]],
"s": [[1,0],[9,0],[4,4],[8,4],[0,5],[8,5]],
"alpha":[[0,0],[3,5],[11,5],[10,1],[5,4],[4,2]],
"beta":[[0,0],[2,4],[1,2],[2,5],[1,1],[3,1]],
"extra_edges_l":[],"extra_edges_r":[],"identified_vertices":["x4R","x9yL"],
"cycles_l":paths('''
x4L x3y2R x3yR x5L x4L
x3y5R x3R x6y5L x4y2L x3y5R
x3y5R x3R x6y5L x4R x5y4L x3y5R
x4L x3y2R x6yL x5y4L x4R x4L
x3yR x3y2R x6yL x4y2R x5L x3yR
'''),
"cycles_r":paths('''
x9yL x8y4R x8y5R x11y4L x9yL
xyL xR x4y4R x3y4L xyL
1L y5R x9R x9yL x8y4R 1L
'''),
"bridge_l":"x6y5L x4y2L x3y5R x5y4L x6yL x4y2R x5L x4L x3y2R x3yR x3R".split(),
"bridge_r":"x11y4L x8y5R x8y4R 1L xR x4y4R x8L x9R y5R x3y4L xyL".split(),
"expected_full_graph":{"vertices":23,"edges":47,"selected_cycle_checks":19,"physical_lpu_qubits":90},
"logical_Mx":[[0,1,0,1,0,0],[0,1,0,0,0,1],[0,0,1,1,0,0],[1,1,0,1,1,0],[0,1,0,0,1,0],[1,1,1,1,0,1]],
"logical_My":[[1,0,0,0,0,1],[1,1,1,0,0,1],[0,0,0,0,1,0],[0,1,0,0,0,0],[0,1,1,0,0,1],[0,0,1,1,0,1]]}
two={**base,"name":"two_gross","m":12,"n":288,"k":12,"code_distance_published":18,"cycles_reference":18,
"p":[[2,0],[2,2],[8,2],[9,2],[3,3],[4,3],[7,4],[8,6],[6,7],[7,11]],
"q":[[3,2],[5,3],[7,3],[11,3],[8,4],[8,5],[6,7],[4,8],[1,9],[1,10]],
"r":[[4,2],[11,2],[0,5],[1,5],[5,5],[6,5],[1,8],[8,8],[2,11],[10,11]],
"s":[[2,6],[11,6],[2,9],[11,9],[2,10],[11,10],[8,7],[11,7],[5,8],[11,8]],
"alpha":[[0,0],[0,3],[3,7],[11,11],[2,9],[7,4]],
"beta":[[0,0],[1,1],[4,0],[5,4],[4,3],[3,5]],
"extra_edges_l":paths('''x3y3L x7y11L
xy9R x8y5R'''),
"extra_edges_r":paths('''x5y5L x11y10R
x11y9R x2y6R'''),
"identified_vertices":["x3y2R","x10y11L"],
"cycles_l":paths('''
x2L x3y3L x4y3L x2L
x7y11L x8y2L x9y2L x7y11L
xy10R xy9R x4y8R xy10R
x8y5R x8y4R x11y3R x8y5R
x6y7L x5y3R x8y2L x7y11L x6y7R x6y7L
x3y3L x4y3L x5y3R x8y2L x7y11L x3y3L
x7y11L x6y7R x8y6L x7y3R x9y2L x7y11L
x2y2L xy10R xy9R x8y5R x11y3R x2y2L
x7y4L x7y3R x8y6L x8y5R x8y4R x7y4L
x2y2L x11y3R x8y4R x7y4L x3y2R x2y2L
x3y3L x3y2R x7y4L x7y3R x9y2L x7y11L x3y3L
'''),
"cycles_r":paths('''
x11y2L xy5L y5L x11y2L
x4y2L x5y5L x6y5L x4y2L
x11y8R x2y6R x11y9R x11y8R
x11y8R x2y6R x11y7R x11y8R
x2y10R x2y9R x5y8R x2y10R
x5y5L x2y6R x11y9R x11y10R x5y5L
x5y5L x6y5L x8y8L x10y11L x11y10R x5y5L
x11y2L xy5L x11y6R x8y7R x8y8L x10y11L x11y2L
y5L xy8L x11y9R x11y10R x10y11L x11y2L y5L
'''),
"bridge_l":"x7y4L x7y3R x8y6L x6y7R x7y11L x3y3L x2L x4y3L x5y3R x6y7L x4y8R xy9R xy10R x2y2L x11y3R x8y5R x8y4R".split(),
"bridge_r":"x8y8L x6y5L x4y2L x5y5L x2y6R x11y9R x11y10R x2y9R x5y8R x2y10R x2y11L xy8L y5L x11y2L xy5L x11y6R x8y7R".split(),
"expected_full_graph":{"vertices":39,"edges":81,"selected_cycle_checks":37,"physical_lpu_qubits":158},
"logical_Mx":[[0,1,1,1,0,1],[1,0,1,0,1,1],[1,0,1,0,1,0],[1,0,1,1,1,1],[0,1,1,1,1,1],[1,0,0,1,1,0]],
"logical_My":[[1,1,1,1,1,0],[1,1,0,1,1,1],[0,1,1,0,0,0],[1,0,0,0,1,0],[1,0,0,1,1,1],[1,0,0,0,0,1]]}
for spec in [gross,two]:
 (ROOT/'reference'/f'{spec["name"]}.json').write_text(json.dumps(spec,indent=2)+'\n')
rows=[('gross_idle',-31.02,8.66,5,24,210960,10),('gross_shift',-28.63,7.13,5,24,483840,10),('gross_X',-23.97,6.31,5,23,324526,1),('gross_XX',-22.06,5.87,5,23,398717,1),('gross_Y',-19.49,4.65,5,23,400117,1),('gross_inter_XX',-18.32,5.19,5,23,743456,1),('two_gross_idle',-95.83,25.78,9,24,762912,18),('two_gross_shift',-108.53,28.22,9,24,1748736,18)]
import csv
with (ROOT/'reference'/'table6.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['series','log_f0','gamma_fit','w0','K_published','N_expanded','rate_divisor']);w.writerows(rows)
print('Reference data written.')
