"use strict";

const COPY = {
  ar: {
    brand: "احتراف الأكاديمية", brandSub: "خدمات أكاديمية موثوقة",
    navHome: "الرئيسية", navServices: "الخدمات", navRequests: "طلباتي", navNotifications: "الإشعارات", navHelp: "المساعدة",
    splashTag: "منصة الخدمات الأكاديمية", splashTitle: "مرحباً بك في احتراف الأكاديمية",
    splashText: "اكتشف خدمات أكاديمية موثوقة، قدّم طلبك، وتابع حالته من مكان واحد.",
    enter: "ابدأ الاستخدام", splashFoot: "وجهتك الواضحة للخدمات الطلابية",
    homeEyebrow: "مساحتك الأكاديمية", homeTitle: "مرحباً بك", homeText: "ما الخدمة الأكاديمية التي تبحث عنها اليوم؟",
    search: "ابحث عن خدمة أو تخصص...", categories: "التخصصات", categoriesSub: "اكتشف المجالات الأكاديمية المتاحة",
    allCategories: "كل التخصصات", viewAll: "عرض الكل", viewLess: "عرض أقل", services: "خدمات مقترحة",
    browseServices: "تصفح الخدمات المتاحة", requestCtaTitle: "لديك عمل أكاديمي؟", requestCtaText: "ابدأ طلباً جديداً بخطوات بسيطة وواضحة.",
    startRequest: "إنشاء طلب", serviceCount: "خدمة", specialtyCount: "خدمات",
    categoryTitle: "جميع التخصصات", categorySub: "اختر المجال لعرض الخدمات المتاحة",
    categorySearch: "ابحث عن تخصص...", categoryServicesSearch: "ابحث في هذا التخصص...",
    categoryServicesTitle: "الخدمات المتاحة", chooseService: "اختر الخدمة المناسبة لاحتياجك",
    createRequest: "اطلب هذه الخدمة", noServices: "لا توجد خدمات متاحة في هذا التخصص حالياً.",
    noCategories: "لا توجد تخصصات متاحة حالياً.", noSearch: "لم نعثر على نتائج مطابقة. جرّب عبارة أخرى.",
    loadServices: "جارٍ تحميل الخدمات المتاحة...", loadFailed: "تعذر تحميل الخدمات. تحقق من اتصالك وحاول مجدداً.",
    retry: "إعادة المحاولة", requestTitle: "طلب جديد", requestIntro: "أرسل احتياجك الأكاديمي بخطوات واضحة.",
    stepService: "الخدمة", stepDetails: "التفاصيل", stepReview: "المراجعة",
    serviceLabel: "الخدمة المطلوبة", selectService: "اختر خدمة", detailsLabel: "وصف الطلب",
    detailsPlaceholder: "اشرح ما تحتاج إليه بوضوح...", detailsHint: "أضف المتطلبات أو النقاط التي تساعدنا على فهم طلبك.",
    titleLabel: "عنوان الطلب (اختياري)", titlePlaceholder: "مثال: إعداد خطة بحث",
    specializationLabel: "التخصص الدراسي (اختياري)", specializationPlaceholder: "مثال: إدارة الأعمال",
    deadlineLabel: "الموعد المطلوب (اختياري)", attachmentTitle: "المرفقات",
    attachmentUnavailable: "رفع الملفات غير متاح حالياً في التطبيق. أرسل وصف المتطلبات ضمن تفاصيل الطلب.",
    continue: "متابعة", previous: "السابق", review: "مراجعة الطلب", sendRequest: "إرسال الطلب",
    reviewIntro: "تأكد من بيانات الطلب قبل الإرسال.", requestSummary: "ملخص الطلب",
    requiredService: "اختر الخدمة المطلوبة أولاً.", requiredDetails: "اكتب تفاصيل الطلب (3 أحرف على الأقل).",
    titleTooShort: "يجب أن يتكون عنوان الطلب من 3 أحرف على الأقل.", authRequiredTitle: "يلزم تسجيل الدخول",
    authRequiredBody: "عرض طلباتك وإرسال طلب جديد يتطلبان رمز وصول Bearer صالحاً. لا يتوفر رمز وصول في هذه الجلسة، ولم يتم استخدام بيانات Telegram كبديل.",
    authGapHint: "لا توجد آلية مصادقة Telegram مرتبطة بهذه الواجهة حتى الآن.",
    requestFailed: "تعذر إرسال الطلب. لم يتم إنشاء طلب جديد. تحقق من البيانات ثم حاول مجدداً.",
    requestCreated: "تم إرسال طلبك بنجاح.", requestListTitle: "طلباتي", requestListSub: "الطلبات التي أرسلتها إلى المنصة",
    requestEmptyTitle: "لا توجد طلبات لعرضها", requestEmptyBody: "ستظهر هنا الطلبات المرتبطة بحسابك بعد تفعيل الوصول الموثق.",
    filterAll: "الكل", filterActive: "قيد التنفيذ", filterCompleted: "مكتملة", filterClosed: "ملغاة",
    requestsLoadFailed: "تعذر تحميل الطلبات. لم يتم تعديل أي بيانات.",
    retryRequests: "إعادة تحميل الطلبات", auth: "المصادقة", requestDetailTitle: "تفاصيل الطلب",
    requestNumber: "رقم الطلب", serviceName: "الخدمة", createdAt: "تاريخ الإرسال", deadline: "الموعد المطلوب",
    status: "الحالة", description: "تفاصيل الطلب", statusOnlyTitle: "حالة الطلب الحالية",
    statusOnlyBody: "تعرض هذه الصفحة الحالة المسجلة في الطلب فقط. سجل التحديثات غير متاح حالياً.",
    requestNotFound: "لم نعثر على هذا الطلب ضمن الطلبات المحملة.", goRequests: "العودة إلى طلباتي",
    notificationTitle: "الإشعارات", notificationSub: "آخر التنبيهات المرتبطة بطلباتك",
    notificationUnavailableTitle: "الإشعارات غير متاحة بعد",
    notificationUnavailableBody: "لا توجد إشعارات مرتبطة بحسابك حالياً.",
    notificationsLoading: "جارٍ تحميل إشعاراتك…", notificationsEmpty: "لا توجد إشعارات جديدة حالياً.", notificationsFailed: "تعذر تحميل الإشعارات. حاول مرة أخرى.", notificationDate: "تاريخ الإشعار",
    supportTitle: "الدعم والمساعدة", supportSub: "إجابات سريعة حول استخدام المنصة",
    supportContactTitle: "التواصل مع الدعم", supportContactBody: "لم يتم إعداد وسيلة تواصل رسمية داخل التطبيق بعد.",
    faqTitle: "الأسئلة الشائعة", faq1: "كيف أجد الخدمة المناسبة؟", faq1a: "تصفح التخصصات أو استخدم البحث لعرض الخدمات المتاحة في الكتالوج.",
    faq2: "كيف أرسل طلباً؟", faq2a: "اختر الخدمة، اكتب التفاصيل، راجع المعلومات ثم أرسل الطلب. يتطلب الإرسال رمز وصول صالحاً.",
    faq3: "أين أتابع طلبي؟", faq3a: "افتح «طلباتي» لعرض الطلبات الفعلية المرتبطة بحسابك. تظهر تفاصيل الطلب والحالة المسجلة فقط.",
    faq4: "هل يمكن إرفاق ملف؟", faq4a: "رفع الملفات غير متاح حالياً. أدرج المعلومات اللازمة في وصف الطلب.",
    faq5: "كيف أتواصل مع فريق الدعم؟", faq5a: "وسيلة التواصل الرسمية غير مهيأة في التطبيق حالياً.",
    languageTitle: "اختيار اللغة", languageSub: "اختر اللغة المفضلة للتطبيق", arabic: "العربية", english: "English",
    save: "حفظ", close: "إغلاق", languageSaved: "تم حفظ تفضيل اللغة.",
    statusUnknown: "غير محددة", statusNew: "جديد", statusPending: "قيد الانتظار",
    statusInProgress: "قيد التنفيذ", statusCompleted: "مكتمل", statusCancelled: "ملغي",
    statusRejected: "مرفوض", statusReview: "قيد المراجعة", requiredField: "هذا الحقل مطلوب.",
    back: "رجوع", emptyValue: "غير محدد", categoryOther: "غير مصنف",
  },
  en: {
    brand: "Professional Academy", brandSub: "Trusted academic services",
    navHome: "Home", navServices: "Services", navRequests: "Requests", navNotifications: "Alerts", navHelp: "Help",
    splashTag: "ACADEMIC SERVICES PLATFORM", splashTitle: "Welcome to Professional Academy",
    splashText: "Find trusted academic support, send a request, and follow its status in one place.",
    enter: "Get started", splashFoot: "A clearer way to access student services",
    homeEyebrow: "YOUR ACADEMIC SPACE", homeTitle: "Welcome", homeText: "What academic service are you looking for today?",
    search: "Search services or specialties...", categories: "Specialties", categoriesSub: "Explore the available academic fields",
    allCategories: "All specialties", viewAll: "View all", viewLess: "Show less", services: "Suggested services",
    browseServices: "Browse available services", requestCtaTitle: "Working on something academic?", requestCtaText: "Start a new request with a few clear steps.",
    startRequest: "New request", serviceCount: "services", specialtyCount: "services",
    categoryTitle: "All specialties", categorySub: "Choose a field to see available services",
    categorySearch: "Search specialties...", categoryServicesSearch: "Search this specialty...",
    categoryServicesTitle: "Available services", chooseService: "Choose the service that fits your needs",
    createRequest: "Request this service", noServices: "No services are available in this specialty right now.",
    noCategories: "No specialties are available right now.", noSearch: "No matching results. Try another search.",
    loadServices: "Loading available services...", loadFailed: "Services could not be loaded. Check your connection and try again.",
    retry: "Try again", requestTitle: "New request", requestIntro: "Share your academic needs in a few clear steps.",
    stepService: "Service", stepDetails: "Details", stepReview: "Review",
    serviceLabel: "Requested service", selectService: "Choose a service", detailsLabel: "Request description",
    detailsPlaceholder: "Describe what you need...", detailsHint: "Include requirements or details that will help us understand your request.",
    titleLabel: "Request title (optional)", titlePlaceholder: "For example: Research plan",
    specializationLabel: "Area of study (optional)", specializationPlaceholder: "For example: Business administration",
    deadlineLabel: "Requested deadline (optional)", attachmentTitle: "Attachments",
    attachmentUnavailable: "File uploads are not available in the app yet. Include requirements in your request description.",
    continue: "Continue", previous: "Back", review: "Review request", sendRequest: "Submit request",
    reviewIntro: "Check your request details before submitting.", requestSummary: "Request summary",
    requiredService: "Choose a service first.", requiredDetails: "Enter request details (at least 3 characters).",
    titleTooShort: "The request title must be at least 3 characters.", authRequiredTitle: "Authentication required",
    authRequiredBody: "Viewing your requests and submitting a new one require a valid Bearer access token. No access token is available in this session; Telegram data is not used as a substitute.",
    authGapHint: "Telegram authentication is not connected to this interface yet.",
    requestFailed: "The request could not be submitted. No new request was created. Check the details and try again.",
    requestCreated: "Your request was submitted.", requestListTitle: "My requests", requestListSub: "Requests you have sent to the platform",
    requestEmptyTitle: "No requests to show", requestEmptyBody: "Requests linked to your account will appear here when authenticated access is available.",
    filterAll: "All", filterActive: "In progress", filterCompleted: "Completed", filterClosed: "Closed",
    requestsLoadFailed: "Requests could not be loaded. No data was changed.",
    retryRequests: "Reload requests", auth: "Authentication", requestDetailTitle: "Request details",
    requestNumber: "Request ID", serviceName: "Service", createdAt: "Submitted", deadline: "Requested deadline",
    status: "Status", description: "Request details", statusOnlyTitle: "Current request status",
    statusOnlyBody: "This page shows only the status recorded on the request. An update history is not available.",
    requestNotFound: "This request was not found in the loaded request list.", goRequests: "Back to my requests",
    notificationTitle: "Notifications", notificationSub: "Alerts related to your requests",
    notificationUnavailableTitle: "No notifications yet",
    notificationUnavailableBody: "There are no notifications linked to your account yet.",
    notificationsLoading: "Loading your notifications…", notificationsEmpty: "You have no notifications right now.", notificationsFailed: "Notifications could not be loaded. Please try again.", notificationDate: "Notification date",
    supportTitle: "Help & support", supportSub: "Quick answers about using the platform",
    supportContactTitle: "Contact support", supportContactBody: "An official contact method has not been configured in the app.",
    faqTitle: "Frequently asked questions", faq1: "How do I find the right service?", faq1a: "Browse specialties or search the catalog to see available services.",
    faq2: "How do I submit a request?", faq2a: "Choose a service, describe what you need, review the details, then submit. A valid access token is required.",
    faq3: "Where can I follow a request?", faq3a: "Open My requests to see real requests linked to your account. Only recorded details and status are shown.",
    faq4: "Can I attach a file?", faq4a: "File uploads are not available yet. Include necessary information in the request description.",
    faq5: "How can I contact support?", faq5a: "An official support contact method is not configured in the app.",
    languageTitle: "Choose language", languageSub: "Select your preferred app language", arabic: "العربية", english: "English",
    save: "Save", close: "Close", languageSaved: "Language preference saved.",
    statusUnknown: "Not specified", statusNew: "New", statusPending: "Pending",
    statusInProgress: "In progress", statusCompleted: "Completed", statusCancelled: "Cancelled",
    statusRejected: "Rejected", statusReview: "In review", requiredField: "This field is required.",
    back: "Back", emptyValue: "Not specified", categoryOther: "Uncategorized",
  }
};

