"use strict";

const translations = {
  ar: {
    brand: "احتراف الأكاديمية",
    brandSubtitle: "خدمات أكاديمية احترافية",
    welcomeLabel: "مساحتك الأكاديمية",
    welcome: "مرحباً بك 👋",
    welcomeText: "كيف يمكننا مساعدتك اليوم؟",
    searchPlaceholder: "ابحث عن خدمة أو تخصص...",
    categoriesTitle: "تصفح التخصصات",
    categoriesSubtitle: "اختر التخصص المناسب لاحتياجك",
    showAllCategories: "عرض جميع الأصناف",
    showLessCategories: "عرض أقل",
    servicesTitle: "الخدمات الأكاديمية",
    servicesSubtitle: "اختر الخدمة التي تناسب احتياجك",
    allServices: "جميع الخدمات",
    clearCategory: "إلغاء التصفية",
    requestTitle: "أنشئ طلبك",
    requestSubtitle: "أخبرنا بما تحتاج إليه",
    serviceLabel: "نوع الخدمة",
    chooseService: "اختر الخدمة",
    detailsLabel: "تفاصيل الطلب",
    detailsPlaceholder: "اكتب تفاصيل ما تحتاج إليه...",
    submitRequest: "متابعة الطلب",
    myRequests: "طلباتي",
    trackingTitle: "طلباتي",
    trackingSubtitle: "تابع طلباتك وتحديثاتها",
    emptyTitle: "لا توجد طلبات حتى الآن",
    emptyText: "ستظهر طلباتك هنا بعد ربط إرسالها بالخادم.",
    notifications: "الإشعارات",
    notificationsTitle: "الإشعارات",
    notificationsSubtitle: "تابع آخر التنبيهات والتحديثات",
    noNotifications: "لا توجد إشعارات حالياً",
    account: "حسابي",
    accountTitle: "حسابي والإعدادات",
    profileSetting: "الملف الشخصي",
    languageSetting: "لغة التطبيق",
    notificationsSetting: "الإشعارات",
    appearanceSetting: "المظهر",
    supportTitle: "الدعم والمساعدة",
    supportText: "هل تحتاج إلى مساعدة؟ تواصل مع فريق الدعم.",
    home: "الرئيسية",
    services: "الخدمات",
    loadingServices: "جارٍ تحميل الخدمات...",
    servicesLoadFailed: "تعذّر تحميل الخدمات. تحقق من الاتصال ثم حدّث الصفحة.",
    noServices: "لا توجد خدمات متاحة حالياً.",
    noSearchResults: "لا توجد نتائج مطابقة لبحثك.",
    serviceCount: "خدمة",
    selectServiceFirst: "يرجى اختيار نوع الخدمة.",
    enterDetails: "يرجى كتابة تفاصيل الطلب.",
    requestPrepared: "تم التحقق من بيانات الطلب محلياً فقط. لم يُرسل إلى الخادم بعد.",
    categoryCount: "تخصص",
    profileNotice: "إدارة الملف الشخصي تحتاج إلى ربطها بنظام الحسابات.",
    notificationsNotice: "إعدادات الإشعارات ستتوفر عند ربط خدمة الإشعارات.",
    appearanceNotice: "المظهر الحالي هو الوضع الفاتح.",
    supportNotice: "يرجى إضافة وسيلة التواصل الرسمية مع الدعم.",
    research: "البحوث العلمية",
    graduation: "مشاريع التخرج",
    editing: "التدقيق الأكاديمي",
    consulting: "الاستشارات التعليمية"
  },
  en: {
    brand: "Professional Academy",
    brandSubtitle: "Professional Academic Services",
    welcomeLabel: "YOUR ACADEMIC SPACE",
    welcome: "Welcome 👋",
    welcomeText: "How can we help you today?",
    searchPlaceholder: "Search services or specialties...",
    categoriesTitle: "Explore Specialties",
    categoriesSubtitle: "Choose a specialty that fits your needs",
    showAllCategories: "View All Categories",
    showLessCategories: "Show Less",
    servicesTitle: "Academic Services",
    servicesSubtitle: "Choose a service that fits your needs",
    allServices: "All Services",
    clearCategory: "Clear Filter",
    requestTitle: "Create a Request",
    requestSubtitle: "Tell us what you need",
    serviceLabel: "Service Type",
    chooseService: "Choose a service",
    detailsLabel: "Request Details",
    detailsPlaceholder: "Describe what you need...",
    submitRequest: "Continue Request",
    myRequests: "My Requests",
    trackingTitle: "My Requests",
    trackingSubtitle: "Track your requests and updates",
    emptyTitle: "No requests yet",
    emptyText: "Your requests will appear here once submission is connected to the server.",
    notifications: "Notifications",
    notificationsTitle: "Notifications",
    notificationsSubtitle: "Stay up to date with alerts and updates",
    noNotifications: "No notifications yet",
    account: "Account",
    accountTitle: "Account & Settings",
    profileSetting: "Profile",
    languageSetting: "App Language",
    notificationsSetting: "Notifications",
    appearanceSetting: "Appearance",
    supportTitle: "Help & Support",
    supportText: "Need help? Contact the support team.",
    home: "Home",
    services: "Services",
    loadingServices: "Loading services...",
    servicesLoadFailed: "Could not load services. Check your connection and refresh.",
    noServices: "No services are currently available.",
    noSearchResults: "No matching results found.",
    serviceCount: "services",
    selectServiceFirst: "Please choose a service type.",
    enterDetails: "Please enter request details.",
    requestPrepared: "Request details validated locally only. Nothing has been sent to the server.",
    categoryCount: "specialties",
    profileNotice: "Profile management needs to be connected to the account system.",
    notificationsNotice: "Notification settings will be available when the notification service is connected.",
    appearanceNotice: "The current appearance is light mode.",
    supportNotice: "Please configure the official support contact method.",
    research: "Research Support",
    graduation: "Graduation Projects",
    editing: "Academic Editing",
    consulting: "Education Consulting"
  }
};

