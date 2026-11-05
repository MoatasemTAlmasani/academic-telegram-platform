(function(){
"use strict";
var period=30;
var serviceId="";
var text={
ar:{period:"فترة التحليل",service:"الخدمة",allServices:"كل الخدمات",d7:"آخر 7 أيام",d30:"آخر 30 يوماً",d90:"آخر 90 يوماً",d365:"آخر 12 شهراً",services:"أداء الخدمات خلال الفترة",operations:"مركز العمليات",requests:"الطلبات خلال الفترة",trendDescription:"الطلبات المنشأة خلال آخر {days} يوماً",requestDistribution:"توزيع حالات الطلبات",overdue:"طلبات متأخرة",quotes:"عروض أسعار بانتظار الرد",openRequest:"فتح الطلب",loading:"جارٍ تحميل التحليلات…",retry:"إعادة المحاولة",empty:"لا توجد بيانات خلال الفترة المحددة",error:"تعذر تحميل التحليلات"},
en:{period:"Analytics period",service:"Service",allServices:"All services",d7:"Last 7 days",d30:"Last 30 days",d90:"Last 90 days",d365:"Last 12 months",services:"Service performance for period",operations:"Operations center",requests:"Requests in period",trendDescription:"Requests created in the last {days} days",requestDistribution:"Request status distribution",overdue:"Overdue requests",quotes:"Quotations awaiting response",openRequest:"Open request",loading:"Loading analytics…",retry:"Retry",empty:"No data for the selected period",error:"Unable to load analytics"}
};
function lang(){return document.documentElement.lang==="ar"?"ar":"en"}
function t(k){return text[lang()][k]||text.en[k]||k}
function esc(v){return String(v==null?"":v).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]})}
function fmt(v){return new Intl.NumberFormat(lang()==="ar"?"ar":"en-US").format(Number(v||0))}
function fmtDate(v){if(!v)return "—";var date=new Date(v);return Number.isNaN(date.getTime())?String(v):date.toLocaleString(lang()==="ar"?"ar":"en-US",{dateStyle:"medium",timeStyle:"short"})}
function refreshLabels(){
 var wrap=document.querySelector(".dashboard-period-control");if(wrap){wrap.querySelector("span").textContent=t("period");var select=wrap.querySelector("select");if(select){select.options[0].text=t("d7");select.options[1].text=t("d30");select.options[2].text=t("d90");select.options[3].text=t("d365");}}
 var serviceWrap=document.querySelector(".dashboard-service-control");if(serviceWrap){serviceWrap.querySelector("span").textContent=t("service");var serviceSelect=serviceWrap.querySelector("select");if(serviceSelect&&serviceSelect.options.length)serviceSelect.options[0].text=t("allServices");}
 var heads=document.querySelectorAll("#dashboardPeriodPanels .surface-head h3");if(heads[0])heads[0].textContent=t("services");if(heads[1])heads[1].textContent=t("operations");var p=document.querySelector("#dashboardPeriodPanels .surface-head p");if(p)p.firstChild.textContent=t("requests")+": ";
}
function addUI(){
 var actions=document.querySelector("#page-dashboard .heading-actions");if(!actions||document.getElementById("dashboardPeriod"))return;
 var label=document.createElement("label");label.className="dashboard-period-control";
 label.innerHTML='<span>'+t("period")+'</span><select id="dashboardPeriod" class="filter-select"><option value="7">'+t("d7")+'</option><option value="30" selected>'+t("d30")+'</option><option value="90">'+t("d90")+'</option><option value="365">'+t("d365")+'</option></select>';
 actions.insertBefore(label,actions.firstChild);
 var serviceLabel=document.createElement("label");serviceLabel.className="dashboard-service-control";serviceLabel.innerHTML='<span>'+t("service")+'</span><select id="dashboardServiceFilter" class="filter-select"><option value="">'+t("allServices")+'</option></select>';actions.insertBefore(serviceLabel,label.nextSibling);
 document.getElementById("dashboardServiceFilter").addEventListener("change",function(e){serviceId=e.target.value||"";load()});
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
 serviceId=d.service_id||serviceId;
 var serviceSelect=document.getElementById("dashboardServiceFilter");if(serviceSelect){var options=d.service_options||[];serviceSelect.innerHTML='<option value="">'+t("allServices")+'</option>'+options.map(function(x){return '<option value="'+esc(x.id)+'">'+esc(x.name)+'</option>'}).join("");serviceSelect.value=serviceId;}
 var chip=document.querySelector("#page-dashboard .period-chip");if(chip)chip.textContent=t("d"+period);
 ["new_customers","new_users","new_requests"].forEach(function(key){var card=document.querySelector('[data-metric="'+key+'"] .metric-value');if(card)card.textContent=fmt(metrics[key]||0)});
 var trendDescription=document.querySelector("#page-dashboard .chart-surface .surface-head p");if(trendDescription)trendDescription.textContent=t("trendDescription").replace("{days}",String(period));
 var requests=document.getElementById("periodRequests");if(requests)requests.textContent=fmt(metrics.requests_in_period);
 var trend=d.requests_trend||[],max=Math.max(1,...trend.map(x=>Number(x.count||0))),chart=document.getElementById("trendChart");
 if(chart)chart.innerHTML=trend.length?'<div class="chart-bars">'+trend.map(x=>'<div class="chart-bar" title="'+esc(x.date)+': '+fmt(x.count)+'" style="height:'+Math.max(3,Number(x.count||0)/max*100)+'%"></div>').join("")+'</div><div class="chart-labels"><span>'+esc(trend[0].date)+'</span><span>'+esc(trend[Math.floor(trend.length/2)].date)+'</span><span>'+esc(trend[trend.length-1].date)+'</span></div>':'<div class="empty-cell">'+t("empty")+'</div>';
 var statuses=d.requests_by_status||[],sm=Math.max(1,...statuses.map(x=>Number(x.count||0))),status=document.getElementById("statusChart");
 if(status)status.innerHTML=statuses.length?statuses.map(x=>'<div class="status-row"><span>'+esc(String(x.status||"").replace(/_/g," "))+'</span><span class="status-track"><span class="status-fill" style="display:block;width:'+(Number(x.count||0)/sm*100)+'%"></span></span><span class="status-count">'+fmt(x.count)+'</span></div>').join(""):'<div class="empty-cell">'+t("empty")+'</div>';
 drawBars(d.requests_by_service||[]);
 if(chart){chart.setAttribute("role","img");chart.setAttribute("aria-label",t("trendDescription").replace("{days}",String(period)));}
 if(status){status.setAttribute("role","img");status.setAttribute("aria-label",t("requestDistribution"));}
 var ops=document.getElementById("periodOperations");
 if(ops){
  var overdueItems=d.overdue_items||[],quoteItems=d.pending_quotation_items||[];
  var requestButton=function(title){return '<button type="button" class="operation-open-request" data-request-title="'+esc(title)+'">'+t("openRequest")+'</button>'};
  ops.innerHTML='<div class="operation-alert danger"><span>'+t("overdue")+'</span><b>'+fmt(alerts.overdue_requests)+'</b></div>'+
   (overdueItems.length?overdueItems.map(function(x){return '<div class="operation-item"><div><b>'+esc(x.title)+'</b><small>'+esc(x.customer)+' · '+esc(fmtDate(x.deadline))+'</small></div>'+requestButton(x.title)+'</div>'}).join(""):'<div class="operation-empty">'+t("empty")+'</div>')+
   '<div class="operation-alert warning"><span>'+t("quotes")+'</span><b>'+fmt(alerts.pending_quotations)+'</b></div>'+
   (quoteItems.length?quoteItems.map(function(x){return '<div class="operation-item"><div><b>'+esc(x.quote_number)+' · '+esc(x.request_title)+'</b><small>'+esc(fmtDate(x.expires_at))+'</small></div>'+requestButton(x.request_title)+'</div>'}).join(""):'<div class="operation-empty">'+t("empty")+'</div>');
 }
}
async function load(){
 addUI();var token=localStorage.getItem("admin_access_token");if(!token)return;
 var select=document.getElementById("dashboardPeriod"),serviceSelect=document.getElementById("dashboardServiceFilter");if(select){select.value=String(period);select.disabled=true;}if(serviceSelect){serviceSelect.value=serviceId;serviceSelect.disabled=true;}
 var loadingMarkup='<div class="dashboard-analytics-state" role="status">'+t("loading")+'</div>';
 ["periodServiceChart","periodOperations","trendChart","statusChart"].forEach(function(id){var el=document.getElementById(id);if(el)el.innerHTML=loadingMarkup});
 try{var query="?period_days="+period+(serviceId?"&service_id="+encodeURIComponent(serviceId):"");var r=await fetch("/api/v1/admin/dashboard/overview"+query,{headers:{Accept:"application/json",Authorization:"Bearer "+token}});if(!r.ok)throw Error("HTTP "+r.status);render(await r.json())}
 catch(e){var errorMarkup='<div class="dashboard-analytics-state" role="alert">'+t("error")+' <button type="button" class="operation-open-request" data-dashboard-retry>'+t("retry")+'</button></div>';
  ["periodServiceChart","periodOperations","trendChart","statusChart"].forEach(function(id){var el=document.getElementById(id);if(el)el.innerHTML=errorMarkup});
  ["new_customers","new_users","new_requests"].forEach(function(key){var card=document.querySelector('[data-metric="'+key+'"] .metric-value');if(card)card.textContent="—"});
 }finally{if(select)select.disabled=false;if(serviceSelect)serviceSelect.disabled=false;}
}
document.addEventListener("click",function(event){
 var retry=event.target.closest&&event.target.closest("[data-dashboard-retry]");if(retry){load();return;}
 var button=event.target.closest&&event.target.closest("[data-request-title]");if(!button)return;
 var nav=document.querySelector('.nav-item[data-page="requests"]'),search=document.getElementById("requestSearch");
 if(!nav||nav.hidden||!search)return;
 search.value=button.getAttribute("data-request-title")||"";
 nav.click();
});
window.refreshDashboardPeriodAnalytics=load;
document.addEventListener("DOMContentLoaded",function(){addUI();var previousLang=document.documentElement.lang;new MutationObserver(function(){if(previousLang!==document.documentElement.lang){previousLang=document.documentElement.lang;refreshLabels();load()}}).observe(document.documentElement,{attributes:true,attributeFilter:["lang"]})});
})();
