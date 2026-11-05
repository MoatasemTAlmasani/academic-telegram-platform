(function(){
"use strict";
var period=30;
var text={
ar:{period:"فترة التحليل",d7:"آخر 7 أيام",d30:"آخر 30 يوماً",d90:"آخر 90 يوماً",d365:"آخر 12 شهراً",services:"أداء الخدمات خلال الفترة",operations:"مركز العمليات",requests:"الطلبات خلال الفترة",overdue:"طلبات متأخرة",quotes:"عروض أسعار بانتظار الرد",empty:"لا توجد بيانات خلال الفترة المحددة",error:"تعذر تحميل التحليلات"},
en:{period:"Analytics period",d7:"Last 7 days",d30:"Last 30 days",d90:"Last 90 days",d365:"Last 12 months",services:"Service performance for period",operations:"Operations center",requests:"Requests in period",overdue:"Overdue requests",quotes:"Quotations awaiting response",empty:"No data for the selected period",error:"Unable to load analytics"}
};
function lang(){return document.documentElement.lang==="ar"?"ar":"en"}
function t(k){return text[lang()][k]||text.en[k]||k}
function esc(v){return String(v==null?"":v).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]})}
function fmt(v){return new Intl.NumberFormat(lang()==="ar"?"ar":"en-US").format(Number(v||0))}
function refreshLabels(){\n var wrap=document.querySelector(".dashboard-period-control");if(wrap){wrap.querySelector("span").textContent=t("period");var select=wrap.querySelector("select");if(select){select.options[0].text=t("d7");select.options[1].text=t("d30");select.options[2].text=t("d90");select.options[3].text=t("d365");}}\n var heads=document.querySelectorAll("#dashboardPeriodPanels .surface-head h3");if(heads[0])heads[0].textContent=t("services");if(heads[1])heads[1].textContent=t("operations");var p=document.querySelector("#dashboardPeriodPanels .surface-head p");if(p)p.firstChild.textContent=t("requests")+": ";\n}\nfunction addUI(){
 var actions=document.querySelector("#page-dashboard .heading-actions");if(!actions||document.getElementById("dashboardPeriod"))return;
 var label=document.createElement("label");label.className="dashboard-period-control";
 label.innerHTML='<span>'+t("period")+'</span><select id="dashboardPeriod" class="filter-select"><option value="7">'+t("d7")+'</option><option value="30" selected>'+t("d30")+'</option><option value="90">'+t("d90")+'</option><option value="365">'+t("d365")+'</option></select>';
 actions.insertBefore(label,actions.firstChild);
 var anchor=document.getElementById("availabilityNote"),section=document.createElement("div");section.id="dashboardPeriodPanels";section.className="dashboard-grid dashboard-period-panels";
 section.innerHTML='<section class="surface"><div class="surface-head"><div><h3>'+t("services")+'</h3></div></div><div id="periodServiceChart" class="service-performance"></div></section><section class="surface"><div class="surface-head"><div><h3>'+t("operations")+'</h3><p>'+t("requests")+': <strong id="periodRequests">—</strong></p></div></div><div id="periodOperations" class="operations-center"></div></section>';
 if(anchor&&anchor.parentNode)anchor.parentNode.insertBefore(section,anchor.nextSibling);
 document.getElementById("dashboardPeriod").addEventListener("change",function(e){period=Number(e.target.value)||30;load()});
}
function drawBars(items){
 var el=document.getElementById("periodServiceChart"),max=Math.max(1,...items.map(x=>Number(x.count||0)));
 if(!items.length){el.innerHTML='<div class="empty-cell">'+t("empty")+'</div>';return}
 el.innerHTML=items.map(x=>'<div class="service-row"><div class="service-row-head"><span>'+esc(x.service)+'</span><b>'+fmt(x.count)+'</b></div><div class="service-track"><span style="width:'+Math.max(x.count?2:0,Number(x.count||0)/max*100)+'%"></span></div></div>').join("");
}
function render(d){
 var metrics=d.metrics||{},alerts=d.alerts||{};
 var chip=document.querySelector("#page-dashboard .period-chip");if(chip)chip.textContent=t("d"+period);
 var requests=document.getElementById("periodRequests");if(requests)requests.textContent=fmt(metrics.requests_in_period);
 var trend=d.requests_trend||[],max=Math.max(1,...trend.map(x=>Number(x.count||0))),chart=document.getElementById("trendChart");
 if(chart)chart.innerHTML=trend.length?'<div class="chart-bars">'+trend.map(x=>'<div class="chart-bar" title="'+esc(x.date)+': '+fmt(x.count)+'" style="height:'+Math.max(3,Number(x.count||0)/max*100)+'%"></div>').join("")+'</div><div class="chart-labels"><span>'+esc(trend[0].date)+'</span><span>'+esc(trend[Math.floor(trend.length/2)].date)+'</span><span>'+esc(trend[trend.length-1].date)+'</span></div>':'<div class="empty-cell">'+t("empty")+'</div>';
 var statuses=d.requests_by_status||[],sm=Math.max(1,...statuses.map(x=>Number(x.count||0))),status=document.getElementById("statusChart");
 if(status)status.innerHTML=statuses.length?statuses.map(x=>'<div class="status-row"><span>'+esc(String(x.status||"").replace(/_/g," "))+'</span><span class="status-track"><span class="status-fill" style="display:block;width:'+(Number(x.count||0)/sm*100)+'%"></span></span><span class="status-count">'+fmt(x.count)+'</span></div>').join(""):'<div class="empty-cell">'+t("empty")+'</div>';
 drawBars(d.requests_by_service||[]);
 var ops=document.getElementById("periodOperations");if(ops)ops.innerHTML='<div class="operation-alert danger"><span>'+t("overdue")+'</span><b>'+fmt(alerts.overdue_requests)+'</b></div><div class="operation-alert warning"><span>'+t("quotes")+'</span><b>'+fmt(alerts.pending_quotations)+'</b></div>';
}
async function load(){
 addUI();var token=localStorage.getItem("admin_access_token");if(!token)return;
 var select=document.getElementById("dashboardPeriod");if(select)select.value=String(period);
 try{var r=await fetch("/api/v1/admin/dashboard/overview?period_days="+period,{headers:{Accept:"application/json",Authorization:"Bearer "+token}});if(!r.ok)throw Error("HTTP "+r.status);render(await r.json())}
 catch(e){var target=document.getElementById("periodServiceChart");if(target)target.innerHTML='<div class="empty-cell">'+t("error")+'</div>'}
}
document.addEventListener("DOMContentLoaded",function(){addUI();setTimeout(load,0);var refresh=document.getElementById("refreshDashboard");if(refresh)refresh.addEventListener("click",load);var previousLang=document.documentElement.lang;new MutationObserver(function(){if(previousLang!==document.documentElement.lang){previousLang=document.documentElement.lang;refreshLabels();load()}}).observe(document.documentElement,{attributes:true,attributeFilter:["lang"]})});
})();