const categoryTranslations = {
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

let language = "ar";
let services = [];
let categories = [];
let selectedCategory = null;
let showAllCategories = false;
let searchQuery = "";

const $ = (id) => document.getElementById(id);
const t = (key) => translations[language][key] || translations.ar[key] || key;

function displayCategoryName(name) {
  if (language === "en") return categoryTranslations[name] || name;
  return name;
}

function getCategoryName(service) {
  if (typeof service.category === "string") return service.category;
  return (service.category && typeof service.category === "object" && service.category.name) || service.category_name || "";
}

function getServiceDescription(service) {
  return String(
    service.short_description ||
    service.description ||
    getCategoryName(service) ||
    ""
  );
}

function setLanguage(next) {
  language = next;
  document.documentElement.lang = next;
  document.documentElement.dir = next === "ar" ? "rtl" : "ltr";
  document.body.dir = document.documentElement.dir;

  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.dataset.i18n;
    if (translations[language][key]) element.textContent = t(key);
  });

  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.placeholder = t(element.dataset.i18nPlaceholder);
  });

  const languageButton = $("languageBtn");
  if (languageButton) {
    languageButton.textContent = next === "ar" ? "English" : "العربية";
  }

  renderCategories();
  renderServices();
  updateCategoryHeading();
}

function getFilteredServices() {
  let result = services;

  if (selectedCategory) {
    result = result.filter(
      (service) => getCategoryName(service) === selectedCategory
    );
  }

  if (searchQuery) {
    const query = searchQuery.toLocaleLowerCase();
    result = result.filter((service) => {
      const text = [
        service.name,
        getServiceDescription(service),
        getCategoryName(service)
      ].join(" ").toLocaleLowerCase();

      const translatedCategory = displayCategoryName(
        getCategoryName(service)
      ).toLocaleLowerCase();

      return text.includes(query) || translatedCategory.includes(query);
    });
  }

  return result;
}