const CATEGORY_NAMES = {
  "الشبكات والبنية التحتية": "Networking & Infrastructure",
  "البرمجة وتطوير الأنظمة": "Programming & Systems Development",
  "الأمن السيبراني": "Cybersecurity",
  "تحليل البيانات والإحصاء": "Data Analytics & Statistics",
  "الحوسبة السحابية وDevOps": "Cloud Computing & DevOps",
  "البحوث والدراسات": "Research & Studies",
  "مشاريع التخرج": "Graduation Projects",
  "المراجع والتوثيق": "References & Citation",
  "تطوير الويب": "Web Development",
  "الكتابة الأكاديمية": "Academic Writing",
  "قواعد البيانات": "Databases",
  "الذكاء الاصطناعي": "Artificial Intelligence",
  "الخدمات الطلابية العامة": "General Student Services",
  "التدريب والاستشارات": "Training & Consulting",
  "التدقيق والمراجعة": "Proofreading & Review",
  "تطبيقات الهاتف": "Mobile Applications",
  "التصميم والمحتوى المرئي": "Design & Visual Content",
  "الواجبات والمهام الدراسية": "Assignments & Coursework",
  "الترجمة": "Translation",
  "العروض والتقديم": "Presentations"
};

const ICONS = {
  cap: '<path d="m3 10 9-6 9 6-9 6-9-6Z"/><path d="M7 13v5c3 2.6 7 2.6 10 0v-5M21 11v6"/>',
  book: '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v17H6.5A2.5 2.5 0 0 1 4 17.5z"/><path d="M4 17.5A2.5 2.5 0 0 1 6.5 15H20M9 7h7M9 10h7"/>',
  code: '<path d="m8 7-5 5 5 5M16 7l5 5-5 5M14 4l-4 16"/>',
  chart: '<path d="M4 19V5M4 19h17"/><path d="m7 15 4-4 3 2 6-7"/>',
  shield: '<path d="M12 3 20 6v5c0 5-3.5 8-8 10-4.5-2-8-5-8-10V6z"/><path d="m9 12 2 2 4-4"/>',
  cloud: '<path d="M7 18h10a4 4 0 0 0 .3-8 6 6 0 0 0-11.5 1A3.5 3.5 0 0 0 7 18Z"/>',
  search: '<circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 4.5 4.5"/>',
  arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  chevron: '<path d="m9 18 6-6-6-6"/>',
  file: '<path d="M6 3h8l5 5v13H6z"/><path d="M14 3v6h5M9 14h7M9 17h7"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  alert: '<path d="M12 3 2.8 20h18.4L12 3Z"/><path d="M12 9v5M12 17h.01"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  close: '<path d="m6 6 12 12M18 6 6 18"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/>',
  help: '<circle cx="12" cy="12" r="9"/><path d="M9.7 9a2.4 2.4 0 1 1 4 1.8c-1 .7-1.7 1-1.7 2.2M12 17h.01"/>',
  mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m4 7 8 6 8-6"/>',
  globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18"/>',
  bell: '<path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9ZM10 21h4"/>',
  refresh: '<path d="M20 7v5h-5M4 17v-5h5"/><path d="M5.5 9A7 7 0 0 1 18 6l2 6M4 12l2 6a7 7 0 0 0 12.5-3"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="m19.4 15 .1.1 1.4 1.1-1.4 2.4-1.7-.6a8 8 0 0 1-1.5.9l-.3 1.8h-2.8l-.3-1.8a8 8 0 0 1-1.5-.9l-1.7.6-1.4-2.4 1.4-1.1a7 7 0 0 1 0-1.8l-1.4-1.1 1.4-2.4 1.7.6a8 8 0 0 1 1.5-.9l.3-1.8h2.8l.3 1.8a8 8 0 0 1 1.5.9l1.7-.6 1.4 2.4-1.4 1.1a7 7 0 0 1 0 1.7Z"/>'
};

