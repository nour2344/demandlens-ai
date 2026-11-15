import json
import re
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
GREEN, AMBER, GRAY = '#315C52', '#C37C36', '#AAB7B1'
NAMES = {'router':'Router','data_analyst':'Data analyst','demand_estimator':'Demand estimator', 'knowledge_agent':'Knowledge agent','quality_controller':'Quality controller','final_response':'Response','clarification':'Clarification'}
KEYS = {'data_analyst':'data_result','demand_estimator':'demand_result','knowledge_agent':'knowledge_result','quality_controller':'quality_result','router':'router_result'}


def number(value):
    return f'{value:.4f}' if isinstance(value, (int,float)) else '—'


def chart(fig, height=230):
    fig.update_layout(template='plotly_white', height=height, margin=dict(l=8,r=8,t=12,b=12), font=dict(size=12,color='#66776E'), paper_bgcolor='white', plot_bgcolor='white', legend=dict(orientation='h',y=1.13,x=0), hoverlabel=dict(bgcolor='white'))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})


def trace(result):
    nodes = result.get('execution_trace', [])
    if not nodes:
        st.caption('No execution trace.')
        return
    for i,node in enumerate(nodes,1):
        item = result.get(KEYS.get(node,''), {})
        status = item.get('status', 'Completed')
        with st.container(border=True):
            a,b = st.columns([1,6])
            a.caption(f'{i:02d}')
            b.markdown(f'**{NAMES.get(node,node)}**')
            b.caption(str(status).replace('_',' ').capitalize())
    router = result.get('router_result')
    if router:
        with st.expander('Routing details'):
            st.json(router)


def quality(result):
    q = result.get('quality_result',{})
    if not q:
        st.info('No quality review was required.')
        return
    if q.get('approved') is True:
        st.success('Review passed')
    else:
        st.error('Review did not approve the output')
    st.caption(f"{q.get('validation_type','Verification')} · Attempts: {q.get('attempts','—')}")
    for issue in q.get('issues',[]):
        st.write('• '+issue)
    if q.get('recommendation'):
        st.write(q['recommendation'])
    st.caption('Review is not a guarantee of factual accuracy.')


def evidence(result):
    if result.get('quality_result',{}).get('approved') is not True:
        st.info('Unapproved scientific output is withheld.')
        return
    knowledge = result.get('knowledge_result',{})
    sources = knowledge.get('sources',[])
    if not sources:
        st.info('No scientific passages retrieved for this run.')
        return
    st.markdown(knowledge.get('analysis',''))
    st.caption('Retrieved passages')
    for s in sources:
        with st.expander(f"[{s['citation_id']}] {s['source']} · p. {s['page']}"):
            st.write(s['text'])
            st.caption(f"Cosine distance: {s['distance']} (not a confidence score)")