function renderCategories() {
  const grid = $("categoryGrid");
  if (!grid) return;

  grid.replaceChildren();

  const filteredCategories = searchQuery
    ? categories.filter((category) => {
        const name = category.name.toLocaleLowerCase();
        const translated = displayCategoryName(category.name).toLocaleLowerCase();
        return name.includes(searchQuery.toLocaleLowerCase()) ||
          translated.includes(searchQuery.toLocaleLowerCase());
      })
    : categories;

  const visibleCategories = showAllCategories || searchQuery
    ? filteredCategories
    : filteredCategories.slice(0, 4);

  const styles = [
    { color: "blue", icon: "⌘" },
    { color: "purple", icon: "▤" },
    { color: "cyan", icon: "⌁" },
    { color: "gold", icon: "◇" }
  ];

  visibleCategories.forEach((category, index) => {
    const style = styles[index % styles.length];
    const button = document.createElement("button");
    button.type = "button";
    button.className = "category-card";
    button.setAttribute("aria-pressed", String(selectedCategory === category.name));
    if (selectedCategory === category.name) {
      button.style.borderColor = "var(--teal)";
      button.style.background = "#f0fcfa";
    }

    const icon = document.createElement("span");
    icon.className = `category-icon ${style.color}`;
    icon.textContent = style.icon;

    const title = document.createElement("strong");
    title.textContent = displayCategoryName(category.name);

    const count = document.createElement("small");
    count.textContent = `${category.count} ${t("serviceCount")}`;

    button.append(icon, title, count);
    button.addEventListener("click", () => {
      selectedCategory = selectedCategory === category.name ? null : category.name;
      renderCategories();
      renderServices();
      updateCategoryHeading();

      const section = $("serviceSection");
      if (section) section.scrollIntoView({ behavior: "smooth", block: "start" });
    });

    grid.appendChild(button);
  });

  if (!visibleCategories.length) {
    const message = document.createElement("p");
    message.className = "form-message";
    message.textContent = t("noSearchResults");
    grid.appendChild(message);
  }

  const toggle = $("showAllCategories");
  if (toggle) {
    toggle.hidden = Boolean(searchQuery) || categories.length <= 4;
    toggle.textContent = showAllCategories
      ? t("showLessCategories")
      : t("showAllCategories");
  }
}

function updateCategoryHeading() {
  const label = $("selectedCategoryLabel");
  if (label) {
    label.textContent = selectedCategory
      ? displayCategoryName(selectedCategory)
      : t("allServices");
  }

  const clearButton = $("clearCategory");
  if (clearButton) clearButton.hidden = !selectedCategory;
}

function renderServices() {
  const grid = $("serviceGrid");
  const select = $("service");
  if (!grid) return;

  grid.replaceChildren();

  if (select) {
    const previousValue = select.value;
    select.replaceChildren();

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = t("chooseService");
    select.appendChild(placeholder);

    services.forEach((service) => {
      const option = document.createElement("option");
      option.value = String(service.id);
      option.textContent = service.name;
      select.appendChild(option);
    });

    if (previousValue && services.some(
      (service) => String(service.id) === previousValue
    )) {
      select.value = previousValue;
    }
  }

  const visibleServices = getFilteredServices();

  if (!visibleServices.length) {
    const message = document.createElement("p");
    message.className = "form-message";
    message.textContent = services.length ? t("noSearchResults") : t("noServices");
    grid.appendChild(message);
    return;
  }

  const styles = [
    { color: "blue", icon: "⌘" },
    { color: "purple", icon: "▤" },
    { color: "cyan", icon: "✎" },
    { color: "gold", icon: "◇" }
  ];

  visibleServices.forEach((service, index) => {
    const style = styles[index % styles.length];
    const button = document.createElement("button");
    button.type = "button";
    button.className = "service-card";
    button.dataset.service = String(service.id);

    const icon = document.createElement("span");
    icon.className = `service-icon ${style.color}`;
    icon.textContent = style.icon;

    const title = document.createElement("strong");
    title.textContent = String(service.name || "Service");

    const summary = document.createElement("small");
    summary.textContent = getServiceDescription(service);

    const arrow = document.createElement("span");
    arrow.className = "card-arrow";
    arrow.textContent = "↗";

    button.append(icon, title, summary, arrow);

    button.addEventListener("click", () => {
      if (select) select.value = String(service.id);
      const form = $("createRequest") || $("requestForm");
      if (form) form.scrollIntoView({ behavior: "smooth", block: "center" });
    });

    grid.appendChild(button);
  });
}

function buildCategories() {
  const map = new Map();

  services.forEach((service) => {
    const name = getCategoryName(service) || "أخرى";
    if (!map.has(name)) map.set(name, { name, count: 0 });
    map.get(name).count += 1;
  });

  categories = Array.from(map.values()).sort((a, b) =>
    b.count - a.count || a.name.localeCompare(b.name, "ar")
  );
}

