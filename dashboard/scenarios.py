"""Hypothetical intervention outcomes, anchored to measured ranking performance."""
import math
def routing_scenario(total_questions, review_fraction, unresolved_share, capture_rate,
                     success_rate, minutes_per_review, hourly_cost, value_per_resolution,
                     implementation_cost=0):
    values=[total_questions,review_fraction,unresolved_share,capture_rate,success_rate,minutes_per_review,hourly_cost,value_per_resolution,implementation_cost]
    if any(not math.isfinite(v) or v<0 for v in values) or any(v>1 for v in [review_fraction,unresolved_share,capture_rate,success_rate]):
        raise ValueError('Inputs must be nonnegative; rates must be in [0,1].')
    reviewed=total_questions*review_fraction
    found=min(reviewed,total_questions*unresolved_share*capture_rate)
    random_found=reviewed*unresolved_share
    cost=reviewed*minutes_per_review/60*hourly_cost
    additional=(found-random_found)*success_rate
    return {'questions_reviewed':reviewed,'proxy_negative_identified':found,'random_expected_identified':random_found,
        'additional_identified':found-random_found,'assumed_additional_resolutions':additional,
        'review_cost':cost,'implementation_cost':implementation_cost,
        'assumed_net_vs_no_review':found*success_rate*value_per_resolution-cost-implementation_cost,
        'assumed_net_vs_same_capacity_random':additional*value_per_resolution-implementation_cost}

def render_scenario():
    import pandas as pd
    import streamlit as st
    from dashboard.common import load_data
    st.subheader('Expert-routing scenario')
    st.caption('Historical ranking evidence plus hypothetical intervention assumptions. These benefits have not been observed in a pilot. Both routing policies review the same number of questions.')
    capture=load_data('v2_capture.csv')
    metrics=load_data('v2_classifier_metrics.csv')
    rate=float(metrics.query("split == 'august_2026' and variant == 'sigmoid_calibrated'").iloc[0].positive_rate)
    a,b,c=st.columns(3)
    volume=a.number_input('Scenario question volume',100,100000,1000,100)
    fraction=b.selectbox('Review capacity',capture.review_fraction.tolist(),index=2,format_func=lambda x:f'{x:.0%}')
    success=c.slider('Assumed intervention success',0.0,1.0,.2,.05)
    a,b,c,d=st.columns(4)
    minutes=a.number_input('Minutes per review',1.0,120.0,5.0)
    cost=b.number_input('Reviewer cost per hour (₹)',0.0,100000.0,500.0)
    value=c.number_input('Assumed value per additional resolution (₹)',0.0,1000000.0,500.0)
    setup=d.number_input('Incremental model-operation cost (₹)',0.0,1000000.0,1000.0)
    row=capture[capture.review_fraction.eq(fraction)].iloc[0]
    output=[]
    for label,s in [('Lower success',success/2),('Base',success),('Higher success',min(1,success*1.5))]:
        output.append(dict(scenario=label,assumed_success=s,**routing_scenario(volume,fraction,1-rate,float(row.capture_rate),s,minutes,cost,value,setup)))
    frame=pd.DataFrame(output)
    base=frame[frame.scenario.eq('Base')].iloc[0]
    a,b,c=st.columns(3)
    a.metric('Assumed extra resolutions vs random',f"{base.assumed_additional_resolutions:.1f}")
    b.metric('Total review cost',f"₹{base.review_cost:,.0f}")
    c.metric('Assumed net benefit vs random',f"₹{base.assumed_net_vs_same_capacity_random:,.0f}")
    display=frame[['scenario','assumed_success','assumed_additional_resolutions','assumed_net_vs_no_review','assumed_net_vs_same_capacity_random']].rename(columns={
        'scenario':'Scenario','assumed_success':'Assumed success rate',
        'assumed_additional_resolutions':'Extra resolutions vs random',
        'assumed_net_vs_no_review':'Net vs no review (₹)',
        'assumed_net_vs_same_capacity_random':'Net vs random (₹)'})
    st.dataframe(display.round(2),hide_index=True)
    st.caption('Ranking rates come from 389 August 2026 questions. Scaling assumes the same case mix and ranking performance. Equal review costs cancel in the comparison with random routing. Zero benefit and negative net value are possible; intervention success is an assumption, not a model prediction.')
    st.download_button('Download scenario assumptions and outcomes',frame.to_csv(index=False),'routing_scenario.csv')
