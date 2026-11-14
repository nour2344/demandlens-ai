from datetime import date
from time import perf_counter
import streamlit as st
from src.workflows.static_workflow import build_static_workflow
from src.workflows.dynamic_workflow import build_dynamic_workflow
from src.ui.styles import apply_styles
from src.ui.components import overview, trace, quality, evidence, evaluation

st.set_page_config(page_title='DemandLens | Retail intelligence',page_icon=':material/query_stats:',layout='wide')
apply_styles()
CASES={
    'Full investigation': ('Estimate lost demand for this product and explain the scientific forecasting implications.',1,793,True),
    'Stock availability': ('Did this product experience a stockout?',1,793,True),
    'Demand estimation': ('Estimate hidden demand for this product.',1,793,True),
    'Research question': ('What is censored demand in retail?',1,793,False),
    'Insufficient evidence': ('Estimate lost demand for this product.',0,72,True),
    'Missing information': ('Estimate lost demand for my product.',1,793,False),
}
with st.sidebar:
    st.markdown('### DemandLens /')
    st.caption('RETAIL INTELLIGENCE')
    st.divider()
    page=st.radio('Workspace',['Investigate','System evaluation'],label_visibility='collapsed')
    st.divider()
    st.caption('DATASET')
    st.markdown('**FreshRetailNet-50K**')
    st.caption('10,000-row research sample · Mar–Jun 2024')
    st.divider()
    st.caption('ENGINE')
    st.write('GPT-OSS-20B / LangGraph')
    st.caption('Research prototype · local workspace')

if page=='System evaluation':
    evaluation()
else:
    st.markdown('<div class="dl-kicker">Workspace / Investigations</div>',unsafe_allow_html=True)
    st.title('Demand investigation')
    st.caption('Inspect stock availability, reconstruct censored sales and review the supporting evidence.')
    scenario=st.selectbox('Investigation preset',list(CASES))
    q,s,p,include=CASES[scenario]
    with st.form('run_form',border=True):
        a,b,c,d=st.columns([1,1,1.3,1.2])
        store=a.number_input('Store ID',min_value=0,value=s,step=1,key=f'store_{scenario}')
        product=b.number_input('Product ID',min_value=0,value=p,step=1,key=f'product_{scenario}')
        day=c.date_input('Date',value=date(2024,6,25),min_value=date(2024,3,28),max_value=date(2024,6,25))
        mode=d.selectbox('Workflow',['Dynamic','Static'])
        question=st.text_area('Investigation question',value=q,height=88,key=f'q_{scenario}')
        left,right,action=st.columns([1.3,1,1],vertical_alignment='bottom')
        ids=left.checkbox('Include retail identifiers',value=include,key=f'ids_{scenario}')
        k=right.selectbox('Retrieved passages',[1,2,3,4,5,6,7,8],index=2)
        submitted=action.form_submit_button('Run investigation',type='primary',use_container_width=True)
        st.caption('Static workflow always includes retail identifiers. Dynamic workflow can ask for clarification.')
    if submitted:
        if not question.strip():
            st.warning('Enter an investigation question.')
        else:
            state=dict(question=question,top_k=k,execution_trace=[],retry_count=0,retry_tokens=0)
            if ids or mode=='Static': state.update(store_id=int(store),product_id=int(product),date=day.isoformat())
            st.session_state.pop('dl_run',None)
            with st.spinner('Running investigation and quality review…'):
                t=perf_counter()
                try:
                    graph=build_static_workflow() if mode=='Static' else build_dynamic_workflow()
                    result=graph.invoke(state)
                    st.session_state.dl_run=dict(result=result,mode=mode,latency=perf_counter()-t,request=state)
                except Exception as exc:
                    st.error(f'Investigation failed: {type(exc).__name__}')
    saved=st.session_state.get('dl_run')
    if not saved:
        with st.container(border=True):
            st.subheader('Start an investigation')
            st.write('Choose a preset or enter a retail question. Results, evidence and execution details will appear here after a run.')
    else:
        result=saved['result']; request=saved['request']; qc=result.get('quality_result',{})
        st.divider()
        st.subheader('Investigation results')
        snapshot=' · '.join([saved['mode'], f"Store {request['store_id']} / Product {request['product_id']} / {request['date']}" if 'store_id' in request else 'No retail identifiers',f"k={request['top_k']}"])
        st.caption('Last completed run · '+snapshot)
        st.write(request['question'])
        label='Approved' if qc.get('approved') is True else 'Clarification required' if 'clarification' in result.get('execution_trace',[]) else 'Not approved'
        st.caption(f"{label}  /  {saved['latency']:.2f}s  /  {result.get('total_tokens',0):,} reported tokens")
        tabs=st.tabs(['Overview','Scientific evidence','Agent execution','Quality review'])
        with tabs[0]: overview(result)
        with tabs[1]: evidence(result)
        with tabs[2]: trace(result)
        with tabs[3]: quality(result)