async function loadServices() {
  const grid = $("serviceGrid");
  if (grid) {
    grid.replaceChildren();
    const loading = document.createElement("p");
    loading.className = "form-message";
    loading.textContent = t("loadingServices");
    grid.appendChild(loading);
  }

  try {
    const response = await fetch("/api/v1/public/services", {
      headers: { Accept: "application/json" }
    });

    if (!response.ok) {
      throw new Error(`Services request failed: ${response.status}`);
    }

    const data = await response.json();
    if (!Array.isArray(data.items)) {
      throw new Error("Unexpected services response format");
    }

    services = data.items.filter(
      (item) => item && item.id != null && item.name
    );

    buildCategories();
    renderCategories();
    renderServices();
    updateCategoryHeading();
  } catch (error) {
    console.error("Failed to load public services:", error);

    const message = document.createElement("p");
    message.className = "form-message";
    message.textContent = t("servicesLoadFailed");

    if (grid) {
      grid.replaceChildren();
      grid.appendChild(message);
    }

    const categoryGrid = $("categoryGrid");
    if (categoryGrid) {
      categoryGrid.replaceChildren();
      const categoryMessage = document.createElement("p");
      categoryMessage.className = "form-message";
      categoryMessage.textContent = t("servicesLoadFailed");
      categoryGrid.appendChild(categoryMessage);
    }
  }
}

function showNotice(message) {
  const formMessage = $("formMessage");
  if (formMessage) {
    formMessage.textContent = message;
    formMessage.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } else {
    window.alert(message);
  }
}


function initializeIntroScreens() {
  const overlay = document.getElementById("introScreens");
  const welcome = document.getElementById("introWelcome");
  const about = document.getElementById("introAbout");

  if (!overlay || !welcome || !about) return;

  document.body.classList.add("intro-active");

  const showAbout = () => {
    welcome.hidden = true;
    about.hidden = false;
  };

  const closeIntro = () => {
    overlay.hidden = true;
    document.body.classList.remove("intro-active");
  };

  document.getElementById("startIntro")?.addEventListener("click", showAbout);
  document.getElementById("skipIntro")?.addEventListener("click", closeIntro);
  document.getElementById("finishIntro")?.addEventListener("click", closeIntro);
}

function initializeInterface() {
  const languageButton = $("languageBtn");
  if (languageButton) {
    languageButton.addEventListener("click", () => {
      setLanguage(language === "ar" ? "en" : "ar");
    });
  }

  const toggle = $("showAllCategories");
  if (toggle) {
    toggle.addEventListener("click", () => {
      showAllCategories = !showAllCategories;
      renderCategories();
    });
  }

  const clearButton = $("clearCategory");
  if (clearButton) {
    clearButton.addEventListener("click", () => {
      selectedCategory = null;
      renderCategories();
      renderServices();
      updateCategoryHeading();
    });
  }

  const search = $("serviceSearch");
  if (search) {
    search.addEventListener("input", () => {
      searchQuery = search.value.trim();
      renderCategories();
      renderServices();
    });
  }

  const form = $("requestForm");
  if (form) {
    form.addEventListener("submit", (event) => {
      event.preventDefault();

      const service = ($("service") && $("service").value) || "";
      const details = ($("details") && $("details").value.trim()) || "";

      if (!service) {
        showNotice(t("selectServiceFirst"));
        return;
      }

      if (!details) {
        showNotice(t("enterDetails"));
        return;
      }

      showNotice(t("requestPrepared"));
    });
  }

  document.querySelectorAll("[data-account-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const action = button.dataset.accountAction;

      if (action === "language") {
        setLanguage(language === "ar" ? "en" : "ar");
      } else if (action === "profile") {
        showNotice(t("profileNotice"));
      } else if (action === "notifications") {
        showNotice(t("notificationsNotice"));
      } else if (action === "appearance") {
        showNotice(t("appearanceNotice"));
      }
    });
  });

  document.querySelectorAll(".bottom-nav .nav-item").forEach((link) => {
    link.addEventListener("click", () => {
      document.querySelectorAll(".bottom-nav .nav-item").forEach((item) => {
        item.classList.remove("active");
      });
      link.classList.add("active");
    });
  });

  initializeIntroScreens();
  setLanguage("ar");
  loadServices();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeInterface);
} else {
  initializeInterface();
}