const $ = (id) => document.getElementById(id);
const t = (key) => COPY[state.language][key] || COPY.ar[key] || key;
const state = {
  language: localStorage.getItem("academic-miniapp-language") === "en" ? "en" : "ar",
  services: [],
  categories: [],
  servicesState: "loading",
  servicesError: false,
  search: "",
  showAll: false,
  requests: [],
  requestsState: "idle",
  notifications: [],
  notificationsState: "idle",
  requestFilter: "all",
  draft: { serviceId: "", title: "", description: "", specialization: "", deadline: "" },
  faqOpen: null,
  languageReturnRoute: "home",
  current: { name: "splash", id: null, step: "service", query: new URLSearchParams() },
  toastTimer: null
};

function icon(name, extraClass = "") {
  return `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ICONS.book}</svg>`;
}

function escapeHTML(value) {
  return String(value == null ? "" : value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);
}

function setLanguage(language, persist = true) {
  state.language = language === "en" ? "en" : "ar";
  document.documentElement.lang = state.language;
  document.documentElement.dir = state.language === "ar" ? "rtl" : "ltr";
  document.body.dir = document.documentElement.dir;
  if (persist) localStorage.setItem("academic-miniapp-language", state.language);
  const languageButton = $("languageBtn");
  if (languageButton) {
    languageButton.textContent = state.language === "ar" ? "English" : "العربية";
    languageButton.setAttribute("aria-label", state.language === "ar" ? "اختيار اللغة" : "Choose language");
  }
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.placeholder = t(element.dataset.i18nPlaceholder);
  });
}

function getExistingBearerToken() {
  // Integration seam for an already-authenticated host. This app deliberately
  // does not acquire, persist, or infer credentials from Telegram initData.
  const token = window.__ACADEMIC_BEARER_TOKEN__;
  return typeof token === "string" && token.trim() ? token.trim() : null;
}

function categoryName(service) {
  return (service && service.category && service.category.name) || service.category_name || "";
}

function categoryId(service) {
  return (service && service.category && service.category.id) || service.category_id || "__uncategorized__";
}

function displayCategoryName(name) {
  if (!name) return t("categoryOther");
  return state.language === "en" ? (CATEGORY_NAMES[name] || name) : name;
}

function serviceDescription(service) {
  return service && (service.short_description || service.description) || "";
}

function buildCategories() {
  const groups = new Map();
  state.services.forEach((service) => {
    const id = categoryId(service);
    const name = categoryName(service) || t("categoryOther");
    if (!groups.has(id)) groups.set(id, { id, name, count: 0 });
    groups.get(id).count += 1;
  });
  state.categories = [...groups.values()].sort((a, b) =>
    b.count - a.count || a.name.localeCompare(b.name, state.language === "ar" ? "ar" : "en")
  );
}

