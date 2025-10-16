
import pandas as pd
from src.optimizer import LineupOptimizer, OptimizeResult

def sample_players():
    data = [
        ("QB1","A","QB",7000,22,5,"A@B"),
        ("RB1","A","RB",6800,18,4,"A@B"),
        ("RB2","B","RB",6200,16,3.5,"A@B"),
        ("WR1","A","WR",7200,19,4.5,"A@B"),
        ("WR2","B","WR",5900,15,3.2,"A@B"),
        ("WR3","C","WR",5400,14,3.0,"C@D"),
        ("TE1","C","TE",4800,12,2.5,"C@D"),
        ("DST1","D","DST",3200,7,2.0,"C@D"),
        ("RB3","D","RB",5000,13,3.0,"C@D"),
        ("WR4","D","WR",5100,13.5,3.1,"C@D"),
        ("TE2","B","TE",4000,10,2.0,"A@B"),
        ("DST2","A","DST",3000,6,1.8,"A@B"),
    ]
    return pd.DataFrame(data, columns=['name','team','position','salary','ev','sigma','game'])

def test_cash_optimizer_builds_valid_lineup():
    df = sample_players()
    opt = LineupOptimizer(salary_cap=50000)
    res: OptimizeResult = opt.optimize(df, objective='cash', risk_aversion=0.1)
    lu = res.lineup
    assert (lu['slot']=='QB').sum() == 1
    assert (lu['slot']=='RB').sum() == 2
    assert (lu['slot']=='WR').sum() == 3
    assert (lu['slot']=='TE').sum() == 1
    assert (lu['slot']=='FLEX').sum() == 1
    assert (lu['slot']=='DST').sum() == 1
    assert res.total_salary <= 50000

def test_gpp_optimizer_builds_valid_lineup():
    df = sample_players()
    opt = LineupOptimizer(salary_cap=50000)
    res: OptimizeResult = opt.optimize(df, objective='gpp')
    assert len(res.lineup)==9
    assert res.total_salary <= 50000