def overview(result):
    if 'clarification' in result.get('execution_trace', []):
        st.info(result.get('final_answer', 'Please provide the missing details.'))
        return
    if result.get('quality_result', {}).get('approved') is not True:
        st.warning('We could not verify this investigation. No conclusions have been released.')
        st.caption('Open Quality review for the reason, then try again.')
        return
    data = result.get('data_result', {}).get('data', {})
    demand = result.get('demand_result', {}).get('data', {})
    if data.get('status') != 'success':
        st.markdown(result.get('final_answer', 'No matching retail record.'))
        return
    hours = sorted(data.get('stockout_hours', []))
    recorded = data.get('recorded_sales')
    valid = demand.get('status') == 'success'
    lost = demand.get('estimated_lost_demand') if valid else None
    total = demand.get('estimated_total_demand') if valid else None
    share = lost / total if valid and total and total > 0 and lost is not None else None
    estimates = demand.get('hourly_estimates', []) if valid else []
    peaks = [e['hour'] for e in estimates if e['estimated_lost_demand'] > 0 and e['estimated_lost_demand'] == max(x['estimated_lost_demand'] for x in estimates)]
    def clock(h):
        return f'{h:02d}:00' if h < 24 else '24:00'
    groups = []
    for h in hours:
        if groups and groups[-1][-1] + 1 == h:
            groups[-1].append(h)
        else:
            groups.append([h])
    windows = ', '.join(f'{clock(g[0])}–{clock(g[-1]+1)}' for g in groups)
    left, right = st.columns([2, 1], gap='medium')
    with left:
        with st.container(border=True):
            st.caption('01 / WHAT HAPPENED')
            if hours:
                st.markdown(f'## Out of stock for {len(hours)} hours')
                st.write(windows)
            else:
                st.markdown('## No stockout recorded')
                st.caption('All 24 hourly flags indicate availability.')
            fig = go.Figure(go.Bar(x=list(range(24)), y=[1]*24, marker_color=[AMBER if h in hours else GREEN for h in range(24)], customdata=['Out of stock' if h in hours else 'Available' for h in range(24)], hovertemplate='%{x}:00 – %{customdata}<extra></extra>'))
            fig.update_yaxes(visible=False, range=[0,1])
            fig.update_xaxes(tickmode='array',tickvals=[0,6,12,18,23],ticktext=['00:00','06:00','12:00','18:00','23:00'],showgrid=False)
            fig.update_layout(bargap=.08)
            chart(fig,105)
            st.caption('Green = available   ·   Amber = out of stock')
    with right:
        with st.container(border=True):
            st.caption('02 / ESTIMATED IMPACT')
            if share is not None:
                st.markdown(f'## {share:.1%} demand gap')
                st.write('Estimated share of adjusted daily demand not captured in sales.')
                st.caption('Daytime losses only · not measured lost sales')
            elif demand.get('status') == 'insufficient_evidence':
                st.markdown('## Estimate unavailable')
                st.write('Not enough comparable historical sales to quantify the gap.')
            else:
                st.markdown('## Not estimated')
                st.write('This investigation has no approved demand estimate.')
    if valid:
        with st.container(border=True):
            st.caption('03 / SALES WE SAW VS. SALES WE MAY HAVE MISSED')
            a,b,c=st.columns(3)
            a.metric('Recorded sales',number(recorded)); b.metric('Estimated missed sales',number(lost)); c.metric('Adjusted demand',number(total))
            if total and total > 0 and lost is not None and recorded is not None:
                fig=go.Figure([go.Bar(y=['Adjusted demand'],x=[recorded],orientation='h',name='Recorded',marker_color=GREEN,text=[f'{recorded/total:.1%} recorded'],textposition='inside'),go.Bar(y=['Adjusted demand'],x=[lost],orientation='h',name='Estimated gap',marker_color=AMBER,text=[f'{lost/total:.1%} estimated gap'],textposition='inside')]); fig.update_layout(barmode='stack',showlegend=False); fig.update_yaxes(visible=False); fig.update_xaxes(visible=False); chart(fig,75)
            st.caption('Values use a normalized sales scale; these are not item counts or money.')
    a,b=st.columns([2,1],gap='medium')
    with a:
        with st.container(border=True):
            st.caption('04 / WHERE TO LOOK FIRST')
            if estimates:
                st.markdown('### '+ ('Highest estimated gap: '+', '.join(clock(h) for h in peaks) if peaks else 'No positive estimated gap'))
                frame=pd.DataFrame(estimates)
                labels=[clock(h) for h in frame.hour]
                fig=go.Figure(go.Bar(x=frame.estimated_lost_demand,y=labels,orientation='h',marker_color=[AMBER if h in peaks else '#C5D1CB' for h in frame.hour],text=[f'{v:.4f}' for v in frame.estimated_lost_demand],textposition='outside',cliponaxis=False)); fig.update_yaxes(autorange='reversed'); fig.update_xaxes(rangemode='tozero',title='Estimated missed sales (normalized)',gridcolor='#edf0ee'); chart(fig,220)
                st.caption('Bars show estimated missed sales, not observed customer behavior.')
                with st.expander('See hourly calculations'):
                    st.dataframe(frame,hide_index=True,use_container_width=True)
            else:
                st.write('No hourly estimate available for this run.')
                if demand.get('unsupported_hours'):
                    st.caption('Hours lacking comparable data: '+', '.join(clock(h) for h in demand['unsupported_hours']))
    with b:
        with st.container(border=True):
            st.caption('05 / SUGGESTED NEXT STEP')
            if peaks:
                st.markdown('### Review replenishment')
                st.write('Check stock and replenishment records before '+', '.join(clock(h) for h in peaks)+'.')
            elif hours:
                st.markdown('### Check the stockout records')
                st.write('Review inventory availability during '+windows+'.')
            else:
                st.markdown('### Continue monitoring')
                st.write('No stockout was detected for the selected day.')
            st.caption('Suggested investigation, not an automated ordering recommendation.')
            if valid:
                counts=[e['comparable_observations'] for e in estimates]
                if counts: st.caption(f'Historical support: {min(counts)}–{max(counts)} observations per hour.')
                st.caption('Estimated window: 06:00–22:00. Later losses are excluded.')
    with st.expander('Read the full investigation and methodology'):
        st.markdown(result.get('final_answer',''))
    st.download_button('Download investigation report',result.get('final_answer',''),'demandlens-report.md',mime='text/markdown')