function parseRouteValue(value) {
  const raw = decodeURIComponent(String(value || "").replace(/^#/, ""));
  const [routeText, queryText = ""] = raw.split("?");
  const parts = routeText.split("/").filter(Boolean);
  const route = { name: parts[0] || "splash", id: parts[1] || null, step: "service", query: new URLSearchParams(queryText) };
  if (route.name === "new-request") {
    route.step = route.query.get("step") || "service";
    const serviceId = route.query.get("service");
    if (serviceId) state.draft.serviceId = serviceId;
  }
  if (!["splash", "home", "categories", "category", "new-request", "requests", "request", "notifications", "support", "language"].includes(route.name)) {
    route.name = "home";
  }
  return route;
}

function parseRoute() {
  return parseRouteValue(window.location.hash);
}

function setHash(route) {
  const nextHash = `#${route}`;
  if (window.location.hash === nextHash) {
    state.current = parseRoute();
    render();
    return;
  }
  window.location.hash = route;
}

function navigate(name, id = null, query = null) {
  let route = name;
  if (id != null) route += `/${encodeURIComponent(String(id))}`;
  if (query instanceof URLSearchParams && query.toString()) route += `?${query.toString()}`;
  setHash(route);
}

function navigateRequestStep(step) {
  const query = new URLSearchParams({ step });
  if (state.draft.serviceId) query.set("service", state.draft.serviceId);
  setHash(`new-request?${query.toString()}`);
}

function back() {
  const route = state.current;
  if (route.name === "language") {
    navigate(state.languageReturnRoute || "home");
  } else if (route.name === "category") {
    navigate("categories");
  } else if (route.name === "request") {
    navigate("requests");
  } else if (route.name === "new-request") {
    if (route.step === "review") navigateRequestStep("details");
    else if (route.step === "details") navigateRequestStep("service");
    else navigate("categories");
  } else {
    navigate("home");
  }
}

function topbarAndNav() {
  const visible = state.current.name !== "splash";
  $("topbar").hidden = !visible;
  $("bottomNav").hidden = !visible || state.current.name === "language";
  document.querySelectorAll("[data-route-nav]").forEach((link) => {
    const nav = link.dataset.routeNav;
    const active = nav === state.current.name ||
      (nav === "categories" && state.current.name === "category") ||
      (nav === "requests" && state.current.name === "request") ||
      (nav === "home" && state.current.name === "new-request");
    link.classList.toggle("active", active);
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
}

function pageHeader(title, subtitle, backButton = true) {
  return `<div class="page-head">
    ${backButton ? `<button type="button" class="back-button" data-action="back" aria-label="${escapeHTML(t("back"))}">${icon("arrow")}</button>` : ""}
    <div class="page-title"><h1>${escapeHTML(title)}</h1>${subtitle ? `<p>${escapeHTML(subtitle)}</p>` : ""}</div>
  </div>`;
}

function stateCard(iconName, title, body, action = "") {
  return `<div class="state-card"><span class="state-icon">${icon(iconName)}</span>
    <strong>${escapeHTML(title)}</strong><p>${escapeHTML(body)}</p>${action ? `<div class="button-row">${action}</div>` : ""}</div>`;
}

function categoryCard(category) {
  return `<button class="category-card" type="button" data-category-id="${escapeHTML(category.id)}">
    <span class="tile-icon">${icon(iconForCategory(category.name))}</span>
    <strong>${escapeHTML(displayCategoryName(category.name))}</strong>
    <small>${category.count} ${escapeHTML(t("serviceCount"))}</small>
    <span class="card-chevron">${icon("chevron")}</span>
  </button>`;
}

function iconForCategory(name) {
  const value = String(name || "").toLowerCase();
  if (/برمج|تطوير|code|program|web|نظم/.test(value)) return "code";
  if (/بيانات|إحصاء|تحليل|data|stat/.test(value)) return "chart";
  if (/أمن|cyber|security/.test(value)) return "shield";
  if (/سحاب|cloud|devops|شبك|infra/.test(value)) return "cloud";
  if (/بحث|دراس|كتابة|مراجع|research|writing/.test(value)) return "book";
  return "cap";
}

function serviceCard(service) {
  return `<article class="service-card">
    <span class="tile-icon">${icon(iconForCategory(categoryName(service)))}</span>
    <strong>${escapeHTML(service.name)}</strong>
    <small class="service-description">${escapeHTML(serviceDescription(service) || displayCategoryName(categoryName(service)))}</small>
    <button class="text-button" type="button" data-action="select-service" data-service-id="${escapeHTML(service.id)}">${escapeHTML(t("createRequest"))}${icon("arrow")}</button>
  </article>`;
}

function renderServicesLoading() {
  return `<div class="loading-card" aria-label="${escapeHTML(t("loadServices"))}">
    <div class="skeleton wide"></div><div class="skeleton"></div><div class="skeleton short"></div>
  </div>`;
}

function renderServicesFailure() {
  return stateCard("refresh", t("loadFailed"), t("loadFailed"),
    `<button class="secondary-button" type="button" data-action="retry-services">${icon("refresh")}${escapeHTML(t("retry"))}</button>`);
}

function categoryMatchesSearch(category, query) {
  return [category.name, displayCategoryName(category.name)].some((name) =>
    name.toLocaleLowerCase().includes(query)
  );
}

function filteredServices(category = null, query = "") {
  const normalized = query.toLocaleLowerCase();
  return state.services.filter((service) => {
    if (category && categoryId(service) !== category.id) return false;
    if (!normalized) return true;
    return [service.name, serviceDescription(service), categoryName(service), displayCategoryName(categoryName(service))]
      .some((value) => String(value || "").toLocaleLowerCase().includes(normalized));
  });
}

function renderHome() {
  const query = state.search.trim().toLocaleLowerCase();
  const matches = state.categories.filter((category) => !query || categoryMatchesSearch(category, query));
  const visibleCategories = (state.showAll || query ? matches : matches.slice(0, 4));
  const serviceMatches = filteredServices(null, state.search.trim()).slice(0, 4);
  const categoryContent = state.servicesState === "loading" ? renderServicesLoading()
    : state.servicesState === "error" ? renderServicesFailure()
      : !state.categories.length ? stateCard("book", t("noCategories"), t("noCategories"))
        : visibleCategories.length ? `<div class="category-grid">${visibleCategories.map(categoryCard).join("")}</div>`
          : stateCard("search", t("noSearch"), t("noSearch"));
  const serviceContent = state.servicesState === "loading" ? renderServicesLoading()
    : state.servicesState === "error" ? ""
      : !serviceMatches.length ? stateCard("search", t("noSearch"), t("noSearch"))
        : `<div class="service-grid">${serviceMatches.map(serviceCard).join("")}</div>`;
  const moreButton = !query && state.categories.length > 4
    ? `<button class="text-button" type="button" data-action="toggle-categories">${escapeHTML(state.showAll ? t("viewLess") : t("viewAll"))}${icon("arrow")}</button>` : "";
  return `<section class="page">
    <div class="hero">
      <div class="hero-copy">
        <span class="eyebrow">${escapeHTML(t("homeEyebrow"))}</span>
        <h1>${escapeHTML(t("homeTitle"))}</h1>
        <p>${escapeHTML(t("homeText"))}</p>
        <label class="search">${icon("search")}<input id="serviceSearch" type="search" value="${escapeHTML(state.search)}" placeholder="${escapeHTML(t("search"))}" autocomplete="off" aria-label="${escapeHTML(t("search"))}"></label>
      </div>
    </div>
    <section class="section">
      <div class="section-heading"><div><h2>${escapeHTML(t("categories"))}</h2><p>${escapeHTML(t("categoriesSub"))}</p></div>${moreButton}</div>
      ${categoryContent}
    </section>
    <section class="section">
      <div class="section-heading"><div><h2>${escapeHTML(t("services"))}</h2><p>${escapeHTML(t("browseServices"))}</p></div></div>
      ${serviceContent}
    </section>
    <div class="quick-panel"><div><strong>${escapeHTML(t("requestCtaTitle"))}</strong><p>${escapeHTML(t("requestCtaText"))}</p></div>
      <button class="primary-button" type="button" data-action="new-request">${icon("plus")}${escapeHTML(t("startRequest"))}</button>
    </div>
  </section>`;
}

function renderCategories() {
  let content;
  if (state.servicesState === "loading") content = renderServicesLoading();
  else if (state.servicesState === "error") content = renderServicesFailure();
  else if (!state.categories.length) content = stateCard("book", t("noCategories"), t("noCategories"));
  else content = `<div class="category-grid">${state.categories.map(categoryCard).join("")}</div>`;
  return `<section class="page">${pageHeader(t("categoryTitle"), t("categorySub"))}${content}</section>`;
}

function renderCategory() {
  const category = state.categories.find((item) => item.id === state.current.id);
  const title = category ? displayCategoryName(category.name) : t("categoryTitle");
  let content;
  if (state.servicesState === "loading") content = renderServicesLoading();
  else if (state.servicesState === "error") content = renderServicesFailure();
  else {
    const list = filteredServices(category || { id: state.current.id }, "");
    content = list.length ? `<div class="service-grid">${list.map(serviceCard).join("")}</div>`
      : stateCard("book", t("noServices"), t("noServices"));
  }
  return `<section class="page">${pageHeader(title, t("chooseService"))}
    <div class="section-heading"><div><h2>${escapeHTML(t("categoryServicesTitle"))}</h2><p>${escapeHTML(t("chooseService"))}</p></div></div>
    ${content}
  </section>`;
}

function stepLabel(step) {
  const steps = ["service", "details", "review"];
  const labels = [t("stepService"), t("stepDetails"), t("stepReview")];
  const index = steps.indexOf(step);
  return `<div class="stepper" aria-label="${escapeHTML(labels[index] || labels[0])}">
    ${steps.map((item, i) => `<div class="step ${i < index ? "done" : ""} ${i === index ? "active" : ""}">
      <span class="step-number">${i < index ? icon("check") : i + 1}</span><span>${escapeHTML(labels[i])}</span>
    </div>${i < 2 ? '<span class="step-line"></span>' : ""}`).join("")}
  </div>`;
}

function requestServiceOptions() {
  return `<option value="">${escapeHTML(t("selectService"))}</option>${state.services.map((service) =>
    `<option value="${escapeHTML(service.id)}" ${String(service.id) === state.draft.serviceId ? "selected" : ""}>${escapeHTML(service.name)}</option>`
  ).join("")}`;
}

function requestStepService() {
  if (state.servicesState === "loading") return renderServicesLoading();
  if (state.servicesState === "error") return renderServicesFailure();
  if (!state.services.length) return stateCard("book", t("noServices"), t("noServices"));
  return `<form class="content-card form-grid" id="requestServiceForm">
    <div class="field"><label for="requestService">${escapeHTML(t("serviceLabel"))}</label>
      <select id="requestService" name="service_id" required>${requestServiceOptions()}</select></div>
    <p class="form-error" id="requestStepError" hidden></p>
    <button class="primary-button" type="submit">${escapeHTML(t("continue"))}${icon("arrow")}</button>
  </form>`;
}

function requestStepDetails() {
  const selected = state.services.find((service) => String(service.id) === state.draft.serviceId);
  if (!selected) return `<div class="content-card">${stateCard("alert", t("requiredService"), t("requiredService"), `<button class="secondary-button" type="button" data-action="request-step" data-step="service">${escapeHTML(t("previous"))}</button>`)}</div>`;
  return `<form class="content-card form-grid" id="requestDetailsForm">
    <div class="field"><label for="requestTitle">${escapeHTML(t("titleLabel"))}</label><input id="requestTitle" name="title" maxlength="300" value="${escapeHTML(state.draft.title)}" placeholder="${escapeHTML(t("titlePlaceholder"))}"></div>
    <div class="field"><label for="requestSpecialization">${escapeHTML(t("specializationLabel"))}</label><input id="requestSpecialization" name="specialization" maxlength="255" value="${escapeHTML(state.draft.specialization)}" placeholder="${escapeHTML(t("specializationPlaceholder"))}"></div>
    <div class="field"><label for="requestDescription">${escapeHTML(t("detailsLabel"))} <span aria-hidden="true">*</span></label><textarea id="requestDescription" name="description" minlength="3" maxlength="10000" required placeholder="${escapeHTML(t("detailsPlaceholder"))}">${escapeHTML(state.draft.description)}</textarea><small class="field-hint">${escapeHTML(t("detailsHint"))}</small></div>
    <div class="field"><label for="requestDeadline">${escapeHTML(t("deadlineLabel"))}</label><input id="requestDeadline" name="deadline" type="datetime-local" value="${escapeHTML(state.draft.deadline)}"></div>
    <div class="notice-banner">${icon("alert")}<p><strong>${escapeHTML(t("attachmentTitle"))}:</strong> ${escapeHTML(t("attachmentUnavailable"))}</p></div>
    <p class="form-error" id="requestStepError" hidden></p>
    <div class="button-row"><button class="secondary-button" type="button" data-action="request-step" data-step="service">${escapeHTML(t("previous"))}</button><button class="primary-button" type="submit">${escapeHTML(t("review"))}${icon("arrow")}</button></div>
  </form>`;
}

function requestStepReview() {
  const service = state.services.find((item) => String(item.id) === state.draft.serviceId);
  if (!service) return requestStepService();
  const deadline = state.draft.deadline ? formatDate(state.draft.deadline) : t("emptyValue");
  return `<div class="content-card">
    <div class="section-heading"><div><h2>${escapeHTML(t("requestSummary"))}</h2><p>${escapeHTML(t("reviewIntro"))}</p></div>${icon("file")}</div>
    <div class="review-line"><span>${escapeHTML(t("serviceName"))}</span><strong>${escapeHTML(service.name)}</strong></div>
    ${state.draft.title ? `<div class="review-line"><span>${escapeHTML(t("titleLabel"))}</span><strong>${escapeHTML(state.draft.title)}</strong></div>` : ""}
    ${state.draft.specialization ? `<div class="review-line"><span>${escapeHTML(t("specializationLabel"))}</span><strong>${escapeHTML(state.draft.specialization)}</strong></div>` : ""}
    <div class="review-line"><span>${escapeHTML(t("deadline"))}</span><strong>${escapeHTML(deadline)}</strong></div>
    <div class="review-line"><span>${escapeHTML(t("detailsLabel"))}</span><strong>${escapeHTML(state.draft.description)}</strong></div>
    <p class="form-error" id="requestSubmitError" hidden></p>
    <div class="button-row" style="margin-top:16px">
      <button class="secondary-button" type="button" data-action="request-step" data-step="details">${escapeHTML(t("previous"))}</button>
      <button class="primary-button" type="button" data-action="submit-request">${escapeHTML(t("sendRequest"))}${icon("arrow")}</button>
    </div>
  </div>`;
}

function renderNewRequest() {
  const step = ["service", "details", "review"].includes(state.current.step) ? state.current.step : "service";
  let content = step === "details" ? requestStepDetails() : step === "review" ? requestStepReview() : requestStepService();
  const authNote = !getExistingBearerToken()
    ? `<div class="notice-banner" style="margin-bottom:14px">${icon("alert")}<p>${escapeHTML(t("authRequiredBody"))}</p></div>`
    : "";
  return `<section class="page">${pageHeader(t("requestTitle"), t("requestIntro"))}${authNote}${stepLabel(step)}${content}</section>`;
}

function formatDate(dateValue) {
  if (!dateValue) return t("emptyValue");
  const date = new Date(dateValue);
  if (Number.isNaN(date.getTime())) return String(dateValue);
  return new Intl.DateTimeFormat(state.language === "ar" ? "ar" : "en", {
    year: "numeric", month: "short", day: "numeric",
    ...(String(dateValue).includes("T") ? { hour: "2-digit", minute: "2-digit" } : {})
  }).format(date);
}

function statusText(status) {
  const normalized = String(status || "").toUpperCase();
  const labels = {
    NEW: "statusNew", PENDING: "statusPending", IN_PROGRESS: "statusInProgress",
    PROCESSING: "statusInProgress", COMPLETED: "statusCompleted", DONE: "statusCompleted",
    CANCELLED: "statusCancelled", CANCELED: "statusCancelled", REJECTED: "statusRejected",
    UNDER_REVIEW: "statusReview", REVIEW: "statusReview"
  };
  return labels[normalized] ? t(labels[normalized]) : (status || t("statusUnknown"));
}

function authenticatedState() {
  return stateCard("user", t("authRequiredTitle"), t("authRequiredBody"),
    `<span class="field-hint">${escapeHTML(t("authGapHint"))}</span>`);
}

async function validateBearerToken(token) {
  const response = await fetch("/api/v1/auth/me", {
    method: "GET",
    headers: { Accept: "application/json", Authorization: `Bearer ${token}` }
  });
  if (!response.ok) {
    const error = new Error(`Authentication check failed (${response.status})`);
    error.authentication = response.status === 401 || response.status === 403;
    throw error;
  }
  return response.json();
}

async function loadRequests(force = false) {
  const token = getExistingBearerToken();
  if (!token) {
    state.requestsState = "auth";
    state.requests = [];
    render();
    return;
  }
  if (state.requestsState === "loading" && !force) return;
  state.requestsState = "loading";
  render();
  try {
    await validateBearerToken(token);
    const response = await fetch("/api/v1/customer/requests", {
      method: "GET",
      headers: { Accept: "application/json", Authorization: `Bearer ${token}` }
    });
    if (!response.ok) throw new Error(`Request list failed (${response.status})`);
    const payload = await response.json();
    if (!Array.isArray(payload.items)) throw new Error("Unexpected request list response");
    state.requests = payload.items;
    state.requestsState = "ready";
  } catch (error) {
    console.error("Could not load customer requests:", error);
    state.requestsState = error.authentication ? "auth" : "error";
  }
  render();
}

function renderRequests() {
  if (state.requestsState === "idle" || state.requestsState === "loading") {
    return `<section class="page">${pageHeader(t("requestListTitle"), t("requestListSub"))}${renderServicesLoading()}</section>`;
  }
  if (state.requestsState === "auth") {
    return `<section class="page">${pageHeader(t("requestListTitle"), t("requestListSub"))}${authenticatedState()}</section>`;
  }
  if (state.requestsState === "error") {
    return `<section class="page">${pageHeader(t("requestListTitle"), t("requestListSub"))}${stateCard("refresh", t("requestsLoadFailed"), t("requestsLoadFailed"), `<button class="secondary-button" type="button" data-action="retry-requests">${icon("refresh")}${escapeHTML(t("retryRequests"))}</button>`)}</section>`;
  }
  const requests = [...state.requests].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  const content = requests.length ? requests.map((request) => `<button class="request-row" type="button" data-request-id="${escapeHTML(request.id)}">
    <span class="request-id-icon">${icon("file")}</span>
    <span class="request-row-copy"><strong>${escapeHTML(request.title || request.service_name)}</strong><small>${escapeHTML(request.service_name)} · ${escapeHTML(formatDate(request.created_at))}</small></span>
    <span class="status-pill">${escapeHTML(statusText(request.status))}</span>
  </button>`).join("") : stateCard("file", t("requestEmptyTitle"), t("requestEmptyBody"));
  return `<section class="page">${pageHeader(t("requestListTitle"), t("requestListSub"))}${content}</section>`;
}

function renderRequestDetail() {
  if (state.requestsState === "idle" || state.requestsState === "loading") {
    return `<section class="page">${pageHeader(t("requestDetailTitle"), "")}${renderServicesLoading()}</section>`;
  }
  if (state.requestsState === "auth") {
    return `<section class="page">${pageHeader(t("requestDetailTitle"), "")}${authenticatedState()}</section>`;
  }
  if (state.requestsState === "error") {
    return `<section class="page">${pageHeader(t("requestDetailTitle"), "")}${stateCard("refresh", t("requestsLoadFailed"), t("requestsLoadFailed"), `<button class="secondary-button" type="button" data-action="retry-requests">${escapeHTML(t("retryRequests"))}</button>`)}</section>`;
  }
  const request = state.requests.find((item) => String(item.id) === String(state.current.id));
  if (!request) return `<section class="page">${pageHeader(t("requestDetailTitle"), "")}${stateCard("file", t("requestNotFound"), t("requestNotFound"), `<button class="secondary-button" type="button" data-action="go-requests">${escapeHTML(t("goRequests"))}</button>`)}</section>`;
  return `<section class="page">${pageHeader(t("requestDetailTitle"), "")}
    <article class="content-card">
      <div class="detail-top"><div><small>${escapeHTML(t("requestNumber"))} · ${escapeHTML(request.id)}</small><h2>${escapeHTML(request.title || request.service_name)}</h2></div><span class="status-pill">${escapeHTML(statusText(request.status))}</span></div>
      <div class="detail-meta">
        <div class="meta-item"><small>${escapeHTML(t("serviceName"))}</small><strong>${escapeHTML(request.service_name)}</strong></div>
        <div class="meta-item"><small>${escapeHTML(t("createdAt"))}</small><strong>${escapeHTML(formatDate(request.created_at))}</strong></div>
        <div class="meta-item"><small>${escapeHTML(t("deadline"))}</small><strong>${escapeHTML(formatDate(request.deadline))}</strong></div>
        <div class="meta-item"><small>${escapeHTML(t("status"))}</small><strong>${escapeHTML(statusText(request.status))}</strong></div>
      </div>
      <h3>${escapeHTML(t("description"))}</h3><p class="detail-description">${escapeHTML(request.description || t("emptyValue"))}</p>
      <div class="request-status-note">${icon("clock")}<span><strong>${escapeHTML(t("statusOnlyTitle"))}</strong><br>${escapeHTML(t("statusOnlyBody"))}</span></div>
    </article>
  </section>`;
}

function renderNotifications() {
  if (state.notificationsState === "idle" || state.notificationsState === "loading") {
    return `<section class="page">${pageHeader(t("notificationTitle"), t("notificationSub"))}${stateCard("bell", t("notificationTitle"), t("notificationsLoading"))}</section>`;
  }
  if (state.notificationsState === "auth") {
    return `<section class="page">${pageHeader(t("notificationTitle"), t("notificationSub"))}${authenticatedState()}</section>`;
  }
  if (state.notificationsState === "error") {
    return `<section class="page">${pageHeader(t("notificationTitle"), t("notificationSub"))}${stateCard("refresh", t("notificationUnavailableTitle"), t("notificationsFailed"), `<button class="secondary-button" type="button" data-action="retry-notifications">${escapeHTML(t("retry"))}</button>`)}</section>`;
  }
  const items = state.notifications.map((item) => `<article class="notification-card"><div class="notification-card-icon">${icon("bell")}</div><div class="notification-card-content"><h3>${escapeHTML(item.title)}</h3><p>${escapeHTML(item.message)}</p><time>${escapeHTML(new Date(item.created_at).toLocaleString(state.language === "ar" ? "ar" : "en-GB"))}</time></div></article>`).join("");
  return `<section class="page">${pageHeader(t("notificationTitle"), t("notificationSub"))}${items || stateCard("bell", t("notificationUnavailableTitle"), t("notificationsEmpty"))}</section>`;
}

async function loadNotifications() {
  const token = getExistingBearerToken();
  if (!token) { state.notificationsState = "auth"; render(); return; }
  state.notificationsState = "loading";
  render();
  try {
    const response = await fetch("/api/v1/notifications/me?limit=50", { method: "GET", headers: { Accept: "application/json", Authorization: `Bearer ${token}` } });
    if (!response.ok) throw new Error(`Notifications request failed (${response.status})`);
    const payload = await response.json();
    if (!Array.isArray(payload.items)) throw new Error("Unexpected notifications response");
    state.notifications = payload.items;
    state.notificationsState = "ready";
  } catch (error) {
    console.error("Could not load notifications:", error);
    state.notificationsState = "error";
  }
  render();
}

function renderSupport() {
  const questions = [1, 2, 3, 4, 5];
  return `<section class="page">${pageHeader(t("supportTitle"), t("supportSub"))}
    <div class="notice-banner">${icon("alert")}<p><strong>${escapeHTML(t("supportContactTitle"))}</strong><br>${escapeHTML(t("supportContactBody"))}</p></div>
    <section class="section"><div class="section-heading"><div><h2>${escapeHTML(t("faqTitle"))}</h2></div></div>
      <div class="faq-list">${questions.map((number) => {
        const open = state.faqOpen === number;
        return `<article class="faq-item">
          <button class="faq-question" type="button" data-faq="${number}" aria-expanded="${open}"><span>${escapeHTML(t(`faq${number}`))}</span>${icon("chevron")}</button>
          ${open ? `<div class="faq-answer">${escapeHTML(t(`faq${number}a`))}</div>` : ""}
        </article>`;
      }).join("")}</div>
    </section>
  </section>`;
}

function renderSplash() {
  return `<section class="splash">
    <div class="splash-inner">
      <div class="splash-mark">${icon("cap")}</div>
      <span class="eyebrow">${escapeHTML(t("splashTag"))}</span>
      <h1>${escapeHTML(t("splashTitle"))}</h1>
      <p class="english-name">Professional Academy</p>
      <p>${escapeHTML(t("splashText"))}</p>
      <button type="button" class="primary-button" data-action="enter">${escapeHTML(t("enter"))}${icon("arrow")}</button>
      <small class="splash-note">${escapeHTML(t("splashFoot"))}</small>
    </div>
  </section>`;
}

function renderLanguageOverlay() {
  const isOpen = state.current.name === "language";
  $("overlayRoot").innerHTML = isOpen ? `<div class="modal-backdrop" data-action="dismiss-language">
    <section class="language-modal" role="dialog" aria-modal="true" aria-labelledby="languageTitle">
      <button type="button" class="modal-close" data-action="close-language" aria-label="${escapeHTML(t("close"))}">${icon("close")}</button>
      <div class="modal-emblem">${icon("globe")}</div>
      <h2 id="languageTitle">${escapeHTML(t("languageTitle"))}</h2><p>${escapeHTML(t("languageSub"))}</p>
      <div class="language-options">
        <button class="language-option" type="button" data-language="ar" aria-pressed="${state.language === "ar"}"><span>${escapeHTML(t("arabic"))}</span>${state.language === "ar" ? icon("check") : ""}</button>
        <button class="language-option" type="button" data-language="en" aria-pressed="${state.language === "en"}"><span>${escapeHTML(t("english"))}</span>${state.language === "en" ? icon("check") : ""}</button>
      </div>
      <button type="button" class="primary-button language-save" data-action="save-language">${escapeHTML(t("save"))}${icon("check")}</button>
    </section>
  </div>` : "";
}

function render() {
  state.current = parseRoute();
  topbarAndNav();
  const screen = $("screen");
  screen.setAttribute("aria-busy", state.servicesState === "loading" && ["home", "categories", "category", "new-request"].includes(state.current.name) ? "true" : "false");
  const renderers = {
    splash: renderSplash,
    home: renderHome,
    categories: renderCategories,
    category: renderCategory,
    "new-request": renderNewRequest,
    requests: renderRequests,
    request: renderRequestDetail,
    notifications: renderNotifications,
    support: renderSupport,
    language: () => {
      const target = state.languageReturnRoute || "home";
      if (target === "home") return renderHome();
      if (target === "requests") return renderRequests();
      if (target === "categories") return renderCategories();
      if (target === "support") return renderSupport();
      if (target === "notifications") return renderNotifications();
      return renderHome();
    }
  };
  if (state.current.name === "language") {
    const overlayRoute = state.current;
    state.current = parseRouteValue(state.languageReturnRoute);
    screen.innerHTML = (renderers[state.current.name] || renderHome)();
    state.current = overlayRoute;
  } else {
    screen.innerHTML = (renderers[state.current.name] || renderHome)();
  }
  renderLanguageOverlay();
  if (state.current.name === "language") $("bottomNav").hidden = true;
  if (state.current.name === "request" && state.requestsState === "idle") {
    loadRequests();
  }
  if (state.current.name === "requests" && state.requestsState === "idle") {
    loadRequests();
  }
  if (state.current.name === "notifications" && state.notificationsState === "idle") {
    loadNotifications();
  }
  updateTelegramBackButton();
}

async function loadServices() {
  state.servicesState = "loading";
  render();
  try {
    const response = await fetch("/api/v1/public/services", {
      method: "GET",
      headers: { Accept: "application/json" }
    });
    if (!response.ok) throw new Error(`Services request failed (${response.status})`);
    const payload = await response.json();
    if (!Array.isArray(payload.items)) throw new Error("Unexpected services response");
    state.services = payload.items.filter((service) => service && service.id != null && service.name);
    buildCategories();
    state.servicesState = "ready";
  } catch (error) {
    console.error("Could not load public services:", error);
    state.servicesState = "error";
  }
  render();
}

function showToast(message) {
  const root = $("toastRoot");
  root.innerHTML = `<div class="toast" role="status">${escapeHTML(message)}</div>`;
  window.clearTimeout(state.toastTimer);
  state.toastTimer = window.setTimeout(() => { root.replaceChildren(); }, 3200);
}

function showFormError(form, message) {
  const error = form.querySelector("#requestStepError");
  if (error) {
    error.textContent = message;
    error.hidden = false;
  } else showToast(message);
}

function collectDetails(form) {
  const data = new FormData(form);
  state.draft.title = String(data.get("title") || "").trim();
  state.draft.specialization = String(data.get("specialization") || "").trim();
  state.draft.description = String(data.get("description") || "").trim();
  state.draft.deadline = String(data.get("deadline") || "").trim();
}

async function submitRequest(button) {
  const token = getExistingBearerToken();
  if (!token) {
    const target = $("requestSubmitError");
    if (target) {
      target.textContent = t("authRequiredBody");
      target.hidden = false;
    } else showToast(t("authRequiredBody"));
    return;
  }
  if (!state.draft.serviceId) {
    showToast(t("requiredService"));
    navigateRequestStep("service");
    return;
  }
  if (state.draft.description.trim().length < 3) {
    navigateRequestStep("details");
    window.setTimeout(() => showToast(t("requiredDetails")), 30);
    return;
  }
  if (state.draft.title && state.draft.title.length < 3) {
    navigateRequestStep("details");
    window.setTimeout(() => showToast(t("titleTooShort")), 30);
    return;
  }
  const payload = {
    service_id: state.draft.serviceId,
    description: state.draft.description
  };
  if (state.draft.title) payload.title = state.draft.title;
  if (state.draft.specialization) payload.specialization = state.draft.specialization;
  if (state.draft.deadline) {
    const deadline = new Date(state.draft.deadline);
    if (Number.isNaN(deadline.getTime())) {
      showToast(t("requiredField"));
      return;
    }
    payload.deadline = deadline.toISOString();
  }
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  try {
    await validateBearerToken(token);
    const response = await fetch("/api/v1/customer/requests", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });
    if (response.status !== 201) {
      let message = t("requestFailed");
      try {
        const errorBody = await response.json();
        if (errorBody && typeof errorBody.detail === "string") message = errorBody.detail;
      } catch (_) { /* Keep the honest generic failure message. */ }
      throw new Error(message);
    }
    const created = await response.json();
    if (!created || !created.id) throw new Error(t("requestFailed"));
    state.requests = [created, ...state.requests.filter((item) => String(item.id) !== String(created.id))];
    state.requestsState = "ready";
    state.draft = { serviceId: "", title: "", description: "", specialization: "", deadline: "" };
    showToast(t("requestCreated"));
    navigate("request", created.id);
  } catch (error) {
    console.error("Request submission failed:", error);
    const message = error.authentication ? t("authRequiredBody") : error instanceof Error ? error.message : t("requestFailed");
    const target = $("requestSubmitError");
    if (target) {
      target.textContent = message;
      target.hidden = false;
    } else showToast(message);
    button.disabled = false;
    button.removeAttribute("aria-busy");
  }
}

function openLanguage() {
  state.languageReturnRoute = state.current.name === "language"
    ? state.languageReturnRoute
    : (window.location.hash.replace(/^#/, "") || "home");
  navigate("language");
}

function closeLanguage() {
  setHash(state.languageReturnRoute || "home");
}

function handleClick(event) {
  const languageButton = event.target.closest("#languageBtn");
  if (languageButton) { openLanguage(); return; }
  const languageOption = event.target.closest("[data-language]");
  if (languageOption) {
    setLanguage(languageOption.dataset.language);
    render();
    return;
  }
  const actionElement = event.target.closest("[data-action]");
  if (actionElement) {
    const action = actionElement.dataset.action;
    if (action === "back") back();
    else if (action === "enter") navigate("home");
    else if (action === "new-request") {
      state.draft = { serviceId: "", title: "", description: "", specialization: "", deadline: "" };
      navigateRequestStep("service");
    } else if (action === "retry-services") loadServices();
    else if (action === "toggle-categories") {
      state.showAll = !state.showAll;
      render();
    } else if (action === "select-service") {
      state.draft.serviceId = actionElement.dataset.serviceId || "";
      navigateRequestStep("details");
    } else if (action === "request-step") {
      if (actionElement.dataset.step === "service") {
        const form = $("requestDetailsForm");
        if (form) collectDetails(form);
        navigateRequestStep("service");
      }
      else if (actionElement.dataset.step === "details") {
        const form = $("requestDetailsForm");
        if (form) collectDetails(form);
        navigateRequestStep("details");
      } else if (actionElement.dataset.step === "service-from-details") {
        const form = $("requestDetailsForm");
        if (form) collectDetails(form);
        navigateRequestStep("service");
      }
    } else if (action === "submit-request") submitRequest(actionElement);
    else if (action === "retry-requests") {
      state.requestsState = "idle";
      loadRequests(true);
    } else if (action === "retry-notifications") {
      state.notificationsState = "idle";
      loadNotifications();
    } else if (action === "go-requests") navigate("requests");
    else if (action === "close-language" || action === "save-language") {
      closeLanguage();
      if (action === "save-language") showToast(t("languageSaved"));
    } else if (action === "dismiss-language" && event.target === actionElement) {
      closeLanguage();
    }
    return;
  }
  const category = event.target.closest("[data-category-id]");
  if (category) {
    navigate("category", category.dataset.categoryId);
    return;
  }
  const request = event.target.closest("[data-request-id]");
  if (request) {
    navigate("request", request.dataset.requestId);
    return;
  }
  const faq = event.target.closest("[data-faq]");
  if (faq) {
    const value = Number(faq.dataset.faq);
    state.faqOpen = state.faqOpen === value ? null : value;
    render();
  }
}

function handleSubmit(event) {
  if (event.target.id === "requestServiceForm") {
    event.preventDefault();
    const serviceSelect = $("requestService");
    const value = serviceSelect ? serviceSelect.value : "";
    if (!value) {
      showFormError(event.target, t("requiredService"));
      return;
    }
    state.draft.serviceId = value;
    navigateRequestStep("details");
  } else if (event.target.id === "requestDetailsForm") {
    event.preventDefault();
    collectDetails(event.target);
    if (!state.draft.description || state.draft.description.length < 3) {
      showFormError(event.target, t("requiredDetails"));
      return;
    }
    if (state.draft.title && state.draft.title.length < 3) {
      showFormError(event.target, t("titleTooShort"));
      return;
    }
    navigateRequestStep("review");
  }
}

function handleInput(event) {
  if (event.target.id === "serviceSearch") {
    state.search = event.target.value;
    const position = event.target.selectionStart;
    render();
    const input = $("serviceSearch");
    if (input) {
      input.focus();
      input.setSelectionRange(position, position);
    }
  }
}

function updateTelegramBackButton() {
  const button = window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.BackButton;
  if (!button) return;
  const visible = !["home", "splash"].includes(state.current.name);
  try {
    if (visible) {
      button.show();
      button.offClick(back);
      button.onClick(back);
    } else {
      button.hide();
      button.offClick(back);
    }
  } catch (error) {
    console.debug("Telegram BackButton is unavailable:", error);
  }
}

function initializeTelegram() {
  const webApp = window.Telegram && window.Telegram.WebApp;
  if (!webApp) return;
  try {
    webApp.ready();
    webApp.expand();
  } catch (error) {
    console.debug("Telegram WebApp initialization was skipped:", error);
  }
}

function initialize() {
  initializeTelegram();
  setLanguage(state.language, false);
  document.addEventListener("click", handleClick);
  document.addEventListener("submit", handleSubmit);
  document.addEventListener("input", handleInput);
  window.addEventListener("hashchange", () => {
    state.current = parseRoute();
    render();
  });
  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && state.current.name === "language") closeLanguage();
  });
  if (!window.location.hash) {
    window.history.replaceState(null, "", `${window.location.pathname}${window.location.search}#splash`);
  }
  state.current = parseRoute();
  render();
  loadServices();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initialize, { once: true });
} else {
  initialize();
}
