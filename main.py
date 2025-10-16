
import argparse, os, pandas as pd
from datetime import datetime
from src.optimizer import LineupOptimizer
def parse_args():
    p=argparse.ArgumentParser(description='Fantasy v4 — Optimize NFL lineups')
    p.add_argument('--players_csv', type=str, default='sample_players.csv')
    p.add_argument('--objective', type=str, choices=['cash','gpp'], default='cash')
    p.add_argument('--risk', type=float, default=0.1)
    p.add_argument('--iterations', type=int, default=10000)
    p.add_argument('--cap', type=int, default=50000)
    p.add_argument('--outdir', type=str, default='output')
    return p.parse_args()
def main():
    args=parse_args(); os.makedirs(args.outdir, exist_ok=True)
    df=pd.read_csv(args.players_csv)
    opt=LineupOptimizer(salary_cap=args.cap)
    res=opt.optimize(df, objective=args.objective, risk_aversion=args.risk)
    print('\n=== Optimized Lineup ({}) ==='.format(args.objective.upper()))
    print(res.lineup[['slot','name','team','position','salary','ev']])
    print('\nTotal Salary:', res.total_salary, '  Total EV:', round(res.total_ev,2))
    ts=datetime.now().strftime('%Y%m%d_%H%M%S')
    out_csv=os.path.join(args.outdir, f'optimized_lineup_{args.objective}_{ts}.csv')
    res.lineup.to_csv(out_csv, index=False); print('\nSaved:', out_csv)
if __name__=='__main__': main()