def report(name):
    p=ROOT/'evaluation'/'results'/name
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except (OSError,ValueError):
        return {}


def evaluation():
    st.title('System evaluation')
    st.caption('Saved benchmarks · no API calls')
    d=report('demand_metrics.json'); w=report('workflow_evaluation.json'); c=report('context_evaluation.json')
    a,b,c_tab=st.tabs(['Demand reconstruction','Workflow reliability','Context experiment'])
    with a:
        if d:
            m=d.get('demand_estimator',{}); base=d.get('zero_demand_baseline',{})
            cols=st.columns(3)
            cols[0].metric('Synthetic cases',d['evaluation_cases']); cols[1].metric('Coverage',f"{d['coverage_percentage']:.0f}%")
            if base.get('mae',0)>0:
                cols[2].metric('MAE reduction',f"{1-m['mae']/base['mae']:.1%}")
                with st.container(border=True):
                    fig=go.Figure([go.Bar(name='Estimator',x=['MAE','RMSE'],y=[m['mae'],m['rmse']],marker_color=GREEN),go.Bar(name='Zero baseline',x=['MAE','RMSE'],y=[base['mae'],base['rmse']],marker_color=GRAY)])
                    fig.update_layout(barmode='group'); chart(fig,300)
                    st.dataframe(pd.DataFrame({'Estimator':m,'Baseline':base}),use_container_width=True)
            st.caption('Synthetic masking; accuracy is conditional on successful estimations.')
        else: st.info('Demand report not found.')
    with b:
        if w:
            s=w['summary']; cols=st.columns(3)
            cols[0].metric('Routing accuracy',f"{s['routing_accuracy']:.0%}"); cols[1].metric('Passed',f"{s['passed_cases']}/{s['total_cases']}"); cols[2].metric('Mean latency',f"{s['average_latency_seconds']:.2f}s")
            cols_show=['case','actual_route','actual_outcome','passed','tokens','latency_seconds']
            st.dataframe(pd.DataFrame(w['results'])[cols_show],hide_index=True,use_container_width=True)
            st.caption('Predefined scenarios; pass rate is not general production accuracy.')
        else: st.info('Workflow report not found.')
    with c_tab:
        if c:
            f=pd.DataFrame(c['configurations']); st.dataframe(f[['top_k','context_characters','total_tokens','verification_tokens','latency_seconds','quality_approved']],hide_index=True,use_container_width=True)
            with st.container(border=True):
                fig=go.Figure(go.Bar(x=[f'k={k}' for k in f.top_k],y=f.total_tokens,marker_color=[GREEN,GRAY])); chart(fig,260)
            st.caption('One run per configuration. Generation tokens exclude verification.')
        else: st.info('Context report not found.')
