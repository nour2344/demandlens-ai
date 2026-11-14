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
    if 'clarification' in result.get('execution_trace',[]):
        st.info(result.get('final_answer','Please clarify the request.'))
        return
    if result.get('quality_result',{}).get('approved') is not True:
        st.warning('Analysis withheld pending a successful quality review.')
        for issue in result.get('quality_result',{}).get('issues',[]):
            st.write(issue)
        return
    data = result.get('data_result',{}).get('data',{})
    demand = result.get('demand_result',{}).get('data',{})
    if data.get('status') != 'success':
        st.markdown(result.get('final_answer',''))
        return
    recorded = data.get('recorded_sales')
    lost = demand.get('estimated_lost_demand')
    total = demand.get('estimated_total_demand')
    for col,label,value,caption in zip(st.columns(4),['Recorded sales','Est. lost demand','Adjusted demand','Stockout hours'],[number(recorded),number(lost),number(total),str(data.get('total_stockout_hours','—'))],['Observed · normalized','Daytime estimate','Observed + estimated loss','Across 24 hours']):
        with col:
            with st.container(border=True):
                st.metric(label,value)
                st.caption(caption)
    if demand.get('status') == 'insufficient_evidence':
        st.warning('No estimate: insufficient comparable observations. Unsupported hours: '+', '.join(map(str,demand.get('unsupported_hours',[]))))
    elif not demand and result.get('route') in ('estimate','hybrid') and data.get('daytime_stockout_hours')==0:
        st.info('No daytime stockout detected; estimation not required within the modeled window.')
    hours = data.get('stockout_hours',[])
    main,side = st.columns([2,1],gap='medium')
    with main:
        with st.container(border=True):
            st.markdown('**Stock availability**')
            st.caption('24-hour observation window')
            fig = go.Figure(go.Bar(x=list(range(24)),y=[1]*24,marker_color=[AMBER if h in hours else GREEN for h in range(24)], customdata=['Stockout' if h in hours else 'Available' for h in range(24)],hovertemplate='%{x}:00 · %{customdata}<extra></extra>'))
            fig.update_yaxes(visible=False)
            fig.update_xaxes(tickmode='array',tickvals=[0,4,8,12,16,20,23],ticktext=['00:00','04:00','08:00','12:00','16:00','20:00','23:00'],showgrid=False)
            fig.update_layout(bargap=.12)
            chart(fig,145)
            st.caption('Green · available     /     Amber · stockout')
            estimates = demand.get('hourly_estimates',[]) if demand.get('status')=='success' else []
            if estimates:
                st.divider()
                st.markdown('**Hourly demand reconstruction**')
                frame=pd.DataFrame(estimates)
                x=[f'{h:02d}:00' for h in frame.hour]
                fig=go.Figure([go.Bar(x=x,y=frame.actual_sales,name='Observed',marker_color=GRAY),go.Bar(x=x,y=frame.expected_sales,name='Expected',marker_color=GREEN)])
                fig.update_layout(barmode='group')
                fig.update_yaxes(title='Normalized sales',gridcolor='#edf0ee',rangemode='tozero')
                chart(fig,260)
                with st.expander('Hourly evidence table'):
                    st.dataframe(frame,hide_index=True,use_container_width=True)
    with side:
        with st.container(border=True):
            st.markdown('**Demand composition**')
            if isinstance(total,(int,float)) and total>0 and isinstance(lost,(int,float)) and isinstance(recorded,(int,float)):
                fig=go.Figure(go.Pie(labels=['Recorded','Estimated loss'],values=[recorded,lost],hole=.72,marker_colors=[GREEN,AMBER],textinfo='none',sort=False))
                fig.update_layout(annotations=[dict(text=f'{lost/total:.1%}',x=.5,y=.5,showarrow=False,font=dict(size=23,color='#182622'))],showlegend=False)
                chart(fig,180)
                st.caption('Estimated loss / adjusted demand')
            else:
                st.caption('No approved numerical estimate for this run.')
            st.divider()
            st.markdown('**Estimation scope**')
            st.write('06:00–22:00 (end exclusive)')
            st.caption('Potential losses outside this window are excluded. Values are normalized, not currency or item counts.')
    st.subheader('Analytical findings')
    for key in ('data_result','demand_result','knowledge_result'):
        item=result.get(key,{})
        if item:
            with st.expander(NAMES.get(item.get('agent'),key),expanded=key=='demand_result'):
                st.markdown(item.get('analysis',''))
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
